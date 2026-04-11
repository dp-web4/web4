#!/usr/bin/env python3
"""
Web4 Reference Implementation: LCT Unified Permission Standard (LUPS v1.0)
Spec: docs/what/specifications/LCT_UNIFIED_PERMISSION_STANDARD.md (657 lines)

Covers:
  §1 Executive Summary & Motivation
  §2 Unified Task Type Taxonomy (10 standard tasks)
  §3 Permission Matrix Specification (6 categories)
  §4 Resource Limits Specification
  §5 Cross-Platform Compatibility (web4 + HRM/SAGE)
  §6 Migration Path
  §7 Benefits
  §8 Implementation Status

Run:  python3 lct_unified_permission_standard.py
"""

import time, math
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List, Tuple

# ── §2  Unified Task Type Taxonomy ─────────────────────────────────────

STANDARD_TASK_TYPES = [
    "perception",
    "planning",
    "planning.strategic",
    "execution.safe",
    "execution.code",
    "delegation.federation",
    "cognition",
    "cognition.sage",
    "admin.readonly",
    "admin.full",
]

# ── §3  Permission Categories ──────────────────────────────────────────

# Category 1: ATP Operations
ATP_PERMISSIONS = {"atp:read", "atp:write", "atp:all"}
# Category 2: Federation
FEDERATION_PERMISSIONS = {"federation:execute", "federation:delegate", "federation:all"}
# Category 3: Code Execution
EXEC_PERMISSIONS = {"exec:safe", "exec:code", "exec:network", "exec:all"}
# Category 4: Network
NETWORK_PERMISSIONS = {"network:http", "network:ws", "network:p2p", "network:all"}
# Category 5: Storage
STORAGE_PERMISSIONS = {"storage:read", "storage:write", "storage:delete", "storage:all"}
# Category 6: Admin
ADMIN_PERMISSIONS = {"admin:read", "admin:write", "admin:full"}

ALL_PERMISSION_CATEGORIES = {
    "atp": ATP_PERMISSIONS,
    "federation": FEDERATION_PERMISSIONS,
    "exec": EXEC_PERMISSIONS,
    "network": NETWORK_PERMISSIONS,
    "storage": STORAGE_PERMISSIONS,
    "admin": ADMIN_PERMISSIONS,
}


@dataclass
class TaskPermissionConfig:
    """Permission configuration for a task type."""
    permissions: Set[str]
    can_delegate: bool
    can_execute_code: bool
    code_execution_level: Optional[str] = None  # "sandbox" or "full"
    description: str = ""


# Complete Permission Matrix from spec §3
UNIFIED_TASK_PERMISSIONS: Dict[str, TaskPermissionConfig] = {
    "perception": TaskPermissionConfig(
        permissions={"atp:read", "network:http", "storage:read", "federation:execute"},
        can_delegate=False,
        can_execute_code=False,
        description="Read-only perception and observation",
    ),
    "planning": TaskPermissionConfig(
        permissions={"atp:read", "federation:execute"},
        can_delegate=False,
        can_execute_code=False,
        description="Basic planning and decision making",
    ),
    "planning.strategic": TaskPermissionConfig(
        permissions={"atp:read", "network:http", "storage:read", "federation:execute"},
        can_delegate=False,
        can_execute_code=False,
        description="Enhanced planning with external data",
    ),
    "execution.safe": TaskPermissionConfig(
        permissions={"atp:read", "atp:write", "storage:read", "storage:write", "exec:safe", "federation:execute"},
        can_delegate=False,
        can_execute_code=True,
        code_execution_level="sandbox",
        description="Sandboxed code execution",
    ),
    "execution.code": TaskPermissionConfig(
        permissions={
            "atp:read", "atp:write", "exec:code", "exec:network",
            "network:http", "network:ws", "storage:read", "storage:write",
            "federation:execute",
        },
        can_delegate=False,
        can_execute_code=True,
        code_execution_level="full",
        description="Full code execution",
    ),
    "delegation.federation": TaskPermissionConfig(
        permissions={
            "atp:read", "atp:write", "network:http", "network:ws", "network:p2p",
            "storage:read", "federation:delegate", "federation:execute",
        },
        can_delegate=True,
        can_execute_code=False,
        description="Cross-platform task delegation",
    ),
    "cognition": TaskPermissionConfig(
        permissions={
            "atp:read", "atp:write", "exec:code", "exec:network",
            "network:http", "network:ws", "network:p2p",
            "storage:read", "storage:write",
            "federation:delegate", "federation:execute",
        },
        can_delegate=True,
        can_execute_code=True,
        code_execution_level="full",
        description="Autonomous cognition loops",
    ),
    "cognition.sage": TaskPermissionConfig(
        permissions={
            "atp:read", "atp:write", "exec:code", "exec:network",
            "network:http", "network:ws", "network:p2p",
            "storage:read", "storage:write", "storage:delete",
            "federation:delegate", "federation:execute",
        },
        can_delegate=True,
        can_execute_code=True,
        code_execution_level="full",
        description="SAGE cognition with enhanced resources",
    ),
    "admin.readonly": TaskPermissionConfig(
        permissions={"atp:read", "network:all", "storage:read", "admin:read", "federation:execute"},
        can_delegate=False,
        can_execute_code=False,
        description="Administrative read access",
    ),
    "admin.full": TaskPermissionConfig(
        permissions={"atp:all", "exec:all", "network:all", "storage:all", "federation:all", "admin:full"},
        can_delegate=True,
        can_execute_code=True,
        code_execution_level="full",
        description="Full administrative access",
    ),
}

