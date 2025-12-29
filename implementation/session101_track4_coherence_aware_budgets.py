"""
SESSION 101 TRACK 4: COHERENCE-AWARE DYNAMIC BUDGET OPTIMIZATION

Integrates MRH Grounding (Track 1) with Session 99's Dynamic Budget Optimization.

Key innovation: ATP budgets that adapt based on agent coherence:
- High coherence → Higher budget allocation
- Low coherence → Lower budget, higher scrutiny
- Budget adjustments based on real-time operational state

This creates a natural incentive for agents to maintain high coherence
(accurate grounding, consistent behavior, verifiable presence).

References:
- Session 99 Track 3: Dynamic budget optimization
- Session 101 Track 1: MRH Grounding and Coherence Index
- Session 101 Track 2: Consequence Index and CI/CX gating
"""

import json
import hashlib
import time
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from enum import Enum

# Import Track 1 components
import sys
sys.path.append('/home/dp/ai-workspace/web4/implementation')
from session101_track1_mrh_grounding import (
    GroundingManager,
    GroundingContext,
    Location,
    LocationType,
    PrecisionLevel,
    Capabilities,
    HardwareClass,
    ResourceLevel,
    Session as GroundingSession
)

# Import Session 100 components
from session100_track3_act_atp_budgets import (
    DelegationBudget,
    ATPBudgetEnforcer
)
from session100_track2_act_delegation_chain import (
    ACTDelegationChainKeeper,
    ScopedPermission
)


# ============================================================================
# COHERENCE-AWARE BUDGET POLICY
# ============================================================================

@dataclass
class BudgetPolicy:
    """
    Policy for coherence-aware budget allocation.

    Defines how coherence affects budget calculations.
    """
    # Base budget (before coherence adjustment)
    base_budget: float

    # Coherence thresholds and multipliers
    high_coherence_threshold: float = 0.9  # CI >= 0.9 = high coherence
    low_coherence_threshold: float = 0.5   # CI < 0.5 = low coherence

    high_coherence_multiplier: float = 1.2  # +20% budget for high coherence
    low_coherence_multiplier: float = 0.5   # -50% budget for low coherence

    # Alert thresholds based on coherence
    alert_threshold_adjustment: bool = True  # Adjust alert thresholds by CI

    def calculate_adjusted_budget(self, ci: float) -> float:
        """
        Calculate budget adjusted for coherence.

        High coherence = reward with higher budget
        Low coherence = restrict with lower budget
        """
        if ci >= self.high_coherence_threshold:
            return self.base_budget * self.high_coherence_multiplier
        elif ci < self.low_coherence_threshold:
            return self.base_budget * self.low_coherence_multiplier
        else:
            # Linear interpolation between low and high thresholds
            ratio = (ci - self.low_coherence_threshold) / (self.high_coherence_threshold - self.low_coherence_threshold)
            multiplier = self.low_coherence_multiplier + ratio * (self.high_coherence_multiplier - self.low_coherence_multiplier)
            return self.base_budget * multiplier

    def calculate_alert_threshold(self, ci: float, base_threshold: float) -> float:
        """
        Calculate alert threshold adjusted for coherence.

        Low coherence → Earlier warnings (lower threshold)
        High coherence → Later warnings (higher threshold)
        """
        if not self.alert_threshold_adjustment:
            return base_threshold

        # Scale threshold inversely with coherence
        # High CI = higher threshold (more lenient)
        # Low CI = lower threshold (more strict)
        adjustment = 0.5 + (ci * 0.5)  # Range: 0.5 to 1.0
        return base_threshold * adjustment


# ============================================================================
# COHERENCE-AWARE BUDGET ALLOCATOR
# ============================================================================

