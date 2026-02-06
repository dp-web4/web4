"""
LCT Identity Permission System

Task-based permission checking and resource limit enforcement for LCT identities.
Implements the permission matrix from LCT_IDENTITY_SYSTEM.md Phase 3.

Now integrated with LCT Unified Permission Standard (LUPS v1.0) from Session #51.

Author: Legion Autonomous Session #49 (original), #52 (LUPS integration)
Date: 2025-12-02
Status: Phase 3 implementation + LUPS v1.0 integration
References: LCT_IDENTITY_SYSTEM.md, lct_identity.py, identity_registry.py,
           LCT_UNIFIED_PERMISSION_STANDARD.md, lct_unified_permissions.py

Permission Philosophy:
- Tasks define capabilities (what an agent can do)
- Permissions are checked before operations
- Resource limits enforced per-identity
- No escalation: agents cannot grant themselves more permissions

Permission Categories:
1. ATP Operations (atp:read, atp:write, atp:all)
2. Federation (federation:delegate, federation:execute)
3. Code Execution (exec:safe, exec:code, exec:network)
4. Admin (admin:read, admin:write, admin:full)
5. Network (network:http, network:ws, network:p2p, network:all)
6. Storage (storage:read, storage:write, storage:delete, storage:all)

Task Types (10 total, from LUPS v1.0):
- perception, planning, planning.strategic
- execution.safe, execution.code
- delegation.federation
- consciousness, consciousness.sage (NEW: for SAGE integration)
- admin.readonly, admin.full
"""

from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class PermissionCategory(Enum):
    """Permission categories for LCT identities"""
    ATP = "atp"
    FEDERATION = "federation"
    EXECUTION = "execution"
    ADMIN = "admin"
    NETWORK = "network"
    STORAGE = "storage"


class ATPPermission(Enum):
    """ATP (Attention Token Protocol) permissions"""
    READ = "atp:read"           # Query ATP balances
    WRITE = "atp:write"         # Transfer ATP within budget
    ALL = "atp:all"             # Unlimited ATP operations


class FederationPermission(Enum):
    """Federation (cross-platform) permissions"""
    DELEGATE = "federation:delegate"    # Delegate tasks to other platforms
    EXECUTE = "federation:execute"      # Execute tasks from other platforms
    ALL = "federation:all"              # Full federation capabilities


class ExecutionPermission(Enum):
    """Code execution permissions"""
    SAFE = "exec:safe"          # Sandboxed execution only
    CODE = "exec:code"          # Execute arbitrary code
    NETWORK = "exec:network"    # Make network calls
    ALL = "exec:all"            # Full execution capabilities


class AdminPermission(Enum):
    """Administrative permissions"""
    READ = "admin:read"         # Read system state
    WRITE = "admin:write"       # Modify system state
    FULL = "admin:full"         # Complete administrative access


class NetworkPermission(Enum):
    """Network access permissions"""
    HTTP = "network:http"       # HTTP/HTTPS requests
    WEBSOCKET = "network:ws"    # WebSocket connections
    P2P = "network:p2p"         # Direct peer-to-peer
    ALL = "network:all"         # All network access


class StoragePermission(Enum):
    """Storage access permissions"""
    READ = "storage:read"       # Read from storage
    WRITE = "storage:write"     # Write to storage
    DELETE = "storage:delete"   # Delete from storage
    ALL = "storage:all"         # All storage operations


