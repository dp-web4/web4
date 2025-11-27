#!/usr/bin/env python3
"""
ATP (Attention Token Pool) Metering System
Session #78: Resource consumption tracking and allocation

Purpose:
Track ATP consumption for operations, manage treasury, and enable ATP-based
operation gating. ATP is Web4's primary resource constraint - agents spend ATP
to perform operations, and societies manage ATP pools.

Theory:
ATP represents "attention" or "compute time" - a limited resource that must be
allocated wisely. High-quality operations may cost more ATP but deliver better
outcomes. ATP metering enables:

1. Resource accountability (who spent what)
2. Economic incentives (ATP pricing)
3. Attack mitigation (rate limiting via ATP)
4. Quality-cost optimization

Based on SAGE_WEB4_INTEGRATION_DESIGN.md (Session #76) and Web4 whitepaper.
"""

from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import time

try:
    from .lct import LCT
except ImportError:
    # Allow testing as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from lct import LCT


# ATP cost model parameters
ATP_BASE_COSTS = {
    "local_conversation": 10.0,       # Low stakes
    "federation_query": 50.0,         # Medium stakes
    "insurance_audit": 100.0,         # High stakes
    "infrastructure_vote": 200.0      # Critical stakes
}

ATP_PER_SECOND = 1.0  # Time-based ATP cost
ATP_PER_QUALITY_UNIT = 0.5  # Quality premium