# ── §4  Resource Limits ────────────────────────────────────────────────

@dataclass
class UnifiedResourceLimits:
    """Unified resource limits for LCT tasks."""
    atp_budget: float = 0.0
    memory_mb: int = 1024
    cpu_cores: int = 1
    disk_mb: int = 1024
    network_bandwidth_mbps: int = 10
    max_tasks: int = 10
    max_concurrent_tasks: int = 10  # Alias for HRM/SAGE compatibility
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        self.max_concurrent_tasks = self.max_tasks


UNIFIED_RESOURCE_LIMITS: Dict[str, UnifiedResourceLimits] = {
    "perception": UnifiedResourceLimits(
        atp_budget=200.0, memory_mb=2048, cpu_cores=2,
        disk_mb=1024, network_bandwidth_mbps=10, max_tasks=5,
    ),
    "planning": UnifiedResourceLimits(
        atp_budget=500.0, memory_mb=2048, cpu_cores=2,
        disk_mb=1024, network_bandwidth_mbps=0, max_tasks=10,
    ),
    "planning.strategic": UnifiedResourceLimits(
        atp_budget=500.0, memory_mb=4096, cpu_cores=4,
        disk_mb=2048, network_bandwidth_mbps=10, max_tasks=20,
    ),
    "execution.safe": UnifiedResourceLimits(
        atp_budget=200.0, memory_mb=2048, cpu_cores=2,
        disk_mb=2048, network_bandwidth_mbps=0, max_tasks=10,
    ),
    "execution.code": UnifiedResourceLimits(
        atp_budget=1000.0, memory_mb=8192, cpu_cores=8,
        disk_mb=10240, network_bandwidth_mbps=100, max_tasks=20,
    ),
    "delegation.federation": UnifiedResourceLimits(
        atp_budget=1000.0, memory_mb=4096, cpu_cores=2,
        disk_mb=2048, network_bandwidth_mbps=100, max_tasks=50,
    ),
    "cognition": UnifiedResourceLimits(
        atp_budget=1000.0, memory_mb=16384, cpu_cores=8,
        disk_mb=20480, network_bandwidth_mbps=100, max_tasks=100,
    ),
    "cognition.sage": UnifiedResourceLimits(
        atp_budget=2000.0, memory_mb=32768, cpu_cores=16,
        disk_mb=51200, network_bandwidth_mbps=1000, max_tasks=200,
    ),
    "admin.readonly": UnifiedResourceLimits(
        atp_budget=100.0, memory_mb=1024, cpu_cores=1,
        disk_mb=1024, network_bandwidth_mbps=10, max_tasks=5,
    ),
    "admin.full": UnifiedResourceLimits(
        atp_budget=float('inf'), memory_mb=1024 * 1024, cpu_cores=128,
        disk_mb=1024 * 1024, network_bandwidth_mbps=10000, max_tasks=10000,
    ),
}