@dataclass
class ResourceLimits:
    """
    Resource limits for LCT identity.

    Enforced by platform to prevent resource abuse.
    """
    atp_budget: float = 0.0           # Maximum ATP this identity can spend
    memory_mb: int = 1024             # Maximum memory (MB)
    cpu_cores: int = 1                # Maximum CPU cores
    disk_mb: int = 1024               # Maximum disk space (MB)
    network_bandwidth_mbps: int = 10  # Maximum network bandwidth (Mbps)
    max_tasks: int = 10               # Maximum concurrent tasks

    def __post_init__(self):
        """Validate resource limits"""
        if self.atp_budget < 0:
            raise ValueError("ATP budget cannot be negative")
        if self.memory_mb <= 0:
            raise ValueError("Memory limit must be positive")
        if self.cpu_cores <= 0:
            raise ValueError("CPU cores must be positive")
        if self.disk_mb <= 0:
            raise ValueError("Disk limit must be positive")
        if self.network_bandwidth_mbps < 0:
            raise ValueError("Network bandwidth cannot be negative")
        if self.max_tasks <= 0:
            raise ValueError("Max tasks must be positive")


@dataclass
class TaskPermissionDefinition:
    """
    Permission definition for a task type.

    Defines what a task is allowed to do.
    """
    task_name: str
    permissions: Set[str] = field(default_factory=set)
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    description: str = ""
    can_delegate: bool = False
    can_execute_code: bool = False

    def has_permission(self, permission: str) -> bool:
        """Check if task has a specific permission"""
        # Check exact match
        if permission in self.permissions:
            return True

        # Check wildcard permissions
        category = permission.split(':')[0] if ':' in permission else ''
        if f"{category}:all" in self.permissions:
            return True

        return False

    def check_resource_limit(self, resource: str, value: float) -> Tuple[bool, str]:
        """
        Check if resource usage is within limits.

        Args:
            resource: Resource type (atp, memory, cpu, etc.)
            value: Requested value

        Returns:
            (allowed, reason) tuple
        """
        if resource == "atp":
            if value > self.resource_limits.atp_budget:
                return (False, f"ATP request {value} exceeds budget {self.resource_limits.atp_budget}")
            return (True, "")

        elif resource == "memory":
            if value > self.resource_limits.memory_mb:
                return (False, f"Memory request {value}MB exceeds limit {self.resource_limits.memory_mb}MB")
            return (True, "")

        elif resource == "cpu":
            if value > self.resource_limits.cpu_cores:
                return (False, f"CPU request {value} cores exceeds limit {self.resource_limits.cpu_cores} cores")
            return (True, "")

        elif resource == "disk":
            if value > self.resource_limits.disk_mb:
                return (False, f"Disk request {value}MB exceeds limit {self.resource_limits.disk_mb}MB")
            return (True, "")

        elif resource == "network":
            if value > self.resource_limits.network_bandwidth_mbps:
                return (False, f"Network request {value}Mbps exceeds limit {self.resource_limits.network_bandwidth_mbps}Mbps")
            return (True, "")

        elif resource == "tasks":
            if value > self.resource_limits.max_tasks:
                return (False, f"Task count {value} exceeds limit {self.resource_limits.max_tasks}")
            return (True, "")

        else:
            return (False, f"Unknown resource type: {resource}")


# ============================================================================
# Task Permission Matrix (from LCT_IDENTITY_SYSTEM.md)
# ============================================================================

