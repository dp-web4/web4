"""
Trust Maintenance: Economic Decay Prevention

Track BQ: Integrates trust decay with ATP maintenance payments.

Key principle: Trust naturally decays toward baseline over time.
Federations can prevent decay by paying ATP maintenance fees.

Mechanisms:
1. Trust decay applies to inter-federation trust relationships
2. Maintenance payments reset the decay timer
3. Missed maintenance causes trust to decay toward baseline
4. Higher trust levels cost more to maintain (incentivizes appropriate trust)

This creates:
- Economic cost for high-trust relationships
- Natural trust cleanup (abandoned relationships decay)
- Sybil resistance (maintaining fake federations is expensive)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .trust_decay import TrustDecayCalculator, DecayConfig
from .economic_federation import EconomicFederationRegistry, EconomicOperationResult
from .trust_economics import TrustOperationType


@dataclass
class MaintenanceStatus:
    """Status of trust maintenance for a relationship."""
    source_federation: str
    target_federation: str
    current_trust: float
    last_maintenance: str  # ISO timestamp
    next_due: str  # ISO timestamp
    days_until_due: int
    maintenance_cost: float
    is_overdue: bool
    decay_if_missed: float  # Expected trust after decay


@dataclass
class DecayEvent:
    """Record of trust decay due to missed maintenance."""
    source_federation: str
    target_federation: str
    timestamp: str
    trust_before: float
    trust_after: float
    decay_amount: float
    reason: str


class TrustMaintenanceManager:
    """
    Manages trust decay and maintenance for federations.

    Track BQ: Trust decays unless maintained with ATP.

    Wraps EconomicFederationRegistry with decay mechanics.
    """

    # Decay parameters for federation trust
    DECAY_RATE = 0.05  # 5% decay per missed maintenance period
    DECAY_MINIMUM = 0.3  # Trust floor (below this, decay stops)
    MAINTENANCE_PERIOD_DAYS = 7  # Weekly maintenance

    def __init__(
        self,
        economic_registry: EconomicFederationRegistry = None,
        db_path: Optional[str] = None,
    ):
        """
        Initialize the trust maintenance manager.

        Args:
            economic_registry: Existing economic registry (creates new if None)
            db_path: Path for database (used if creating new registry)
        """
        self.registry = economic_registry or EconomicFederationRegistry(db_path=db_path)
        self.decay_calculator = TrustDecayCalculator(DecayConfig(
            baseline=self.DECAY_MINIMUM,
            decay_rates={'trust': self.DECAY_RATE},
            decay_period=self.MAINTENANCE_PERIOD_DAYS * 86400,  # Convert to seconds
        ))

        # Track last maintenance times (relationship -> timestamp)
        self._last_maintenance: Dict[Tuple[str, str], str] = {}

        # Track decay events for audit
        self._decay_events: List[DecayEvent] = []

    def register_federation(
        self,
        federation_id: str,
        name: str,
        initial_atp: float = 1000.0,
    ) -> Tuple:
        """Register federation (delegates to economic registry)."""
        return self.registry.register_federation(federation_id, name, initial_atp)

    def establish_trust(
        self,
        source_federation_id: str,
        target_federation_id: str,
        **kwargs,
    ) -> EconomicOperationResult:
        """
        Establish trust relationship with maintenance tracking.

        Sets initial maintenance timestamp.
        """
        result = self.registry.establish_trust(
            source_federation_id,
            target_federation_id,
            **kwargs,
        )

        if result.success:
            # Set initial maintenance time
            key = (source_federation_id, target_federation_id)
            self._last_maintenance[key] = datetime.now(timezone.utc).isoformat()

        return result

    def get_maintenance_status(
        self,
        source_federation_id: str,
        target_federation_id: str,
    ) -> Optional[MaintenanceStatus]:
        """
        Get maintenance status for a trust relationship.
        """
        trust = self.registry.registry.get_trust(
            source_federation_id, target_federation_id
        )

        if not trust:
            return None

        key = (source_federation_id, target_federation_id)
        last_maintenance = self._last_maintenance.get(
            key,
            datetime.now(timezone.utc).isoformat()
        )

        # Calculate next due date
        last_dt = datetime.fromisoformat(last_maintenance.replace('Z', '+00:00'))
        next_due_dt = last_dt + timedelta(days=self.MAINTENANCE_PERIOD_DAYS)
        now = datetime.now(timezone.utc)

        days_until_due = (next_due_dt - now).days
        is_overdue = days_until_due < 0

        # Calculate maintenance cost
        cost, _ = self.registry.economics.calculate_maintain_cost(
            trust.trust_score,
            is_cross_federation=True,
        )

        # Calculate decay if missed
        decay_if_missed = self._calculate_decay(trust.trust_score)

        return MaintenanceStatus(
            source_federation=source_federation_id,
            target_federation=target_federation_id,
            current_trust=trust.trust_score,
            last_maintenance=last_maintenance,
            next_due=next_due_dt.isoformat(),
            days_until_due=max(0, days_until_due),
            maintenance_cost=cost,
            is_overdue=is_overdue,
            decay_if_missed=decay_if_missed,
        )

    def pay_maintenance(
        self,
        source_federation_id: str,
        target_federation_id: str,
    ) -> EconomicOperationResult:
        """
        Pay maintenance to prevent trust decay.

        Resets the maintenance timer for this relationship.
        """
        result = self.registry.pay_maintenance(
            source_federation_id,
            target_federation_id,
        )

        if result.success:
            key = (source_federation_id, target_federation_id)
            self._last_maintenance[key] = datetime.now(timezone.utc).isoformat()

        return result

    def apply_decay_to_overdue(
        self,
        federation_id: str,
    ) -> List[DecayEvent]:
        """
        Apply trust decay to all overdue relationships for a federation.

        Returns list of decay events.
        """
        events = []

        # Find all trust relationships from this federation
        all_feds = list(self.registry.economics.entity_balances.keys())

        for target_id in all_feds:
            if target_id == federation_id:
                continue

            status = self.get_maintenance_status(federation_id, target_id)
            if not status or not status.is_overdue:
                continue

            # Apply decay
            old_trust = status.current_trust
            new_trust = self._calculate_decay(old_trust)

            # Update trust in registry
            if new_trust < old_trust:
                self.registry.registry.update_trust(
                    federation_id, target_id, new_trust
                )

                event = DecayEvent(
                    source_federation=federation_id,
                    target_federation=target_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    trust_before=old_trust,
                    trust_after=new_trust,
                    decay_amount=old_trust - new_trust,
                    reason="Missed maintenance payment",
                )
                events.append(event)
                self._decay_events.append(event)

        return events

    def _calculate_decay(self, current_trust: float) -> float:
        """
        Calculate trust after one decay period.

        Uses exponential decay toward minimum:
        new_trust = min + (current - min) * (1 - rate)
        """
        if current_trust <= self.DECAY_MINIMUM:
            return current_trust

        decay_factor = 1 - self.DECAY_RATE
        new_trust = self.DECAY_MINIMUM + (
            (current_trust - self.DECAY_MINIMUM) * decay_factor
        )

        return max(self.DECAY_MINIMUM, new_trust)

    def get_all_maintenance_status(
        self,
        federation_id: str,
    ) -> List[MaintenanceStatus]:
        """
        Get maintenance status for all trust relationships from a federation.
        """
        statuses = []

        for key in self._last_maintenance:
            source, target = key
            if source == federation_id:
                status = self.get_maintenance_status(source, target)
                if status:
                    statuses.append(status)

        return statuses

    def simulate_maintenance_costs(
        self,
        federation_id: str,
        periods: int = 4,  # 4 weeks
    ) -> Dict:
        """
        Simulate maintenance costs over multiple periods.

        Shows total cost to maintain all trust relationships.
        """
        statuses = self.get_all_maintenance_status(federation_id)

        total_per_period = sum(s.maintenance_cost for s in statuses)
        total_projected = total_per_period * periods

        balance = self.registry.get_balance(federation_id)
        can_afford = balance >= total_projected

        return {
            "federation_id": federation_id,
            "current_balance": balance,
            "relationships": len(statuses),
            "cost_per_period": total_per_period,
            "periods": periods,
            "total_projected_cost": total_projected,
            "can_afford": can_afford,
            "balance_after": balance - total_projected,
            "relationships_detail": [
                {
                    "target": s.target_federation,
                    "trust": s.current_trust,
                    "cost": s.maintenance_cost,
                }
                for s in statuses
            ],
        }

    def get_decay_history(
        self,
        federation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[DecayEvent]:
        """
        Get history of decay events.

        Args:
            federation_id: Filter to specific federation (None for all)
            limit: Maximum events to return
        """
        events = self._decay_events

        if federation_id:
            events = [
                e for e in events
                if e.source_federation == federation_id
            ]

        return events[-limit:]

    def get_federation_health(
        self,
        federation_id: str,
    ) -> Dict:
        """
        Assess federation's maintenance health.

        Considers:
        - Current balance vs maintenance costs
        - Overdue relationships
        - Projected sustainability
        """
        statuses = self.get_all_maintenance_status(federation_id)
        balance = self.registry.get_balance(federation_id)

        overdue = [s for s in statuses if s.is_overdue]
        overdue_cost = sum(s.maintenance_cost for s in overdue)

        simulation = self.simulate_maintenance_costs(federation_id)

        # Health assessment
        if simulation["can_afford"] and len(overdue) == 0:
            health = "healthy"
        elif simulation["can_afford"]:
            health = "warning"  # Can afford but has overdue
        elif balance > overdue_cost:
            health = "at_risk"  # Can pay overdue but not projected
        else:
            health = "critical"  # Cannot pay overdue

        return {
            "federation_id": federation_id,
            "health": health,
            "current_balance": balance,
            "total_relationships": len(statuses),
            "overdue_relationships": len(overdue),
            "overdue_cost": overdue_cost,
            "monthly_maintenance_cost": simulation["total_projected_cost"],
            "months_sustainable": int(balance / simulation["cost_per_period"]) if simulation["cost_per_period"] > 0 else float('inf'),
        }


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Trust Maintenance Manager - Self Test")
    print("=" * 60)

    import tempfile

    db_path = Path(tempfile.mkdtemp()) / "trust_maintenance_test.db"
    manager = TrustMaintenanceManager(db_path=db_path)

    # Register federations
    print("\n1. Register federations:")
    manager.register_federation("fed:alpha", "Alpha", initial_atp=500)
    manager.register_federation("fed:beta", "Beta", initial_atp=500)
    manager.register_federation("fed:gamma", "Gamma", initial_atp=100)

    print(f"   Alpha balance: {manager.registry.get_balance('fed:alpha')} ATP")
    print(f"   Gamma balance: {manager.registry.get_balance('fed:gamma')} ATP")

    # Establish trust relationships
    print("\n2. Establish trust relationships:")
    result = manager.establish_trust("fed:alpha", "fed:beta")
    print(f"   Alpha -> Beta: {result.atp_cost} ATP, success={result.success}")

    result = manager.establish_trust("fed:alpha", "fed:gamma")
    print(f"   Alpha -> Gamma: {result.atp_cost} ATP, success={result.success}")

    # Get maintenance status
    print("\n3. Maintenance status:")
    status = manager.get_maintenance_status("fed:alpha", "fed:beta")
    if status:
        print(f"   Alpha -> Beta:")
        print(f"     Trust: {status.current_trust:.2f}")
        print(f"     Maintenance cost: {status.maintenance_cost:.1f} ATP")
        print(f"     Days until due: {status.days_until_due}")

    # Simulate costs
    print("\n4. Maintenance cost simulation (4 weeks):")
    simulation = manager.simulate_maintenance_costs("fed:alpha", periods=4)
    print(f"   Relationships: {simulation['relationships']}")
    print(f"   Cost per week: {simulation['cost_per_period']:.1f} ATP")
    print(f"   Total 4-week: {simulation['total_projected_cost']:.1f} ATP")
    print(f"   Can afford: {simulation['can_afford']}")

    # Check health
    print("\n5. Federation health:")
    health = manager.get_federation_health("fed:alpha")
    print(f"   Health: {health['health']}")
    print(f"   Relationships: {health['total_relationships']}")
    print(f"   Months sustainable: {health['months_sustainable']}")

    # Simulate decay
    print("\n6. Decay calculation:")
    trust = 0.8
    decayed = manager._calculate_decay(trust)
    print(f"   Trust 0.8 after 1 period: {decayed:.3f}")
    print(f"   Decay amount: {trust - decayed:.3f}")

    for i in range(10):
        decayed = manager._calculate_decay(decayed)
    print(f"   After 10 periods: {decayed:.3f}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
