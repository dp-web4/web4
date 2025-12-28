"""
SESSION 96 TRACK 3: ATP RESOURCE LIMITS FOR DELEGATED AGENTS

From AI Agent Accountability doc:
> "Resource limits: ATP (Adaptive Trust Points) budget"

This implements ATP budget enforcement for delegated agents, integrating:
- Track 2: DelegationToken with permission scopes
- Session 95: UnifiedLCTProfile with ATP balance
- Session 94: ATP settlement and locking

Key innovations:
- BudgetedDelegationToken: Delegation token with ATP budget
- ATPBudgetEnforcer: Automatic enforcement of spending limits
- BudgetAlert: Warnings when approaching limits
- Hierarchical budgets: Parent delegates sub-budget to child

Example delegation with ATP budget:
  Human (1000 ATP)
    └─ SAGE (delegated 200 ATP for 24h)
          └─ Browser Plugin (delegated 50 ATP for 1h)

Each delegation includes:
- ATP budget (max spending allowed)
- Spending tracking (current usage)
- Budget alerts (80%, 90%, 100%)
- Automatic enforcement (transactions blocked when budget exhausted)

Integration with:
- Track 2: DelegationToken
- Session 95 Track 2: UnifiedLCTProfile (ATP balance)
- Session 94: ATP settlement (lock-commit-rollback)

References:
- Session 94 Track 2: ATP settlement
- Session 95 Track 1: State-aware ATP pricing
- AI Agent Accountability doc: Resource limits
"""

import json
import secrets
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum


# ============================================================================
# BUDGETED DELEGATION TOKEN
# ============================================================================

class BudgetAlertLevel(Enum):
    """Alert levels for budget consumption."""
    WARNING_80 = 0.80  # 80% consumed
    CRITICAL_90 = 0.90  # 90% consumed
    EXHAUSTED_100 = 1.00  # 100% consumed


@dataclass
class BudgetAlert:
    """Alert triggered when budget threshold crossed."""
    token_id: str
    alert_level: BudgetAlertLevel
    budget_allocated: float
    budget_consumed: float
    budget_remaining: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "alert_level": self.alert_level.name,
            "budget_allocated": self.budget_allocated,
            "budget_consumed": self.budget_consumed,
            "budget_remaining": self.budget_remaining,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged
        }


