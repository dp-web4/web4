#!/usr/bin/env python3
"""
Session 93 Track 2: ATP Lock-Commit-Rollback for Remote IRP Invocations

**Date**: 2025-12-27
**Platform**: Legion (RTX 4090)
**Track**: 2 of 3 - Fractal IRP Integration

## Problem Statement

Remote IRP invocations need fair resource settlement:
- **Lock** ATP budget before invocation (prevent double-spend)
- **Commit** ATP to executor on successful completion (quality ≥ threshold)
- **Rollback** ATP to caller on failure or low quality

This is the economic layer that enables:
1. Fair payment for IRP execution
2. Protection against low-quality work
3. Prevention of ATP theft/fraud
4. Incentive alignment for quality work

## Solution: ATP Lock-Commit-Rollback Protocol

Three-phase transaction model:

```
Phase 1: LOCK
  - Caller locks ATP budget before IRP invoke
  - ATP unavailable to caller during execution
  - Prevents double-spend

Phase 2: EXECUTE
  - Remote IRP runs with locked budget
  - Executor cannot access locked ATP
  - IRP returns quality signal

Phase 3: SETTLE
  - If quality ≥ 0.70: COMMIT (ATP → executor)
  - If quality < 0.70: ROLLBACK (ATP → caller)
  - Settlement is atomic (no partial transfers)
```

## Integration with Previous Work

- **Session 92 Track 1**: Cross-federation delegation enables ATP transfer across federations
- **Session 92 Track 2**: Metabolic states affect quality thresholds
- **Session 93 Track 1**: IRP expert registry provides cost estimates

## Test Scenarios

1. **Successful Commit**: High-quality IRP result commits ATP to executor
2. **Quality Rollback**: Low-quality result rolls back ATP to caller
3. **Failure Rollback**: IRP failure rolls back ATP
4. **Double-Spend Prevention**: Cannot spend locked ATP
5. **Cross-Federation Settlement**: ATP transfers across federation boundaries

## Implementation

Based on lock-commit-rollback pattern from distributed databases,
adapted for Web4 ATP economics.
"""

import time
import secrets
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path

# Import from previous sessions
from session93_track1_irp_expert_registry import (
    IRPExpertRegistry,
    IRPExpertDescriptor,
    TaskContext,
)

from session92_track2_metabolic_reputation import (
    MetabolicState,
)

from session88_track1_lct_society_authentication import (
    LCTIdentity,
    create_test_lct_identity,
)


# =============================================================================
# ATP Transaction States
# =============================================================================

class TransactionState(Enum):
    """State of ATP transaction."""
    PENDING = "pending"        # Created but not locked
    LOCKED = "locked"          # ATP locked, execution in progress
    COMMITTED = "committed"    # ATP transferred to executor
    ROLLED_BACK = "rolled_back"  # ATP returned to caller
    FAILED = "failed"          # Transaction failed (ATP returned)


@dataclass
class ATPTransaction:
    """ATP lock-commit-rollback transaction."""

    # Transaction ID
    tx_id: str = field(default_factory=lambda: f"tx_{secrets.token_hex(16)}")

    # Parties
    caller_id: str = ""  # LCT URI of caller
    executor_id: str = ""  # LCT URI of executor (IRP expert)

    # Amount
    amount: float = 0.0  # ATP amount

    # State
    state: TransactionState = TransactionState.PENDING

    # Quality signal (set after execution)
    quality: Optional[float] = None  # 0.0 - 1.0

    # Quality threshold for commit
    commit_threshold: float = 0.70

    # Timestamps
    created_at: float = field(default_factory=time.time)
    locked_at: Optional[float] = None
    settled_at: Optional[float] = None

    # Metadata
    expert_descriptor_id: Optional[str] = None
    task_context: Optional[str] = None  # JSON serialized


# =============================================================================
# ATP Settlement Manager
# =============================================================================

