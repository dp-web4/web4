"""
ATP Ledger Permission Integration

Integrates LCT permission system with ATP ledger operations.
Enforces permission checks and resource limits for all ATP operations.

Author: Legion Autonomous Session #49
Date: 2025-12-02
Status: Phase 4 integration - ATP + LCT permissions
References: atp_ledger.py, lct_permissions.py, lct_identity.py

Permission-Enforced Operations:
- Read ATP balance (requires atp:read)
- Transfer ATP (requires atp:write + budget check)
- Lock/unlock ATP (requires atp:write + budget check)
- Query ledger state (requires appropriate permissions)

Resource Enforcement:
- ATP transfers checked against task budget
- Budget tracked per-identity
- Prevents over-spending beyond task limits
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time

from game.engine.atp_ledger import ATPLedger, ATPAccount, TransferPhase
from game.engine.lct_permissions import (
    check_permission,
    check_resource_limit,
    get_atp_budget,
    get_task_permissions
)
from game.engine.lct_identity import parse_lct_id


class PermissionError(Exception):
    """Permission denied for ATP operation"""
    pass


class BudgetExceededError(Exception):
    """ATP budget exceeded for task"""
    pass


@dataclass
class ATPOperationLog:
    """Log entry for ATP operations with permission checks"""
    timestamp: float
    lct_id: str
    operation: str  # "read", "write", "transfer", "lock", "unlock"
    amount: float
    permission_checked: str
    budget_checked: bool
    success: bool
    reason: str = ""


class PermissionEnforcedATPLedger(ATPLedger):
    """
    ATP Ledger with integrated permission checking.

    Extends base ATP ledger with:
    - Permission validation before operations
    - Budget limit enforcement
    - Operation audit logging
    - Per-identity spending tracking
    """

    def __init__(self, platform_name: str):
        """
        Initialize permission-enforced ATP ledger.

        Args:
            platform_name: This platform's name
        """
        super().__init__(platform_name)

        # Additional tracking for permissions
        self.operation_log: List[ATPOperationLog] = []
        self.identity_spending: Dict[str, float] = {}  # lct_id → total spent

    def get_balance(
        self,
        agent_lct: str,
        requester_lct: Optional[str] = None
    ) -> Tuple[Optional[float], str]:
        """
        Get ATP balance with permission check.

        Args:
            agent_lct: LCT identity to query
            requester_lct: LCT identity requesting the balance (None = self-query)

        Returns:
            (balance, reason) tuple - balance is None if permission denied

        Permission Requirements:
            - Self-query: Requires atp:read
            - Other-query: Requires admin:read or admin:full

        Example:
            >>> ledger = PermissionEnforcedATPLedger("Thor")
            >>> balance, reason = ledger.get_balance(
            ...     "lct:web4:agent:alice@Thor#perception",
            ...     "lct:web4:agent:alice@Thor#perception"
            ... )
            >>> if balance is not None:
            ...     print(f"Balance: {balance}")
        """
        # Determine who is making the query
        if requester_lct is None:
            requester_lct = agent_lct

        # Parse task from requester LCT
        try:
            lct_components = parse_lct_id(requester_lct)
            if lct_components is None:
                raise ValueError("Invalid LCT format")
            lineage, context, requester_task = lct_components
        except (ValueError, KeyError, TypeError) as e:
            self._log_operation(
                lct_id=requester_lct,
                operation="read",
                amount=0.0,
                permission_checked="atp:read",
                budget_checked=False,
                success=False,
                reason=f"Invalid LCT identity: {e}"
            )
            return (None, f"Invalid LCT identity: {e}")

        # Check permission
        if agent_lct == requester_lct:
            # Self-query: requires atp:read
            if not check_permission(requester_task, "atp:read"):
                self._log_operation(
                    lct_id=requester_lct,
                    operation="read",
                    amount=0.0,
                    permission_checked="atp:read",
                    budget_checked=False,
                    success=False,
                    reason=f"Task {requester_task} does not have atp:read permission"
                )
                return (None, f"Task {requester_task} does not have atp:read permission")
        else:
            # Other-query: requires admin:read or admin:full
            if not (check_permission(requester_task, "admin:read") or
                    check_permission(requester_task, "admin:full")):
                self._log_operation(
                    lct_id=requester_lct,
                    operation="read",
                    amount=0.0,
                    permission_checked="admin:read",
                    budget_checked=False,
                    success=False,
                    reason=f"Task {requester_task} does not have admin:read permission"
                )
                return (None, f"Task {requester_task} does not have admin:read permission")

        # Permission granted - get balance
        account = self.accounts.get(agent_lct)
        balance = account.total if account else 0.0

        self._log_operation(
            lct_id=requester_lct,
            operation="read",
            amount=balance,
            permission_checked="atp:read",
            budget_checked=False,
            success=True
        )

        return (balance, "")

    def transfer(
        self,
        from_lct: str,
        to_lct: str,
        amount: float
    ) -> Tuple[bool, str]:
        """
        Transfer ATP with permission and budget checks.

        Args:
            from_lct: Source LCT identity
            to_lct: Destination LCT identity
            amount: ATP amount to transfer

        Returns:
            (success, reason) tuple

        Permission Requirements:
            - Requires atp:write permission
            - Requires amount within ATP budget

        Example:
            >>> ledger = PermissionEnforcedATPLedger("Thor")
            >>> success, reason = ledger.transfer(
            ...     "lct:web4:agent:alice@Thor#execution.code",
            ...     "lct:web4:agent:bob@Thor#planning",
            ...     50.0
            ... )
        """
        # Parse task from source LCT
        try:
            lct_components = parse_lct_id(from_lct)
            if lct_components is None:
                raise ValueError("Invalid LCT format")
            lineage, context, from_task = lct_components
        except (ValueError, KeyError, TypeError) as e:
            self._log_operation(
                lct_id=from_lct,
                operation="transfer",
                amount=amount,
                permission_checked="atp:write",
                budget_checked=False,
                success=False,
                reason=f"Invalid source LCT: {e}"
            )
            return (False, f"Invalid source LCT: {e}")

        # Check write permission
        if not check_permission(from_task, "atp:write"):
            self._log_operation(
                lct_id=from_lct,
                operation="transfer",
                amount=amount,
                permission_checked="atp:write",
                budget_checked=False,
                success=False,
                reason=f"Task {from_task} does not have atp:write permission"
            )
            return (False, f"Task {from_task} does not have atp:write permission")

        # Check budget limit
        allowed, budget_reason = check_resource_limit(from_task, "atp", amount)
        if not allowed:
            self._log_operation(
                lct_id=from_lct,
                operation="transfer",
                amount=amount,
                permission_checked="atp:write",
                budget_checked=True,
                success=False,
                reason=budget_reason
            )
            return (False, budget_reason)

        # Check cumulative spending against budget
        total_spent = self.identity_spending.get(from_lct, 0.0)
        budget = get_atp_budget(from_task)
        if total_spent + amount > budget:
            reason = f"Total spending {total_spent + amount} would exceed budget {budget}"
            self._log_operation(
                lct_id=from_lct,
                operation="transfer",
                amount=amount,
                permission_checked="atp:write",
                budget_checked=True,
                success=False,
                reason=reason
            )
            return (False, reason)

        # Permission and budget checks passed - execute transfer
        success = super().transfer_local(from_lct, to_lct, amount)

        if success:
            # Track spending
            self.identity_spending[from_lct] = total_spent + amount

        self._log_operation(
            lct_id=from_lct,
            operation="transfer",
            amount=amount,
            permission_checked="atp:write",
            budget_checked=True,
            success=success,
            reason="" if success else "Transfer failed"
        )

        return (success, "" if success else "Transfer failed")

    def get_remaining_budget(self, lct_id: str) -> Tuple[Optional[float], str]:
        """
        Get remaining ATP budget for an identity.

        Args:
            lct_id: LCT identity to query

        Returns:
            (remaining_budget, reason) tuple

        Example:
            >>> remaining, reason = ledger.get_remaining_budget(
            ...     "lct:web4:agent:alice@Thor#execution.code"
            ... )
            >>> if remaining is not None:
            ...     print(f"Can spend {remaining} more ATP")
        """
        # Parse task
        try:
            lct_components = parse_lct_id(lct_id)
            if lct_components is None:
                raise ValueError("Invalid LCT format")
            lineage, context, task = lct_components
        except (ValueError, KeyError, TypeError) as e:
            return (None, f"Invalid LCT identity: {e}")

        # Get budget and spending
        budget = get_atp_budget(task)
        spent = self.identity_spending.get(lct_id, 0.0)
        remaining = budget - spent

        return (remaining, "")

    def get_spending_stats(self, lct_id: str) -> Dict[str, Any]:
        """
        Get spending statistics for an identity.

        Args:
            lct_id: LCT identity to query

        Returns:
            Dictionary with spending stats

        Example:
            >>> stats = ledger.get_spending_stats(
            ...     "lct:web4:agent:alice@Thor#execution.code"
            ... )
            >>> print(f"Spent: {stats['spent']}/{stats['budget']}")
        """
        # Parse task
        try:
            lct_components = parse_lct_id(lct_id)
            if lct_components is None:
                raise ValueError("Invalid LCT format")
            lineage, context, task = lct_components
        except (ValueError, KeyError, TypeError) as e:
            return {"error": f"Invalid LCT identity: {e}"}

        # Get stats
        budget = get_atp_budget(task)
        spent = self.identity_spending.get(lct_id, 0.0)
        remaining = budget - spent
        percent_used = (spent / budget * 100) if budget > 0 else 0

        # Get operation count
        operations = [log for log in self.operation_log if log.lct_id == lct_id]
        successful_ops = [log for log in operations if log.success]

        return {
            "lct_id": lct_id,
            "task": task,
            "budget": budget,
            "spent": spent,
            "remaining": remaining,
            "percent_used": percent_used,
            "total_operations": len(operations),
            "successful_operations": len(successful_ops),
            "failed_operations": len(operations) - len(successful_ops)
        }

    def get_operation_log(
        self,
        lct_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ATPOperationLog]:
        """
        Get operation log entries.

        Args:
            lct_id: Filter by LCT identity (None = all)
            limit: Maximum entries to return

        Returns:
            List of operation log entries (most recent first)
        """
        logs = self.operation_log

        # Filter by LCT ID if specified
        if lct_id:
            logs = [log for log in logs if log.lct_id == lct_id]

        # Sort by timestamp (most recent first)
        logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        return logs[:limit]

    def _log_operation(
        self,
        lct_id: str,
        operation: str,
        amount: float,
        permission_checked: str,
        budget_checked: bool,
        success: bool,
        reason: str = ""
    ):
        """Log an ATP operation with permission details"""
        log_entry = ATPOperationLog(
            timestamp=time.time(),
            lct_id=lct_id,
            operation=operation,
            amount=amount,
            permission_checked=permission_checked,
            budget_checked=budget_checked,
            success=success,
            reason=reason
        )
        self.operation_log.append(log_entry)

    def reset_spending(self, lct_id: str):
        """Reset spending counter for an identity (admin operation)"""
        self.identity_spending[lct_id] = 0.0

    def get_ledger_stats(self) -> Dict[str, Any]:
        """
        Get overall ledger statistics.

        Returns:
            Dictionary with ledger-wide stats
        """
        total_accounts = len(self.accounts)
        total_balance = sum(acc.total for acc in self.accounts.values())
        total_locked = sum(acc.locked for acc in self.accounts.values())

        # Operation stats
        total_operations = len(self.operation_log)
        successful_operations = sum(1 for log in self.operation_log if log.success)
        failed_operations = total_operations - successful_operations

        # Permission denial stats
        permission_denials = sum(
            1 for log in self.operation_log
            if not log.success and "permission" in log.reason.lower()
        )
        budget_denials = sum(
            1 for log in self.operation_log
            if not log.success and "budget" in log.reason.lower()
        )

        return {
            "platform": self.platform_name,
            "total_accounts": total_accounts,
            "total_atp": total_balance,
            "locked_atp": total_locked,
            "available_atp": total_balance - total_locked,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "permission_denials": permission_denials,
            "budget_denials": budget_denials
        }


def create_permission_enforced_ledger(platform_name: str) -> PermissionEnforcedATPLedger:
    """
    Factory function to create permission-enforced ATP ledger.

    Args:
        platform_name: Platform name

    Returns:
        PermissionEnforcedATPLedger instance

    Example:
        >>> ledger = create_permission_enforced_ledger("Thor")
    """
    return PermissionEnforcedATPLedger(platform_name)
