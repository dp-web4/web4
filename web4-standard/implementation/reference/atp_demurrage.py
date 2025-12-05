"""
ATP Demurrage System
=====================

Implements ATP decay mechanics to prevent hoarding and ensure value circulation.

Key Concepts:
- **Demurrage**: Held ATP gradually decays to ADP over time
- **Velocity**: Minimum circulation rate enforcement
- **Decay Rate**: Configurable per society (e.g., 5% per month)
- **Grace Period**: Recent ATP has lower decay rate
- **Background Jobs**: Automatic decay calculation

Based on Web4 ATP/ADP lifecycle (ATP_INTEGRATION_SUMMARY.md):
- ATP cannot be hoarded indefinitely
- Demurrage encourages rapid circulation
- Rate increases with holding time
- Society configures monetary policy

Author: Legion Autonomous Session (2025-12-05)
Session: Track 7 - ATP Demurrage Implementation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from enum import Enum
import math
import time
import logging

logger = logging.getLogger(__name__)


class DemurrageRate(Enum):
    """Standard demurrage rate presets"""
    NONE = 0.0  # No demurrage (testing only)
    LOW = 0.01  # 1% per month (~12% per year)
    MODERATE = 0.05  # 5% per month (~45% per year)
    HIGH = 0.10  # 10% per month (~68% per year)
    AGGRESSIVE = 0.20  # 20% per month (~89% per year)


@dataclass
class ATPHolding:
    """
    ATP holding record for demurrage calculation.

    Tracks when ATP was acquired and calculates decay over time.
    """
    entity_lct: str
    amount: int  # ATP amount
    acquired_at: datetime  # When ATP was acquired
    last_decay_calculated: datetime  # Last decay calculation
    metadata: Dict[str, any] = field(default_factory=dict)

    def age_days(self, now: Optional[datetime] = None) -> float:
        """Calculate age of holding in days"""
        if now is None:
            now = datetime.now(timezone.utc)
        return (now - self.acquired_at).total_seconds() / 86400

    def time_since_decay(self, now: Optional[datetime] = None) -> float:
        """Calculate time since last decay in days"""
        if now is None:
            now = datetime.now(timezone.utc)
        return (now - self.last_decay_calculated).total_seconds() / 86400


@dataclass
class DemurrageConfig:
    """
    Society-specific demurrage configuration.

    Defines how ATP decays for a particular society.
    """
    society_id: str

    # Base decay rate (per month)
    base_rate: float = 0.05  # 5% per month default

    # Grace period (days) - reduced decay for recently acquired ATP
    grace_period_days: int = 7  # 1 week
    grace_rate_multiplier: float = 0.1  # 10% of base rate during grace

    # Velocity requirements
    min_velocity_per_month: float = 0.5  # Must circulate 50% per month
    velocity_penalty_rate: float = 0.15  # 15% per month if below velocity

    # Calculation frequency
    decay_calculation_interval_hours: int = 24  # Calculate daily

    # Limits
    max_holding_days: int = 365  # After 1 year, force conversion to ADP

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DemurrageEngine:
    """
    ATP Demurrage Engine.

    Calculates and applies ATP decay based on holding time and society policy.
    """

    def __init__(self, config: DemurrageConfig):
        """
        Initialize demurrage engine.

        Args:
            config: Society-specific demurrage configuration
        """
        self.config = config
        self.holdings: Dict[str, List[ATPHolding]] = {}  # entity_lct -> holdings
        self.last_global_decay = datetime.now(timezone.utc)

        logger.info(f"Demurrage Engine initialized for society: {config.society_id}")
        logger.info(f"  Base Rate: {config.base_rate*100:.1f}% per month")
        logger.info(f"  Grace Period: {config.grace_period_days} days")

    def add_holding(
        self,
        entity_lct: str,
        amount: int,
        acquired_at: Optional[datetime] = None
    ) -> ATPHolding:
        """
        Add ATP holding for entity.

        Args:
            entity_lct: Entity LCT identifier
            amount: ATP amount acquired
            acquired_at: Acquisition timestamp (default: now)

        Returns:
            ATPHolding record
        """
        if acquired_at is None:
            acquired_at = datetime.now(timezone.utc)

        holding = ATPHolding(
            entity_lct=entity_lct,
            amount=amount,
            acquired_at=acquired_at,
            last_decay_calculated=acquired_at
        )

        if entity_lct not in self.holdings:
            self.holdings[entity_lct] = []

        self.holdings[entity_lct].append(holding)

        logger.debug(f"Added {amount} ATP holding for {entity_lct}")

        return holding

    def calculate_decay(
        self,
        holding: ATPHolding,
        now: Optional[datetime] = None
    ) -> Tuple[int, int, float]:
        """
        Calculate decay for a holding.

        Args:
            holding: ATP holding to calculate decay for
            now: Current timestamp (default: now)

        Returns:
            (decayed_amount, remaining_amount, decay_rate) tuple
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Time since last decay calculation
        time_since_decay = holding.time_since_decay(now)

        if time_since_decay < (self.config.decay_calculation_interval_hours / 24):
            # Too soon to calculate decay
            return 0, holding.amount, 0.0

        # Determine applicable rate
        age_days = holding.age_days(now)

        if age_days < self.config.grace_period_days:
            # Grace period - reduced decay
            rate = self.config.base_rate * self.config.grace_rate_multiplier
        else:
            # Normal decay
            rate = self.config.base_rate

        # Convert monthly rate to daily rate
        daily_rate = rate / 30.0

        # Calculate decay using exponential decay formula
        # remaining = initial * (1 - daily_rate) ^ days
        decay_factor = (1 - daily_rate) ** time_since_decay

        remaining_amount = int(holding.amount * decay_factor)
        decayed_amount = holding.amount - remaining_amount

        # Check max holding period
        if age_days >= self.config.max_holding_days:
            # Force conversion to ADP
            decayed_amount = holding.amount
            remaining_amount = 0
            logger.warning(f"Holding exceeded max age ({self.config.max_holding_days} days), forcing ADP conversion")

        return decayed_amount, remaining_amount, daily_rate

    def apply_decay(
        self,
        entity_lct: str,
        now: Optional[datetime] = None
    ) -> Tuple[int, int]:
        """
        Apply decay to all holdings for an entity.

        Args:
            entity_lct: Entity LCT identifier
            now: Current timestamp (default: now)

        Returns:
            (total_decayed, total_remaining) tuple
        """
        if now is None:
            now = datetime.now(timezone.utc)

        if entity_lct not in self.holdings:
            return 0, 0

        total_decayed = 0
        total_remaining = 0

        # Calculate decay for each holding
        holdings_to_remove = []

        for i, holding in enumerate(self.holdings[entity_lct]):
            decayed, remaining, rate = self.calculate_decay(holding, now)

            total_decayed += decayed
            total_remaining += remaining

            # Update holding
            holding.amount = remaining
            holding.last_decay_calculated = now

            # Remove if fully decayed
            if remaining == 0:
                holdings_to_remove.append(i)
                logger.debug(f"Holding fully decayed for {entity_lct}: {decayed} ATP → ADP")

        # Remove fully decayed holdings
        for i in reversed(holdings_to_remove):
            del self.holdings[entity_lct][i]

        if total_decayed > 0:
            logger.info(f"Applied decay for {entity_lct}: {total_decayed} ATP → ADP (remaining: {total_remaining})")

        return total_decayed, total_remaining

    def apply_global_decay(
        self,
        now: Optional[datetime] = None
    ) -> Dict[str, Tuple[int, int]]:
        """
        Apply decay to all holdings across all entities.

        Args:
            now: Current timestamp (default: now)

        Returns:
            Dict mapping entity_lct → (decayed, remaining)
        """
        if now is None:
            now = datetime.now(timezone.utc)

        results = {}

        for entity_lct in list(self.holdings.keys()):
            decayed, remaining = self.apply_decay(entity_lct, now)
            results[entity_lct] = (decayed, remaining)

        self.last_global_decay = now

        total_decayed = sum(d for d, r in results.values())
        total_remaining = sum(r for d, r in results.values())

        logger.info(f"Global decay applied: {total_decayed} ATP → ADP across {len(results)} entities")
        logger.info(f"  Total remaining ATP: {total_remaining}")

        return results

    def get_total_holdings(self, entity_lct: str) -> int:
        """Get total ATP holdings for entity (before decay)"""
        if entity_lct not in self.holdings:
            return 0
        return sum(h.amount for h in self.holdings[entity_lct])

    def get_velocity(
        self,
        entity_lct: str,
        period_days: int = 30
    ) -> float:
        """
        Calculate velocity for entity over period.

        Velocity = ATP_transacted / ATP_held

        Args:
            entity_lct: Entity LCT identifier
            period_days: Period to calculate over (default: 30 days)

        Returns:
            Velocity ratio (0.0-1.0+)
        """
        # TODO: Integrate with ATP transaction history
        # For now, return placeholder
        return 0.5

    def check_velocity_requirement(
        self,
        entity_lct: str,
        now: Optional[datetime] = None
    ) -> Tuple[bool, float, float]:
        """
        Check if entity meets velocity requirements.

        Args:
            entity_lct: Entity LCT identifier
            now: Current timestamp (default: now)

        Returns:
            (meets_requirement, actual_velocity, required_velocity) tuple
        """
        if now is None:
            now = datetime.now(timezone.utc)

        actual_velocity = self.get_velocity(entity_lct, period_days=30)
        required_velocity = self.config.min_velocity_per_month

        meets = actual_velocity >= required_velocity

        if not meets:
            logger.warning(f"Velocity requirement not met for {entity_lct}: {actual_velocity:.2f} < {required_velocity:.2f}")

        return meets, actual_velocity, required_velocity