# ── §3-§5  Permission Checker ──────────────────────────────────────────

class LUPSPermissionChecker:
    """Unified permission checker compatible with web4 + HRM/SAGE."""

    def __init__(self):
        self.task_permissions = UNIFIED_TASK_PERMISSIONS
        self.resource_limits = UNIFIED_RESOURCE_LIMITS

    def check_permission(self, task_type: str, permission: str) -> bool:
        """Check if a task type has a specific permission."""
        config = self.task_permissions.get(task_type)
        if not config:
            return False
        # Direct match
        if permission in config.permissions:
            return True
        # Check wildcard (:all) permissions
        category = permission.split(":")[0]
        wildcard = f"{category}:all"
        if wildcard in config.permissions:
            return True
        # admin:full covers all admin:* permissions
        if category == "admin" and "admin:full" in config.permissions:
            return True
        return False

    def can_delegate(self, task_type: str) -> bool:
        config = self.task_permissions.get(task_type)
        return config.can_delegate if config else False

    def can_execute_code(self, task_type: str) -> bool:
        config = self.task_permissions.get(task_type)
        return config.can_execute_code if config else False

    def get_code_execution_level(self, task_type: str) -> Optional[str]:
        config = self.task_permissions.get(task_type)
        return config.code_execution_level if config else None

    def get_atp_budget(self, task_type: str) -> float:
        limits = self.resource_limits.get(task_type)
        return limits.atp_budget if limits else 0.0

    def get_resource_limits(self, task_type: str) -> Optional[UnifiedResourceLimits]:
        return self.resource_limits.get(task_type)

    def validate_operation(self, task_type: str, operation: str, atp_cost: float = 0.0) -> Tuple[bool, str]:
        """Validate a complete operation against task permissions and resources."""
        config = self.task_permissions.get(task_type)
        if not config:
            return False, "unknown_task_type"

        if not self.check_permission(task_type, operation):
            return False, "permission_denied"

        limits = self.resource_limits.get(task_type)
        if limits and atp_cost > limits.atp_budget:
            return False, "exceeds_atp_budget"

        return True, "allowed"


# ── §5  Cross-Platform Compatibility ───────────────────────────────────

class Web4PermissionAdapter:
    """Adapter for web4 7-task system → unified 10-task system."""

    WEB4_LEGACY_TASKS = [
        "perception", "planning", "execution.safe", "execution.code",
        "delegation.federation", "admin.readonly", "admin.full",
    ]

    @staticmethod
    def is_legacy_task(task_type: str) -> bool:
        return task_type in Web4PermissionAdapter.WEB4_LEGACY_TASKS

    @staticmethod
    def get_new_tasks() -> List[str]:
        """Tasks added by LUPS that weren't in original web4."""
        return ["planning.strategic", "cognition", "cognition.sage"]


class SAGEPermissionAdapter:
    """Adapter for HRM/SAGE 9-task system → unified 10-task system."""

    SAGE_ORIGINAL_TASKS = [
        "perception", "planning", "planning.strategic",
        "execution.safe", "execution.code",
        "delegation.federation", "cognition",
        "admin.readonly", "admin.full",
    ]

    @staticmethod
    def convert_to_atp_enum(permissions: Set[str]) -> Set[str]:
        """Convert unified permission strings to SAGE ATP enum format."""
        atp_perms = set()
        for p in permissions:
            if p.startswith("atp:"):
                atp_perms.add(p.upper().replace(":", "_"))
        return atp_perms

    @staticmethod
    def get_new_tasks() -> List[str]:
        """Tasks added by LUPS that weren't in original SAGE."""
        return ["cognition.sage"]


# ── §6  Migration ──────────────────────────────────────────────────────