TASK_PERMISSIONS: Dict[str, TaskPermissionDefinition] = {
    # Perception tasks - Read-only, safe operations
    "perception": TaskPermissionDefinition(
        task_name="perception",
        permissions={
            ATPPermission.READ.value,
            NetworkPermission.HTTP.value,
            StoragePermission.READ.value  # Added in LUPS v1.0
        },
        resource_limits=ResourceLimits(
            atp_budget=200.0,  # Updated to LUPS v1.0
            memory_mb=2048,
            cpu_cores=2,
            disk_mb=1024,
            network_bandwidth_mbps=10,
            max_tasks=5
        ),
        description="Perception and information gathering (read-only)",
        can_delegate=False,
        can_execute_code=False
    ),

    # Planning tasks - Read-only, no execution
    "planning": TaskPermissionDefinition(
        task_name="planning",
        permissions={
            ATPPermission.READ.value
        },
        resource_limits=ResourceLimits(
            atp_budget=500.0,  # Updated to LUPS v1.0
            memory_mb=2048,     # Updated to LUPS v1.0
            cpu_cores=2,        # Updated to LUPS v1.0
            disk_mb=1024,
            network_bandwidth_mbps=0,  # No network (LUPS v1.0)
            max_tasks=10
        ),
        description="Planning and reasoning (read-only)",
        can_delegate=False,
        can_execute_code=False
    ),

    # Planning.strategic - Enhanced planning with external data (NEW: LUPS v1.0)
    "planning.strategic": TaskPermissionDefinition(
        task_name="planning.strategic",
        permissions={
            ATPPermission.READ.value,
            NetworkPermission.HTTP.value,
            StoragePermission.READ.value
        },
        resource_limits=ResourceLimits(
            atp_budget=500.0,
            memory_mb=4096,
            cpu_cores=4,
            disk_mb=2048,
            network_bandwidth_mbps=10,
            max_tasks=20
        ),
        description="Enhanced planning with external data",
        can_delegate=False,
        can_execute_code=False
    ),

    # Code execution - Can execute code, read/write ATP
    "execution.code": TaskPermissionDefinition(
        task_name="execution.code",
        permissions={
            ATPPermission.READ.value,
            ATPPermission.WRITE.value,
            ExecutionPermission.CODE.value,
            NetworkPermission.HTTP.value,
            StoragePermission.READ.value,
            StoragePermission.WRITE.value
        },
        resource_limits=ResourceLimits(
            atp_budget=500.0,
            memory_mb=8192,
            cpu_cores=8,
            disk_mb=10240,
            network_bandwidth_mbps=50,
            max_tasks=20
        ),
        description="Code execution with network and storage access",
        can_delegate=False,
        can_execute_code=True
    ),

    # Safe execution - Sandboxed only
    "execution.safe": TaskPermissionDefinition(
        task_name="execution.safe",
        permissions={
            ATPPermission.READ.value,
            ExecutionPermission.SAFE.value
        },
        resource_limits=ResourceLimits(
            atp_budget=200.0,
            memory_mb=2048,
            cpu_cores=2,
            disk_mb=1024,
            network_bandwidth_mbps=0,  # No network
            max_tasks=5
        ),
        description="Sandboxed execution (no network, limited resources)",
        can_delegate=False,
        can_execute_code=True
    ),

    # Federation delegation - Can delegate tasks
    "delegation.federation": TaskPermissionDefinition(
        task_name="delegation.federation",
        permissions={
            ATPPermission.READ.value,
            ATPPermission.WRITE.value,
            FederationPermission.DELEGATE.value,
            NetworkPermission.ALL.value
        },
        resource_limits=ResourceLimits(
            atp_budget=1000.0,
            memory_mb=4096,
            cpu_cores=2,  # Updated to LUPS v1.0
            disk_mb=2048,  # Updated to LUPS v1.0
            network_bandwidth_mbps=100,
            max_tasks=50
        ),
        description="Cross-platform task delegation",
        can_delegate=True,
        can_execute_code=False
    ),

    # Consciousness - Autonomous consciousness loops (NEW: LUPS v1.0 for SAGE)
    "consciousness": TaskPermissionDefinition(
        task_name="consciousness",
        permissions={
            ATPPermission.READ.value,
            ATPPermission.WRITE.value,
            ExecutionPermission.CODE.value,
            ExecutionPermission.NETWORK.value,
            NetworkPermission.HTTP.value,
            NetworkPermission.WEBSOCKET.value,
            NetworkPermission.P2P.value,
            StoragePermission.READ.value,
            StoragePermission.WRITE.value,
            FederationPermission.DELEGATE.value,
            FederationPermission.EXECUTE.value
        },
        resource_limits=ResourceLimits(
            atp_budget=1000.0,
            memory_mb=16384,  # 16GB
            cpu_cores=8,
            disk_mb=20480,  # 20GB
            network_bandwidth_mbps=100,
            max_tasks=100
        ),
        description="Autonomous consciousness loops (SAGE integration)",
        can_delegate=True,
        can_execute_code=True
    ),

    # Consciousness.sage - Enhanced SAGE consciousness (NEW: LUPS v1.0)
    "consciousness.sage": TaskPermissionDefinition(
        task_name="consciousness.sage",
        permissions={
            ATPPermission.READ.value,
            ATPPermission.WRITE.value,
            ExecutionPermission.CODE.value,
            ExecutionPermission.NETWORK.value,
            NetworkPermission.HTTP.value,
            NetworkPermission.WEBSOCKET.value,
            NetworkPermission.P2P.value,
            StoragePermission.READ.value,
            StoragePermission.WRITE.value,
            StoragePermission.DELETE.value,
            FederationPermission.DELEGATE.value,
            FederationPermission.EXECUTE.value
        },
        resource_limits=ResourceLimits(
            atp_budget=2000.0,
            memory_mb=32768,  # 32GB
            cpu_cores=16,
            disk_mb=51200,  # 50GB
            network_bandwidth_mbps=1000,  # 1Gbps
            max_tasks=200
        ),
        description="Enhanced SAGE consciousness with elevated resources",
        can_delegate=True,
        can_execute_code=True
    ),

    # Admin - Full permissions
    "admin.full": TaskPermissionDefinition(
        task_name="admin.full",
        permissions={
            ATPPermission.ALL.value,
            FederationPermission.ALL.value,
            ExecutionPermission.ALL.value,
            AdminPermission.FULL.value,
            NetworkPermission.ALL.value,
            StoragePermission.ALL.value
        },
        resource_limits=ResourceLimits(
            atp_budget=float('inf'),  # Unlimited
            memory_mb=1024 * 100,     # 100GB
            cpu_cores=64,
            disk_mb=1024 * 1000,      # 1TB
            network_bandwidth_mbps=10000,  # 10Gbps
            max_tasks=1000
        ),
        description="Full administrative access (unrestricted)",
        can_delegate=True,
        can_execute_code=True
    ),

    # Admin read-only
    "admin.readonly": TaskPermissionDefinition(
        task_name="admin.readonly",
        permissions={
            AdminPermission.READ.value,
            NetworkPermission.HTTP.value,
            StoragePermission.READ.value
        },
        resource_limits=ResourceLimits(
            atp_budget=100.0,
            memory_mb=4096,
            cpu_cores=4,
            disk_mb=2048,
            network_bandwidth_mbps=10,
            max_tasks=10
        ),
        description="Read-only administrative access",
        can_delegate=False,
        can_execute_code=False
    ),
}