# ============================================================================
# Background Decay Job
# ============================================================================

class DemurrageScheduler:
    """
    Scheduler for automatic demurrage calculation.

    Runs background job to apply decay at configured intervals.
    """

    def __init__(self, engine: DemurrageEngine):
        """
        Initialize demurrage scheduler.

        Args:
            engine: Demurrage engine to run
        """
        self.engine = engine
        self.running = False
        self.last_run = datetime.now(timezone.utc)

        logger.info("Demurrage Scheduler initialized")

    def should_run(self, now: Optional[datetime] = None) -> bool:
        """Check if scheduler should run"""
        if now is None:
            now = datetime.now(timezone.utc)

        interval = timedelta(hours=self.engine.config.decay_calculation_interval_hours)
        return (now - self.last_run) >= interval

    def run_decay_cycle(self, now: Optional[datetime] = None) -> Dict[str, Tuple[int, int]]:
        """
        Run one decay calculation cycle.

        Args:
            now: Current timestamp (default: now)

        Returns:
            Dict mapping entity_lct → (decayed, remaining)
        """
        if now is None:
            now = datetime.now(timezone.utc)

        logger.info(f"Running demurrage cycle at {now.isoformat()}")

        results = self.engine.apply_global_decay(now)

        self.last_run = now

        return results


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == '__main__':
    # Example: Configure demurrage for a society
    print("=== ATP Demurrage System Demo ===\n")

    # Create config
    config = DemurrageConfig(
        society_id="web4:default",
        base_rate=0.05,  # 5% per month
        grace_period_days=7,
        min_velocity_per_month=0.5,
        decay_calculation_interval_hours=24
    )

    print(f"Demurrage Config:")
    print(f"  Society: {config.society_id}")
    print(f"  Base Rate: {config.base_rate*100:.1f}% per month")
    print(f"  Grace Period: {config.grace_period_days} days")
    print(f"  Min Velocity: {config.min_velocity_per_month*100:.0f}% per month\n")

    # Create engine
    engine = DemurrageEngine(config)

    # Add holdings
    entity_lct = "lct:ai:agent:test:001"

    # Holding 1: Recently acquired (in grace period)
    engine.add_holding(
        entity_lct=entity_lct,
        amount=1000,
        acquired_at=datetime.now(timezone.utc) - timedelta(days=5)
    )

    # Holding 2: Older (full decay rate)
    engine.add_holding(
        entity_lct=entity_lct,
        amount=2000,
        acquired_at=datetime.now(timezone.utc) - timedelta(days=30)
    )

    print(f"Added 2 holdings for {entity_lct}:")
    print(f"  Holding 1: 1000 ATP (5 days old, in grace period)")
    print(f"  Holding 2: 2000 ATP (30 days old, full decay)\n")

    # Apply decay
    now = datetime.now(timezone.utc) + timedelta(days=10)
    decayed, remaining = engine.apply_decay(entity_lct, now=now)

    print(f"After 10 days:")
    print(f"  Decayed: {decayed} ATP → ADP")
    print(f"  Remaining: {remaining} ATP")
    print(f"  Decay Rate: {(decayed / (decayed + remaining))*100:.1f}%\n")

    # Global decay
    print("Running global decay cycle...")
    results = engine.apply_global_decay(now)

    for lct, (dec, rem) in results.items():
        print(f"  {lct}: {dec} ATP decayed, {rem} ATP remaining")

    print("\n=== Demo Complete ===")