class MigrationValidator:
    """Validates backward compatibility during migration."""

    def __init__(self, checker: LUPSPermissionChecker):
        self.checker = checker

    def validate_web4_backward_compat(self) -> List[dict]:
        """Ensure all 7 original web4 tasks still work."""
        results = []
        for task in Web4PermissionAdapter.WEB4_LEGACY_TASKS:
            config = self.checker.task_permissions.get(task)
            results.append({
                "task": task,
                "exists": config is not None,
                "has_limits": self.checker.resource_limits.get(task) is not None,
            })
        return results

    def validate_sage_backward_compat(self) -> List[dict]:
        """Ensure all 9 original SAGE tasks still work."""
        results = []
        for task in SAGEPermissionAdapter.SAGE_ORIGINAL_TASKS:
            config = self.checker.task_permissions.get(task)
            results.append({
                "task": task,
                "exists": config is not None,
                "has_limits": self.checker.resource_limits.get(task) is not None,
            })
        return results

    def validate_cognition_hierarchy(self) -> dict:
        """cognition.sage ⊇ cognition (superset of permissions)."""
        cog = self.checker.task_permissions.get("cognition")
        sage = self.checker.task_permissions.get("cognition.sage")
        if not cog or not sage:
            return {"valid": False, "reason": "missing_task"}
        is_superset = cog.permissions.issubset(sage.permissions)
        extra_perms = sage.permissions - cog.permissions
        return {
            "valid": is_superset,
            "cognition_perms": len(cog.permissions),
            "sage_perms": len(sage.permissions),
            "extra_perms": extra_perms,
        }

    def validate_admin_hierarchy(self) -> dict:
        """admin.full ⊇ admin.readonly."""
        readonly = self.checker.task_permissions.get("admin.readonly")
        full = self.checker.task_permissions.get("admin.full")
        if not readonly or not full:
            return {"valid": False}
        # admin.full uses :all wildcards, so check that each readonly perm is covered
        all_covered = True
        for perm in readonly.permissions:
            if not self.checker.check_permission("admin.full", perm):
                all_covered = False
                break
        return {"valid": all_covered}


# ── §4  Resource Limit Hierarchy ───────────────────────────────────────

class ResourceHierarchyValidator:
    """Validates resource limits follow privilege escalation."""

    @staticmethod
    def validate_atp_budget_ordering() -> List[Tuple[str, str, bool]]:
        """Verify ATP budgets are ordered by privilege."""
        expected_order = [
            ("admin.readonly", "perception"),    # 100 < 200
            ("perception", "planning"),           # 200 < 500
            ("execution.safe", "execution.code"), # 200 < 1000
            ("cognition", "cognition.sage"),       # 1000 < 2000
        ]
        results = []
        for lower, higher in expected_order:
            lo_limits = UNIFIED_RESOURCE_LIMITS.get(lower)
            hi_limits = UNIFIED_RESOURCE_LIMITS.get(higher)
            valid = lo_limits.atp_budget <= hi_limits.atp_budget
            results.append((lower, higher, valid))
        return results

    @staticmethod
    def validate_max_tasks_ordering() -> List[Tuple[str, str, bool]]:
        """Verify max_tasks scales with privilege."""
        pairs = [
            ("perception", "planning"),           # 5 < 10
            ("planning", "planning.strategic"),    # 10 < 20
            ("delegation.federation", "cognition"),# 50 < 100
            ("cognition", "cognition.sage"),       # 100 < 200
        ]
        results = []
        for lower, higher in pairs:
            lo = UNIFIED_RESOURCE_LIMITS[lower].max_tasks
            hi = UNIFIED_RESOURCE_LIMITS[higher].max_tasks
            results.append((lower, higher, lo <= hi))
        return results