# ============================================================================
# Permission Checking Functions
# ============================================================================

def get_task_permissions(task: str) -> Optional[TaskPermissionDefinition]:
    """
    Get permission definition for a task.

    Args:
        task: Task identifier (e.g., "perception", "execution.code")

    Returns:
        TaskPermissionDefinition or None if task not found

    Example:
        >>> perms = get_task_permissions("perception")
        >>> perms.has_permission("atp:read")
        True
        >>> perms.has_permission("admin:write")
        False
    """
    return TASK_PERMISSIONS.get(task)


def check_permission(task: str, permission: str) -> bool:
    """
    Check if a task has a specific permission.

    Args:
        task: Task identifier
        permission: Permission to check (e.g., "atp:read", "exec:code")

    Returns:
        True if task has permission, False otherwise

    Example:
        >>> check_permission("perception", "atp:read")
        True
        >>> check_permission("perception", "admin:write")
        False
        >>> check_permission("admin.full", "atp:write")
        True
    """
    task_perms = get_task_permissions(task)
    if not task_perms:
        return False

    return task_perms.has_permission(permission)


def check_resource_limit(
    task: str,
    resource: str,
    requested_value: float
) -> Tuple[bool, str]:
    """
    Check if resource request is within task limits.

    Args:
        task: Task identifier
        resource: Resource type (atp, memory, cpu, disk, network, tasks)
        requested_value: Requested resource amount

    Returns:
        (allowed, reason) tuple

    Example:
        >>> allowed, reason = check_resource_limit("perception", "atp", 50.0)
        >>> allowed
        True
        >>> allowed, reason = check_resource_limit("perception", "atp", 500.0)
        >>> allowed
        False
    """
    task_perms = get_task_permissions(task)
    if not task_perms:
        return (False, f"Unknown task: {task}")

    return task_perms.check_resource_limit(resource, requested_value)


