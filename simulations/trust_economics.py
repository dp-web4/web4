"""
Trust Economics: ATP Cost Layer for Trust Operations

Track BL: Integrates economic costs with trust operations.

Key principles:
1. Trust operations have ATP costs - establishing, maintaining, increasing trust
2. Higher trust levels cost more to achieve and maintain
3. Cross-federation operations are more expensive than intra-team
4. Trust decay can be offset by spending ATP (active maintenance)

Cost structure:
- ESTABLISH_TRUST: One-time cost to create relationship
- MAINTAIN_TRUST: Periodic cost to prevent decay
- INCREASE_TRUST: Cost per trust level increase
- CROSS_FED_MULTIPLIER: Multiplier for cross-federation operations

This creates economic incentives for genuine trust relationships and makes
Sybil attacks expensive.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum


class TrustOperationType(Enum):
    """Types of trust operations that consume ATP."""
    ESTABLISH = "establish"           # Create new trust relationship
    MAINTAIN = "maintain"             # Prevent decay (periodic)
    INCREASE = "increase"             # Boost trust level
    RECORD_SUCCESS = "record_success" # Record successful interaction
    RECORD_FAILURE = "record_failure" # Record failed interaction (free - cost is trust loss)
    CROSS_FED_PROPOSAL = "cross_fed_proposal"  # Create cross-federation proposal
    CROSS_FED_APPROVAL = "cross_fed_approval"  # Approve cross-federation proposal
    EXTERNAL_WITNESS = "external_witness"      # Provide external witness


@dataclass
class TrustCostPolicy:
    """
    Configurable ATP costs for trust operations.

    Track BL: Economic parameters for trust system.
    """
    # Base costs (in ATP units)
    establish_base_cost: float = 10.0       # Create new relationship
    maintain_base_cost: float = 2.0         # Per maintenance period
    increase_base_cost: float = 5.0         # Per 0.1 trust increase
    record_success_cost: float = 1.0        # Record positive interaction
    record_failure_cost: float = 0.0        # Free - failure is its own cost

    # Cross-federation multiplier (more expensive)
    cross_fed_multiplier: float = 3.0       # 3x for cross-federation ops

    # Proposal costs
    proposal_base_cost: float = 15.0        # Create cross-fed proposal
    approval_base_cost: float = 5.0         # Approve a proposal
    witness_base_cost: float = 8.0          # Provide external witness

    # Trust level cost scaling (higher trust = higher maintenance)
    trust_level_cost_multiplier: Dict[str, float] = field(default_factory=lambda: {
        "0.5": 1.0,   # Baseline
        "0.6": 1.2,   # 20% more
        "0.7": 1.5,   # 50% more
        "0.8": 2.0,   # 100% more
        "0.9": 3.0,   # 200% more
        "1.0": 5.0,   # 400% more
    })

    # Maintenance period (days)
    maintenance_period_days: int = 7  # Weekly maintenance

    def get_level_multiplier(self, trust_level: float) -> float:
        """Get cost multiplier for a trust level."""
        # Find the applicable multiplier
        multiplier = 1.0
        for level_str, mult in sorted(self.trust_level_cost_multiplier.items()):
            if trust_level >= float(level_str):
                multiplier = mult
        return multiplier


@dataclass
class TrustTransaction:
    """Record of an ATP-costing trust operation."""
    transaction_id: str
    operation_type: TrustOperationType
    source_entity: str  # Team or federation
    target_entity: str  # Team or federation
    atp_cost: float
    timestamp: str
    details: Dict = field(default_factory=dict)

    # Cost breakdown
    base_cost: float = 0.0
    cross_fed_multiplier: float = 1.0
    trust_level_multiplier: float = 1.0


class TrustEconomicsEngine:
    """
    Manages ATP costs for trust operations.

    Track BL: Economic layer that makes trust manipulation expensive.
    """

    def __init__(self, policy: TrustCostPolicy = None):
        """
        Initialize the economics engine.

        Args:
            policy: Cost policy (uses defaults if not provided)
        """
        self.policy = policy or TrustCostPolicy()
        self.transactions: List[TrustTransaction] = []
        self.entity_balances: Dict[str, float] = {}  # entity_id -> ATP balance

    def initialize_balance(self, entity_id: str, initial_atp: float = 1000.0):
        """Set initial ATP balance for an entity."""
        self.entity_balances[entity_id] = initial_atp

    def get_balance(self, entity_id: str) -> float:
        """Get current ATP balance for an entity."""
        return self.entity_balances.get(entity_id, 0.0)

    def can_afford(self, entity_id: str, cost: float) -> bool:
        """Check if entity can afford an operation."""
        return self.get_balance(entity_id) >= cost

    def calculate_establish_cost(
        self,
        is_cross_federation: bool = False,
    ) -> Tuple[float, Dict]:
        """
        Calculate cost to establish a new trust relationship.

        Returns:
            (total_cost, breakdown_dict)
        """
        base = self.policy.establish_base_cost
        cross_fed_mult = self.policy.cross_fed_multiplier if is_cross_federation else 1.0
        total = base * cross_fed_mult

        return total, {
            "base_cost": base,
            "cross_fed_multiplier": cross_fed_mult,
            "total": total,
        }

    def calculate_maintain_cost(
        self,
        current_trust: float,
        is_cross_federation: bool = False,
    ) -> Tuple[float, Dict]:
        """
        Calculate periodic maintenance cost for a trust relationship.

        Higher trust levels cost more to maintain.

        Returns:
            (total_cost, breakdown_dict)
        """
        base = self.policy.maintain_base_cost
        trust_mult = self.policy.get_level_multiplier(current_trust)
        cross_fed_mult = self.policy.cross_fed_multiplier if is_cross_federation else 1.0
        total = base * trust_mult * cross_fed_mult

        return total, {
            "base_cost": base,
            "trust_level_multiplier": trust_mult,
            "cross_fed_multiplier": cross_fed_mult,
            "total": total,
        }

    def calculate_increase_cost(
        self,
        current_trust: float,
        target_trust: float,
        is_cross_federation: bool = False,
    ) -> Tuple[float, Dict]:
        """
        Calculate cost to increase trust level.

        Cost scales with both current and target levels.

        Returns:
            (total_cost, breakdown_dict)
        """
        if target_trust <= current_trust:
            return 0.0, {"error": "Target must be higher than current"}

        # Calculate increments needed (per 0.1)
        increments = int((target_trust - current_trust) * 10)
        base = self.policy.increase_base_cost * increments

        # Use target level multiplier (incentivizes slower growth)
        trust_mult = self.policy.get_level_multiplier(target_trust)
        cross_fed_mult = self.policy.cross_fed_multiplier if is_cross_federation else 1.0
        total = base * trust_mult * cross_fed_mult

        return total, {
            "base_cost": base,
            "increments": increments,
            "trust_level_multiplier": trust_mult,
            "cross_fed_multiplier": cross_fed_mult,
            "total": total,
        }

    def calculate_proposal_cost(
        self,
        affected_federations: int,
    ) -> Tuple[float, Dict]:
        """
        Calculate cost to create a cross-federation proposal.

        Cost scales with number of affected federations.

        Returns:
            (total_cost, breakdown_dict)
        """
        base = self.policy.proposal_base_cost
        fed_multiplier = max(1.0, affected_federations * 0.5)  # +50% per federation
        total = base * fed_multiplier

        return total, {
            "base_cost": base,
            "federations": affected_federations,
            "federation_multiplier": fed_multiplier,
            "total": total,
        }

    def calculate_approval_cost(self) -> Tuple[float, Dict]:
        """Calculate cost to approve a cross-federation proposal."""
        return self.policy.approval_base_cost, {
            "base_cost": self.policy.approval_base_cost,
            "total": self.policy.approval_base_cost,
        }

    def calculate_witness_cost(self) -> Tuple[float, Dict]:
        """Calculate cost to provide external witness."""
        return self.policy.witness_base_cost, {
            "base_cost": self.policy.witness_base_cost,
            "total": self.policy.witness_base_cost,
        }

    def charge_operation(
        self,
        entity_id: str,
        operation_type: TrustOperationType,
        target_entity: str,
        cost: float,
        details: Dict = None,
    ) -> Optional[TrustTransaction]:
        """
        Charge an entity for a trust operation.

        Args:
            entity_id: Entity being charged
            operation_type: Type of operation
            target_entity: Target of the operation
            cost: ATP cost
            details: Additional details

        Returns:
            TrustTransaction if successful, None if insufficient funds
        """
        if not self.can_afford(entity_id, cost):
            return None

        # Deduct cost
        self.entity_balances[entity_id] = self.get_balance(entity_id) - cost

        # Create transaction record
        import uuid
        txn = TrustTransaction(
            transaction_id=f"trust_txn:{uuid.uuid4().hex[:12]}",
            operation_type=operation_type,
            source_entity=entity_id,
            target_entity=target_entity,
            atp_cost=cost,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details or {},
        )
        self.transactions.append(txn)

        return txn

    def get_entity_costs_summary(
        self,
        entity_id: str,
        time_window_days: int = 30,
    ) -> Dict:
        """
        Get summary of trust operation costs for an entity.

        Returns:
            Dict with cost breakdown by operation type
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        cutoff_str = cutoff.isoformat()

        costs_by_type: Dict[str, float] = {}
        count_by_type: Dict[str, int] = {}

        for txn in self.transactions:
            if txn.source_entity == entity_id and txn.timestamp >= cutoff_str:
                op_type = txn.operation_type.value
                costs_by_type[op_type] = costs_by_type.get(op_type, 0) + txn.atp_cost
                count_by_type[op_type] = count_by_type.get(op_type, 0) + 1

        return {
            "entity_id": entity_id,
            "time_window_days": time_window_days,
            "current_balance": self.get_balance(entity_id),
            "total_spent": sum(costs_by_type.values()),
            "costs_by_operation": costs_by_type,
            "operations_by_type": count_by_type,
        }

    def estimate_sybil_attack_cost(
        self,
        num_fake_federations: int,
        target_trust_level: float = 0.7,
        proposals_per_pair: int = 5,
    ) -> Dict:
        """
        Estimate ATP cost to execute a Sybil attack at federation level.

        Track BL: Shows how economics deters attacks.

        Args:
            num_fake_federations: Number of fake federations to create
            target_trust_level: Trust level to achieve
            proposals_per_pair: Approvals needed per pair

        Returns:
            Dict with cost estimate and breakdown
        """
        # Each fake federation needs to establish trust with others
        pairs = num_fake_federations * (num_fake_federations - 1) // 2

        # Cost to establish all trust relationships
        establish_cost, _ = self.calculate_establish_cost(is_cross_federation=True)
        total_establish = establish_cost * pairs * 2  # Both directions

        # Cost to increase trust (from 0.5 to target)
        increase_cost, _ = self.calculate_increase_cost(
            0.5, target_trust_level, is_cross_federation=True
        )
        total_increase = increase_cost * pairs * 2

        # Cost to create proposals (each pair creates mutual proposals)
        proposal_cost, _ = self.calculate_proposal_cost(2)
        total_proposals = proposal_cost * pairs * proposals_per_pair * 2

        # Cost to approve proposals
        approval_cost, _ = self.calculate_approval_cost()
        total_approvals = approval_cost * pairs * proposals_per_pair * 2

        total_cost = total_establish + total_increase + total_proposals + total_approvals

        return {
            "num_fake_federations": num_fake_federations,
            "trust_pairs": pairs,
            "target_trust_level": target_trust_level,
            "breakdown": {
                "establish_relationships": total_establish,
                "increase_trust": total_increase,
                "create_proposals": total_proposals,
                "approve_proposals": total_approvals,
            },
            "total_attack_cost": total_cost,
            "cost_per_fake_federation": total_cost / num_fake_federations if num_fake_federations > 0 else 0,
            "deterrence_note": f"Creating {num_fake_federations} colluding federations costs {total_cost:.1f} ATP",
        }


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Trust Economics Engine - Self Test")
    print("=" * 60)

    engine = TrustEconomicsEngine()

    # Test cost calculations
    print("\n1. Cost Calculations:")

    est_cost, est_breakdown = engine.calculate_establish_cost(is_cross_federation=True)
    print(f"   Establish (cross-fed): {est_cost} ATP")
    print(f"   Breakdown: {est_breakdown}")

    maint_cost, maint_breakdown = engine.calculate_maintain_cost(0.8, is_cross_federation=True)
    print(f"\n   Maintain (trust=0.8, cross-fed): {maint_cost} ATP")
    print(f"   Breakdown: {maint_breakdown}")

    inc_cost, inc_breakdown = engine.calculate_increase_cost(0.5, 0.8, is_cross_federation=True)
    print(f"\n   Increase 0.5->0.8 (cross-fed): {inc_cost} ATP")
    print(f"   Breakdown: {inc_breakdown}")

    # Test Sybil attack cost estimation
    print("\n2. Sybil Attack Cost Estimation:")
    for num_feds in [2, 5, 10]:
        estimate = engine.estimate_sybil_attack_cost(num_feds)
        print(f"   {num_feds} federations: {estimate['total_attack_cost']:.1f} ATP total")
        print(f"     ({estimate['cost_per_fake_federation']:.1f} ATP per fake fed)")

    # Test entity charging
    print("\n3. Entity Charging:")
    engine.initialize_balance("fed:test", 1000.0)
    print(f"   Initial balance: {engine.get_balance('fed:test')} ATP")

    txn = engine.charge_operation(
        "fed:test",
        TrustOperationType.ESTABLISH,
        "fed:target",
        est_cost,
        {"note": "Test transaction"}
    )
    print(f"   Charged {est_cost} ATP, txn={txn.transaction_id}")
    print(f"   New balance: {engine.get_balance('fed:test')} ATP")

    print("\n" + "=" * 60)
    print("Self-test complete.")
