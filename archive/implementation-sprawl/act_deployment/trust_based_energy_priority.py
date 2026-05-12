"""
Trust-Based Energy Priority System

Integrates Sessions #30-35 trust mechanisms with energy-backed ATP.

Key Concept: Trust affects PRIORITY, not PRICE
- High trust → Work processed immediately
- Low trust → Work waits in queue
- Everyone's work eventually gets done (no exclusion)

Part of Session #36 implementation (Phase 3).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import heapq
import uuid

from energy_backed_atp import EnergyBackedSocietyPool, WorkTicket


# ============================================================================
# Trust Score Interface (Sessions #30-35 integration point)
# ============================================================================

@dataclass
class TrustScore:
    """
    Trust score for an entity.

    In full system, this comes from:
    - Session #30-32: Trust Tensor (V3)
    - Session #33: Trust-based negotiation
    - Session #34: Gaming resistance (bonds, penalties)
    - Session #35: Web of trust (transitive, vouching)

    For now, simple score with components.
    """
    lct_id: str

    # Components (0.0 to 1.0 each)
    direct_trust: float = 0.5  # Direct interaction history
    transitive_trust: float = 0.5  # Web of trust
    bond_trust: float = 0.0  # From identity bonds
    reputation_trust: float = 0.5  # From ADP work history

    # Penalties (Session #34)
    experience_penalty: float = 0.0  # Newcomer penalty (0.0 to 0.5)
    anomaly_penalty: float = 0.0  # Statistical anomaly detection (0.0 to 1.0)

    def get_combined_trust(self) -> float:
        """
        Calculate combined trust score.

        Formula integrates all Sessions #30-35 mechanisms:
        - 40% direct trust (Session #30-32)
        - 20% transitive trust (Session #35)
        - 20% bond trust (Session #34)
        - 20% reputation trust (Session #33)
        - Apply penalties (Session #34)
        """
        base = (
            0.4 * self.direct_trust +
            0.2 * self.transitive_trust +
            0.2 * self.bond_trust +
            0.2 * self.reputation_trust
        )

        # Apply penalties
        penalized = base * (1.0 - self.experience_penalty) * (1.0 - self.anomaly_penalty)

        return max(0.0, min(1.0, penalized))

    def to_dict(self) -> Dict:
        return {
            "lct_id": self.lct_id,
            "combined_trust": self.get_combined_trust(),
            "components": {
                "direct": self.direct_trust,
                "transitive": self.transitive_trust,
                "bond": self.bond_trust,
                "reputation": self.reputation_trust,
            },
            "penalties": {
                "experience": self.experience_penalty,
                "anomaly": self.anomaly_penalty,
            },
        }


# ============================================================================
# Work Request with Priority
# ============================================================================

class RequestPriority(Enum):
    """
    Priority levels for work requests.

    Based on trust score - NOT cost/price.
    """
    CRITICAL = 0  # Emergency/critical work
    HIGH = 1  # High trust entities (≥ 0.9)
    ELEVATED = 2  # Elevated trust (≥ 0.7)
    NORMAL = 3  # Normal trust (≥ 0.5)
    LOW = 4  # Low trust (≥ 0.3)
    DEFERRED = 5  # Very low trust (< 0.3)

    def __lt__(self, other):
        """Support priority queue ordering."""
        if isinstance(other, RequestPriority):
            return self.value < other.value
        return NotImplemented


@dataclass
class WorkRequest:
    """
    Request to allocate ATP for work.

    Trust score determines priority, not cost.
    """
    id: str
    requester_lct: str
    description: str
    atp_needed: float

    # Priority (from trust score)
    priority: RequestPriority
    trust_score: float

    # Timing
    submitted_at: datetime
    deadline: Optional[datetime] = None  # If time-critical

    # Status
    allocated: bool = False
    allocated_at: Optional[datetime] = None
    work_ticket_id: Optional[str] = None

    # Queue position tracking
    queue_position: int = 0

    def wait_time(self) -> timedelta:
        """How long request has been waiting."""
        end = self.allocated_at if self.allocated_at else datetime.now(timezone.utc)
        return end - self.submitted_at

    def is_past_deadline(self) -> bool:
        """Check if past deadline (if deadline set)."""
        if not self.deadline:
            return False
        return datetime.now(timezone.utc) > self.deadline

    def __lt__(self, other):
        """
        Priority queue ordering.

        Lower priority value = processed first.
        Within same priority, FIFO (earlier submission first).
        """
        if isinstance(other, WorkRequest):
            if self.priority != other.priority:
                return self.priority < other.priority
            return self.submitted_at < other.submitted_at
        return NotImplemented

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "requester_lct": self.requester_lct,
            "description": self.description,
            "atp_needed": self.atp_needed,
            "priority": self.priority.name,
            "trust_score": self.trust_score,
            "submitted_at": self.submitted_at.isoformat(),
            "allocated": self.allocated,
            "wait_time_seconds": self.wait_time().total_seconds(),
            "queue_position": self.queue_position,
        }


# ============================================================================
# Trust-Based Energy Priority Queue
# ============================================================================

@dataclass
class TrustBasedEnergyPriority:
    """
    Priority queue for ATP allocation requests.

    Integrates Sessions #30-35 trust with energy-backed ATP.

    Key Properties:
    - Trust determines queue priority (not cost)
    - High trust → immediate processing
    - Low trust → deferred but still processed
    - Everyone eventually served (no exclusion)
    """
    society_lct: str
    energy_pool: EnergyBackedSocietyPool

    # Priority queue (min-heap by priority)
    request_queue: List[WorkRequest] = field(default_factory=list)

    # Trust scores (would come from Sessions #30-35 in full system)
    trust_scores: Dict[str, TrustScore] = field(default_factory=dict)

    # Statistics
    total_requests: int = 0
    total_allocated: int = 0
    total_deferred: int = 0

    def __post_init__(self):
        """Initialize priority queue."""
        heapq.heapify(self.request_queue)

    # ========================================================================
    # Trust Score Management (Integration with Sessions #30-35)
    # ========================================================================

    def register_trust_score(self, trust_score: TrustScore):
        """
        Register trust score for entity.

        In full system, this comes from:
        - trust_tensor module (Sessions #30-32)
        - trust_negotiator module (Session #33)
        - gaming_mitigations module (Session #34)
        - web_of_trust module (Session #35)
        """
        self.trust_scores[trust_score.lct_id] = trust_score

    def get_trust_score(self, lct_id: str) -> TrustScore:
        """
        Get trust score for entity.

        Returns default score if not found (newcomer).
        """
        if lct_id in self.trust_scores:
            return self.trust_scores[lct_id]

        # Default for newcomer (Session #34: experience penalty)
        return TrustScore(
            lct_id=lct_id,
            direct_trust=0.5,
            transitive_trust=0.0,  # No web of trust yet
            bond_trust=0.0,  # No bond yet
            reputation_trust=0.0,  # No work history
            experience_penalty=0.3,  # Newcomer penalty (Session #34)
        )

    def update_trust_from_work(self, lct_id: str, quality_score: float):
        """
        Update trust based on work completion.

        Integrates with Session #34 asymmetric trust dynamics.
        """
        trust = self.get_trust_score(lct_id)

        # Update reputation trust based on quality
        if quality_score >= 0.8:
            # Good work: asymptotic recovery (Session #34)
            gap = 1.0 - trust.reputation_trust
            trust.reputation_trust += 0.01 * gap
        else:
            # Poor work: multiplicative failure (Session #34)
            trust.reputation_trust *= 0.9

        # Reduce experience penalty over time
        if trust.experience_penalty > 0:
            trust.experience_penalty = max(0.0, trust.experience_penalty - 0.05)

        self.trust_scores[lct_id] = trust

    # ========================================================================
    # Priority Calculation
    # ========================================================================

    def calculate_priority(self, trust_score: float) -> RequestPriority:
        """
        Calculate request priority from trust score.

        This is where trust affects queue position, not price.

        Trust tiers:
        - ≥ 0.9: HIGH (immediate processing)
        - ≥ 0.7: ELEVATED (fast processing)
        - ≥ 0.5: NORMAL (regular processing)
        - ≥ 0.3: LOW (slower processing)
        - < 0.3: DEFERRED (slowest, but still processed)
        """
        if trust_score >= 0.9:
            return RequestPriority.HIGH
        elif trust_score >= 0.7:
            return RequestPriority.ELEVATED
        elif trust_score >= 0.5:
            return RequestPriority.NORMAL
        elif trust_score >= 0.3:
            return RequestPriority.LOW
        else:
            return RequestPriority.DEFERRED

    # ========================================================================
    # Work Request Submission
    # ========================================================================

    def submit_work_request(
        self,
        requester_lct: str,
        description: str,
        atp_needed: float,
        deadline: Optional[datetime] = None,
        critical: bool = False
    ) -> WorkRequest:
        """
        Submit work request to priority queue.

        Args:
            requester_lct: Who is requesting work
            description: What work needs to be done
            atp_needed: How much ATP required
            deadline: Optional deadline (doesn't affect priority)
            critical: If True, override priority to CRITICAL

        Returns:
            WorkRequest (queued for processing)
        """
        # Get trust score
        trust = self.get_trust_score(requester_lct)
        trust_score = trust.get_combined_trust()

        # Calculate priority
        if critical:
            priority = RequestPriority.CRITICAL
        else:
            priority = self.calculate_priority(trust_score)

        # Create request
        request = WorkRequest(
            id=f"req-{uuid.uuid4().hex[:12]}",
            requester_lct=requester_lct,
            description=description,
            atp_needed=atp_needed,
            priority=priority,
            trust_score=trust_score,
            submitted_at=datetime.now(timezone.utc),
            deadline=deadline,
        )

        # Add to queue
        heapq.heappush(self.request_queue, request)
        self.total_requests += 1

        # Update queue positions
        self._update_queue_positions()

        return request

    # ========================================================================
    # Work Allocation Processing
    # ========================================================================

    def process_next_request(self) -> Optional[Tuple[WorkRequest, WorkTicket]]:
        """
        Process next request from queue.

        Allocates ATP to highest priority request.

        Returns:
            (WorkRequest, WorkTicket) if successful, None if queue empty or insufficient ATP
        """
        if not self.request_queue:
            return None

        # Get highest priority request
        request = heapq.heappop(self.request_queue)

        # Try to allocate ATP
        ticket = self.energy_pool.allocate_atp_to_work(
            worker_lct=request.requester_lct,
            description=request.description,
            atp_amount=request.atp_needed,
        )

        if not ticket:
            # Insufficient ATP - requeue
            heapq.heappush(self.request_queue, request)
            self.total_deferred += 1
            return None

        # Success - mark request as allocated
        request.allocated = True
        request.allocated_at = datetime.now(timezone.utc)
        request.work_ticket_id = ticket.id

        self.total_allocated += 1

        # Update queue positions
        self._update_queue_positions()

        return (request, ticket)

    def process_all_available(self) -> List[Tuple[WorkRequest, WorkTicket]]:
        """
        Process all requests that can be satisfied with available ATP.

        Returns list of (request, ticket) pairs.
        """
        allocated = []

        while True:
            result = self.process_next_request()
            if not result:
                break
            allocated.append(result)

        return allocated

    # ========================================================================
    # Queue Management
    # ========================================================================

    def _update_queue_positions(self):
        """Update queue positions for all requests."""
        # Sort queue to get positions
        sorted_queue = sorted(self.request_queue)
        for i, request in enumerate(sorted_queue):
            request.queue_position = i + 1

    def get_queue_status(self) -> Dict:
        """Get status of request queue."""
        # Count by priority
        priority_counts = {}
        for request in self.request_queue:
            priority = request.priority.name
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Average wait time
        if self.request_queue:
            avg_wait = sum(r.wait_time().total_seconds() for r in self.request_queue) / len(self.request_queue)
        else:
            avg_wait = 0.0

        return {
            "queue_length": len(self.request_queue),
            "priority_counts": priority_counts,
            "average_wait_seconds": avg_wait,
            "total_requests": self.total_requests,
            "total_allocated": self.total_allocated,
            "total_deferred": self.total_deferred,
            "allocation_rate": self.total_allocated / max(1, self.total_requests),
        }

    # ========================================================================
    # Integration Testing Helpers
    # ========================================================================

    def simulate_work_completion(self, ticket_id: str, quality_score: float) -> bool:
        """
        Simulate work completion for testing.

        In full system, this comes from actual work execution.
        """
        # Complete work in pool
        adp = self.energy_pool.complete_work(ticket_id, quality_score)
        if not adp:
            return False

        # Update trust based on quality
        self.update_trust_from_work(adp.worker_lct, quality_score)

        # Credit reputation (would integrate with Sessions #30-35)
        reputation_earned = adp.amount * quality_score
        self.energy_pool.credit_worker_reputation(adp.id, reputation_earned)

        return True

    def to_dict(self) -> Dict:
        """Serialize priority system to dictionary."""
        return {
            "society_lct": self.society_lct,
            "queue_status": self.get_queue_status(),
            "energy_pool": self.energy_pool.get_stats(),
            "trust_scores": {
                lct: score.to_dict()
                for lct, score in list(self.trust_scores.items())[:10]  # First 10
            },
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    from energy_backed_atp import EnergyBackedSocietyPool
    from energy_capacity import SolarPanelProof, ComputeResourceProof
    import time

    print("Trust-Based Energy Priority System - Example Usage\n")
    print("=" * 70)

    # Create energy pool
    pool = EnergyBackedSocietyPool(society_lct="lct-society-test")

    # Add energy sources
    solar = SolarPanelProof(
        panel_serial="SOLAR-001",
        rated_watts=1000.0,  # Larger panel
        panel_model="Test Panel",
        installation_date=datetime.now(timezone.utc),
        last_verified=datetime.now(timezone.utc),
    )
    pool.register_energy_source(solar)

    gpu = ComputeResourceProof(
        device_type="gpu",
        device_model="RTX4090",
        device_id="GPU-001",
        tdp_watts=450.0,
        last_verified=datetime.now(timezone.utc),
        utilization_factor=0.8,
        idle_power_watts=50.0,
    )
    pool.register_energy_source(gpu)

    # Initialize with ADP
    pool.adp_pool = 2000.0

    # Charge ATP (within capacity: 1000W solar + 370W GPU = 1370W total)
    pool.charge_atp(600.0, solar.source_identifier)

    print(f"Energy Pool: {pool.get_available_atp()} ATP available")

    # Create priority system
    priority = TrustBasedEnergyPriority(
        society_lct=pool.society_lct,
        energy_pool=pool
    )

    print("\n1. Register Trust Scores")
    print("-" * 70)

    # High trust entity (established, bonded)
    priority.register_trust_score(TrustScore(
        lct_id="lct-agent-alice",
        direct_trust=0.95,
        transitive_trust=0.9,
        bond_trust=1.0,
        reputation_trust=0.9,
        experience_penalty=0.0,
    ))
    print("  ✓ Alice (high trust: 0.94)")

    # Medium trust entity
    priority.register_trust_score(TrustScore(
        lct_id="lct-agent-bob",
        direct_trust=0.6,
        transitive_trust=0.5,
        bond_trust=0.5,
        reputation_trust=0.6,
        experience_penalty=0.0,
    ))
    print("  ✓ Bob (medium trust: 0.58)")

    # Low trust entity (newcomer)
    priority.register_trust_score(TrustScore(
        lct_id="lct-agent-charlie",
        direct_trust=0.5,
        transitive_trust=0.0,
        bond_trust=0.0,
        reputation_trust=0.0,
        experience_penalty=0.3,  # Newcomer penalty
    ))
    print("  ✓ Charlie (low trust: 0.07, newcomer)")

    print("\n2. Submit Work Requests (Different Trust Levels)")
    print("-" * 70)

    # Charlie submits first (but low trust)
    req_charlie = priority.submit_work_request(
        requester_lct="lct-agent-charlie",
        description="Charlie's task",
        atp_needed=200.0,
    )
    print(f"  → Charlie submitted (trust: {req_charlie.trust_score:.2f}, priority: {req_charlie.priority.name})")
    time.sleep(0.1)  # Small delay to ensure different timestamps

    # Bob submits second (medium trust)
    req_bob = priority.submit_work_request(
        requester_lct="lct-agent-bob",
        description="Bob's task",
        atp_needed=200.0,
    )
    print(f"  → Bob submitted (trust: {req_bob.trust_score:.2f}, priority: {req_bob.priority.name})")
    time.sleep(0.1)

    # Alice submits last (but high trust)
    req_alice = priority.submit_work_request(
        requester_lct="lct-agent-alice",
        description="Alice's task",
        atp_needed=200.0,
    )
    print(f"  → Alice submitted (trust: {req_alice.trust_score:.2f}, priority: {req_alice.priority.name})")

    print("\n3. Process Queue (Priority Order)")
    print("-" * 70)

    # Process all available
    allocated = priority.process_all_available()

    print(f"  Processed {len(allocated)} requests:")
    for i, (request, ticket) in enumerate(allocated):
        print(f"    {i+1}. {request.requester_lct.split('-')[-1]} "
              f"(trust: {request.trust_score:.2f}, "
              f"priority: {request.priority.name}, "
              f"wait: {request.wait_time().total_seconds():.1f}s)")

    print("\n4. Complete Work & Update Trust")
    print("-" * 70)

    for request, ticket in allocated:
        # Simulate work completion
        quality = 0.95 if "alice" in request.requester_lct else 0.85
        priority.simulate_work_completion(ticket.id, quality)

        # Get updated trust
        updated_trust = priority.get_trust_score(request.requester_lct)
        print(f"  ✓ {request.requester_lct.split('-')[-1]}: "
              f"quality={quality:.2f}, "
              f"new_trust={updated_trust.get_combined_trust():.2f}")

    print("\n5. Queue Status")
    print("-" * 70)

    status = priority.get_queue_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("✅ Trust-based energy priority system operational")
    print("\nKey Insights:")
    print("  - Trust determines queue priority, not cost")
    print("  - High trust entities processed first")
    print("  - Low trust entities still served (deferred)")
    print("  - Trust updates from work quality (Session #34 asymmetric dynamics)")
    print("  - Newcomers face experience penalty (Session #34)")