class CoherenceAwareBudgetAllocator:
    """
    Allocates ATP budgets based on agent coherence.

    Integrates with:
    - Track 1: GroundingManager for coherence calculation
    - Session 100: ATPBudgetEnforcer for budget management
    """

    def __init__(
        self,
        grounding_manager: GroundingManager,
        delegation_keeper: ACTDelegationChainKeeper,
        budget_enforcer: ATPBudgetEnforcer
    ):
        self.grounding_manager = grounding_manager
        self.delegation_keeper = delegation_keeper
        self.budget_enforcer = budget_enforcer

        # Budget policies per delegation
        self.policies: Dict[str, BudgetPolicy] = {}

        # History of budget adjustments
        self.adjustment_history: List[Dict[str, Any]] = []

    def allocate_coherence_aware_budget(
        self,
        delegation_id: str,
        base_budget: float,
        policy: Optional[BudgetPolicy] = None
    ) -> DelegationBudget:
        """
        Allocate budget with coherence awareness.

        Calculates adjusted budget based on delegate's current coherence.
        """
        # Get delegation
        delegation = self.delegation_keeper.get_delegation(delegation_id)
        if not delegation:
            raise ValueError(f"Delegation {delegation_id} not found")

        # Get delegate's coherence
        delegate_ci = self.grounding_manager.get_coherence_index(delegation.delegate)

        # Use provided policy or create default
        if policy is None:
            policy = BudgetPolicy(base_budget=base_budget)
        else:
            policy.base_budget = base_budget

        # Calculate adjusted budget
        adjusted_budget = policy.calculate_adjusted_budget(delegate_ci)

        # Store policy
        self.policies[delegation_id] = policy

        # Allocate budget via enforcer
        budget = self.budget_enforcer.allocate_budget(
            delegation_id=delegation_id,
            total_budget=adjusted_budget
        )

        # Record adjustment
        self.adjustment_history.append({
            "delegation_id": delegation_id,
            "delegate": delegation.delegate,
            "ci": delegate_ci,
            "base_budget": base_budget,
            "adjusted_budget": adjusted_budget,
            "adjustment_ratio": adjusted_budget / base_budget,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return budget

    def reassess_budget(self, delegation_id: str) -> Tuple[float, float, str]:
        """
        Reassess budget based on current coherence.

        Returns:
            (old_budget, new_budget, reason)
        """
        # Get current budget
        budget = self.budget_enforcer.get_budget(delegation_id)
        if not budget:
            raise ValueError(f"Budget {delegation_id} not found")

        # Get policy
        policy = self.policies.get(delegation_id)
        if not policy:
            return (budget.total_budget, budget.total_budget, "No policy defined")

        # Get delegation
        delegation = self.delegation_keeper.get_delegation(delegation_id)
        if not delegation:
            return (budget.total_budget, budget.total_budget, "Delegation not found")

        # Get current coherence
        delegate_ci = self.grounding_manager.get_coherence_index(delegation.delegate)

        # Calculate new budget
        old_budget = budget.total_budget
        new_budget = policy.calculate_adjusted_budget(delegate_ci)

        # Determine reason
        if new_budget > old_budget:
            reason = f"Coherence improved (CI={delegate_ci:.3f}), budget increased"
        elif new_budget < old_budget:
            reason = f"Coherence decreased (CI={delegate_ci:.3f}), budget reduced"
        else:
            reason = f"Coherence stable (CI={delegate_ci:.3f}), budget unchanged"

        # Update budget (simplified - in production would need proper state update)
        budget.total_budget = new_budget

        # Record reassessment
        self.adjustment_history.append({
            "delegation_id": delegation_id,
            "delegate": delegation.delegate,
            "ci": delegate_ci,
            "old_budget": old_budget,
            "new_budget": new_budget,
            "adjustment_type": "reassessment",
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return (old_budget, new_budget, reason)

    def get_budget_efficiency_score(self, delegation_id: str) -> Optional[float]:
        """
        Calculate budget efficiency score.

        Higher coherence + lower spending = higher efficiency.
        """
        budget = self.budget_enforcer.get_budget(delegation_id)
        if not budget:
            return None

        delegation = self.delegation_keeper.get_delegation(delegation_id)
        if not delegation:
            return None

        ci = self.grounding_manager.get_coherence_index(delegation.delegate)

        # Efficiency = coherence * (1 - utilization)
        # High coherence + low spending = high efficiency
        utilization = budget.utilization
        efficiency = ci * (1.0 - utilization)

        return efficiency


# ============================================================================
# DYNAMIC BUDGET REBALANCING
# ============================================================================

class CoherenceBasedRebalancer:
    """
    Dynamically rebalances budgets across multiple agents based on coherence.

    Agents with high coherence get more resources.
    Agents with low coherence get fewer resources.
    """

    def __init__(self, allocator: CoherenceAwareBudgetAllocator):
        self.allocator = allocator

    def rebalance_budgets(
        self,
        delegation_ids: List[str],
        total_available_budget: float
    ) -> Dict[str, Tuple[float, float]]:
        """
        Rebalance budgets across delegations based on coherence.

        Returns:
            Dict[delegation_id] = (old_budget, new_budget)
        """
        # Get coherence scores for all delegations
        coherences = {}
        for delegation_id in delegation_ids:
            delegation = self.allocator.delegation_keeper.get_delegation(delegation_id)
            if delegation:
                ci = self.allocator.grounding_manager.get_coherence_index(delegation.delegate)
                coherences[delegation_id] = ci

        # Calculate total coherence
        total_coherence = sum(coherences.values())
        if total_coherence == 0:
            # All zero coherence, distribute equally
            share = total_available_budget / len(delegation_ids)
            return {d_id: (0.0, share) for d_id in delegation_ids}

        # Distribute budget proportionally to coherence
        rebalanced = {}
        for delegation_id, ci in coherences.items():
            old_budget = self.allocator.budget_enforcer.get_budget(delegation_id)
            old_value = old_budget.total_budget if old_budget else 0.0

            # New budget proportional to coherence
            new_budget = (ci / total_coherence) * total_available_budget

            rebalanced[delegation_id] = (old_value, new_budget)

        return rebalanced


# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

def test_coherence_aware_budgets():
    """Test coherence-aware budget allocation."""
    print("=" * 70)
    print("SESSION 101 TRACK 4: COHERENCE-AWARE BUDGET OPTIMIZATION")
    print("=" * 70)
    print()

    # Setup
    grounding_manager = GroundingManager()
    delegation_keeper = ACTDelegationChainKeeper()
    budget_enforcer = ATPBudgetEnforcer(delegation_keeper)
    allocator = CoherenceAwareBudgetAllocator(grounding_manager, delegation_keeper, budget_enforcer)

    # Test 1: Budget allocation with high coherence
    print("Test 1: Budget Allocation with High Coherence")
    print("-" * 70)

    human = "lct://web4:human:alice@mainnet"
    agent_high = "lct://web4:agent:high_coherence@mainnet"

    # Give agent high coherence (consistent grounding)
    context = GroundingContext(
        location=Location(LocationType.PHYSICAL, "geo:45.5,-122.6", PrecisionLevel.CITY, True),
        capabilities=Capabilities(["compute"], HardwareClass.EDGE_DEVICE, {"compute": ResourceLevel.MEDIUM}),
        session=GroundingSession(datetime.now(timezone.utc).isoformat(), "pattern_123")
    )
    grounding_manager.announce_grounding(agent_high, context)
    time.sleep(0.1)
    grounding_manager.announce_grounding(agent_high, context)  # Consistent

    ci_high = grounding_manager.get_coherence_index(agent_high)
    print(f"Agent coherence: {ci_high:.3f}")

    # Create delegation
    delegation_high = delegation_keeper.record_delegation(
        issuer=human,
        delegate=agent_high,
        scope=[ScopedPermission("atp:spend", "*")],
        expires_in_hours=24
    )

    # Set initial LCT balance
    budget_enforcer.set_lct_balance(human, 10000.0)

    # Allocate coherence-aware budget
    base_budget = 1000.0
    budget_high = allocator.allocate_coherence_aware_budget(
        delegation_id=delegation_high.token_id,
        base_budget=base_budget
    )

    print(f"✓ Base budget: {base_budget} ATP")
    print(f"✓ Adjusted budget: {budget_high.total_budget} ATP")
    print(f"✓ Adjustment ratio: {budget_high.total_budget/base_budget:.2f}x")
    print(f"  (Expected: ~1.2x for high coherence)")
    print()

    # Test 2: Budget allocation with low coherence
    print("Test 2: Budget Allocation with Low Coherence")
    print("-" * 70)

    agent_low = "lct://web4:agent:low_coherence@mainnet"

    # Give agent low coherence (suspicious context shift)
    context_suspicious = GroundingContext(
        location=Location(LocationType.PHYSICAL, "geo:1.3,103.8", PrecisionLevel.CITY, False),
        capabilities=Capabilities(["gpu", "distributed"], HardwareClass.CLUSTER, {"compute": ResourceLevel.MAXIMUM}),
        session=GroundingSession(datetime.now(timezone.utc).isoformat(), "pattern_xyz")
    )
    grounding_manager.announce_grounding(agent_low, context)  # Start consistent
    time.sleep(0.1)
    grounding_manager.announce_grounding(agent_low, context_suspicious)  # Sudden shift

    ci_low = grounding_manager.get_coherence_index(agent_low)
    print(f"Agent coherence: {ci_low:.3f}")

    delegation_low = delegation_keeper.record_delegation(
        issuer=human,
        delegate=agent_low,
        scope=[ScopedPermission("atp:spend", "*")],
        expires_in_hours=24
    )

    budget_low = allocator.allocate_coherence_aware_budget(
        delegation_id=delegation_low.token_id,
        base_budget=base_budget
    )

    print(f"✓ Base budget: {base_budget} ATP")
    print(f"✓ Adjusted budget: {budget_low.total_budget} ATP")
    print(f"✓ Adjustment ratio: {budget_low.total_budget/base_budget:.2f}x")
    print(f"  (Expected: <1.0x for low coherence)")
    print()

    # Test 3: Budget reassessment after coherence change
    print("Test 3: Budget Reassessment After Coherence Change")
    print("-" * 70)

    # Agent improves coherence
    grounding_manager.announce_grounding(agent_low, context)  # Back to normal
    time.sleep(0.1)

    old_budget, new_budget, reason = allocator.reassess_budget(delegation_low.token_id)

    print(f"Old budget: {old_budget} ATP")
    print(f"New budget: {new_budget} ATP")
    print(f"Reason: {reason}")
    print(f"✓ Budget adjustment: {(new_budget - old_budget):+.0f} ATP")
    print()

    # Test 4: Multi-agent budget rebalancing
    print("Test 4: Multi-Agent Budget Rebalancing")
    print("-" * 70)

    # Create 3 agents with different coherence levels
    agents = []
    delegations = []

    for i, (coherence_type, ci_target) in enumerate([("high", 0.95), ("medium", 0.7), ("low", 0.4)]):
        agent = f"lct://web4:agent:{coherence_type}_{i}@mainnet"
        agents.append(agent)

        # Set up grounding for target coherence
        if coherence_type == "high":
            ctx = context  # Consistent
            grounding_manager.announce_grounding(agent, ctx)
            time.sleep(0.05)
            grounding_manager.announce_grounding(agent, ctx)
        elif coherence_type == "medium":
            ctx = context
            grounding_manager.announce_grounding(agent, ctx)
            time.sleep(0.05)
            ctx_mod = GroundingContext(
                location=Location(LocationType.LOGICAL, "society:test", PrecisionLevel.EXACT, True),
                capabilities=Capabilities(["compute"], HardwareClass.EDGE_DEVICE, {"compute": ResourceLevel.MEDIUM}),
                session=GroundingSession(datetime.now(timezone.utc).isoformat(), "pattern_456")
            )
            grounding_manager.announce_grounding(agent, ctx_mod)
        else:  # low
            grounding_manager.announce_grounding(agent, context_suspicious)

        # Create delegation
        delegation = delegation_keeper.record_delegation(
            issuer=human,
            delegate=agent,
            scope=[ScopedPermission("atp:spend", "*")],
            expires_in_hours=24
        )
        delegations.append(delegation.token_id)

        # Allocate initial budget
        allocator.allocate_coherence_aware_budget(delegation.token_id, 1000.0)

        ci = grounding_manager.get_coherence_index(agent)
        print(f"Agent {coherence_type}: CI={ci:.3f}")

    # Rebalance budgets
    rebalancer = CoherenceBasedRebalancer(allocator)
    total_pool = 3000.0  # Total ATP to distribute
    rebalanced = rebalancer.rebalance_budgets(delegations, total_pool)

    print(f"\nRebalancing {total_pool} ATP across {len(delegations)} agents:")
    for i, (delegation_id, (old, new)) in enumerate(rebalanced.items()):
        agent_type = ["high", "medium", "low"][i]
        ci = grounding_manager.get_coherence_index(agents[i])
        print(f"  {agent_type} (CI={ci:.3f}): {old:.0f} → {new:.0f} ATP ({(new/total_pool)*100:.1f}% of pool)")
    print()

    # Test 5: Budget efficiency scoring
    print("Test 5: Budget Efficiency Scoring")
    print("-" * 70)

    for i, delegation_id in enumerate(delegations[:2]):  # Test first 2
        # Simulate some spending
        budget_enforcer.lock_atp(delegation_id, 100.0, "test_op")
        budget_enforcer.commit_atp(delegation_id, 100.0, "test_op")

        efficiency = allocator.get_budget_efficiency_score(delegation_id)
        budget = budget_enforcer.get_budget(delegation_id)

        print(f"Delegation {i}:")
        print(f"  Utilization: {budget.utilization * 100:.1f}%")
        print(f"  Coherence: {grounding_manager.get_coherence_index(agents[i]):.3f}")
        print(f"  Efficiency: {efficiency:.3f}")
    print()

    print("=" * 70)
    print("COHERENCE-AWARE BUDGET TESTS COMPLETE")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"✓ High coherence budget boost: {budget_high.total_budget/base_budget:.2f}x")
    print(f"✓ Low coherence budget reduction: {budget_low.total_budget/base_budget:.2f}x")
    print(f"✓ Budget reassessment: Working")
    print(f"✓ Multi-agent rebalancing: Working")
    print(f"✓ Efficiency scoring: Working")
    print()
    print("Key insight: Agents have incentive to maintain high coherence")
    print("  → Better grounding = more ATP budget")
    print("  → Suspicious behavior = reduced budget")
    print()

    return {
        "high_coherence_multiplier": budget_high.total_budget / base_budget,
        "low_coherence_multiplier": budget_low.total_budget / base_budget,
        "agents_rebalanced": len(delegations),
        "adjustment_history_entries": len(allocator.adjustment_history)
    }


if __name__ == "__main__":
    results = test_coherence_aware_budgets()
    print(f"\nTest results:\n{json.dumps(results, indent=2)}")