# ════════════════════════════════════════════════════════════════════════
#  TESTS
# ════════════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(label, condition):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✓ {label}")
        else:
            failed += 1
            print(f"  ✗ {label}")

    # ── §2  Task Type Taxonomy ─────────────────────────────────────
    print("\n§2 Unified Task Type Taxonomy")

    check("T1.1 10 standard task types", len(STANDARD_TASK_TYPES) == 10)
    check("T1.2 perception in tasks", "perception" in STANDARD_TASK_TYPES)
    check("T1.3 cognition.sage in tasks", "cognition.sage" in STANDARD_TASK_TYPES)
    check("T1.4 admin.full in tasks", "admin.full" in STANDARD_TASK_TYPES)
    check("T1.5 All tasks have configs", all(t in UNIFIED_TASK_PERMISSIONS for t in STANDARD_TASK_TYPES))
    check("T1.6 All tasks have limits", all(t in UNIFIED_RESOURCE_LIMITS for t in STANDARD_TASK_TYPES))

    # Task descriptions from spec
    check("T1.7 perception description", "perception" in UNIFIED_TASK_PERMISSIONS["perception"].description.lower())
    check("T1.8 planning description", "planning" in UNIFIED_TASK_PERMISSIONS["planning"].description.lower())
    check("T1.9 cognition description", "cognition" in UNIFIED_TASK_PERMISSIONS["cognition"].description.lower())

    # ── §3  Permission Matrix ──────────────────────────────────────
    print("\n§3 Permission Matrix Specification")

    checker = LUPSPermissionChecker()

    # Category 1: ATP Operations
    check("T2.1 perception has atp:read", checker.check_permission("perception", "atp:read"))
    check("T2.2 perception lacks atp:write", not checker.check_permission("perception", "atp:write"))
    check("T2.3 execution.safe has atp:write", checker.check_permission("execution.safe", "atp:write"))
    check("T2.4 admin.full has atp:all", checker.check_permission("admin.full", "atp:all"))
    check("T2.5 admin.full atp:read via wildcard", checker.check_permission("admin.full", "atp:read"))

    # Category 2: Federation
    check("T2.6 perception has federation:execute", checker.check_permission("perception", "federation:execute"))
    check("T2.7 perception lacks federation:delegate", not checker.check_permission("perception", "federation:delegate"))
    check("T2.8 delegation.federation has delegate", checker.check_permission("delegation.federation", "federation:delegate"))
    check("T2.9 cognition has federation:delegate", checker.check_permission("cognition", "federation:delegate"))

    # Category 3: Code Execution
    check("T2.10 perception cannot exec", not checker.can_execute_code("perception"))
    check("T2.11 execution.safe sandbox", checker.get_code_execution_level("execution.safe") == "sandbox")
    check("T2.12 execution.code full", checker.get_code_execution_level("execution.code") == "full")
    check("T2.13 cognition full exec", checker.get_code_execution_level("cognition") == "full")

    # Category 4: Network
    check("T2.14 planning no network", not checker.check_permission("planning", "network:http"))
    check("T2.15 perception has http", checker.check_permission("perception", "network:http"))
    check("T2.16 delegation has p2p", checker.check_permission("delegation.federation", "network:p2p"))
    check("T2.17 admin.readonly has all network", checker.check_permission("admin.readonly", "network:http"))

    # Category 5: Storage
    check("T2.18 perception has storage:read", checker.check_permission("perception", "storage:read"))
    check("T2.19 perception lacks storage:write", not checker.check_permission("perception", "storage:write"))
    check("T2.20 execution.safe has storage:write", checker.check_permission("execution.safe", "storage:write"))
    check("T2.21 cognition.sage has storage:delete", checker.check_permission("cognition.sage", "storage:delete"))
    check("T2.22 cognition lacks storage:delete", not checker.check_permission("cognition", "storage:delete"))

    # Category 6: Admin
    check("T2.23 admin.readonly has admin:read", checker.check_permission("admin.readonly", "admin:read"))
    check("T2.24 admin.readonly lacks admin:write", not checker.check_permission("admin.readonly", "admin:write"))
    check("T2.25 admin.full has admin:full", checker.check_permission("admin.full", "admin:full"))

    # Delegation flags
    check("T2.26 perception cannot delegate", not checker.can_delegate("perception"))
    check("T2.27 delegation.federation can delegate", checker.can_delegate("delegation.federation"))
    check("T2.28 cognition can delegate", checker.can_delegate("cognition"))
    check("T2.29 cognition.sage can delegate", checker.can_delegate("cognition.sage"))
    check("T2.30 admin.full can delegate", checker.can_delegate("admin.full"))

    # ── §3  Permission Category Coverage ───────────────────────────
    print("\n§3b Permission Categories")

    check("T3.1 6 permission categories", len(ALL_PERMISSION_CATEGORIES) == 6)
    check("T3.2 ATP has 3 perms", len(ATP_PERMISSIONS) == 3)
    check("T3.3 Federation has 3 perms", len(FEDERATION_PERMISSIONS) == 3)
    check("T3.4 Exec has 4 perms", len(EXEC_PERMISSIONS) == 4)
    check("T3.5 Network has 4 perms", len(NETWORK_PERMISSIONS) == 4)
    check("T3.6 Storage has 4 perms", len(STORAGE_PERMISSIONS) == 4)
    check("T3.7 Admin has 3 perms", len(ADMIN_PERMISSIONS) == 3)

    # All permissions in matrix are from known categories
    all_known = set()
    for perms in ALL_PERMISSION_CATEGORIES.values():
        all_known.update(perms)
    for task, config in UNIFIED_TASK_PERMISSIONS.items():
        for perm in config.permissions:
            if perm not in all_known:
                check(f"T3.x Unknown permission {perm} in {task}", False)
    check("T3.8 All permissions from known categories", True)

    # ── §4  Resource Limits ────────────────────────────────────────
    print("\n§4 Resource Limits Specification")

    # Spec-defined values
    perc_limits = UNIFIED_RESOURCE_LIMITS["perception"]
    check("T4.1 perception atp_budget = 200", perc_limits.atp_budget == 200.0)
    check("T4.2 perception memory_mb = 2048", perc_limits.memory_mb == 2048)
    check("T4.3 perception cpu_cores = 2", perc_limits.cpu_cores == 2)
    check("T4.4 perception max_tasks = 5", perc_limits.max_tasks == 5)

    plan_limits = UNIFIED_RESOURCE_LIMITS["planning"]
    check("T4.5 planning atp_budget = 500", plan_limits.atp_budget == 500.0)
    check("T4.6 planning network = 0 (no network)", plan_limits.network_bandwidth_mbps == 0)

    sage_limits = UNIFIED_RESOURCE_LIMITS["cognition.sage"]
    check("T4.7 sage atp_budget = 2000", sage_limits.atp_budget == 2000.0)
    check("T4.8 sage memory_mb = 32768", sage_limits.memory_mb == 32768)
    check("T4.9 sage cpu_cores = 16", sage_limits.cpu_cores == 16)
    check("T4.10 sage max_tasks = 200", sage_limits.max_tasks == 200)
    check("T4.11 sage network = 1000", sage_limits.network_bandwidth_mbps == 1000)

    admin_limits = UNIFIED_RESOURCE_LIMITS["admin.full"]
    check("T4.12 admin.full atp_budget = inf", admin_limits.atp_budget == float('inf'))
    check("T4.13 admin.full cpu_cores = 128", admin_limits.cpu_cores == 128)
    check("T4.14 admin.full max_tasks = 10000", admin_limits.max_tasks == 10000)

    exec_limits = UNIFIED_RESOURCE_LIMITS["execution.code"]
    check("T4.15 exec.code atp = 1000", exec_limits.atp_budget == 1000.0)
    check("T4.16 exec.code memory = 8192", exec_limits.memory_mb == 8192)
    check("T4.17 exec.code disk = 10240", exec_limits.disk_mb == 10240)

    # max_concurrent_tasks alias
    check("T4.18 max_concurrent = max_tasks", perc_limits.max_concurrent_tasks == perc_limits.max_tasks)

    # ── §4b  Resource Hierarchy ────────────────────────────────────
    print("\n§4b Resource Hierarchy Validation")

    rhv = ResourceHierarchyValidator()

    atp_ordering = rhv.validate_atp_budget_ordering()
    for lower, higher, valid in atp_ordering:
        check(f"T5.{atp_ordering.index((lower,higher,valid))+1} ATP: {lower} ≤ {higher}", valid)

    task_ordering = rhv.validate_max_tasks_ordering()
    for lower, higher, valid in task_ordering:
        check(f"T5.{len(atp_ordering)+task_ordering.index((lower,higher,valid))+1} Tasks: {lower} ≤ {higher}", valid)

    # ── §5  Cross-Platform Compatibility ───────────────────────────
    print("\n§5 Cross-Platform Compatibility")

    # web4 adapter
    check("T6.1 7 web4 legacy tasks", len(Web4PermissionAdapter.WEB4_LEGACY_TASKS) == 7)
    check("T6.2 perception is legacy", Web4PermissionAdapter.is_legacy_task("perception"))
    check("T6.3 cognition is NOT legacy", not Web4PermissionAdapter.is_legacy_task("cognition"))
    check("T6.4 3 new web4 tasks", len(Web4PermissionAdapter.get_new_tasks()) == 3)
    check("T6.5 cognition in new tasks", "cognition" in Web4PermissionAdapter.get_new_tasks())
    check("T6.6 cognition.sage in new tasks", "cognition.sage" in Web4PermissionAdapter.get_new_tasks())
    check("T6.7 planning.strategic in new", "planning.strategic" in Web4PermissionAdapter.get_new_tasks())

    # SAGE adapter
    check("T6.8 9 SAGE original tasks", len(SAGEPermissionAdapter.SAGE_ORIGINAL_TASKS) == 9)
    check("T6.9 cognition in SAGE", "cognition" in SAGEPermissionAdapter.SAGE_ORIGINAL_TASKS)
    check("T6.10 1 new SAGE task", len(SAGEPermissionAdapter.get_new_tasks()) == 1)
    check("T6.11 cognition.sage is new for SAGE", "cognition.sage" in SAGEPermissionAdapter.get_new_tasks())

    # ATP enum conversion
    test_perms = {"atp:read", "atp:write", "network:http"}
    atp_enums = SAGEPermissionAdapter.convert_to_atp_enum(test_perms)
    check("T6.12 ATP enum conversion", "ATP_READ" in atp_enums)
    check("T6.13 ATP enum count = 2", len(atp_enums) == 2)

    # ── §6  Migration Validation ───────────────────────────────────
    print("\n§6 Migration Path Validation")

    mv = MigrationValidator(checker)

    # web4 backward compat
    web4_results = mv.validate_web4_backward_compat()
    check("T7.1 All 7 web4 tasks exist", all(r["exists"] for r in web4_results))
    check("T7.2 All 7 web4 tasks have limits", all(r["has_limits"] for r in web4_results))

    # SAGE backward compat
    sage_results = mv.validate_sage_backward_compat()
    check("T7.3 All 9 SAGE tasks exist", all(r["exists"] for r in sage_results))
    check("T7.4 All 9 SAGE tasks have limits", all(r["has_limits"] for r in sage_results))

    # Cognition hierarchy
    cog_hier = mv.validate_cognition_hierarchy()
    check("T7.5 cognition ⊂ cognition.sage", cog_hier["valid"])
    check("T7.6 sage has more perms", cog_hier["sage_perms"] > cog_hier["cognition_perms"])
    check("T7.7 storage:delete is extra", "storage:delete" in cog_hier["extra_perms"])

    # Admin hierarchy
    admin_hier = mv.validate_admin_hierarchy()
    check("T7.8 admin.readonly ⊂ admin.full", admin_hier["valid"])

    # ── §3  Permission Checker Validation ──────────────────────────
    print("\n§3c Permission Checker Operations")

    # validate_operation
    ok, reason = checker.validate_operation("perception", "atp:read", 50.0)
    check("T8.1 Perception atp:read allowed", ok)
    check("T8.2 Reason allowed", reason == "allowed")

    ok2, reason2 = checker.validate_operation("perception", "atp:write", 0.0)
    check("T8.3 Perception atp:write denied", not ok2)
    check("T8.4 Reason permission_denied", reason2 == "permission_denied")

    ok3, reason3 = checker.validate_operation("perception", "atp:read", 999.0)
    check("T8.5 Perception exceeds budget", not ok3)
    check("T8.6 Reason exceeds_atp_budget", reason3 == "exceeds_atp_budget")

    ok4, reason4 = checker.validate_operation("unknown_task", "atp:read", 0.0)
    check("T8.7 Unknown task rejected", not ok4)
    check("T8.8 Reason unknown_task_type", reason4 == "unknown_task_type")

    # get_atp_budget
    check("T8.9 perception budget = 200", checker.get_atp_budget("perception") == 200.0)
    check("T8.10 cognition budget = 1000", checker.get_atp_budget("cognition") == 1000.0)
    check("T8.11 unknown budget = 0", checker.get_atp_budget("nonexistent") == 0.0)

    # get_resource_limits
    limits = checker.get_resource_limits("execution.code")
    check("T8.12 exec.code limits exist", limits is not None)
    check("T8.13 exec.code memory = 8192", limits.memory_mb == 8192)
    check("T8.14 Unknown task no limits", checker.get_resource_limits("nope") is None)

    # ── §2  Task Type Specific Properties ──────────────────────────
    print("\n§2b Task-Specific Properties")

    # From spec table: ATP Budget ranges
    check("T9.1 perception ATP 100-200", 100 <= UNIFIED_RESOURCE_LIMITS["perception"].atp_budget <= 200)
    check("T9.2 planning ATP 100-500", 100 <= UNIFIED_RESOURCE_LIMITS["planning"].atp_budget <= 500)
    check("T9.3 exec.code ATP 500-1000", 500 <= UNIFIED_RESOURCE_LIMITS["execution.code"].atp_budget <= 1000)
    check("T9.4 delegation ATP = 1000", UNIFIED_RESOURCE_LIMITS["delegation.federation"].atp_budget == 1000)
    check("T9.5 cognition ATP = 1000", UNIFIED_RESOURCE_LIMITS["cognition"].atp_budget == 1000)
    check("T9.6 cognition.sage ATP = 2000", UNIFIED_RESOURCE_LIMITS["cognition.sage"].atp_budget == 2000)

    # Execution.safe: sandbox = no network
    check("T9.7 exec.safe no network", UNIFIED_RESOURCE_LIMITS["execution.safe"].network_bandwidth_mbps == 0)
    check("T9.8 exec.safe has exec:safe perm", checker.check_permission("execution.safe", "exec:safe"))
    check("T9.9 exec.safe lacks exec:code", not checker.check_permission("execution.safe", "exec:code"))

    # Cognition.sage has everything cognition has + storage:delete
    cog_perms = UNIFIED_TASK_PERMISSIONS["cognition"].permissions
    sage_perms = UNIFIED_TASK_PERMISSIONS["cognition.sage"].permissions
    check("T9.10 sage ⊇ cognition", cog_perms.issubset(sage_perms))
    check("T9.11 sage has storage:delete", "storage:delete" in sage_perms)
    check("T9.12 cognition lacks storage:delete", "storage:delete" not in cog_perms)

    # admin.full has all wildcard permissions
    admin_perms = UNIFIED_TASK_PERMISSIONS["admin.full"].permissions
    check("T9.13 admin has atp:all", "atp:all" in admin_perms)
    check("T9.14 admin has exec:all", "exec:all" in admin_perms)
    check("T9.15 admin has network:all", "network:all" in admin_perms)
    check("T9.16 admin has storage:all", "storage:all" in admin_perms)
    check("T9.17 admin has federation:all", "federation:all" in admin_perms)
    check("T9.18 admin has admin:full", "admin:full" in admin_perms)

    # ── §1  Motivation Cross-Check ─────────────────────────────────
    print("\n§1 Motivation Cross-Check")

    # Unified standard must have at least 10 tasks
    check("T10.1 ≥10 tasks in unified", len(UNIFIED_TASK_PERMISSIONS) >= 10)

    # All web4 legacy tasks preserved
    for task in Web4PermissionAdapter.WEB4_LEGACY_TASKS:
        check(f"T10.{2+Web4PermissionAdapter.WEB4_LEGACY_TASKS.index(task)} web4 {task} preserved",
              task in UNIFIED_TASK_PERMISSIONS)

    # Cross-platform portability: cognition available
    check("T10.9 cognition exists for SAGE agents", "cognition" in UNIFIED_TASK_PERMISSIONS)
    check("T10.10 delegation exists for web4 agents", "delegation.federation" in UNIFIED_TASK_PERMISSIONS)

    # ── Summary ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"LCT Unified Permission Standard: {passed}/{total} checks passed")
    if failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {failed} checks FAILED")
    print(f"{'='*60}")
    return failed == 0


if __name__ == "__main__":
    run_tests()
