"""
Energy-Backed Identity Bond

Adapts Session #34's IdentityBond to work with energy-backed ATP.

Key Changes from Session #34:
- OLD: Stake ATP currency (can be reclaimed)
- NEW: Commit energy capacity (must be maintained)
- OLD: Forfeit ATP (money seized)
- NEW: Forfeit reputation (trust score reduced)
- OLD: Bonds as economic barrier
- NEW: Bonds as capacity commitment proof

Part of Session #36 implementation (Phase 4).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum

from energy_capacity import EnergyCapacityProof, EnergyCapacityRegistry


# ============================================================================
# Bond Status
# ============================================================================

class BondStatus(Enum):
    """Status of identity bond."""
    ACTIVE = "active"  # Bond active, capacity maintained
    FULFILLED = "fulfilled"  # Lock period complete, bond released
    VIOLATED = "violated"  # Capacity not maintained
    ABANDONED = "abandoned"  # Identity abandoned early


# ============================================================================
# Energy-Backed Identity Bond
# ============================================================================

@dataclass
class EnergyBackedIdentityBond:
    """
    Identity bond backed by energy capacity commitment.

    Session #34 Design:
    - Stake 1,000 ATP currency
    - Lock for 30 days
    - Forfeit if abandoned early

    Session #36 Design:
    - Commit X watts of energy capacity
    - Prove capacity exists (energy sources)
    - Maintain capacity for 30 days
    - Forfeit REPUTATION if capacity drops or identity abandoned

    Why This Works:
    - Sybil attacks: Must prove real energy capacity (can't fake)
    - Reputation washing: Forfeit hard-earned reputation
    - Identity value: Capacity commitment shows serious participation
    """
    society_lct: str
    created_at: datetime

    # Energy capacity commitment (replaces ATP stake)
    committed_capacity_watts: float
    energy_sources: List[str] = field(default_factory=list)  # Source identifiers

    # Lock period
    lock_period_days: int = 30

    # Status
    status: BondStatus = BondStatus.ACTIVE

    # Reputation at risk (forfeit if violated)
    reputation_at_risk: float = 0.5  # 50% trust score reduction

    # Tracking
    last_verified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    violations: List[str] = field(default_factory=list)

    def age_days(self) -> int:
        """Calculate bond age in days."""
        age = datetime.now(timezone.utc) - self.created_at
        return age.days

    def is_lock_expired(self) -> bool:
        """Check if lock period has expired."""
        return self.age_days() >= self.lock_period_days

    def time_remaining(self) -> timedelta:
        """Time remaining in lock period."""
        if self.is_lock_expired():
            return timedelta(0)
        expiration = self.created_at + timedelta(days=self.lock_period_days)
        return expiration - datetime.now(timezone.utc)

    def validate_capacity(
        self,
        energy_registry: EnergyCapacityRegistry
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that committed energy capacity still exists.

        Returns: (is_valid, violation_reason)
        """
        # Get current capacity from energy sources
        current_capacity = 0.0
        invalid_sources = []

        for source_id in self.energy_sources:
            source = energy_registry.find_source(source_id)
            if not source:
                invalid_sources.append(source_id)
                continue

            if not source.is_valid():
                invalid_sources.append(source_id)
                continue

            current_capacity += source.capacity_watts

        # Check if capacity maintained
        if current_capacity < self.committed_capacity_watts:
            reason = (
                f"Capacity dropped below commitment: "
                f"{current_capacity:.0f}W < {self.committed_capacity_watts:.0f}W"
            )
            if invalid_sources:
                reason += f" (invalid sources: {', '.join(invalid_sources)})"
            return (False, reason)

        if invalid_sources:
            reason = f"Invalid energy sources: {', '.join(invalid_sources)}"
            return (False, reason)

        # Update verification timestamp
        self.last_verified = datetime.now(timezone.utc)

        return (True, None)

    def handle_violation(self, reason: str) -> float:
        """
        Handle capacity violation.

        Returns reputation penalty to apply.
        """
        if self.status == BondStatus.VIOLATED:
            return 0.0  # Already violated

        self.status = BondStatus.VIOLATED
        self.violations.append(f"{datetime.now(timezone.utc).isoformat()}: {reason}")

        return self.reputation_at_risk

    def abandon_identity(self) -> float:
        """
        Abandon identity before lock period ends.

        Returns reputation penalty to apply.
        """
        if self.status != BondStatus.ACTIVE:
            return 0.0  # Already resolved

        if self.is_lock_expired():
            # Lock expired - no penalty for leaving
            self.status = BondStatus.FULFILLED
            return 0.0

        # Abandoning early - forfeit reputation
        self.status = BondStatus.ABANDONED
        self.violations.append(f"{datetime.now(timezone.utc).isoformat()}: Abandoned early")

        return self.reputation_at_risk

    def fulfill_bond(self, current_trust_score: float) -> Tuple[bool, str]:
        """
        Fulfill bond after lock period with good standing.

        Args:
            current_trust_score: Current trust score

        Returns:
            (success, message)
        """
        if self.status == BondStatus.FULFILLED:
            return (False, "Bond already fulfilled")

        if self.status == BondStatus.VIOLATED:
            return (False, "Bond violated - cannot fulfill")

        if self.status == BondStatus.ABANDONED:
            return (False, "Bond abandoned - cannot fulfill")

        if not self.is_lock_expired():
            return (
                False,
                f"Lock period not expired (age: {self.age_days()} days, "
                f"need: {self.lock_period_days} days)"
            )

        # Require minimum trust to fulfill
        min_trust = 0.6
        if current_trust_score < min_trust:
            return (
                False,
                f"Trust too low to fulfill bond (current: {current_trust_score:.2f}, "
                f"minimum: {min_trust})"
            )

        # Success - bond fulfilled
        self.status = BondStatus.FULFILLED
        return (True, "Bond fulfilled successfully")

    def to_dict(self) -> Dict:
        return {
            "society_lct": self.society_lct,
            "committed_capacity_watts": self.committed_capacity_watts,
            "energy_source_count": len(self.energy_sources),
            "age_days": self.age_days(),
            "lock_period_days": self.lock_period_days,
            "is_lock_expired": self.is_lock_expired(),
            "status": self.status.value,
            "reputation_at_risk": self.reputation_at_risk,
            "last_verified": self.last_verified.isoformat(),
            "violations_count": len(self.violations),
        }


# ============================================================================
# Energy-Backed Vouching System (Session #35 adaptation)
# ============================================================================

@dataclass
class EnergyBackedVouch:
    """
    Vouch for newcomer by committing energy allocation.

    Session #35 Design:
    - Stake 200 ATP currency for newcomer
    - Lose stake if newcomer fails

    Session #36 Design:
    - Commit portion of energy budget to newcomer
    - Sponsor newcomer's ATP needs during bootstrap
    - Forfeit REPUTATION if newcomer violates trust

    Why This Works:
    - Vouchers have skin in game (reputation at risk)
    - Newcomers get real energy to bootstrap
    - Sybil attacks: Can't vouch without real capacity
    """
    voucher_lct: str
    newcomer_lct: str
    created_at: datetime

    # Energy allocation commitment (portion of voucher's budget)
    allocated_energy_watts: float
    bootstrap_period_days: int = 30

    # Reputation at risk
    reputation_at_risk: float = 0.3  # 30% penalty if newcomer fails

    # Status
    active: bool = True
    successful: bool = False
    violated: bool = False

    # Tracking
    energy_allocated_total: float = 0.0  # How much energy given to newcomer
    newcomer_violations: List[str] = field(default_factory=list)

    def age_days(self) -> int:
        """Age of vouch in days."""
        age = datetime.now(timezone.utc) - self.created_at
        return age.days

    def is_bootstrap_complete(self) -> bool:
        """Check if bootstrap period ended."""
        return self.age_days() >= self.bootstrap_period_days

    def can_allocate_energy(self, amount: float) -> bool:
        """Check if can allocate more energy to newcomer."""
        if not self.active:
            return False
        if self.is_bootstrap_complete():
            return False
        # Could add budget checks here
        return True

    def record_energy_allocation(self, amount: float):
        """Record energy allocated to newcomer."""
        self.energy_allocated_total += amount

    def record_newcomer_violation(self, violation: str) -> float:
        """
        Record newcomer violation.

        Returns reputation penalty for voucher.
        """
        if self.violated:
            return 0.0  # Already violated

        self.violated = True
        self.active = False
        self.newcomer_violations.append(f"{datetime.now(timezone.utc).isoformat()}: {violation}")

        return self.reputation_at_risk

    def complete_vouch(self, newcomer_established: bool) -> Tuple[bool, float]:
        """
        Complete vouching period.

        Args:
            newcomer_established: Did newcomer establish themselves?

        Returns:
            (success, reputation_penalty)
        """
        if not self.active:
            return (False, 0.0)

        self.active = False

        if newcomer_established:
            # Success - no penalty
            self.successful = True
            return (True, 0.0)
        else:
            # Failure - voucher loses reputation
            self.violated = True
            return (False, self.reputation_at_risk)

    def to_dict(self) -> Dict:
        return {
            "voucher_lct": self.voucher_lct,
            "newcomer_lct": self.newcomer_lct,
            "allocated_energy_watts": self.allocated_energy_watts,
            "energy_allocated_total": self.energy_allocated_total,
            "age_days": self.age_days(),
            "bootstrap_period_days": self.bootstrap_period_days,
            "is_bootstrap_complete": self.is_bootstrap_complete(),
            "active": self.active,
            "successful": self.successful,
            "violated": self.violated,
            "reputation_at_risk": self.reputation_at_risk,
            "violations_count": len(self.newcomer_violations),
        }


# ============================================================================
# Bond Registry
# ============================================================================

@dataclass
class EnergyBackedBondRegistry:
    """
    Registry of energy-backed identity bonds.

    Tracks all bonds and vouching relationships.
    """
    bonds: Dict[str, EnergyBackedIdentityBond] = field(default_factory=dict)
    vouches: List[EnergyBackedVouch] = field(default_factory=list)

    def register_bond(
        self,
        society_lct: str,
        energy_sources: List[EnergyCapacityProof],
        lock_period_days: int = 30
    ) -> EnergyBackedIdentityBond:
        """
        Register new identity bond.

        Args:
            society_lct: Society creating bond
            energy_sources: Energy sources backing bond
            lock_period_days: Lock period

        Returns:
            EnergyBackedIdentityBond
        """
        # Calculate total capacity
        total_capacity = sum(source.capacity_watts for source in energy_sources)

        # Create bond
        bond = EnergyBackedIdentityBond(
            society_lct=society_lct,
            created_at=datetime.now(timezone.utc),
            committed_capacity_watts=total_capacity,
            energy_sources=[source.source_identifier for source in energy_sources],
            lock_period_days=lock_period_days,
        )

        self.bonds[society_lct] = bond
        return bond

    def get_bond(self, society_lct: str) -> Optional[EnergyBackedIdentityBond]:
        """Get bond for society."""
        return self.bonds.get(society_lct)

    def validate_all_bonds(
        self,
        energy_registry: EnergyCapacityRegistry
    ) -> List[Tuple[str, str]]:
        """
        Validate all active bonds.

        Returns list of (society_lct, violation_reason) for violations.
        """
        violations = []

        for society_lct, bond in self.bonds.items():
            if bond.status != BondStatus.ACTIVE:
                continue

            is_valid, reason = bond.validate_capacity(energy_registry)
            if not is_valid:
                violations.append((society_lct, reason))

        return violations

    def register_vouch(
        self,
        voucher_lct: str,
        newcomer_lct: str,
        allocated_energy_watts: float,
        bootstrap_period_days: int = 30
    ) -> EnergyBackedVouch:
        """
        Register vouching relationship.

        Args:
            voucher_lct: Established member vouching
            newcomer_lct: Newcomer being vouched for
            allocated_energy_watts: Energy committed to newcomer
            bootstrap_period_days: Bootstrap period

        Returns:
            EnergyBackedVouch
        """
        vouch = EnergyBackedVouch(
            voucher_lct=voucher_lct,
            newcomer_lct=newcomer_lct,
            created_at=datetime.now(timezone.utc),
            allocated_energy_watts=allocated_energy_watts,
            bootstrap_period_days=bootstrap_period_days,
        )

        self.vouches.append(vouch)
        return vouch

    def get_active_vouches_for_newcomer(
        self,
        newcomer_lct: str
    ) -> List[EnergyBackedVouch]:
        """Get all active vouches for newcomer."""
        return [
            vouch for vouch in self.vouches
            if vouch.newcomer_lct == newcomer_lct and vouch.active
        ]

    def get_stats(self) -> Dict:
        """Get registry statistics."""
        active_bonds = sum(1 for b in self.bonds.values() if b.status == BondStatus.ACTIVE)
        fulfilled_bonds = sum(1 for b in self.bonds.values() if b.status == BondStatus.FULFILLED)
        violated_bonds = sum(1 for b in self.bonds.values() if b.status == BondStatus.VIOLATED)

        active_vouches = sum(1 for v in self.vouches if v.active)
        successful_vouches = sum(1 for v in self.vouches if v.successful)
        violated_vouches = sum(1 for v in self.vouches if v.violated)

        return {
            "total_bonds": len(self.bonds),
            "active_bonds": active_bonds,
            "fulfilled_bonds": fulfilled_bonds,
            "violated_bonds": violated_bonds,
            "total_vouches": len(self.vouches),
            "active_vouches": active_vouches,
            "successful_vouches": successful_vouches,
            "violated_vouches": violated_vouches,
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    from energy_capacity import (
        SolarPanelProof,
        ComputeResourceProof,
        EnergyCapacityRegistry,
    )

    print("Energy-Backed Identity Bond - Example Usage\n")
    print("=" * 70)

    # Create energy registry
    energy_registry = EnergyCapacityRegistry(society_lct="lct-global")

    # Create bond registry
    bond_registry = EnergyBackedBondRegistry()

    print("\n1. New Society Creates Bond with Energy Sources")
    print("-" * 70)

    # Society has solar and compute
    solar = SolarPanelProof(
        panel_serial="SOLAR-ALICE-001",
        rated_watts=500.0,
        panel_model="SunPower 500W",
        installation_date=datetime.now(timezone.utc),
        last_verified=datetime.now(timezone.utc),
    )
    energy_registry.register_source(solar)

    gpu = ComputeResourceProof(
        device_type="gpu",
        device_model="RTX4090",
        device_id="GPU-ALICE-001",
        tdp_watts=450.0,
        last_verified=datetime.now(timezone.utc),
        utilization_factor=0.8,
        idle_power_watts=50.0,
    )
    energy_registry.register_source(gpu)

    # Register bond
    bond = bond_registry.register_bond(
        society_lct="lct-society-alice",
        energy_sources=[solar, gpu],
        lock_period_days=30,
    )

    print(f"  ✓ Bond registered for lct-society-alice")
    print(f"    Committed capacity: {bond.committed_capacity_watts:.0f}W")
    print(f"    Energy sources: {len(bond.energy_sources)}")
    print(f"    Lock period: {bond.lock_period_days} days")
    print(f"    Reputation at risk: {bond.reputation_at_risk * 100:.0f}%")

    print("\n2. Validate Bond (Capacity Maintained)")
    print("-" * 70)

    is_valid, reason = bond.validate_capacity(energy_registry)
    if is_valid:
        print(f"  ✓ Bond valid - capacity maintained")
    else:
        print(f"  ✗ Bond violated: {reason}")

    print("\n3. Established Member Vouches for Newcomer")
    print("-" * 70)

    vouch = bond_registry.register_vouch(
        voucher_lct="lct-society-alice",
        newcomer_lct="lct-society-bob",
        allocated_energy_watts=100.0,
        bootstrap_period_days=30,
    )

    print(f"  ✓ Alice vouches for Bob")
    print(f"    Energy allocated: {vouch.allocated_energy_watts}W")
    print(f"    Bootstrap period: {vouch.bootstrap_period_days} days")
    print(f"    Reputation at risk: {vouch.reputation_at_risk * 100:.0f}%")

    print("\n4. Simulate Energy Allocation to Newcomer")
    print("-" * 70)

    # Newcomer uses vouched energy
    vouch.record_energy_allocation(50.0)
    print(f"  → Bob used 50W of vouched energy")
    print(f"    Total allocated: {vouch.energy_allocated_total}W / {vouch.allocated_energy_watts}W")

    print("\n5. Newcomer Establishes, Vouch Completes Successfully")
    print("-" * 70)

    # Simulate time passing and newcomer establishing
    success, penalty = vouch.complete_vouch(newcomer_established=True)
    if success:
        print(f"  ✓ Vouch successful - no reputation penalty")
    else:
        print(f"  ✗ Vouch failed - reputation penalty: {penalty * 100:.0f}%")

    print("\n6. Bond Fulfillment After Lock Period")
    print("-" * 70)

    # Simulate lock period passing (would be 30 days in reality)
    # For demo, just check current state
    current_trust = 0.85  # High trust from good behavior

    can_fulfill, message = bond.fulfill_bond(current_trust)
    if can_fulfill:
        print(f"  ✓ {message}")
    else:
        print(f"  → {message}")
        print(f"    (Bond age: {bond.age_days()} days, need: {bond.lock_period_days} days)")

    print("\n7. Registry Statistics")
    print("-" * 70)

    stats = bond_registry.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("✅ Energy-backed identity bond system operational")
    print("\nKey Differences from Session #34 (Currency-Based):")
    print("  - Bonds commit CAPACITY (watts), not currency (ATP)")
    print("  - Forfeiture penalizes REPUTATION, not money")
    print("  - Capacity must be PROVEN and MAINTAINED")
    print("  - Vouching commits ENERGY ALLOCATION, not stakes")
    print("\nAnti-Sybil Properties:")
    print("  - Can't fake energy capacity (thermodynamic proof)")
    print("  - Reputation loss matters (hard to rebuild)")
    print("  - Vouching requires real capacity commitment")