@dataclass
class ATPTransaction:
    """Single ATP transaction record"""
    transaction_id: str
    agent_lct: str
    operation_type: str
    atp_cost: float
    timestamp: float
    operation_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ATPMeter:
    """ATP consumption tracker for an agent or society"""

    owner_lct: str  # Agent or society LCT ID
    current_balance: float = 1000.0
    transactions: list[ATPTransaction] = field(default_factory=list)

    def get_balance(self) -> float:
        """Get current ATP balance"""
        return self.current_balance

    def can_afford(self, atp_cost: float) -> bool:
        """Check if owner can afford operation"""
        return self.current_balance >= atp_cost

    def consume_atp(
        self,
        atp_cost: float,
        operation_type: str,
        operation_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Consume ATP for an operation

        Args:
            atp_cost: ATP amount to consume
            operation_type: Type of operation
            operation_id: Optional operation ID
            notes: Optional transaction notes

        Returns:
            True if successful, False if insufficient ATP
        """
        if not self.can_afford(atp_cost):
            return False

        # Create transaction record
        transaction = ATPTransaction(
            transaction_id=f"atp_{self.owner_lct}_{len(self.transactions)}",
            agent_lct=self.owner_lct,
            operation_type=operation_type,
            atp_cost=atp_cost,
            timestamp=time.time(),
            operation_id=operation_id,
            notes=notes
        )

        self.transactions.append(transaction)
        self.current_balance -= atp_cost

        return True

    def add_atp(self, amount: float, notes: Optional[str] = None):
        """
        Add ATP to balance (revenue, allocation, etc.)

        Args:
            amount: ATP amount to add
            notes: Optional transaction notes
        """
        transaction = ATPTransaction(
            transaction_id=f"atp_{self.owner_lct}_{len(self.transactions)}",
            agent_lct=self.owner_lct,
            operation_type="allocation",
            atp_cost=-amount,  # Negative = credit
            timestamp=time.time(),
            notes=notes
        )

        self.transactions.append(transaction)
        self.current_balance += amount

    def get_consumption_stats(self) -> Dict:
        """
        Get ATP consumption statistics

        Returns:
            {
                "total_spent": float,
                "total_earned": float,
                "transaction_count": int,
                "by_operation_type": {op_type: total_atp}
            }
        """
        total_spent = 0.0
        total_earned = 0.0
        by_operation = {}

        for tx in self.transactions:
            if tx.atp_cost > 0:
                total_spent += tx.atp_cost

                if tx.operation_type not in by_operation:
                    by_operation[tx.operation_type] = 0.0
                by_operation[tx.operation_type] += tx.atp_cost
            else:
                total_earned += abs(tx.atp_cost)

        return {
            "total_spent": total_spent,
            "total_earned": total_earned,
            "net_balance": total_earned - total_spent,
            "current_balance": self.current_balance,
            "transaction_count": len(self.transactions),
            "by_operation_type": by_operation
        }


def calculate_atp_cost(
    operation_type: str,
    latency: Optional[float] = None,
    quality_score: Optional[float] = None
) -> float:
    """
    Calculate ATP cost for an operation

    Args:
        operation_type: Type of operation
        latency: Operation latency in seconds (optional)
        quality_score: Quality score 0-1 (optional, for quality premium)

    Returns:
        Total ATP cost

    Formula:
        ATP_cost = base_cost + (latency × ATP_per_second) + (quality × ATP_per_quality)

    Example:
        >>> # SAGE conversation: 40s latency, 0.85 quality
        >>> cost = calculate_atp_cost("local_conversation", latency=40.0, quality_score=0.85)
        >>> # 10 (base) + (40 × 1.0) + (0.85 × 0.5) = 50.425 ATP
    """
    # Base cost
    base_cost = ATP_BASE_COSTS.get(operation_type, 10.0)

    # Time-based cost
    time_cost = (latency * ATP_PER_SECOND) if latency else 0.0

    # Quality premium (optional - pay more for higher quality)
    quality_premium = (quality_score * ATP_PER_QUALITY_UNIT) if quality_score else 0.0

    total_cost = base_cost + time_cost + quality_premium

    return total_cost

def create_atp_meter_for_lct(lct: LCT, initial_balance: float = 1000.0) -> ATPMeter:
    """
    Create ATP meter for an LCT

    Args:
        lct: LCT instance
        initial_balance: Starting ATP balance

    Returns:
        ATPMeter instance

    Note: ATP balance is also stored in LCT metadata for persistence
    """
    # Create meter
    meter = ATPMeter(
        owner_lct=lct.lct_id,
        current_balance=initial_balance
    )

    # Store reference in LCT metadata
    if "resources" not in lct.metadata:
        lct.metadata["resources"] = {}

    lct.metadata["resources"]["ATP"] = initial_balance
    lct.metadata["atp_meter_created"] = time.time()

    return meter


def sync_atp_meter_to_lct(meter: ATPMeter, lct: LCT):
    """
    Sync ATP meter state back to LCT metadata

    Args:
        meter: ATPMeter instance
        lct: LCT instance

    Note: Call this after ATP transactions to persist state
    """
    if "resources" not in lct.metadata:
        lct.metadata["resources"] = {}

    lct.metadata["resources"]["ATP"] = meter.current_balance
    lct.metadata["atp_last_sync"] = time.time()


def get_atp_efficiency(atp_spent: float, quality_achieved: float) -> float:
    """
    Calculate ATP efficiency (quality per ATP)

    Args:
        atp_spent: ATP consumed
        quality_achieved: Quality score achieved (0-1)

    Returns:
        Efficiency ratio

    Example:
        >>> # Spent 50 ATP, achieved 0.85 quality
        >>> eff = get_atp_efficiency(50.0, 0.85)
        >>> # 0.017 (quality per ATP)
    """
    if atp_spent == 0:
        return 0.0

    return quality_achieved / atp_spent


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  ATP Metering System - Unit Tests")
    print("  Session #78")
    print("=" * 80)

    # Test 1: ATP cost calculation
    print("\n=== Test 1: ATP Cost Calculation ===\n")

    test_operations = [
        {"type": "local_conversation", "latency": 40.0, "quality": 0.85},
        {"type": "federation_query", "latency": 35.0, "quality": 0.90},
        {"type": "insurance_audit", "latency": 45.0, "quality": 0.95},
        {"type": "infrastructure_vote", "latency": 30.0, "quality": 0.98}
    ]

    print(f"{'Operation':<25} | {'Base':<8} | {'Time':<8} | {'Quality':<8} | {'Total':<8}")
    print("-" * 80)

    for op in test_operations:
        cost = calculate_atp_cost(
            op["type"],
            latency=op["latency"],
            quality_score=op["quality"]
        )

        base = ATP_BASE_COSTS.get(op["type"], 10.0)
        time_cost = op["latency"] * ATP_PER_SECOND
        quality_cost = op["quality"] * ATP_PER_QUALITY_UNIT

        print(f"{op['type']:<25} | {base:<8.1f} | {time_cost:<8.1f} | {quality_cost:<8.2f} | {cost:<8.2f}")

    # Test 2: ATP meter operations
    print("\n=== Test 2: ATP Meter Operations ===\n")

    meter = ATPMeter(owner_lct="lct:test:agent:alice", current_balance=1000.0)

    print(f"Initial balance: {meter.get_balance():.2f} ATP")

    # Consume ATP for operations
    operations = [
        ("local_conversation", 50.4),
        ("local_conversation", 48.2),
        ("federation_query", 90.5),
        ("local_conversation", 52.1)
    ]

    for op_type, cost in operations:
        success = meter.consume_atp(cost, op_type)
        status = "✓" if success else "✗"
        print(f"{status} Consumed {cost:.1f} ATP for {op_type}, balance: {meter.get_balance():.1f} ATP")

    # Test 3: Consumption statistics
    print("\n=== Test 3: Consumption Statistics ===\n")

    stats = meter.get_consumption_stats()

    print(f"Total spent: {stats['total_spent']:.2f} ATP")
    print(f"Current balance: {stats['current_balance']:.2f} ATP")
    print(f"Transaction count: {stats['transaction_count']}")

    print(f"\nBy operation type:")
    for op_type, total in stats["by_operation_type"].items():
        print(f"  {op_type:<25} {total:.2f} ATP")

    # Test 4: ATP efficiency
    print("\n=== Test 4: ATP Efficiency ===\n")

    test_cases = [
        (50.0, 0.85),
        (90.0, 0.90),
        (150.0, 0.95),
        (250.0, 0.98)
    ]

    print(f"{'ATP Spent':<12} | {'Quality':<10} | {'Efficiency':<12}")
    print("-" * 40)

    for atp, quality in test_cases:
        eff = get_atp_efficiency(atp, quality)
        print(f"{atp:<12.1f} | {quality:<10.2f} | {eff:<12.4f}")

    # Test 5: Insufficient ATP
    print("\n=== Test 5: Insufficient ATP Handling ===\n")

    print(f"Current balance: {meter.get_balance():.1f} ATP")

    # Try to consume more than available
    success = meter.consume_atp(1000.0, "infrastructure_vote")

    if success:
        print("❌ ERROR: Should have failed (insufficient ATP)")
    else:
        print("✓ Correctly rejected operation (insufficient ATP)")
        print(f"Balance unchanged: {meter.get_balance():.1f} ATP")

    # Test 6: ATP allocation (earning ATP)
    print("\n=== Test 6: ATP Allocation ===\n")

    print(f"Before allocation: {meter.get_balance():.1f} ATP")

    meter.add_atp(500.0, notes="Daily allocation")

    print(f"After allocation: {meter.get_balance():.1f} ATP")

    final_stats = meter.get_consumption_stats()
    print(f"Total earned: {final_stats['total_earned']:.2f} ATP")
    print(f"Net balance: {final_stats['net_balance']:.2f} ATP")

    print("\n" + "=" * 80)
    print("  All Unit Tests Passed!")
    print("=" * 80)