class ATPSettlementManager:
    """Manages ATP lock-commit-rollback for IRP invocations."""

    def __init__(self):
        # ATP balances (LCT URI → balance)
        self.balances: Dict[str, float] = {}

        # Locked ATP (LCT URI → locked amount)
        self.locked: Dict[str, float] = {}

        # Transactions
        self.transactions: Dict[str, ATPTransaction] = {}

    def initialize_account(self, lct_uri: str, initial_balance: float = 100.0):
        """Initialize ATP account for agent."""
        self.balances[lct_uri] = initial_balance
        self.locked[lct_uri] = 0.0

    def get_available_balance(self, lct_uri: str) -> float:
        """Get available (unlocked) ATP balance."""
        total = self.balances.get(lct_uri, 0.0)
        locked = self.locked.get(lct_uri, 0.0)
        return total - locked

    def lock_atp(
        self,
        caller_lct: str,
        executor_lct: str,
        amount: float,
        commit_threshold: float = 0.70,
        expert_id: Optional[str] = None
    ) -> Optional[str]:
        """Lock ATP for remote IRP invocation.

        Args:
            caller_lct: Caller's LCT URI
            executor_lct: Executor's LCT URI
            amount: ATP amount to lock
            commit_threshold: Quality threshold for commit
            expert_id: IRP expert descriptor ID

        Returns:
            Transaction ID if successful, None if insufficient funds
        """
        # Check available balance
        available = self.get_available_balance(caller_lct)
        if available < amount:
            return None  # Insufficient funds

        # Create transaction
        tx = ATPTransaction(
            caller_id=caller_lct,
            executor_id=executor_lct,
            amount=amount,
            state=TransactionState.LOCKED,
            commit_threshold=commit_threshold,
            expert_descriptor_id=expert_id
        )
        tx.locked_at = time.time()

        # Lock ATP
        self.locked[caller_lct] = self.locked.get(caller_lct, 0.0) + amount

        # Store transaction
        self.transactions[tx.tx_id] = tx

        return tx.tx_id

    def commit_atp(self, tx_id: str, quality: float) -> bool:
        """Commit ATP to executor (successful execution).

        Args:
            tx_id: Transaction ID
            quality: Quality signal (0.0 - 1.0)

        Returns:
            True if committed, False if rolled back
        """
        if tx_id not in self.transactions:
            raise ValueError(f"Unknown transaction: {tx_id}")

        tx = self.transactions[tx_id]

        if tx.state != TransactionState.LOCKED:
            raise ValueError(f"Transaction not locked: {tx.state.value}")

        # Set quality
        tx.quality = quality

        # Check quality threshold
        if quality >= tx.commit_threshold:
            # COMMIT: Transfer ATP to executor
            self.balances[tx.caller_id] -= tx.amount
            self.locked[tx.caller_id] -= tx.amount
            self.balances[tx.executor_id] = self.balances.get(tx.executor_id, 0.0) + tx.amount

            tx.state = TransactionState.COMMITTED
            tx.settled_at = time.time()

            return True
        else:
            # ROLLBACK: Return ATP to caller
            self.locked[tx.caller_id] -= tx.amount

            tx.state = TransactionState.ROLLED_BACK
            tx.settled_at = time.time()

            return False

    def rollback_atp(self, tx_id: str, reason: str = "failure") -> bool:
        """Rollback ATP to caller (failed execution).

        Args:
            tx_id: Transaction ID
            reason: Rollback reason

        Returns:
            True if rolled back successfully
        """
        if tx_id not in self.transactions:
            raise ValueError(f"Unknown transaction: {tx_id}")

        tx = self.transactions[tx_id]

        if tx.state != TransactionState.LOCKED:
            raise ValueError(f"Transaction not locked: {tx.state.value}")

        # ROLLBACK: Return ATP to caller
        self.locked[tx.caller_id] -= tx.amount

        tx.state = TransactionState.FAILED if reason == "failure" else TransactionState.ROLLED_BACK
        tx.settled_at = time.time()

        return True

    def get_transaction_status(self, tx_id: str) -> Optional[ATPTransaction]:
        """Get transaction status."""
        return self.transactions.get(tx_id)


# =============================================================================
# Integrated IRP Invocation with ATP Settlement
# =============================================================================

@dataclass
class IRPInvocationResult:
    """Result of IRP invocation with ATP settlement."""

    # Transaction
    tx_id: str
    settled: bool  # True if ATP committed, False if rolled back

    # IRP result
    quality: float
    confidence: float
    outputs: Dict

    # ATP settlement
    atp_amount: float
    commit_threshold: float


def invoke_irp_with_settlement(
    registry: IRPExpertRegistry,
    settlement: ATPSettlementManager,
    caller_lct: str,
    expert_id: str,
    task_context: TaskContext,
    inputs: Dict
) -> IRPInvocationResult:
    """Invoke remote IRP with ATP lock-commit-rollback settlement.

    Args:
        registry: IRP expert registry
        settlement: ATP settlement manager
        caller_lct: Caller's LCT URI
        expert_id: Expert ID
        task_context: Task context
        inputs: Task inputs

    Returns:
        IRPInvocationResult with settlement outcome
    """
    # Get expert
    expert = registry.experts.get(expert_id)
    if not expert:
        raise ValueError(f"Unknown expert: {expert_id}")

    executor_lct = expert.identity.lct_identity.to_lct_uri()

    # Estimate cost (use p95 for budgeting)
    cost = expert.cost_model.estimate_p95

    # PHASE 1: LOCK ATP
    tx_id = settlement.lock_atp(
        caller_lct=caller_lct,
        executor_lct=executor_lct,
        amount=cost,
        commit_threshold=0.70,  # Default threshold
        expert_id=expert_id
    )

    if not tx_id:
        raise ValueError("Insufficient ATP balance")

    # PHASE 2: EXECUTE IRP (simulated)
    # In production, this would be actual remote invocation
    # For testing, we simulate based on expert capabilities
    simulated_quality = 0.85 if "verification_oriented" in [t.value for t in expert.capabilities.tags] else 0.60
    simulated_confidence = 0.80

    outputs = {
        "result": "IRP execution completed",
        "expert": expert.name,
        "inputs_received": inputs
    }

    # PHASE 3: SETTLE ATP
    settled = settlement.commit_atp(tx_id, quality=simulated_quality)

    return IRPInvocationResult(
        tx_id=tx_id,
        settled=settled,
        quality=simulated_quality,
        confidence=simulated_confidence,
        outputs=outputs,
        atp_amount=cost,
        commit_threshold=0.70
    )


