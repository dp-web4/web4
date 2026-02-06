"""
Economic Federation: ATP-Aware Multi-Federation Operations

Track BN: Integrates TrustEconomicsEngine with MultiFederationRegistry.

Every trust operation now has an ATP cost:
- Establishing trust relationships
- Maintaining trust (periodic)
- Increasing trust levels
- Creating proposals
- Approving proposals
- Providing external witness

This creates economic barriers against:
- Sybil attacks (expensive to create fake federations)
- Trust manipulation (expensive to rapidly increase trust)
- Collusion (expensive to maintain many trust relationships)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from hardbound.multi_federation import (
    MultiFederationRegistry,
    FederationProfile,
    InterFederationTrust,
    CrossFederationProposal,
    FederationRelationship,
)
from hardbound.trust_economics import (
    TrustEconomicsEngine,
    TrustCostPolicy,
    TrustOperationType,
    TrustTransaction,
)


@dataclass
class EconomicOperationResult:
    """Result of an ATP-gated trust operation."""
    success: bool
    operation_type: TrustOperationType
    atp_cost: float
    atp_remaining: float
    transaction: Optional[TrustTransaction] = None
    error: Optional[str] = None
    result_data: Dict = field(default_factory=dict)


class EconomicFederationRegistry:
    """
    Multi-federation registry with integrated ATP economics.

    Track BN: Every trust operation costs ATP.

    Wraps MultiFederationRegistry with economic checks and charges.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        economics: TrustEconomicsEngine = None,
        policy: TrustCostPolicy = None,
    ):
        """
        Initialize the economic federation registry.

        Args:
            db_path: Path to SQLite database for federation data
            economics: Existing economics engine (creates new if None)
            policy: Cost policy (uses defaults if None)
        """
        self.registry = MultiFederationRegistry(db_path=db_path)
        self.economics = economics or TrustEconomicsEngine(policy=policy)

        # Track maintenance schedules
        self._maintenance_due: Dict[str, str] = {}  # (source, target) -> next_due_date

    # === Federation Registration (free - no ATP cost) ===

    def register_federation(
        self,
        federation_id: str,
        name: str,
        initial_atp: float = 1000.0,
        **kwargs,
    ) -> Tuple[FederationProfile, float]:
        """
        Register a new federation with initial ATP balance.

        Federation registration is free to encourage participation.
        The initial ATP balance enables operations.

        Returns:
            (FederationProfile, initial_atp_balance)
        """
        profile = self.registry.register_federation(
            federation_id=federation_id,
            name=name,
            **kwargs,
        )

        # Initialize ATP balance
        self.economics.initialize_balance(federation_id, initial_atp)

        return profile, initial_atp

    def get_federation(self, federation_id: str) -> Optional[FederationProfile]:
        """Get federation profile."""
        return self.registry.get_federation(federation_id)

    def get_balance(self, federation_id: str) -> float:
        """Get federation's current ATP balance."""
        return self.economics.get_balance(federation_id)

    # === Trust Operations (all cost ATP) ===

    def establish_trust(
        self,
        source_federation_id: str,
        target_federation_id: str,
        relationship: FederationRelationship = FederationRelationship.PEER,
        initial_trust: float = 0.5,
        witness_allowed: bool = True,
    ) -> EconomicOperationResult:
        """
        Establish trust relationship, paying ATP cost.

        Track BN: Establishing trust costs ATP.
        Cross-federation relationships cost more.
        """
        # Calculate cost
        cost, breakdown = self.economics.calculate_establish_cost(
            is_cross_federation=True  # Always cross-federation in this context
        )

        # Check if source can afford
        if not self.economics.can_afford(source_federation_id, cost):
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.ESTABLISH,
                atp_cost=cost,
                atp_remaining=self.economics.get_balance(source_federation_id),
                error=f"Insufficient ATP: need {cost}, have {self.economics.get_balance(source_federation_id)}",
            )

        # Execute the trust establishment
        trust = self.registry.establish_trust(
            source_federation_id=source_federation_id,
            target_federation_id=target_federation_id,
            relationship=relationship,
            initial_trust=initial_trust,
            witness_allowed=witness_allowed,
        )

        # Charge ATP
        txn = self.economics.charge_operation(
            source_federation_id,
            TrustOperationType.ESTABLISH,
            target_federation_id,
            cost,
            details={"initial_trust": initial_trust, "relationship": relationship.value, **breakdown},
        )

        # Schedule maintenance
        self._schedule_maintenance(source_federation_id, target_federation_id)

        return EconomicOperationResult(
            success=True,
            operation_type=TrustOperationType.ESTABLISH,
            atp_cost=cost,
            atp_remaining=self.economics.get_balance(source_federation_id),
            transaction=txn,
            result_data={"trust": trust.__dict__ if trust else {}},
        )

    def increase_trust(
        self,
        source_federation_id: str,
        target_federation_id: str,
        target_trust: float,
    ) -> EconomicOperationResult:
        """
        Increase trust level, paying ATP cost.

        Track BN: Increasing trust requires ATP based on:
        - Amount of increase (per 0.1 increment)
        - Target trust level (higher = more expensive)
        """
        # Get current trust
        current_trust = self.registry.get_trust(source_federation_id, target_federation_id)
        if current_trust is None:
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.INCREASE,
                atp_cost=0,
                atp_remaining=self.economics.get_balance(source_federation_id),
                error="No existing trust relationship",
            )

        if target_trust <= current_trust.trust_score:
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.INCREASE,
                atp_cost=0,
                atp_remaining=self.economics.get_balance(source_federation_id),
                error=f"Target trust {target_trust} must be higher than current {current_trust.trust_score}",
            )

        # Calculate cost
        cost, breakdown = self.economics.calculate_increase_cost(
            current_trust=current_trust.trust_score,
            target_trust=target_trust,
            is_cross_federation=True,
        )

        # Check funds
        if not self.economics.can_afford(source_federation_id, cost):
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.INCREASE,
                atp_cost=cost,
                atp_remaining=self.economics.get_balance(source_federation_id),
                error=f"Insufficient ATP: need {cost}, have {self.economics.get_balance(source_federation_id)}",
            )

        # Check if increase is allowed by bootstrap limits
        max_by_age = self.registry._get_max_trust_by_age(
            self.registry.get_federation(target_federation_id).created_at
        )
        max_by_interactions = self.registry._get_max_trust_by_interactions(
            source_federation_id, target_federation_id
        )
        max_allowed = min(max_by_age, max_by_interactions)

        if target_trust > max_allowed:
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.INCREASE,
                atp_cost=0,
                atp_remaining=self.economics.get_balance(source_federation_id),
                error=f"Trust capped at {max_allowed} by bootstrap limits (age: {max_by_age}, interactions: {max_by_interactions})",
                result_data={"max_allowed": max_allowed, "max_by_age": max_by_age, "max_by_interactions": max_by_interactions},
            )

        # Execute the increase
        new_trust = self.registry.update_trust(
            source_federation_id, target_federation_id, target_trust
        )

        # Charge ATP
        txn = self.economics.charge_operation(
            source_federation_id,
            TrustOperationType.INCREASE,
            target_federation_id,
            cost,
            details={
                "from_trust": current_trust.trust_score,
                "to_trust": target_trust,
                **breakdown,
            },
        )

        return EconomicOperationResult(
            success=True,
            operation_type=TrustOperationType.INCREASE,
            atp_cost=cost,
            atp_remaining=self.economics.get_balance(source_federation_id),
            transaction=txn,
            result_data={"new_trust_score": new_trust},
        )

    def record_interaction(
        self,
        source_federation_id: str,
        target_federation_id: str,
        success: bool,
    ) -> EconomicOperationResult:
        """
        Record interaction between federations.

        Track BN: Successful interactions cost ATP (investment).
        Failed interactions are free (punishment is trust loss).
        """
        if success:
            # Successful interactions cost ATP
            cost = self.economics.policy.record_success_cost

            if not self.economics.can_afford(source_federation_id, cost):
                return EconomicOperationResult(
                    success=False,
                    operation_type=TrustOperationType.RECORD_SUCCESS,
                    atp_cost=cost,
                    atp_remaining=self.economics.get_balance(source_federation_id),
                    error="Insufficient ATP for interaction recording",
                )

            result = self.registry.record_interaction(
                source_federation_id, target_federation_id, success=True
            )

            txn = self.economics.charge_operation(
                source_federation_id,
                TrustOperationType.RECORD_SUCCESS,
                target_federation_id,
                cost,
            )

            return EconomicOperationResult(
                success=True,
                operation_type=TrustOperationType.RECORD_SUCCESS,
                atp_cost=cost,
                atp_remaining=self.economics.get_balance(source_federation_id),
                transaction=txn,
                result_data=result,
            )
        else:
            # Failed interactions are free
            result = self.registry.record_interaction(
                source_federation_id, target_federation_id, success=False
            )

            return EconomicOperationResult(
                success=True,
                operation_type=TrustOperationType.RECORD_FAILURE,
                atp_cost=0,
                atp_remaining=self.economics.get_balance(source_federation_id),
                result_data=result,
            )

    # === Proposal Operations ===

    def create_proposal(
        self,
        proposing_federation_id: str,
        proposing_team_id: str,
        affected_federation_ids: List[str],
        action_type: str,
        description: str,
    ) -> EconomicOperationResult:
        """
        Create a cross-federation proposal, paying ATP cost.

        Track BN: Proposals cost ATP based on number of affected federations.
        """
        # Calculate cost
        cost, breakdown = self.economics.calculate_proposal_cost(
            len(affected_federation_ids)
        )

        if not self.economics.can_afford(proposing_federation_id, cost):
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.CROSS_FED_PROPOSAL,
                atp_cost=cost,
                atp_remaining=self.economics.get_balance(proposing_federation_id),
                error="Insufficient ATP for proposal",
            )

        # Create proposal
        proposal = self.registry.create_cross_federation_proposal(
            proposing_federation_id=proposing_federation_id,
            proposing_team_id=proposing_team_id,
            affected_federation_ids=affected_federation_ids,
            action_type=action_type,
            description=description,
        )

        # Charge ATP
        txn = self.economics.charge_operation(
            proposing_federation_id,
            TrustOperationType.CROSS_FED_PROPOSAL,
            ",".join(affected_federation_ids),
            cost,
            details={"proposal_id": proposal.proposal_id, **breakdown},
        )

        return EconomicOperationResult(
            success=True,
            operation_type=TrustOperationType.CROSS_FED_PROPOSAL,
            atp_cost=cost,
            atp_remaining=self.economics.get_balance(proposing_federation_id),
            transaction=txn,
            result_data={"proposal": proposal.__dict__},
        )

    def approve_proposal(
        self,
        proposal_id: str,
        approving_federation_id: str,
        approving_teams: List[str],
    ) -> EconomicOperationResult:
        """
        Approve a cross-federation proposal, paying ATP cost.

        Track BN: Approvals cost ATP.
        """
        cost, breakdown = self.economics.calculate_approval_cost()

        if not self.economics.can_afford(approving_federation_id, cost):
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.CROSS_FED_APPROVAL,
                atp_cost=cost,
                atp_remaining=self.economics.get_balance(approving_federation_id),
                error="Insufficient ATP for approval",
            )

        # Record approval
        success = self.registry.approve_proposal(
            proposal_id=proposal_id,
            approving_federation_id=approving_federation_id,
            approving_teams=approving_teams,
        )

        if not success:
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.CROSS_FED_APPROVAL,
                atp_cost=0,
                atp_remaining=self.economics.get_balance(approving_federation_id),
                error="Approval failed (invalid proposal or federation)",
            )

        # Charge ATP
        txn = self.economics.charge_operation(
            approving_federation_id,
            TrustOperationType.CROSS_FED_APPROVAL,
            proposal_id,
            cost,
            details=breakdown,
        )

        return EconomicOperationResult(
            success=True,
            operation_type=TrustOperationType.CROSS_FED_APPROVAL,
            atp_cost=cost,
            atp_remaining=self.economics.get_balance(approving_federation_id),
            transaction=txn,
        )

    def provide_external_witness(
        self,
        proposal_id: str,
        witness_federation_id: str,
    ) -> EconomicOperationResult:
        """
        Provide external witness for a proposal, paying ATP cost.

        Track BN: Witnessing costs ATP (stake in the decision).
        """
        cost, breakdown = self.economics.calculate_witness_cost()

        if not self.economics.can_afford(witness_federation_id, cost):
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.EXTERNAL_WITNESS,
                atp_cost=cost,
                atp_remaining=self.economics.get_balance(witness_federation_id),
                error="Insufficient ATP for witnessing",
            )

        # Add witness
        success = self.registry.add_external_witness(
            proposal_id=proposal_id,
            witness_federation_id=witness_federation_id,
        )

        if not success:
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.EXTERNAL_WITNESS,
                atp_cost=0,
                atp_remaining=self.economics.get_balance(witness_federation_id),
                error="Witness failed (ineligible or already witnessed)",
            )

        # Charge ATP
        txn = self.economics.charge_operation(
            witness_federation_id,
            TrustOperationType.EXTERNAL_WITNESS,
            proposal_id,
            cost,
            details=breakdown,
        )

        return EconomicOperationResult(
            success=True,
            operation_type=TrustOperationType.EXTERNAL_WITNESS,
            atp_cost=cost,
            atp_remaining=self.economics.get_balance(witness_federation_id),
            transaction=txn,
        )

    # === Maintenance Operations ===

    def _schedule_maintenance(
        self,
        source_federation_id: str,
        target_federation_id: str,
    ):
        """Schedule next maintenance payment for a trust relationship."""
        next_due = datetime.now(timezone.utc) + timedelta(
            days=self.economics.policy.maintenance_period_days
        )
        # Use tuple as key to avoid colon parsing issues
        key = (source_federation_id, target_federation_id)
        self._maintenance_due[key] = next_due.isoformat()

    def get_maintenance_due(
        self,
        federation_id: str,
    ) -> List[Dict]:
        """
        Get all trust relationships that need maintenance.

        Returns:
            List of relationships with maintenance info
        """
        now = datetime.now(timezone.utc)
        due_relationships = []

        for key, due_date_str in self._maintenance_due.items():
            source, target = key
            if source == federation_id:
                due_date = datetime.fromisoformat(due_date_str)
                if now >= due_date:
                    trust = self.registry.get_trust(source, target)
                    if trust:
                        cost, _ = self.economics.calculate_maintain_cost(
                            trust.trust_score, is_cross_federation=True
                        )
                        due_relationships.append({
                            "target_federation": target,
                            "trust_score": trust.trust_score,
                            "maintenance_cost": cost,
                            "due_date": due_date_str,
                            "overdue": True,
                        })

        return due_relationships

    def pay_maintenance(
        self,
        source_federation_id: str,
        target_federation_id: str,
    ) -> EconomicOperationResult:
        """
        Pay maintenance for a trust relationship.

        Track BN: Trust relationships require periodic ATP maintenance.
        Failure to maintain causes trust decay.
        """
        trust = self.registry.get_trust(source_federation_id, target_federation_id)
        if not trust:
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.MAINTAIN,
                atp_cost=0,
                atp_remaining=self.economics.get_balance(source_federation_id),
                error="No trust relationship found",
            )

        cost, breakdown = self.economics.calculate_maintain_cost(
            trust.trust_score, is_cross_federation=True
        )

        if not self.economics.can_afford(source_federation_id, cost):
            return EconomicOperationResult(
                success=False,
                operation_type=TrustOperationType.MAINTAIN,
                atp_cost=cost,
                atp_remaining=self.economics.get_balance(source_federation_id),
                error="Insufficient ATP for maintenance",
                result_data={"trust_may_decay": True},
            )

        # Charge ATP
        txn = self.economics.charge_operation(
            source_federation_id,
            TrustOperationType.MAINTAIN,
            target_federation_id,
            cost,
            details={"trust_score": trust.trust_score, **breakdown},
        )

        # Reschedule next maintenance
        self._schedule_maintenance(source_federation_id, target_federation_id)

        return EconomicOperationResult(
            success=True,
            operation_type=TrustOperationType.MAINTAIN,
            atp_cost=cost,
            atp_remaining=self.economics.get_balance(source_federation_id),
            transaction=txn,
            result_data={"trust_maintained": True, "next_due_days": self.economics.policy.maintenance_period_days},
        )

    # === Economic Analysis ===

    def get_federation_economics(
        self,
        federation_id: str,
    ) -> Dict:
        """
        Get comprehensive economic analysis for a federation.
        """
        balance = self.economics.get_balance(federation_id)
        costs_summary = self.economics.get_entity_costs_summary(federation_id)
        maintenance_due = self.get_maintenance_due(federation_id)

        # Calculate upcoming maintenance costs
        upcoming_maintenance_cost = sum(r["maintenance_cost"] for r in maintenance_due)

        return {
            "federation_id": federation_id,
            "current_balance": balance,
            "costs_30_day": costs_summary,
            "maintenance_due": maintenance_due,
            "upcoming_maintenance_cost": upcoming_maintenance_cost,
            "projected_balance_after_maintenance": balance - upcoming_maintenance_cost,
            "health": "healthy" if balance > upcoming_maintenance_cost * 2 else (
                "warning" if balance > upcoming_maintenance_cost else "critical"
            ),
        }

    def estimate_operation_impact(
        self,
        federation_id: str,
        operation: TrustOperationType,
        **kwargs,
    ) -> Dict:
        """
        Estimate the ATP impact of an operation before executing.
        """
        balance = self.economics.get_balance(federation_id)

        if operation == TrustOperationType.ESTABLISH:
            cost, breakdown = self.economics.calculate_establish_cost(
                is_cross_federation=kwargs.get("is_cross_federation", True)
            )
        elif operation == TrustOperationType.INCREASE:
            cost, breakdown = self.economics.calculate_increase_cost(
                kwargs.get("current_trust", 0.5),
                kwargs.get("target_trust", 0.6),
                is_cross_federation=kwargs.get("is_cross_federation", True),
            )
        elif operation == TrustOperationType.MAINTAIN:
            cost, breakdown = self.economics.calculate_maintain_cost(
                kwargs.get("trust_level", 0.5),
                is_cross_federation=kwargs.get("is_cross_federation", True),
            )
        elif operation == TrustOperationType.CROSS_FED_PROPOSAL:
            cost, breakdown = self.economics.calculate_proposal_cost(
                kwargs.get("affected_federations", 1)
            )
        elif operation == TrustOperationType.CROSS_FED_APPROVAL:
            cost, breakdown = self.economics.calculate_approval_cost()
        elif operation == TrustOperationType.EXTERNAL_WITNESS:
            cost, breakdown = self.economics.calculate_witness_cost()
        else:
            cost, breakdown = 0, {"unknown_operation": True}

        return {
            "operation": operation.value,
            "estimated_cost": cost,
            "current_balance": balance,
            "balance_after": balance - cost,
            "can_afford": balance >= cost,
            "breakdown": breakdown,
        }


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Economic Federation Registry - Self Test")
    print("=" * 60)

    import tempfile

    db_path = Path(tempfile.mkdtemp()) / "economic_fed_test.db"
    registry = EconomicFederationRegistry(db_path=db_path)

    # Register federations
    print("\n1. Register federations with initial ATP:")
    fed_a, balance_a = registry.register_federation("fed:alpha", "Alpha Federation", initial_atp=1000)
    fed_b, balance_b = registry.register_federation("fed:beta", "Beta Federation", initial_atp=1000)
    fed_c, balance_c = registry.register_federation("fed:gamma", "Gamma Federation", initial_atp=500)
    print(f"   Alpha: {balance_a} ATP")
    print(f"   Beta: {balance_b} ATP")
    print(f"   Gamma: {balance_c} ATP")

    # Establish trust (costs ATP)
    print("\n2. Establish trust relationships:")
    result = registry.establish_trust("fed:alpha", "fed:beta")
    print(f"   Alpha -> Beta: {'OK' if result.success else 'FAILED'}")
    print(f"   Cost: {result.atp_cost} ATP, Remaining: {result.atp_remaining} ATP")

    result = registry.establish_trust("fed:beta", "fed:alpha")
    print(f"   Beta -> Alpha: {'OK' if result.success else 'FAILED'}")
    print(f"   Cost: {result.atp_cost} ATP, Remaining: {result.atp_remaining} ATP")

    # Try with low balance
    result = registry.establish_trust("fed:gamma", "fed:alpha")
    print(f"\n3. Gamma -> Alpha (500 ATP balance):")
    print(f"   {'OK' if result.success else 'FAILED'}: {result.error or 'Success'}")
    print(f"   Cost: {result.atp_cost} ATP")

    # Record successful interactions
    print("\n4. Record interactions (costs 1 ATP each):")
    for i in range(3):
        result = registry.record_interaction("fed:alpha", "fed:beta", success=True)
        if i == 0:
            print(f"   Success recording cost: {result.atp_cost} ATP")

    result = registry.record_interaction("fed:alpha", "fed:beta", success=False)
    print(f"   Failure recording cost: {result.atp_cost} ATP (free)")

    # Get economics summary
    print("\n5. Economic summary for Alpha:")
    economics = registry.get_federation_economics("fed:alpha")
    print(f"   Balance: {economics['current_balance']:.1f} ATP")
    print(f"   30-day spend: {economics['costs_30_day']['total_spent']:.1f} ATP")
    print(f"   Health: {economics['health']}")

    # Estimate operation impact
    print("\n6. Operation cost estimates:")
    for op in [TrustOperationType.ESTABLISH, TrustOperationType.CROSS_FED_PROPOSAL]:
        estimate = registry.estimate_operation_impact("fed:alpha", op, affected_federations=3)
        print(f"   {op.value}: {estimate['estimated_cost']:.1f} ATP")

    print("\n" + "=" * 60)
    print("Self-test complete.")