def can_delegate(task: str) -> bool:
    """Check if task can delegate to other agents"""
    task_perms = get_task_permissions(task)
    return task_perms.can_delegate if task_perms else False


def can_execute_code(task: str) -> bool:
    """Check if task can execute code"""
    task_perms = get_task_permissions(task)
    return task_perms.can_execute_code if task_perms else False


def get_atp_budget(task: str) -> float:
    """Get ATP budget limit for task"""
    task_perms = get_task_permissions(task)
    return task_perms.resource_limits.atp_budget if task_perms else 0.0


def list_permissions(task: str) -> Set[str]:
    """List all permissions for a task"""
    task_perms = get_task_permissions(task)
    return task_perms.permissions if task_perms else set()


def get_resource_limits(task: str) -> Optional[ResourceLimits]:
    """Get resource limits for a task"""
    task_perms = get_task_permissions(task)
    return task_perms.resource_limits if task_perms else None


# ============================================================================
# Permission Validation
# ============================================================================

def validate_task_permissions() -> List[str]:
    """
    Validate task permission definitions.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    for task_name, task_def in TASK_PERMISSIONS.items():
        # Check task name matches
        if task_def.task_name != task_name:
            errors.append(f"Task name mismatch: {task_name} != {task_def.task_name}")

        # Validate resource limits
        try:
            ResourceLimits(**task_def.resource_limits.__dict__)
        except ValueError as e:
            errors.append(f"Invalid resource limits for {task_name}: {e}")

        # Check for empty permissions (except admin.full which has 'all' permissions)
        if not task_def.permissions and task_name != "admin.full":
            errors.append(f"Task {task_name} has no permissions")

    return errors


def get_permission_matrix() -> Dict[str, Dict[str, Any]]:
    """
    Get complete permission matrix for all tasks.

    Returns:
        Dictionary mapping task → capabilities

    Example output:
        {
            "perception": {
                "atp": "read",
                "federation": "no",
                "code_exec": "no",
                "admin": "no",
                "atp_budget": 100.0
            },
            ...
        }
    """
    matrix = {}

    for task_name, task_def in TASK_PERMISSIONS.items():
        # Determine capability levels
        atp_level = "no"
        if check_permission(task_name, "atp:all"):
            atp_level = "all"
        elif check_permission(task_name, "atp:write"):
            atp_level = "read/write"
        elif check_permission(task_name, "atp:read"):
            atp_level = "read"

        federation_level = "yes" if task_def.can_delegate else "no"
        exec_level = "yes" if task_def.can_execute_code else "no"

        admin_level = "no"
        if check_permission(task_name, "admin:full"):
            admin_level = "full"
        elif check_permission(task_name, "admin:write"):
            admin_level = "write"
        elif check_permission(task_name, "admin:read"):
            admin_level = "read"

        matrix[task_name] = {
            "atp": atp_level,
            "federation": federation_level,
            "code_exec": exec_level,
            "admin": admin_level,
            "atp_budget": task_def.resource_limits.atp_budget,
            "memory_mb": task_def.resource_limits.memory_mb,
            "cpu_cores": task_def.resource_limits.cpu_cores,
            "description": task_def.description
        }

    return matrix