# =============================================================================
# Test Scenarios
# =============================================================================

def test_successful_commit():
    """Test Scenario 1: High-quality IRP result commits ATP to executor."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 1: Successful ATP Commit")
    print("=" * 80)

    settlement = ATPSettlementManager()
    registry = IRPExpertRegistry()

    # Create caller and executor
    caller, caller_priv = create_test_lct_identity("alice", "web4.network")
    executor, executor_priv = create_test_lct_identity("sage_expert", "web4.network")

    caller_lct = caller.to_lct_uri()
    executor_lct = executor.to_lct_uri()

    # Initialize accounts
    settlement.initialize_account(caller_lct, initial_balance=100.0)
    settlement.initialize_account(executor_lct, initial_balance=0.0)

    # Register expert (high-quality)
    from session93_track1_irp_expert_registry import IRPExpertDescriptor, ExpertKind, IRPCapabilities, CapabilityTag, IRPCostModel
    expert_desc = IRPExpertDescriptor(
        kind=ExpertKind.LOCAL_IRP,
        name="high_quality_expert",
        capabilities=IRPCapabilities(tags=[CapabilityTag.VERIFICATION_ORIENTED]),
        cost_model=IRPCostModel(estimate_p50=10.0, estimate_p95=15.0)
    )
    expert_id = registry.register_expert(expert_desc, executor, executor_priv)

    print(f"\n💰 Initial balances:")
    print(f"  Caller ({caller_lct[:30]}...): {settlement.balances[caller_lct]} ATP")
    print(f"  Executor ({executor_lct[:30]}...): {settlement.balances[executor_lct]} ATP")

    # Invoke IRP
    result = invoke_irp_with_settlement(
        registry=registry,
        settlement=settlement,
        caller_lct=caller_lct,
        expert_id=expert_id,
        task_context=TaskContext(salience=0.7, confidence=0.6, budget_remaining=100.0),
        inputs={"task": "verify_claim"}
    )

    print(f"\n🔄 IRP Execution:")
    print(f"  Quality: {result.quality:.2f}")
    print(f"  Threshold: {result.commit_threshold:.2f}")
    print(f"  Cost: {result.atp_amount} ATP")

    print(f"\n💰 Final balances:")
    print(f"  Caller: {settlement.balances[caller_lct]} ATP")
    print(f"  Executor: {settlement.balances[executor_lct]} ATP")

    print(f"\n✅ Settlement: {'COMMITTED' if result.settled else 'ROLLED_BACK'}")

    # Verify ATP transferred
    assert result.settled is True
    assert settlement.balances[caller_lct] == 100.0 - result.atp_amount
    assert settlement.balances[executor_lct] == result.atp_amount

    return {"status": "success", "committed": True, "atp_transferred": result.atp_amount}


def test_quality_rollback():
    """Test Scenario 2: Low-quality result rolls back ATP to caller."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 2: Quality Rollback")
    print("=" * 80)

    settlement = ATPSettlementManager()
    registry = IRPExpertRegistry()

    # Create accounts
    caller, caller_priv = create_test_lct_identity("alice", "web4.network")
    executor, executor_priv = create_test_lct_identity("low_quality_expert", "web4.network")

    caller_lct = caller.to_lct_uri()
    executor_lct = executor.to_lct_uri()

    settlement.initialize_account(caller_lct, 100.0)
    settlement.initialize_account(executor_lct, 0.0)

    # Register low-quality expert
    from session93_track1_irp_expert_registry import IRPExpertDescriptor, ExpertKind, IRPCapabilities, IRPCostModel
    expert_desc = IRPExpertDescriptor(
        kind=ExpertKind.LOCAL_IRP,
        name="cheap_low_quality",
        capabilities=IRPCapabilities(tags=[]),  # No quality tags
        cost_model=IRPCostModel(estimate_p50=5.0, estimate_p95=8.0)
    )
    expert_id = registry.register_expert(expert_desc, executor, executor_priv)

    print(f"\n💰 Initial balances:")
    print(f"  Caller: {settlement.balances[caller_lct]} ATP")
    print(f"  Executor: {settlement.balances[executor_lct]} ATP")

    # Invoke IRP (will produce low quality due to no quality tags)
    result = invoke_irp_with_settlement(
        registry=registry,
        settlement=settlement,
        caller_lct=caller_lct,
        expert_id=expert_id,
        task_context=TaskContext(salience=0.5, confidence=0.8, budget_remaining=100.0),
        inputs={"task": "quick_task"}
    )

    print(f"\n🔄 IRP Execution:")
    print(f"  Quality: {result.quality:.2f}")
    print(f"  Threshold: {result.commit_threshold:.2f}")
    print(f"  Below threshold: {result.quality < result.commit_threshold}")

    print(f"\n💰 Final balances:")
    print(f"  Caller: {settlement.balances[caller_lct]} ATP (unchanged)")
    print(f"  Executor: {settlement.balances[executor_lct]} ATP (no payment)")

    print(f"\n✅ Settlement: {'COMMITTED' if result.settled else 'ROLLED_BACK'}")

    # Verify ATP returned to caller
    assert result.settled is False
    assert settlement.balances[caller_lct] == 100.0  # Unchanged
    assert settlement.balances[executor_lct] == 0.0  # No payment

    return {"status": "success", "committed": False, "rollback_reason": "low_quality"}