@dataclass
class BudgetedDelegationToken:
    """
    Delegation token with ATP budget.

    Extends Track 2's DelegationToken with:
    - ATP budget (max spending allowed)
    - Spending tracking (current usage)
    - Budget alerts (warnings when approaching limits)
    """
    # Core delegation (from Track 2)
    token_id: str
    issuer: str  # LCT identity of issuer
    delegate: str  # LCT identity of delegate

    # Time bounds
    issued_at: str
    expires_at: str

    # ATP budget
    atp_budget: float  # Maximum ATP this token can spend
    atp_consumed: float = 0.0  # ATP spent so far
    atp_locked: float = 0.0  # ATP in pending transactions

    # Budget alerts
    alerts_triggered: List[BudgetAlert] = field(default_factory=list)
    alert_thresholds: List[float] = field(default_factory=lambda: [0.80, 0.90, 1.00])

    # Revocation
    revoked: bool = False
    revoked_at: Optional[str] = None

    # Hierarchy
    parent_token_id: Optional[str] = None
    child_budgets: Dict[str, float] = field(default_factory=dict)  # child_token_id -> budget allocated

    @property
    def atp_available(self) -> float:
        """ATP still available for spending."""
        return self.atp_budget - self.atp_consumed - self.atp_locked

    @property
    def atp_remaining(self) -> float:
        """ATP remaining (total budget - consumed)."""
        return self.atp_budget - self.atp_consumed

    @property
    def budget_utilization(self) -> float:
        """Fraction of budget consumed (0.0-1.0)."""
        if self.atp_budget == 0:
            return 1.0
        return self.atp_consumed / self.atp_budget

    @property
    def is_exhausted(self) -> bool:
        """Check if budget is exhausted."""
        return self.atp_available <= 0

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired, not revoked, budget available)."""
        if self.revoked:
            return False

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(self.expires_at)
        if now > expires_at:
            return False

        if self.is_exhausted:
            return False

        return True

    def lock_atp(self, amount: float) -> bool:
        """
        Lock ATP for pending transaction.

        Returns:
            True if lock successful, False if insufficient budget
        """
        if amount > self.atp_available:
            return False

        self.atp_locked += amount
        return True

    def commit_atp(self, amount: float) -> bool:
        """
        Commit ATP (move from locked to consumed).

        Returns:
            True if commit successful
        """
        if amount > self.atp_locked:
            return False

        self.atp_locked -= amount
        self.atp_consumed += amount

        # Check for budget alerts
        self._check_budget_alerts()

        return True

    def rollback_atp(self, amount: float) -> bool:
        """
        Rollback ATP (unlock without consuming).

        Returns:
            True if rollback successful
        """
        if amount > self.atp_locked:
            return False

        self.atp_locked -= amount
        return True

    def _check_budget_alerts(self):
        """Check if budget thresholds crossed and trigger alerts."""
        utilization = self.budget_utilization

        for threshold in self.alert_thresholds:
            # Check if threshold crossed and alert not already triggered
            if utilization >= threshold:
                # Check if alert already exists for this threshold
                existing = any(
                    abs(alert.alert_level.value - threshold) < 0.01
                    for alert in self.alerts_triggered
                )

                if not existing:
                    # Determine alert level
                    if threshold >= 1.00:
                        level = BudgetAlertLevel.EXHAUSTED_100
                    elif threshold >= 0.90:
                        level = BudgetAlertLevel.CRITICAL_90
                    else:
                        level = BudgetAlertLevel.WARNING_80

                    alert = BudgetAlert(
                        token_id=self.token_id,
                        alert_level=level,
                        budget_allocated=self.atp_budget,
                        budget_consumed=self.atp_consumed,
                        budget_remaining=self.atp_remaining
                    )
                    self.alerts_triggered.append(alert)

    def allocate_child_budget(self, child_token_id: str, child_budget: float) -> bool:
        """
        Allocate portion of budget to child delegation.

        Returns:
            True if allocation successful
        """
        # Calculate total child budgets
        total_child_budgets = sum(self.child_budgets.values())

        # Check if enough budget available for child
        if total_child_budgets + child_budget > self.atp_budget:
            return False

        self.child_budgets[child_token_id] = child_budget
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "issuer": self.issuer,
            "delegate": self.delegate,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "atp_budget": self.atp_budget,
            "atp_consumed": self.atp_consumed,
            "atp_locked": self.atp_locked,
            "atp_available": self.atp_available,
            "budget_utilization": self.budget_utilization,
            "alerts_triggered": [a.to_dict() for a in self.alerts_triggered],
            "revoked": self.revoked,
            "revoked_at": self.revoked_at,
            "parent_token_id": self.parent_token_id,
            "child_budgets": self.child_budgets
        }


# ============================================================================
# ATP BUDGET ENFORCER
# ============================================================================

class ATPBudgetEnforcer:
    """
    Enforces ATP budget limits for delegated agents.

    Responsibilities:
    - Create budgeted delegation tokens
    - Lock/commit/rollback ATP transactions
    - Trigger budget alerts
    - Prevent overspending
    - Track budget hierarchy
    """

    def __init__(self):
        self.tokens: Dict[str, BudgetedDelegationToken] = {}
        self.transactions: Dict[str, Dict[str, Any]] = {}  # tx_id -> transaction data

    def create_budgeted_delegation(
        self,
        issuer: str,
        delegate: str,
        atp_budget: float,
        duration_hours: int = 24,
        parent_token_id: Optional[str] = None
    ) -> BudgetedDelegationToken:
        """
        Create delegation token with ATP budget.

        Args:
            issuer: LCT identity of issuer
            delegate: LCT identity of delegate
            atp_budget: Maximum ATP delegate can spend
            duration_hours: Token validity duration
            parent_token_id: Parent token (if sub-delegation)

        Returns:
            BudgetedDelegationToken
        """
        token_id = f"token_{secrets.token_hex(16)}"

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=duration_hours)

        # If parent token, verify issuer is delegate and budget available
        if parent_token_id:
            if parent_token_id not in self.tokens:
                raise ValueError(f"Parent token not found: {parent_token_id}")

            parent = self.tokens[parent_token_id]

            # Verify issuer is delegate of parent
            if parent.delegate != issuer:
                raise ValueError(f"Issuer {issuer} is not delegate of parent token")

            # Allocate child budget from parent
            if not parent.allocate_child_budget(token_id, atp_budget):
                raise ValueError(f"Insufficient parent budget for {atp_budget} ATP")

        token = BudgetedDelegationToken(
            token_id=token_id,
            issuer=issuer,
            delegate=delegate,
            issued_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            atp_budget=atp_budget,
            parent_token_id=parent_token_id
        )

        self.tokens[token_id] = token

        return token

    def lock_transaction(
        self,
        token_id: str,
        amount: float,
        description: str = ""
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Lock ATP for pending transaction.

        Returns:
            (transaction_id, error_message)
        """
        if token_id not in self.tokens:
            return None, f"Token not found: {token_id}"

        token = self.tokens[token_id]

        # Check token validity
        if not token.is_valid:
            if token.revoked:
                return None, "Token revoked"
            elif token.is_exhausted:
                return None, f"Budget exhausted ({token.atp_remaining:.2f} ATP remaining)"
            else:
                return None, "Token expired"

        # Lock ATP
        if not token.lock_atp(amount):
            return None, f"Insufficient budget (available: {token.atp_available:.2f} ATP, requested: {amount:.2f} ATP)"

        # Create transaction record
        tx_id = f"tx_{secrets.token_hex(16)}"
        self.transactions[tx_id] = {
            "tx_id": tx_id,
            "token_id": token_id,
            "amount": amount,
            "description": description,
            "status": "locked",
            "locked_at": datetime.now(timezone.utc).isoformat()
        }

        return tx_id, None

    def commit_transaction(self, tx_id: str) -> Tuple[bool, Optional[str]]:
        """
        Commit transaction (move ATP from locked to consumed).

        Returns:
            (success, error_message)
        """
        if tx_id not in self.transactions:
            return False, f"Transaction not found: {tx_id}"

        tx = self.transactions[tx_id]

        if tx["status"] != "locked":
            return False, f"Transaction not in locked state: {tx['status']}"

        token_id = tx["token_id"]
        if token_id not in self.tokens:
            return False, f"Token not found: {token_id}"

        token = self.tokens[token_id]

        # Commit ATP
        if not token.commit_atp(tx["amount"]):
            return False, "Commit failed (insufficient locked ATP)"

        tx["status"] = "committed"
        tx["committed_at"] = datetime.now(timezone.utc).isoformat()

        return True, None

    def rollback_transaction(self, tx_id: str) -> Tuple[bool, Optional[str]]:
        """
        Rollback transaction (unlock ATP without consuming).

        Returns:
            (success, error_message)
        """
        if tx_id not in self.transactions:
            return False, f"Transaction not found: {tx_id}"

        tx = self.transactions[tx_id]

        if tx["status"] != "locked":
            return False, f"Transaction not in locked state: {tx['status']}"

        token_id = tx["token_id"]
        if token_id not in self.tokens:
            return False, f"Token not found: {token_id}"

        token = self.tokens[token_id]

        # Rollback ATP
        if not token.rollback_atp(tx["amount"]):
            return False, "Rollback failed (insufficient locked ATP)"

        tx["status"] = "rolled_back"
        tx["rolled_back_at"] = datetime.now(timezone.utc).isoformat()

        return True, None

    def get_budget_status(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get current budget status for token."""
        if token_id not in self.tokens:
            return None

        token = self.tokens[token_id]

        return {
            "token_id": token_id,
            "issuer": token.issuer,
            "delegate": token.delegate,
            "atp_budget": token.atp_budget,
            "atp_consumed": token.atp_consumed,
            "atp_locked": token.atp_locked,
            "atp_available": token.atp_available,
            "atp_remaining": token.atp_remaining,
            "budget_utilization": token.budget_utilization,
            "is_exhausted": token.is_exhausted,
            "is_valid": token.is_valid,
            "alerts_count": len(token.alerts_triggered),
            "latest_alert": token.alerts_triggered[-1].to_dict() if token.alerts_triggered else None
        }

    def get_pending_alerts(self, token_id: str) -> List[BudgetAlert]:
        """Get unacknowledged alerts for token."""
        if token_id not in self.tokens:
            return []

        token = self.tokens[token_id]
        return [a for a in token.alerts_triggered if not a.acknowledged]


# ============================================================================
# TEST SCENARIOS
# ============================================================================

def test_budgeted_delegation_creation():
    """Test creating delegation with ATP budget."""
    print("="*80)
    print("TEST SCENARIO 1: Budgeted Delegation Creation")
    print("="*80)

    enforcer = ATPBudgetEnforcer()

    # Human delegates 200 ATP to SAGE for 24 hours
    token = enforcer.create_budgeted_delegation(
        issuer="lct://user:dennis@laptop",
        delegate="lct://sage:main@mainnet",
        atp_budget=200.0,
        duration_hours=24
    )

    print(f"\n✅ Budgeted delegation created:")
    print(f"   Token ID: {token.token_id}")
    print(f"   Issuer: {token.issuer}")
    print(f"   Delegate: {token.delegate}")
    print(f"   ATP Budget: {token.atp_budget}")
    print(f"   ATP Available: {token.atp_available}")
    print(f"   Valid: {token.is_valid}")

    return token.is_valid and token.atp_budget == 200.0


def test_transaction_lock_commit():
    """Test locking and committing ATP transactions."""
    print("\n" + "="*80)
    print("TEST SCENARIO 2: Transaction Lock and Commit")
    print("="*80)

    enforcer = ATPBudgetEnforcer()

    # Create token with 100 ATP budget
    token = enforcer.create_budgeted_delegation(
        issuer="lct://user:alice@laptop",
        delegate="lct://sage:agent@mainnet",
        atp_budget=100.0
    )

    print(f"\n📊 Initial state:")
    print(f"   Budget: {token.atp_budget} ATP")
    print(f"   Available: {token.atp_available} ATP")

    # Lock 30 ATP for transaction
    tx_id, error = enforcer.lock_transaction(token.token_id, 30.0, "IRP invocation")

    if tx_id:
        print(f"\n✅ Transaction locked:")
        print(f"   TX ID: {tx_id}")
        print(f"   Amount: 30.0 ATP")
        print(f"   Available after lock: {token.atp_available} ATP")
        print(f"   Locked: {token.atp_locked} ATP")
    else:
        print(f"\n❌ Lock failed: {error}")

    # Commit transaction
    success, error = enforcer.commit_transaction(tx_id)

    if success:
        print(f"\n✅ Transaction committed:")
        print(f"   Consumed: {token.atp_consumed} ATP")
        print(f"   Locked: {token.atp_locked} ATP")
        print(f"   Available: {token.atp_available} ATP")
        print(f"   Utilization: {token.budget_utilization:.1%}")
    else:
        print(f"\n❌ Commit failed: {error}")

    return success and token.atp_consumed == 30.0


def test_budget_alerts():
    """Test budget alert triggering."""
    print("\n" + "="*80)
    print("TEST SCENARIO 3: Budget Alerts")
    print("="*80)

    enforcer = ATPBudgetEnforcer()

    # Create token with 100 ATP budget
    token = enforcer.create_budgeted_delegation(
        issuer="lct://user:bob@laptop",
        delegate="lct://sage:worker@mainnet",
        atp_budget=100.0
    )

    print(f"\n📊 Budget: {token.atp_budget} ATP")
    print(f"   Alert thresholds: {token.alert_thresholds}")

    # Consume 85 ATP (should trigger 80% alert)
    tx1_id, _ = enforcer.lock_transaction(token.token_id, 85.0)
    enforcer.commit_transaction(tx1_id)

    print(f"\n✅ Consumed 85 ATP (85%):")
    print(f"   Alerts triggered: {len(token.alerts_triggered)}")
    if token.alerts_triggered:
        alert = token.alerts_triggered[0]
        print(f"   Latest alert: {alert.alert_level.name}")
        print(f"   Budget remaining: {alert.budget_remaining:.2f} ATP")

    # Consume another 8 ATP (should trigger 90% alert)
    tx2_id, _ = enforcer.lock_transaction(token.token_id, 8.0)
    enforcer.commit_transaction(tx2_id)

    print(f"\n✅ Consumed 93 ATP (93%):")
    print(f"   Alerts triggered: {len(token.alerts_triggered)}")
    if len(token.alerts_triggered) > 1:
        alert = token.alerts_triggered[1]
        print(f"   Latest alert: {alert.alert_level.name}")

    return len(token.alerts_triggered) >= 2


def test_budget_exhaustion():
    """Test budget exhaustion prevents overspending."""
    print("\n" + "="*80)
    print("TEST SCENARIO 4: Budget Exhaustion")
    print("="*80)

    enforcer = ATPBudgetEnforcer()

    # Create token with 50 ATP budget
    token = enforcer.create_budgeted_delegation(
        issuer="lct://user:charlie@laptop",
        delegate="lct://sage:limited@mainnet",
        atp_budget=50.0
    )

    print(f"\n📊 Budget: {token.atp_budget} ATP")

    # Consume 50 ATP (exhaust budget)
    tx1_id, _ = enforcer.lock_transaction(token.token_id, 50.0)
    enforcer.commit_transaction(tx1_id)

    print(f"\n✅ Consumed 50 ATP (100%):")
    print(f"   Available: {token.atp_available} ATP")
    print(f"   Exhausted: {token.is_exhausted}")
    print(f"   Valid: {token.is_valid}")

    # Try to lock more ATP (should fail)
    tx2_id, error = enforcer.lock_transaction(token.token_id, 10.0)

    if tx2_id:
        print(f"\n❌ Lock succeeded (should have failed!)")
    else:
        print(f"\n✅ Lock blocked: {error}")

    return tx2_id is None and token.is_exhausted


def test_hierarchical_budgets():
    """Test hierarchical budget allocation."""
    print("\n" + "="*80)
    print("TEST SCENARIO 5: Hierarchical Budgets")
    print("="*80)

    enforcer = ATPBudgetEnforcer()

    # Level 0: Human delegates 500 ATP to SAGE
    human_token = enforcer.create_budgeted_delegation(
        issuer="lct://user:dennis@laptop",
        delegate="lct://sage:main@mainnet",
        atp_budget=500.0
    )

    print(f"\n✅ Level 0: Human → SAGE")
    print(f"   Budget: {human_token.atp_budget} ATP")

    # Level 1: SAGE delegates 100 ATP to browser plugin
    plugin_token = enforcer.create_budgeted_delegation(
        issuer="lct://sage:main@mainnet",
        delegate="lct://sage:browser_plugin@mainnet",
        atp_budget=100.0,
        parent_token_id=human_token.token_id
    )

    print(f"\n✅ Level 1: SAGE → Plugin")
    print(f"   Budget: {plugin_token.atp_budget} ATP")
    print(f"   Parent token: {plugin_token.parent_token_id}")

    # Check parent's child budget tracking
    print(f"\n📊 Parent token child budgets:")
    print(f"   Total allocated to children: {sum(human_token.child_budgets.values())} ATP")
    print(f"   Remaining for parent: {human_token.atp_budget - sum(human_token.child_budgets.values())} ATP")

    # Plugin consumes 30 ATP
    tx_id, _ = enforcer.lock_transaction(plugin_token.token_id, 30.0)
    enforcer.commit_transaction(tx_id)

    print(f"\n✅ Plugin consumed 30 ATP:")
    print(f"   Plugin consumed: {plugin_token.atp_consumed} ATP")
    print(f"   Plugin available: {plugin_token.atp_available} ATP")
    print(f"   Parent consumed: {human_token.atp_consumed} ATP (plugin spending doesn't affect parent directly)")

    return (
        plugin_token.atp_consumed == 30.0 and
        plugin_token.parent_token_id == human_token.token_id
    )


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test scenarios."""
    print("="*80)
    print("SESSION 96 TRACK 3: ATP RESOURCE LIMITS")
    print("="*80)
    print("\nFrom AI Agent Accountability doc:")
    print("  Resource limits: ATP (Adaptive Trust Points) budget")
    print()

    results = []

    # Run tests
    results.append(("Budgeted delegation creation", test_budgeted_delegation_creation()))
    results.append(("Transaction lock and commit", test_transaction_lock_commit()))
    results.append(("Budget alerts", test_budget_alerts()))
    results.append(("Budget exhaustion", test_budget_exhaustion()))
    results.append(("Hierarchical budgets", test_hierarchical_budgets()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    all_passed = all(result for _, result in results)
    print(f"\n✅ All scenarios passed: {all_passed}")

    print(f"\nScenarios tested:")
    for i, (name, passed) in enumerate(results, 1):
        status = "✅" if passed else "❌"
        print(f"  {i}. {status} {name}")

    # Save results
    output = {
        "session": "96",
        "track": "3",
        "focus": "ATP Resource Limits for Delegated Agents",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_results": [
            {"scenario": name, "passed": passed}
            for name, passed in results
        ],
        "all_passed": all_passed,
        "innovations": [
            "BudgetedDelegationToken with ATP budget tracking",
            "ATPBudgetEnforcer with automatic enforcement",
            "Budget alerts (80%, 90%, 100% thresholds)",
            "Lock-commit-rollback for ATP transactions",
            "Hierarchical budget allocation (parent → child)",
        ]
    }

    output_path = "/home/dp/ai-workspace/web4/implementation/session96_track3_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Results saved to: {output_path}")

    print("\n" + "="*80)
    print("Key Innovations:")
    print("="*80)
    for i, innovation in enumerate(output["innovations"], 1):
        print(f"{i}. {innovation}")

    print("\n" + "="*80)
    print("ATP resource limits enable:")
    print("- Automatic spending enforcement (no overspending)")
    print("- Budget alerts (warning, critical, exhausted)")
    print("- Hierarchical delegation (parent allocates sub-budgets)")
    print("- Transaction safety (lock-commit-rollback)")
    print("- Accountability (all spending tracked)")
    print("="*80)

    return all_passed


if __name__ == "__main__":
    run_all_tests()
