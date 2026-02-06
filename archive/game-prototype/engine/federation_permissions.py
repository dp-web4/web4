"""
Federation + LCT Permission Integration

Integrates LCT permission system with federation task delegation.
Enforces permission checks and capability verification for federated operations.

Author: Legion Autonomous Session #50
Date: 2025-12-02
Status: Phase 4 integration - Federation + LCT permissions
References: lct_permissions.py, signed_federation_delegation.py

Permission-Enforced Operations:
- Delegate task (requires federation:delegate)
- Execute task (requires appropriate task permissions)
- Route task based on capabilities
- Verify task compatibility with executor permissions

Key Concepts:
- Delegation requires federation:delegate permission
- Execution requires task-appropriate permissions
- Task routing considers executor capabilities
- Permission mismatch detected before delegation
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time

from game.engine.lct_permissions import (
    check_permission,
    check_resource_limit,
    can_delegate,
    can_execute_code,
    get_task_permissions,
    get_resource_limits,
    TaskPermissionDefinition
)
from game.engine.lct_identity import parse_lct_id


class DelegationPermissionError(Exception):
    """Delegation permission denied"""
    pass


class ExecutionCapabilityError(Exception):
    """Executor lacks required capabilities"""
    pass


@dataclass
class FederationTaskRequirements:
    """
    Requirements for a federation task.

    Defines what permissions/capabilities the executing agent must have.
    """
    required_permissions: List[str] = field(default_factory=list)
    required_capabilities: Dict[str, bool] = field(default_factory=dict)
    estimated_atp_cost: float = 0.0
    estimated_memory_mb: int = 1024
    estimated_cpu_cores: int = 1
    requires_network: bool = False
    requires_code_execution: bool = False

    def check_compatibility(
        self,
        executor_task: str
    ) -> Tuple[bool, List[str]]:
        """
        Check if executor task is compatible with requirements.

        Args:
            executor_task: Task type of potential executor

        Returns:
            (compatible, reasons) tuple

        Example:
            >>> reqs = FederationTaskRequirements(
            ...     required_permissions=["atp:write", "exec:code"],
            ...     requires_code_execution=True
            ... )
            >>> compatible, reasons = reqs.check_compatibility("execution.code")
            >>> if not compatible:
            ...     print(f"Incompatible: {reasons}")
        """
        reasons = []

        # Check permissions
        for permission in self.required_permissions:
            if not check_permission(executor_task, permission):
                reasons.append(f"Missing permission: {permission}")

        # Check code execution capability
        if self.requires_code_execution:
            if not can_execute_code(executor_task):
                reasons.append("Requires code execution capability")

        # Check resource limits
        executor_limits = get_resource_limits(executor_task)
        if executor_limits:
            # Check ATP budget
            if self.estimated_atp_cost > executor_limits.atp_budget:
                reasons.append(
                    f"ATP cost {self.estimated_atp_cost} exceeds "
                    f"executor budget {executor_limits.atp_budget}"
                )

            # Check memory
            if self.estimated_memory_mb > executor_limits.memory_mb:
                reasons.append(
                    f"Memory requirement {self.estimated_memory_mb}MB exceeds "
                    f"executor limit {executor_limits.memory_mb}MB"
                )

            # Check CPU
            if self.estimated_cpu_cores > executor_limits.cpu_cores:
                reasons.append(
                    f"CPU requirement {self.estimated_cpu_cores} cores exceeds "
                    f"executor limit {executor_limits.cpu_cores} cores"
                )

            # Check network
            if self.requires_network and executor_limits.network_bandwidth_mbps == 0:
                reasons.append("Requires network access but executor has no network")

        return (len(reasons) == 0, reasons)


@dataclass
class DelegationLog:
    """Log entry for federation delegation operations"""
    timestamp: float
    delegator_lct: str
    executor_lct: str
    task_type: str
    requirements: FederationTaskRequirements
    permission_checked: bool
    capability_checked: bool
    success: bool
    reason: str = ""


class PermissionEnforcedFederationRouter:
    """
    Federation router with LCT permission enforcement.

    Routes tasks based on:
    - Delegator has federation:delegate permission
    - Executor has required task capabilities
    - Resource requirements compatible with executor limits
    """

    def __init__(self, platform_name: str):
        """
        Initialize permission-enforced federation router.

        Args:
            platform_name: This platform's name
        """
        self.platform_name = platform_name
        self.delegation_log: List[DelegationLog] = []

    def can_delegate_task(
        self,
        delegator_lct: str
    ) -> Tuple[bool, str]:
        """
        Check if delegator can delegate tasks.

        Args:
            delegator_lct: LCT identity of delegating agent

        Returns:
            (can_delegate, reason) tuple

        Example:
            >>> router = PermissionEnforcedFederationRouter("Thor")
            >>> can_del, reason = router.can_delegate_task(
            ...     "lct:web4:agent:alice@Thor#delegation.federation"
            ... )
            >>> if can_del:
            ...     print("Can delegate")
        """
        # Parse LCT identity
        try:
            lct_components = parse_lct_id(delegator_lct)
            if lct_components is None:
                return (False, "Invalid LCT identity format")
            lineage, context, delegator_task = lct_components
        except (ValueError, TypeError) as e:
            return (False, f"Invalid LCT identity: {e}")

        # Check delegation permission
        if not can_delegate(delegator_task):
            return (
                False,
                f"Task '{delegator_task}' does not have delegation capability"
            )

        return (True, "")

    def find_compatible_executors(
        self,
        requirements: FederationTaskRequirements,
        available_executors: List[str]
    ) -> List[Tuple[str, float]]:
        """
        Find executors compatible with task requirements.

        Args:
            requirements: Task requirements
            available_executors: List of LCT identities of potential executors

        Returns:
            List of (executor_lct, compatibility_score) tuples, sorted by score

        Compatibility score:
        - 1.0: Perfect match (all requirements met with margin)
        - 0.5-1.0: Acceptable (requirements met, limited margin)
        - 0.0: Incompatible (missing requirements)

        Example:
            >>> router = PermissionEnforcedFederationRouter("Thor")
            >>> reqs = FederationTaskRequirements(
            ...     required_permissions=["atp:write", "exec:code"],
            ...     requires_code_execution=True,
            ...     estimated_atp_cost=100.0
            ... )
            >>> executors = router.find_compatible_executors(
            ...     reqs,
            ...     ["lct:web4:agent:bob@Sprout#execution.code"]
            ... )
        """
        compatible = []

        for executor_lct in available_executors:
            # Parse LCT identity
            try:
                lct_components = parse_lct_id(executor_lct)
                if lct_components is None:
                    continue
                lineage, context, executor_task = lct_components
            except (ValueError, TypeError):
                continue

            # Check compatibility
            is_compatible, reasons = requirements.check_compatibility(executor_task)

            if is_compatible:
                # Calculate compatibility score
                score = self._calculate_compatibility_score(
                    requirements,
                    executor_task
                )
                compatible.append((executor_lct, score))

        # Sort by compatibility score (descending)
        compatible.sort(key=lambda x: x[1], reverse=True)

        return compatible

    def delegate_task(
        self,
        delegator_lct: str,
        executor_lct: str,
        task_type: str,
        requirements: FederationTaskRequirements
    ) -> Tuple[bool, str]:
        """
        Delegate task with permission and capability checks.

        Args:
            delegator_lct: LCT identity of delegating agent
            executor_lct: LCT identity of executing agent
            task_type: Type of task being delegated
            requirements: Task requirements

        Returns:
            (success, reason) tuple

        Example:
            >>> router = PermissionEnforcedFederationRouter("Thor")
            >>> success, reason = router.delegate_task(
            ...     "lct:web4:agent:alice@Thor#delegation.federation",
            ...     "lct:web4:agent:bob@Sprout#execution.code",
            ...     "code_execution",
            ...     FederationTaskRequirements(
            ...         required_permissions=["exec:code"],
            ...         requires_code_execution=True
            ...     )
            ... )
        """
        # Check delegator permission
        can_del, reason = self.can_delegate_task(delegator_lct)
        if not can_del:
            self._log_delegation(
                delegator_lct=delegator_lct,
                executor_lct=executor_lct,
                task_type=task_type,
                requirements=requirements,
                permission_checked=True,
                capability_checked=False,
                success=False,
                reason=reason
            )
            return (False, reason)

        # Parse executor LCT
        try:
            lct_components = parse_lct_id(executor_lct)
            if lct_components is None:
                raise ValueError("Invalid executor LCT format")
            lineage, context, executor_task = lct_components
        except (ValueError, TypeError) as e:
            reason = f"Invalid executor LCT: {e}"
            self._log_delegation(
                delegator_lct=delegator_lct,
                executor_lct=executor_lct,
                task_type=task_type,
                requirements=requirements,
                permission_checked=True,
                capability_checked=False,
                success=False,
                reason=reason
            )
            return (False, reason)

        # Check executor compatibility
        is_compatible, incompatibility_reasons = requirements.check_compatibility(
            executor_task
        )

        if not is_compatible:
            reason = f"Executor incompatible: {'; '.join(incompatibility_reasons)}"
            self._log_delegation(
                delegator_lct=delegator_lct,
                executor_lct=executor_lct,
                task_type=task_type,
                requirements=requirements,
                permission_checked=True,
                capability_checked=True,
                success=False,
                reason=reason
            )
            return (False, reason)

        # Delegation allowed
        self._log_delegation(
            delegator_lct=delegator_lct,
            executor_lct=executor_lct,
            task_type=task_type,
            requirements=requirements,
            permission_checked=True,
            capability_checked=True,
            success=True
        )

        return (True, "")

    def _calculate_compatibility_score(
        self,
        requirements: FederationTaskRequirements,
        executor_task: str
    ) -> float:
        """
        Calculate compatibility score for executor.

        Score factors:
        - Has all required permissions: +0.5
        - Resource limits have margin: +0.0 to +0.5
        """
        score = 0.0

        # Check permissions (0.5 for having all)
        has_all_permissions = all(
            check_permission(executor_task, perm)
            for perm in requirements.required_permissions
        )
        if has_all_permissions:
            score += 0.5

        # Check resource margin
        executor_limits = get_resource_limits(executor_task)
        if executor_limits:
            # ATP margin
            if requirements.estimated_atp_cost > 0:
                atp_margin = (
                    (executor_limits.atp_budget - requirements.estimated_atp_cost)
                    / executor_limits.atp_budget
                )
                score += min(0.2, atp_margin * 0.2)

            # Memory margin
            if requirements.estimated_memory_mb > 0:
                mem_margin = (
                    (executor_limits.memory_mb - requirements.estimated_memory_mb)
                    / executor_limits.memory_mb
                )
                score += min(0.2, mem_margin * 0.2)

            # CPU margin
            if requirements.estimated_cpu_cores > 0:
                cpu_margin = (
                    (executor_limits.cpu_cores - requirements.estimated_cpu_cores)
                    / executor_limits.cpu_cores
                )
                score += min(0.1, cpu_margin * 0.1)

        return min(1.0, score)

    def _log_delegation(
        self,
        delegator_lct: str,
        executor_lct: str,
        task_type: str,
        requirements: FederationTaskRequirements,
        permission_checked: bool,
        capability_checked: bool,
        success: bool,
        reason: str = ""
    ):
        """Log a delegation operation"""
        log_entry = DelegationLog(
            timestamp=time.time(),
            delegator_lct=delegator_lct,
            executor_lct=executor_lct,
            task_type=task_type,
            requirements=requirements,
            permission_checked=permission_checked,
            capability_checked=capability_checked,
            success=success,
            reason=reason
        )
        self.delegation_log.append(log_entry)

    def get_delegation_log(
        self,
        delegator_lct: Optional[str] = None,
        limit: int = 100
    ) -> List[DelegationLog]:
        """
        Get delegation log entries.

        Args:
            delegator_lct: Filter by delegator (None = all)
            limit: Maximum entries to return

        Returns:
            List of delegation log entries (most recent first)
        """
        logs = self.delegation_log

        # Filter by delegator if specified
        if delegator_lct:
            logs = [log for log in logs if log.delegator_lct == delegator_lct]

        # Sort by timestamp (most recent first)
        logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        return logs[:limit]

    def get_router_stats(self) -> Dict[str, Any]:
        """
        Get overall router statistics.

        Returns:
            Dictionary with router-wide stats
        """
        total_delegations = len(self.delegation_log)
        successful_delegations = sum(1 for log in self.delegation_log if log.success)
        failed_delegations = total_delegations - successful_delegations

        # Permission denial stats
        permission_denials = sum(
            1 for log in self.delegation_log
            if not log.success and "delegation" in log.reason.lower()
        )

        # Capability mismatch stats
        capability_mismatches = sum(
            1 for log in self.delegation_log
            if not log.success and "incompatible" in log.reason.lower()
        )

        return {
            "platform": self.platform_name,
            "total_delegations": total_delegations,
            "successful_delegations": successful_delegations,
            "failed_delegations": failed_delegations,
            "permission_denials": permission_denials,
            "capability_mismatches": capability_mismatches
        }


def create_task_requirements_from_type(task_type: str) -> FederationTaskRequirements:
    """
    Create task requirements from task type.

    Args:
        task_type: Type of task (e.g., "perception", "code_execution", "planning")

    Returns:
        FederationTaskRequirements appropriate for task type

    Example:
        >>> reqs = create_task_requirements_from_type("code_execution")
        >>> reqs.requires_code_execution
        True
    """
    if task_type == "perception":
        return FederationTaskRequirements(
            required_permissions=["atp:read", "network:http"],
            required_capabilities={"can_perceive": True},
            estimated_atp_cost=50.0,
            estimated_memory_mb=2048,
            estimated_cpu_cores=2,
            requires_network=True,
            requires_code_execution=False
        )

    elif task_type == "planning":
        return FederationTaskRequirements(
            required_permissions=["atp:read"],
            required_capabilities={"can_plan": True},
            estimated_atp_cost=50.0,
            estimated_memory_mb=4096,
            estimated_cpu_cores=4,
            requires_network=False,
            requires_code_execution=False
        )

    elif task_type == "code_execution":
        return FederationTaskRequirements(
            required_permissions=["atp:write", "exec:code", "storage:write"],
            required_capabilities={"can_execute_code": True},
            estimated_atp_cost=200.0,
            estimated_memory_mb=8192,
            estimated_cpu_cores=8,
            requires_network=True,
            requires_code_execution=True
        )

    elif task_type == "data_processing":
        return FederationTaskRequirements(
            required_permissions=["atp:write", "storage:read", "storage:write"],
            required_capabilities={"can_process_data": True},
            estimated_atp_cost=100.0,
            estimated_memory_mb=4096,
            estimated_cpu_cores=4,
            requires_network=False,
            requires_code_execution=False
        )

    else:
        # Default requirements
        return FederationTaskRequirements(
            required_permissions=["atp:read"],
            estimated_atp_cost=50.0,
            estimated_memory_mb=2048,
            estimated_cpu_cores=2,
            requires_network=False,
            requires_code_execution=False
        )