def test_double_spend_prevention():
    """Test Scenario 3: Cannot spend locked ATP."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 3: Double-Spend Prevention")
    print("=" * 80)

    settlement = ATPSettlementManager()

    # Create account
    caller, _ = create_test_lct_identity("alice", "web4.network")
    executor1, _ = create_test_lct_identity("expert1", "web4.network")
    executor2, _ = create_test_lct_identity("expert2", "web4.network")

    caller_lct = caller.to_lct_uri()
    executor1_lct = executor1.to_lct_uri()
    executor2_lct = executor2.to_lct_uri()

    settlement.initialize_account(caller_lct, 100.0)

    print(f"\n💰 Initial balance: {settlement.balances[caller_lct]} ATP")

    # Lock ATP for first transaction
    tx1 = settlement.lock_atp(caller_lct, executor1_lct, 80.0)
    print(f"\n🔒 Transaction 1: Locked 80 ATP")
    print(f"  Available balance: {settlement.get_available_balance(caller_lct)} ATP")

    # Try to lock more ATP than available
    tx2 = settlement.lock_atp(caller_lct, executor2_lct, 30.0)
    print(f"\n🔒 Transaction 2: Attempting to lock 30 ATP (only 20 available)")
    print(f"  Result: {'SUCCESS' if tx2 else 'FAILED (insufficient funds)'}")

    # Verify second lock failed
    assert tx1 is not None
    assert tx2 is None  # Should fail

    # Try with available amount
    tx3 = settlement.lock_atp(caller_lct, executor2_lct, 15.0)
    print(f"\n🔒 Transaction 3: Attempting to lock 15 ATP (within available 20)")
    print(f"  Result: {'SUCCESS' if tx3 else 'FAILED'}")
    print(f"  Available balance: {settlement.get_available_balance(caller_lct)} ATP")

    assert tx3 is not None  # Should succeed

    return {"status": "success", "double_spend_prevented": True}


# =============================================================================
# Main Test Execution
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SESSION 93 TRACK 2: ATP LOCK-COMMIT-ROLLBACK SETTLEMENT")
    print("=" * 80)

    results = {}

    # Run test scenarios
    results["scenario_1"] = test_successful_commit()
    results["scenario_2"] = test_quality_rollback()
    results["scenario_3"] = test_double_spend_prevention()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_success = all(r["status"] == "success" for r in results.values())

    print(f"\n✅ All scenarios passed: {all_success}")
    print(f"\nScenarios tested:")
    print(f"  1. Successful ATP commit (quality ≥ 0.70)")
    print(f"  2. Quality rollback (quality < 0.70)")
    print(f"  3. Double-spend prevention (locked ATP unavailable)")

    # Save results
    results_file = Path(__file__).parent / "session93_track2_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to: {results_file}")

    print("\n" + "=" * 80)
    print("Key Innovations:")
    print("=" * 80)
    print("1. Three-phase ATP settlement (LOCK → EXECUTE → SETTLE)")
    print("2. Quality-based commit/rollback (threshold = 0.70)")
    print("3. Double-spend prevention via locked balances")
    print("4. Fair payment: executor paid only for quality work")
    print("5. Caller protection: ATP returned on failure/low quality")
    print("\nATP Lock-Commit-Rollback creates fair economic settlement for")
    print("remote IRP invocations, enabling Web4's decentralized AI marketplace.")
    print("=" * 80)
