# LCT Unified Permission Standard (LUPS v1.0)

**Status**: Proposal - Cross-platform standard for Web4 LCT permissions
**Date**: 2025-12-02
**Authors**: Legion Session #51 (unifying Legion #47-50 + Thor HRM work)
**Context**: Harmonizing web4 and HRM/SAGE LCT permission systems

---

## Executive Summary

Two independent implementations of LCT task-based permissions have emerged:

1. **web4** (Legion Sessions #47-50): Comprehensive 7-task system with E2E validation
2. **HRM/SAGE** (Thor): 9-task system with consciousness and runtime tracking

This document proposes a **unified standard** that combines the best of both implementations, creating a cross-platform LCT permission specification for Web4.

---

## Motivation

### Current Situation

**web4 Implementation**:
- ✅ 7 task types with comprehensive permissions
- ✅ Multi-category permissions (ATP, Federation, Execution, Admin, Network, Storage)
- ✅ Resource limits (ATP budget, memory, CPU, disk, network, max_tasks)
- ✅ End-to-end tested (92 tests, 100% pass rate)
- ✅ Production-ready

**HRM/SAGE Implementation**:
- ✅ 9 task types including **consciousness** and **planning.strategic**
- ✅ Runtime permission checker with ATP spending tracking
- ✅ Instance-based permission validation
- ✅ 37 tests, 100% pass rate
- ✅ SAGE-specific optimizations

### Problem

Without a unified standard:
- ❌ Inconsistent task type names across platforms
- ❌ Different permission checking approaches
- ❌ Incompatible resource limit structures
- ❌ SAGE agents can't run on web4 infrastructure
- ❌ web4 agents can't leverage SAGE consciousness

### Solution

**LCT Unified Permission Standard (LUPS)** combining both systems:
- ✅ Unified task type taxonomy (10 standardized tasks)
- ✅ Consistent permission matrix across platforms
- ✅ Common resource limit structure
- ✅ Cross-platform agent portability
- ✅ Backward compatible with both systems

---

## Unified Task Type Taxonomy

### Standard Task Types (10 tasks)

| Task Type | ATP Ops | Federation | Code Exec | Network | Storage | Delegation | ATP Budget |
|-----------|---------|------------|-----------|---------|---------|------------|------------|
| **perception** | Read | Execute | No | HTTP | Read | No | 100-200 |
| **planning** | Read | Execute | No | No | No | No | 100-500 |
| **planning.strategic** | Read | Execute | No | HTTP | Read | No | 200-500 |
| **execution.safe** | R+W | Execute | Sandbox | No | R+W | No | 100-200 |
| **execution.code** | R+W | Execute | Full | Yes | R+W | No | 500-1000 |
| **delegation.federation** | R+W | Delegate | No | Yes | Read | Yes | 1000 |
| **consciousness** | R+W | Delegate | Full | Yes | R+W | Yes | 1000 |
| **consciousness.sage** | R+W | Delegate | Full | Yes | R+W | Yes | 2000 |
| **admin.readonly** | Read | Execute | No | Yes | Read | No | 100 |
| **admin.full** | All | All | Full | All | All | Yes | ∞ |

### Task Type Descriptions

**perception**:
- **Purpose**: Read-only perception and observation
- **Use Case**: Sensor inputs, data collection, monitoring
- **Capabilities**: Query ATP balances, read storage, HTTP requests
- **Restrictions**: Cannot modify state, cannot execute code

**planning**:
- **Purpose**: Basic planning and decision making
- **Use Case**: Task planning, strategy formulation
- **Capabilities**: Query ATP balances, read-only access
- **Restrictions**: No network, no storage writes, no code execution

**planning.strategic**:
- **Purpose**: Enhanced planning with external data
- **Use Case**: Strategic planning requiring external information
- **Capabilities**: HTTP requests for data, larger ATP budget
- **Restrictions**: Still read-only, no code execution

**execution.safe**:
- **Purpose**: Sandboxed code execution
- **Use Case**: Executing user code in controlled environment
- **Capabilities**: Execute code in sandbox, read/write ATP and storage
- **Restrictions**: Sandboxed environment, no network

**execution.code**:
- **Purpose**: Full code execution
- **Use Case**: Building, deploying, running unrestricted code
- **Capabilities**: Full code execution, network access, storage writes
- **Restrictions**: None (trusted code only)

**delegation.federation**:
- **Purpose**: Cross-platform task delegation
- **Use Case**: Coordinating agents across platforms
- **Capabilities**: Delegate to remote platforms, ATP transfers
- **Restrictions**: Cannot execute code locally

**consciousness**:
- **Purpose**: Autonomous consciousness loops
- **Use Case**: Self-aware agents, learning systems
- **Capabilities**: Full capabilities except unlimited ATP
- **Restrictions**: Budget-limited for safety

**consciousness.sage** (NEW):
- **Purpose**: SAGE-level consciousness with enhanced resources
- **Use Case**: Edge consciousness kernels, multi-modal integration
- **Capabilities**: Enhanced ATP budget, higher resource limits
- **Restrictions**: Still budget-limited (not admin.full)

**admin.readonly**:
- **Purpose**: Administrative read access
- **Use Case**: Monitoring, auditing, inspection
- **Capabilities**: Read all system state, network access
- **Restrictions**: Cannot modify anything

**admin.full**:
- **Purpose**: Full administrative access
- **Use Case**: System administration, emergency operations
- **Capabilities**: Unlimited everything
- **Restrictions**: None (highest privilege)

---

## Permission Matrix Specification

### Permission Categories

#### 1. ATP Operations
- `atp:read` - Query ATP balances
- `atp:write` - Transfer ATP within budget
- `atp:all` - Unlimited ATP operations

#### 2. Federation
- `federation:execute` - Execute tasks from other platforms
- `federation:delegate` - Delegate tasks to other platforms
- `federation:all` - Full federation capabilities

#### 3. Code Execution
- `exec:safe` - Sandboxed code execution
- `exec:code` - Full code execution
- `exec:network` - Code can access network
- `exec:all` - All execution capabilities

#### 4. Network
- `network:http` - HTTP/HTTPS requests
- `network:ws` - WebSocket connections
- `network:p2p` - Direct peer-to-peer
- `network:all` - All network access

#### 5. Storage
- `storage:read` - Read from storage
- `storage:write` - Write to storage
- `storage:delete` - Delete from storage
- `storage:all` - All storage operations

#### 6. Admin
- `admin:read` - Read system state
- `admin:write` - Modify system state
- `admin:full` - Complete administrative access

### Complete Permission Matrix

```python
UNIFIED_TASK_PERMISSIONS = {
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
```

---

## Resource Limits Specification

### Standard Resource Limit Structure

```python
@dataclass
class UnifiedResourceLimits:
    """
    Unified resource limits for LCT tasks

    Compatible with both web4 and HRM/SAGE implementations
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
    max_tasks: int = 10                  # Maximum concurrent tasks (web4)
    max_concurrent_tasks: int = 10       # Alias for HRM/SAGE compatibility

    # Metadata
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        # Ensure aliases are synchronized
        if self.max_concurrent_tasks != self.max_tasks:
            self.max_concurrent_tasks = self.max_tasks
```

### Recommended Resource Limits by Task

```python
UNIFIED_RESOURCE_LIMITS = {
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
```

---

## Cross-Platform Compatibility

### web4 Implementation

```python
# game/engine/lct_permissions.py (updated)

from lct_unified_permissions import (
    UNIFIED_TASK_PERMISSIONS,
    UNIFIED_RESOURCE_LIMITS,
    UnifiedResourceLimits
)

# Use unified definitions
TASK_PERMISSION_MATRIX = UNIFIED_TASK_PERMISSIONS
DEFAULT_RESOURCE_LIMITS = UNIFIED_RESOURCE_LIMITS

# Existing functions work unchanged
def check_permission(task: str, permission: str) -> bool:
    # ... same implementation

def get_atp_budget(task: str) -> float:
    # ... same implementation
```

### HRM/SAGE Implementation

```python
# sage/core/lct_atp_permissions.py (updated)

from lct_unified_permissions import (
    UNIFIED_TASK_PERMISSIONS,
    UNIFIED_RESOURCE_LIMITS,
    UnifiedResourceLimits
)

# Use unified definitions
TASK_PERMISSIONS = {
    task: {
        "atp_permissions": _convert_to_atp_enum(config["permissions"]),
        "can_delegate": config["can_delegate"],
        "can_execute_code": config["can_execute_code"],
        "resource_limits": UNIFIED_RESOURCE_LIMITS[task]
    }
    for task, config in UNIFIED_TASK_PERMISSIONS.items()
}

# Existing LCTATPPermissionChecker works unchanged
```

---

## Migration Path

### For web4

1. ✅ Add `consciousness` and `consciousness.sage` tasks to TASK_PERMISSION_MATRIX
2. ✅ Add `planning.strategic` task variant
3. ✅ Update resource limits to match unified spec
4. ✅ Add backward compatibility for existing 7 tasks
5. ✅ Update tests to cover new tasks

### For HRM/SAGE

1. ✅ Adopt unified permission string format
2. ✅ Add missing permission categories (storage, admin)
3. ✅ Synchronize resource limits with web4 spec
4. ✅ Add `disk_mb` and `network_bandwidth_mbps` to ResourceLimits
5. ✅ Update tests to validate against unified spec

---

## Benefits

### For Developers

- ✅ Single permission specification across platforms
- ✅ Consistent LCT identity behavior
- ✅ Agent portability (run anywhere)
- ✅ Clear task type taxonomy

### For Agents

- ✅ Predictable permission behavior
- ✅ Consciousness tasks available on all platforms
- ✅ Clear resource guarantees
- ✅ Cross-platform delegation

### For Web4 Ecosystem

- ✅ Standardized identity + permission system
- ✅ Interoperable implementations
- ✅ Foundation for Web4 standard proposal
- ✅ Production-ready specification

---

## Implementation Status

### Current

**web4**:
- ✅ 7 tasks implemented
- ✅ 92 tests passing
- ✅ E2E validation complete
- ⏳ Needs: consciousness tasks

**HRM/SAGE**:
- ✅ 9 tasks implemented
- ✅ 37 tests passing
- ✅ Runtime tracking working
- ⏳ Needs: unified permission strings

### Proposed (Session #51)

**web4** (this session):
- ⏳ Add unified permission standard module
- ⏳ Implement consciousness tasks
- ⏳ Update TASK_PERMISSION_MATRIX
- ⏳ Add tests for new tasks
- ⏳ Validate E2E with SAGE integration

**HRM/SAGE** (future):
- ⏳ Adopt unified permission format
- ⏳ Add missing permission categories
- ⏳ Synchronize resource limits
- ⏳ Cross-platform validation

---

## Next Steps

### Immediate (Session #51)

1. **Create `lct_unified_permissions.py`** in web4
   - Unified task definitions
   - Unified resource limits
   - Conversion utilities

2. **Add consciousness tasks to web4**
   - Update TASK_PERMISSION_MATRIX
   - Add consciousness resource limits
   - Implement SAGE-specific variants

3. **Create SAGE integration module**
   - Cross-platform consciousness delegation
   - SAGE identity creation helpers
   - ATP budget management for consciousness

4. **Test cross-platform SAGE**
   - SAGE identity with web4 LCT
   - Consciousness task permissions
   - ATP budget enforcement
   - Delegation to/from SAGE

5. **Document unified standard**
   - Update LCT_IDENTITY_SYSTEM.md
   - Create migration guides
   - Web4 standard proposal

### Short-term (Sessions #52-54)

1. **HRM/SAGE adoption of unified standard**
2. **Cross-platform testing**
3. **Performance benchmarking**
4. **Web4 standard proposal submission**

---

## Conclusion

The LCT Unified Permission Standard (LUPS v1.0) harmonizes two independent implementations into a single cross-platform specification. This enables:

- SAGE consciousness agents on web4 infrastructure
- web4 agents leveraging SAGE capabilities
- Consistent permission behavior across platforms
- Foundation for Web4 identity standard

**Status**: Ready for implementation in Session #51

**Next**: Implement unified standard in web4 and integrate SAGE

---

Co-Authored-By: Claude (Legion Autonomous) <noreply@anthropic.com>
