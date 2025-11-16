"""
Energy-Backed ATP/ADP System

Implements ATP as energy flow (not currency) with:
- ATP charging backed by real energy capacity
- ATP expiration (prevents hoarding)
- ATP discharge to ADP via work
- ADP return to pool for reputation credit

Part of Session #36 implementation (Phase 2).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from enum import Enum
import uuid

from energy_capacity import (
    EnergyCapacityProof,
    EnergyCapacityRegistry,
    EnergyCapacityValidator,
)


# ============================================================================
# Charged ATP with Expiration
# ============================================================================

@dataclass
class ChargedATP:
    """
    ATP backed by real energy with expiration.

    This is NOT currency - it's charged energy allocation that:
    - Expires if not used (like battery discharge)
    - Can only be created with energy proof
    - Discharges to ADP when work is done
    """
    id: str
    amount: float
    charged_at: datetime
    expiration: datetime
    energy_source_identifier: str  # Which energy source backed this
    society_lct: str

    # Optional metadata
    charging_context: Optional[str] = None  # Why/when charged

    def is_expired(self) -> bool:
        """Check if ATP has expired."""
        return datetime.now(timezone.utc) > self.expiration

    def remaining_lifetime(self) -> timedelta:
        """Time until expiration."""
        remaining = self.expiration - datetime.now(timezone.utc)
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    def lifetime_fraction_remaining(self) -> float:
        """
        Fraction of lifetime remaining (0.0 to 1.0).

        1.0 = just charged
        0.5 = half life remaining
        0.0 = expired
        """
        total_lifetime = self.expiration - self.charged_at
        remaining = self.remaining_lifetime()

        if total_lifetime.total_seconds() <= 0:
            return 0.0

        return max(0.0, remaining.total_seconds() / total_lifetime.total_seconds())

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "charged_at": self.charged_at.isoformat(),
            "expiration": self.expiration.isoformat(),
            "energy_source_identifier": self.energy_source_identifier,
            "society_lct": self.society_lct,
            "is_expired": self.is_expired(),
            "remaining_lifetime_seconds": self.remaining_lifetime().total_seconds(),
            "lifetime_fraction_remaining": self.lifetime_fraction_remaining(),
        }


# ============================================================================
# Work Ticket (ATP allocated to work, not yet discharged)
# ============================================================================

class WorkStatus(Enum):
    """Status of work ticket."""
    ALLOCATED = "allocated"  # ATP reserved, work not started
    IN_PROGRESS = "in_progress"  # Work being performed
    COMPLETED = "completed"  # Work done, ATP discharged to ADP
    FAILED = "failed"  # Work failed, ATP returned to pool
    EXPIRED = "expired"  # Work took too long, ATP expired


@dataclass
class WorkTicket:
    """
    ATP allocated to specific work.

    ATP is reserved (removed from pool) but not yet discharged.
    Work completion discharges ATP → ADP.
    """
    id: str
    society_lct: str
    worker_lct: str
    description: str

    # ATP allocation
    atp_allocated: float
    atp_batch_ids: List[str]  # Which ChargedATP batches used

    # Status
    status: WorkStatus
    allocated_at: datetime
    deadline: datetime

    # Results (filled when completed)
    completed_at: Optional[datetime] = None
    quality_score: float = 0.0  # 0.0 to 1.0
    adp_generated: float = 0.0

    def is_expired(self) -> bool:
        """Check if work deadline expired."""
        return datetime.now(timezone.utc) > self.deadline

    def duration(self) -> timedelta:
        """How long work has been running."""
        end = self.completed_at if self.completed_at else datetime.now(timezone.utc)
        return end - self.allocated_at

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "society_lct": self.society_lct,
            "worker_lct": self.worker_lct,
            "description": self.description,
            "atp_allocated": self.atp_allocated,
            "atp_batch_count": len(self.atp_batch_ids),
            "status": self.status.value,
            "allocated_at": self.allocated_at.isoformat(),
            "deadline": self.deadline.isoformat(),
            "is_expired": self.is_expired(),
            "duration_seconds": self.duration().total_seconds(),
            "quality_score": self.quality_score,
            "adp_generated": self.adp_generated,
        }


# ============================================================================
# Discharged ADP (result of work)
# ============================================================================

@dataclass
class DischargedADP:
    """
    ADP token created when ATP is discharged via work.

    ADP represents:
    - Proof that work was done
    - Energy that was spent
    - Reputation credit for worker
    """
    id: str
    amount: float
    work_ticket_id: str
    worker_lct: str
    society_lct: str

    created_at: datetime
    quality_score: float  # Work quality (affects reputation)

    # Link to original ATP (for audit trail)
    original_atp_batch_ids: List[str]

    # Reputation tracking (from Session #33-35)
    reputation_credited: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "work_ticket_id": self.work_ticket_id,
            "worker_lct": self.worker_lct,
            "society_lct": self.society_lct,
            "created_at": self.created_at.isoformat(),
            "quality_score": self.quality_score,
            "original_atp_count": len(self.original_atp_batch_ids),
            "reputation_credited": self.reputation_credited,
        }


# ============================================================================
# Energy-Backed Society Pool
# ============================================================================

@dataclass
class EnergyBackedSocietyPool:
    """
    Society's ATP/ADP pool backed by real energy.

    ATP = Charged energy (can do work)
    ADP = Discharged energy (reputation credit)

    Key properties:
    - ATP expires (can't hoard)
    - ATP requires energy proof to charge
    - ATP → ADP via work only
    - ADP can be recharged to ATP (with new energy)
    """
    society_lct: str

    # Energy backing
    energy_registry: EnergyCapacityRegistry = field(
        default_factory=lambda: EnergyCapacityRegistry(society_lct="")
    )

    # ATP pool (charged energy)
    charged_atp_batches: List[ChargedATP] = field(default_factory=list)

    # ADP pool (discharged energy, available for reputation/recharging)
    adp_pool: float = 0.0

    # Work tracking
    active_work: List[WorkTicket] = field(default_factory=list)
    completed_work: List[WorkTicket] = field(default_factory=list)

    # ADP tokens (detailed tracking)
    adp_tokens: List[DischargedADP] = field(default_factory=list)

    # Configuration
    default_atp_lifetime_days: int = 7
    default_work_deadline_hours: int = 24

    def __post_init__(self):
        """Initialize energy registry with society LCT."""
        self.energy_registry = EnergyCapacityRegistry(society_lct=self.society_lct)

    # ========================================================================
    # Energy Capacity Management
    # ========================================================================

    def register_energy_source(self, proof: EnergyCapacityProof) -> bool:
        """Register new energy source backing this pool."""
        return self.energy_registry.register_source(proof)

    def get_total_energy_capacity(self) -> float:
        """Total energy capacity from all valid sources."""
        return self.energy_registry.get_total_capacity()

    def get_energy_sources(self) -> List[EnergyCapacityProof]:
        """Get all valid energy sources."""
        return self.energy_registry.get_valid_sources()

    # ========================================================================
    # ATP Charging (ADP → ATP with energy proof)
    # ========================================================================

    def charge_atp(
        self,
        amount: float,
        energy_source_identifier: str,
        lifetime_days: Optional[int] = None,
        context: Optional[str] = None
    ) -> Optional[ChargedATP]:
        """
        Charge ADP to ATP backed by energy source.

        Args:
            amount: How much ATP to charge
            energy_source_identifier: Which energy source backs this
            lifetime_days: How long ATP lasts (default: 7 days)
            context: Optional context for why charging

        Returns:
            ChargedATP if successful, None if insufficient capacity/ADP
        """
        # Validate we have enough ADP to charge
        if amount > self.adp_pool:
            return None

        # Find energy source
        source = self.energy_registry.find_source(energy_source_identifier)
        if not source:
            return None

        # Validate energy source
        validator = EnergyCapacityValidator()
        if not validator.validate_proof(source):
            return None

        # Check if we have capacity
        # Note: This is simplified - real system would track allocated vs total capacity
        total_capacity = self.get_total_energy_capacity()
        current_allocation = self.get_available_atp()

        if current_allocation + amount > total_capacity:
            return None  # Insufficient capacity

        # Charge ATP
        lifetime = timedelta(days=lifetime_days or self.default_atp_lifetime_days)
        now = datetime.now(timezone.utc)

        charged = ChargedATP(
            id=f"atp-{uuid.uuid4().hex[:12]}",
            amount=amount,
            charged_at=now,
            expiration=now + lifetime,
            energy_source_identifier=energy_source_identifier,
            society_lct=self.society_lct,
            charging_context=context,
        )

        # Update pools
        self.adp_pool -= amount
        self.charged_atp_batches.append(charged)

        return charged

    # ========================================================================
    # ATP Queries
    # ========================================================================

    def get_available_atp(self) -> float:
        """Get total available (non-expired) ATP."""
        total = 0.0
        for batch in self.charged_atp_batches:
            if not batch.is_expired():
                total += batch.amount
        return total

    def get_valid_atp_batches(self) -> List[ChargedATP]:
        """Get all non-expired ATP batches."""
        return [b for b in self.charged_atp_batches if not b.is_expired()]

    def cleanup_expired_atp(self) -> float:
        """
        Remove expired ATP batches.

        This is energy waste - ATP that was charged but never used.
        Returns amount of ATP that expired.
        """
        expired = [b for b in self.charged_atp_batches if b.is_expired()]
        expired_amount = sum(b.amount for b in expired)

        for batch in expired:
            self.charged_atp_batches.remove(batch)

        return expired_amount

    # ========================================================================
    # Work Allocation (ATP reserved for work)
    # ========================================================================

    def allocate_atp_to_work(
        self,
        worker_lct: str,
        description: str,
        atp_amount: float,
        deadline_hours: Optional[int] = None
    ) -> Optional[WorkTicket]:
        """
        Allocate ATP to work task.

        ATP is removed from pool and reserved for this work.
        Work completion will discharge ATP → ADP.

        Returns:
            WorkTicket if successful, None if insufficient ATP
        """
        # Check available ATP
        if atp_amount > self.get_available_atp():
            return None

        # Allocate from oldest batches first (FIFO)
        batches_to_use = []
        remaining = atp_amount

        for batch in sorted(self.charged_atp_batches, key=lambda b: b.charged_at):
            if batch.is_expired():
                continue
            if remaining <= 0:
                break

            # Use this batch (partial or full)
            use_amount = min(remaining, batch.amount)
            batches_to_use.append((batch.id, use_amount))
            remaining -= use_amount

        if remaining > 0:
            return None  # Couldn't allocate enough (shouldn't happen given check above)

        # Create work ticket
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=deadline_hours or self.default_work_deadline_hours)

        ticket = WorkTicket(
            id=f"work-{uuid.uuid4().hex[:12]}",
            society_lct=self.society_lct,
            worker_lct=worker_lct,
            description=description,
            atp_allocated=atp_amount,
            atp_batch_ids=[b[0] for b in batches_to_use],
            status=WorkStatus.ALLOCATED,
            allocated_at=now,
            deadline=deadline,
        )

        # Deduct ATP from batches
        for batch_id, use_amount in batches_to_use:
            for batch in self.charged_atp_batches:
                if batch.id == batch_id:
                    batch.amount -= use_amount
                    if batch.amount <= 0:
                        self.charged_atp_batches.remove(batch)
                    break

        self.active_work.append(ticket)
        return ticket

    # ========================================================================
    # Work Completion (ATP → ADP discharge)
    # ========================================================================

    def complete_work(
        self,
        ticket_id: str,
        quality_score: float
    ) -> Optional[DischargedADP]:
        """
        Complete work, discharging ATP to ADP.

        This is the ONLY way ATP becomes ADP - through work.

        Args:
            ticket_id: Work ticket ID
            quality_score: Quality of work (0.0 to 1.0)

        Returns:
            DischargedADP if successful, None if ticket not found
        """
        # Find ticket
        ticket = None
        for t in self.active_work:
            if t.id == ticket_id:
                ticket = t
                break

        if not ticket:
            return None

        # Update ticket
        now = datetime.now(timezone.utc)
        ticket.status = WorkStatus.COMPLETED
        ticket.completed_at = now
        ticket.quality_score = quality_score
        ticket.adp_generated = ticket.atp_allocated

        # Create ADP token
        adp = DischargedADP(
            id=f"adp-{uuid.uuid4().hex[:12]}",
            amount=ticket.atp_allocated,
            work_ticket_id=ticket.id,
            worker_lct=ticket.worker_lct,
            society_lct=self.society_lct,
            created_at=now,
            quality_score=quality_score,
            original_atp_batch_ids=ticket.atp_batch_ids,
        )

        # Update pools
        self.adp_pool += ticket.atp_allocated
        self.adp_tokens.append(adp)

        # Move ticket to completed
        self.active_work.remove(ticket)
        self.completed_work.append(ticket)

        return adp

    def fail_work(self, ticket_id: str) -> bool:
        """
        Mark work as failed.

        ATP returns to pool (recharged with original energy backing).
        No ADP generated.
        """
        # Find ticket
        ticket = None
        for t in self.active_work:
            if t.id == ticket_id:
                ticket = t
                break

        if not ticket:
            return False

        # Return ATP to pool
        # Note: In real system, would track which batches to return to
        # For simplicity, just add back as ADP (can be recharged)
        self.adp_pool += ticket.atp_allocated

        # Update ticket
        ticket.status = WorkStatus.FAILED
        ticket.completed_at = datetime.now(timezone.utc)

        # Move to completed (as failed)
        self.active_work.remove(ticket)
        self.completed_work.append(ticket)

        return True

    # ========================================================================
    # Reputation Integration (Session #33-35)
    # ========================================================================

    def credit_worker_reputation(
        self,
        adp_id: str,
        reputation_delta: float
    ) -> bool:
        """
        Credit worker reputation for ADP.

        This is where Session #33-35 trust systems integrate.
        ADP amount × quality_score = reputation earned.

        In full system, this would:
        - Update trust tensor (Session #30-32)
        - Update trust-based negotiator (Session #33)
        - Update web of trust (Session #35)

        For now, just marks ADP as credited.
        """
        # Find ADP token
        for adp in self.adp_tokens:
            if adp.id == adp_id:
                if adp.reputation_credited:
                    return False  # Already credited

                adp.reputation_credited = True

                # In full system, would call:
                # self.trust_tensor.update_trust(adp.worker_lct, reputation_delta)
                # self.web_of_trust.record_success(adp.worker_lct)

                return True

        return False

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_stats(self) -> Dict:
        """Get pool statistics."""
        return {
            "society_lct": self.society_lct,
            "energy_capacity_watts": self.get_total_energy_capacity(),
            "energy_sources_count": len(self.get_energy_sources()),
            "available_atp": self.get_available_atp(),
            "adp_pool": self.adp_pool,
            "atp_batches_count": len(self.get_valid_atp_batches()),
            "active_work_count": len(self.active_work),
            "completed_work_count": len(self.completed_work),
            "adp_tokens_count": len(self.adp_tokens),
            "reputation_credited_count": sum(1 for adp in self.adp_tokens if adp.reputation_credited),
        }

    def to_dict(self) -> Dict:
        """Serialize pool to dictionary."""
        return {
            "stats": self.get_stats(),
            "energy_sources": self.energy_registry.to_dict(),
            "atp_batches": [b.to_dict() for b in self.get_valid_atp_batches()],
            "active_work": [t.to_dict() for t in self.active_work],
            "adp_tokens_recent": [a.to_dict() for a in self.adp_tokens[-10:]],  # Last 10
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    from energy_capacity import (
        SolarPanelProof,
        ComputeResourceProof,
        GridConnectionProof,
    )

    print("Energy-Backed ATP/ADP System - Example Usage\n")
    print("=" * 70)

    # Create society pool
    pool = EnergyBackedSocietyPool(society_lct="lct-society-sage-123")

    print("\n1. Register Energy Sources")
    print("-" * 70)

    # Solar panel
    solar = SolarPanelProof(
        panel_serial="SOLAR-001",
        rated_watts=300.0,
        panel_model="SunPower 300W",
        installation_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        last_verified=datetime.now(timezone.utc),
        degradation_factor=0.95,
    )
    pool.register_energy_source(solar)
    print(f"  ✓ Solar panel: {solar.capacity_watts}W")

    # GPU compute
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
    print(f"  ✓ GPU: {gpu.capacity_watts}W")

    # Grid
    grid = GridConnectionProof(
        meter_id="METER-001",
        allocated_watts=1000.0,
        utility_provider="PG&E",
        account_number="ACCT-123",
        last_verified=datetime.now(timezone.utc),
    )
    pool.register_energy_source(grid)
    print(f"  ✓ Grid: {grid.capacity_watts}W")

    print(f"\n  Total Capacity: {pool.get_total_energy_capacity()}W")

    # Initialize pool with some ADP
    pool.adp_pool = 1000.0
    print(f"\n  Initial ADP Pool: {pool.adp_pool}")

    print("\n2. Charge ATP from Energy Sources")
    print("-" * 70)

    # Charge 500 ATP from solar
    atp1 = pool.charge_atp(
        amount=500.0,
        energy_source_identifier=solar.source_identifier,
        context="Morning solar charging"
    )
    print(f"  ✓ Charged 500 ATP from solar")
    print(f"    Expires: {atp1.expiration}")
    print(f"    Lifetime: {atp1.default_atp_lifetime_days if hasattr(atp1, 'default_atp_lifetime_days') else 7} days")

    # Charge 300 ATP from GPU
    atp2 = pool.charge_atp(
        amount=300.0,
        energy_source_identifier=gpu.source_identifier,
        context="Compute allocation"
    )
    print(f"  ✓ Charged 300 ATP from GPU")

    print(f"\n  Available ATP: {pool.get_available_atp()}")
    print(f"  ADP Pool: {pool.adp_pool}")

    print("\n3. Allocate ATP to Work")
    print("-" * 70)

    # Allocate ATP to work
    ticket = pool.allocate_atp_to_work(
        worker_lct="lct-agent-worker-001",
        description="Process tax forms batch #42",
        atp_amount=200.0,
        deadline_hours=4
    )
    print(f"  ✓ Allocated 200 ATP to work")
    print(f"    Worker: {ticket.worker_lct}")
    print(f"    Deadline: {ticket.deadline}")

    print(f"\n  Available ATP: {pool.get_available_atp()}")
    print(f"  Active Work: {len(pool.active_work)}")

    print("\n4. Complete Work (Discharge ATP → ADP)")
    print("-" * 70)

    # Complete work
    adp = pool.complete_work(
        ticket_id=ticket.id,
        quality_score=0.95  # 95% quality
    )
    print(f"  ✓ Work completed")
    print(f"    ADP Generated: {adp.amount}")
    print(f"    Quality Score: {adp.quality_score}")

    print(f"\n  Available ATP: {pool.get_available_atp()}")
    print(f"  ADP Pool: {pool.adp_pool}")

    print("\n5. Credit Reputation")
    print("-" * 70)

    # Credit reputation (would integrate with Sessions #30-35)
    reputation_earned = adp.amount * adp.quality_score
    pool.credit_worker_reputation(
        adp_id=adp.id,
        reputation_delta=reputation_earned
    )
    print(f"  ✓ Reputation credited: {reputation_earned}")
    print(f"    Worker: {adp.worker_lct}")

    print("\n6. Pool Statistics")
    print("-" * 70)

    stats = pool.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("✅ Energy-backed ATP/ADP system operational")
    print("\nKey Insights:")
    print("  - ATP backed by real energy sources")
    print("  - ATP expires (prevents hoarding)")
    print("  - ATP → ADP only via work")
    print("  - ADP can be recharged to ATP (with new energy)")
    print("  - System enforces thermodynamic constraints")
