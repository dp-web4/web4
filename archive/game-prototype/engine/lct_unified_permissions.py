"""
LCT Unified Permission Standard (LUPS v1.0)

Cross-platform standard for Web4 LCT task-based permissions.
Harmonizes web4 (Legion Sessions #47-50) and HRM/SAGE (Thor) implementations.

This module provides:
- Unified task type taxonomy (10 standardized tasks)
- Consistent permission matrix across platforms
- Common resource limit structure
- Cross-platform compatibility layer

Author: Legion Autonomous Session #51
Date: 2025-12-02
References: LCT_UNIFIED_PERMISSION_STANDARD.md
"""

from typing import Dict, Set, Any
from dataclasses import dataclass, field
import time


@dataclass
class UnifiedResourceLimits:
    """
    Unified resource limits for LCT tasks

    Compatible with both web4 and HRM/SAGE implementations.
    """
    # ATP
    atp_budget: float = 0.0              # Maximum ATP to spend

    # Compute
    memory_mb: int = 1024                # Maximum memory (MB)
    cpu_cores: int = 1                   # Maximum CPU cores

    # Storage
    disk_mb: int = 1024                  # Maximum disk space (MB)

    # Network
    network_bandwidth_mbps: int = 10     # Maximum network bandwidth (Mbps)

    # Concurrency
    max_tasks: int = 10                  # Maximum concurrent tasks

    # Metadata
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate resource limits"""
        if self.atp_budget < 0 and self.atp_budget != float('inf'):
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

    @property
    def max_concurrent_tasks(self) -> int:
        """Alias for HRM/SAGE compatibility"""
        return self.max_tasks

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "atp_budget": self.atp_budget,
            "memory_mb": self.memory_mb,
            "cpu_cores": self.cpu_cores,
            "disk_mb": self.disk_mb,
            "network_bandwidth_mbps": self.network_bandwidth_mbps,
            "max_tasks": self.max_tasks,
            "created_at": self.created_at
        }


# Unified Task Permission Matrix
UNIFIED_TASK_PERMISSIONS: Dict[str, Dict[str, Any]] = {
    "perception": {
        "permissions": {
            "atp:read",
            "network:http",
            "storage:read",
            "federation:execute"
        },
        "can_delegate": False,
        "can_execute_code": False,
        "description": "Read-only perception and observation"
    },

    "planning": {
        "permissions": {
            "atp:read",
            "federation:execute"
        },
        "can_delegate": False,
        "can_execute_code": False,
        "description": "Basic planning and decision making"
    },

    "planning.strategic": {
        "permissions": {
            "atp:read",
            "network:http",
            "storage:read",
            "federation:execute"
        },
        "can_delegate": False,
        "can_execute_code": False,
        "description": "Enhanced planning with external data"
    },

    "execution.safe": {
        "permissions": {
            "atp:read",
            "atp:write",
            "storage:read",
            "storage:write",
            "exec:safe",
            "federation:execute"
        },
        "can_delegate": False,
        "can_execute_code": True,
        "code_execution_level": "sandbox",
        "description": "Sandboxed code execution"
    },

    "execution.code": {
        "permissions": {
            "atp:read",
            "atp:write",
            "exec:code",
            "exec:network",
            "network:http",
            "network:ws",
            "storage:read",
            "storage:write",
            "federation:execute"
        },
        "can_delegate": False,
        "can_execute_code": True,
        "code_execution_level": "full",
        "description": "Full code execution"
    },

    "delegation.federation": {
        "permissions": {
            "atp:read",
            "atp:write",
            "network:http",
            "network:ws",
            "network:p2p",
            "storage:read",
            "federation:delegate",
            "federation:execute"
        },
        "can_delegate": True,
        "can_execute_code": False,
        "description": "Cross-platform task delegation"
    },

    "consciousness": {
        "permissions": {
            "atp:read",
            "atp:write",
            "exec:code",
            "exec:network",
            "network:http",
            "network:ws",
            "network:p2p",
            "storage:read",
            "storage:write",
            "federation:delegate",
            "federation:execute"
        },
        "can_delegate": True,
        "can_execute_code": True,
        "code_execution_level": "full",
        "description": "Autonomous consciousness loops"
    },

    "consciousness.sage": {
        "permissions": {
            "atp:read",
            "atp:write",
            "exec:code",
            "exec:network",
            "network:http",
            "network:ws",
            "network:p2p",
            "storage:read",
            "storage:write",
            "storage:delete",
            "federation:delegate",
            "federation:execute"
        },
        "can_delegate": True,
        "can_execute_code": True,
        "code_execution_level": "full",
        "description": "SAGE consciousness with enhanced resources"
    },

    "admin.readonly": {
        "permissions": {
            "atp:read",
            "network:all",
            "storage:read",
            "admin:read",
            "federation:execute"
        },
        "can_delegate": False,
        "can_execute_code": False,
        "description": "Administrative read access"
    },

    "admin.full": {
        "permissions": {
            "atp:all",
            "exec:all",
            "network:all",
            "storage:all",
            "federation:all",
            "admin:full"
        },
        "can_delegate": True,
        "can_execute_code": True,
        "code_execution_level": "full",
        "description": "Full administrative access"
    }
}


# Unified Resource Limits by Task
UNIFIED_RESOURCE_LIMITS: Dict[str, UnifiedResourceLimits] = {
    "perception": UnifiedResourceLimits(
        atp_budget=200.0,
        memory_mb=2048,
        cpu_cores=2,
        disk_mb=1024,
        network_bandwidth_mbps=10,
        max_tasks=5
    ),

    "planning": UnifiedResourceLimits(
        atp_budget=500.0,
        memory_mb=2048,
        cpu_cores=2,
        disk_mb=1024,
        network_bandwidth_mbps=0,  # No network
        max_tasks=10
    ),

    "planning.strategic": UnifiedResourceLimits(
        atp_budget=500.0,
        memory_mb=4096,
        cpu_cores=4,
        disk_mb=2048,
        network_bandwidth_mbps=10,
        max_tasks=20
    ),

    "execution.safe": UnifiedResourceLimits(
        atp_budget=200.0,
        memory_mb=2048,
        cpu_cores=2,
        disk_mb=2048,
        network_bandwidth_mbps=0,  # Sandboxed, no network
        max_tasks=10
    ),

    "execution.code": UnifiedResourceLimits(
        atp_budget=1000.0,
        memory_mb=8192,
        cpu_cores=8,
        disk_mb=10240,  # 10GB
        network_bandwidth_mbps=100,
        max_tasks=20
    ),

    "delegation.federation": UnifiedResourceLimits(
        atp_budget=1000.0,
        memory_mb=4096,
        cpu_cores=2,
        disk_mb=2048,
        network_bandwidth_mbps=100,
        max_tasks=50
    ),

    "consciousness": UnifiedResourceLimits(
        atp_budget=1000.0,
        memory_mb=16384,  # 16GB
        cpu_cores=8,
        disk_mb=20480,  # 20GB
        network_bandwidth_mbps=100,
        max_tasks=100
    ),

    "consciousness.sage": UnifiedResourceLimits(
        atp_budget=2000.0,
        memory_mb=32768,  # 32GB
        cpu_cores=16,
        disk_mb=51200,  # 50GB
        network_bandwidth_mbps=1000,  # 1Gbps
        max_tasks=200
    ),

    "admin.readonly": UnifiedResourceLimits(
        atp_budget=100.0,
        memory_mb=1024,
        cpu_cores=1,
        disk_mb=1024,
        network_bandwidth_mbps=10,
        max_tasks=5
    ),

    "admin.full": UnifiedResourceLimits(
        atp_budget=float('inf'),
        memory_mb=1024 * 1024,  # 1TB (effectively unlimited)
        cpu_cores=128,
        disk_mb=1024 * 1024,  # 1TB
        network_bandwidth_mbps=10000,  # 10Gbps
        max_tasks=10000
    )
}


def get_unified_task_permissions(task: str) -> Set[str]:
    """
    Get unified permission set for task

    Parameters:
    -----------
    task : str
        Task type (e.g., "consciousness", "perception")

    Returns:
    --------
    Set[str]
        Set of permission strings

    Examples:
    ---------
    >>> perms = get_unified_task_permissions("consciousness")
    >>> "atp:write" in perms
    True
    >>> "federation:delegate" in perms
    True
    """
    if task not in UNIFIED_TASK_PERMISSIONS:
        raise ValueError(f"Unknown task: {task}. Valid tasks: {list(UNIFIED_TASK_PERMISSIONS.keys())}")

    return UNIFIED_TASK_PERMISSIONS[task]["permissions"].copy()


def get_unified_resource_limits(task: str) -> UnifiedResourceLimits:
    """
    Get unified resource limits for task

    Parameters:
    -----------
    task : str
        Task type (e.g., "consciousness.sage", "execution.code")

    Returns:
    --------
    UnifiedResourceLimits
        Resource limits for task

    Examples:
    ---------
    >>> limits = get_unified_resource_limits("consciousness.sage")
    >>> limits.atp_budget
    2000.0
    >>> limits.memory_mb
    32768
    """
    if task not in UNIFIED_RESOURCE_LIMITS:
        raise ValueError(f"Unknown task: {task}. Valid tasks: {list(UNIFIED_RESOURCE_LIMITS.keys())}")

    return UNIFIED_RESOURCE_LIMITS[task]


def can_unified_delegate(task: str) -> bool:
    """
    Check if task can delegate to other platforms

    Parameters:
    -----------
    task : str
        Task type

    Returns:
    --------
    bool
        True if task can delegate

    Examples:
    ---------
    >>> can_unified_delegate("consciousness")
    True
    >>> can_unified_delegate("perception")
    False
    """
    if task not in UNIFIED_TASK_PERMISSIONS:
        return False

    return UNIFIED_TASK_PERMISSIONS[task]["can_delegate"]


def can_unified_execute_code(task: str) -> bool:
    """
    Check if task can execute code

    Parameters:
    -----------
    task : str
        Task type

    Returns:
    --------
    bool
        True if task can execute code

    Examples:
    ---------
    >>> can_unified_execute_code("consciousness.sage")
    True
    >>> can_unified_execute_code("planning")
    False
    """
    if task not in UNIFIED_TASK_PERMISSIONS:
        return False

    return UNIFIED_TASK_PERMISSIONS[task]["can_execute_code"]


def check_unified_permission(task: str, permission: str) -> bool:
    """
    Check if task has specific permission

    Parameters:
    -----------
    task : str
        Task type
    permission : str
        Permission to check (e.g., "atp:write", "exec:code")

    Returns:
    --------
    bool
        True if task has permission

    Examples:
    ---------
    >>> check_unified_permission("consciousness", "atp:write")
    True
    >>> check_unified_permission("perception", "atp:write")
    False
    """
    if task not in UNIFIED_TASK_PERMISSIONS:
        return False

    permissions = UNIFIED_TASK_PERMISSIONS[task]["permissions"]

    # Check exact match
    if permission in permissions:
        return True

    # Check wildcard permissions
    category = permission.split(':')[0] if ':' in permission else ''
    if f"{category}:all" in permissions:
        return True

    return False


def get_unified_atp_budget(task: str) -> float:
    """
    Get ATP budget for task

    Parameters:
    -----------
    task : str
        Task type

    Returns:
    --------
    float
        ATP budget (may be inf for admin.full)

    Examples:
    ---------
    >>> get_unified_atp_budget("consciousness.sage")
    2000.0
    >>> get_unified_atp_budget("admin.full")
    inf
    """
    return get_unified_resource_limits(task).atp_budget


def is_consciousness_task(task: str) -> bool:
    """
    Check if task is a consciousness variant

    Parameters:
    -----------
    task : str
        Task type

    Returns:
    --------
    bool
        True if task is consciousness or consciousness.sage

    Examples:
    ---------
    >>> is_consciousness_task("consciousness")
    True
    >>> is_consciousness_task("consciousness.sage")
    True
    >>> is_consciousness_task("perception")
    False
    """
    return task in ("consciousness", "consciousness.sage")


def is_sage_task(task: str) -> bool:
    """
    Check if task is SAGE-level consciousness

    Parameters:
    -----------
    task : str
        Task type

    Returns:
    --------
    bool
        True if task is consciousness.sage

    Examples:
    ---------
    >>> is_sage_task("consciousness.sage")
    True
    >>> is_sage_task("consciousness")
    False
    """
    return task == "consciousness.sage"


# Backward compatibility aliases for web4
TASK_PERMISSION_MATRIX = UNIFIED_TASK_PERMISSIONS
DEFAULT_RESOURCE_LIMITS = UNIFIED_RESOURCE_LIMITS

# Export all public symbols
__all__ = [
    'UnifiedResourceLimits',
    'UNIFIED_TASK_PERMISSIONS',
    'UNIFIED_RESOURCE_LIMITS',
    'get_unified_task_permissions',
    'get_unified_resource_limits',
    'can_unified_delegate',
    'can_unified_execute_code',
    'check_unified_permission',
    'get_unified_atp_budget',
    'is_consciousness_task',
    'is_sage_task',
    'TASK_PERMISSION_MATRIX',
    'DEFAULT_RESOURCE_LIMITS'
]
