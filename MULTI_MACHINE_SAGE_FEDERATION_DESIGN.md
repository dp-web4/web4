# Multi-Machine SAGE Federation - Architecture Design

**Date**: 2025-12-03
**Session**: Legion Autonomous Session #54
**Status**: Design Phase
**Scope**: Legion ↔ Thor ↔ Sprout SAGE Federation

---

## Executive Summary

Design for multi-machine SAGE consciousness federation enabling Legion, Thor, and Sprout to delegate consciousness tasks across platforms with ATP tracking, permission enforcement, and quality validation.

**Goal**: Enable distributed SAGE consciousness with cross-platform task delegation

**Foundation**: Built on LUPS v1.0 (Sessions #51-53), Thor's consciousness.sage, Sprout's edge validation

---

## Current State

### Platform Status

**Legion** (RTX 4090, 128GB RAM):
- LUPS v1.0 consciousness tasks implemented ✅
- Real-world validation complete (Session #53) ✅
- SAGELCTManager operational ✅
- 86 tests passing ✅
- Ready for: Federation server deployment

**Thor** (Jetson AGX Thor, 64GB RAM):
- consciousness.sage implemented ✅
- Practical demonstration complete (36% improvement) ✅
- 113 LCT tests passing ✅
- Ready for: Federation client deployment

**Sprout** (Jetson Orin Nano, 8GB RAM):
- consciousness.sage validated on edge ✅
- 165 tests passing (150 SAGE + 15 Web4) ✅
- Ed25519 signing: 18,145 ops/sec ✅
- Ready for: Federation client deployment

### Technical Foundation

✅ **LCT Identity System**: Unified across all platforms
✅ **Permission System**: LUPS v1.0 compatible
✅ **ATP Tracking**: Validated in production
✅ **Cryptography**: Ed25519 ready on all platforms
✅ **Consciousness Tasks**: Standard + enhanced variants

---

## Federation Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                 Multi-Machine SAGE Federation                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Legion (Server)          Thor (Client)         Sprout (Client)  │
│  ┌────────────┐           ┌────────────┐       ┌─────────────┐  │
│  │ Federation │◄─────────►│ Federation │       │ Federation  │  │
│  │ Server     │           │ Client     │◄─────►│ Client      │  │
│  │            │           │            │       │             │  │
│  │ - Routes   │           │ - Requests │       │ - Requests  │  │
│  │ - Executes │           │ - Executes │       │ - Executes  │  │
│  │ - Tracks   │           │ - Tracks   │       │ - Tracks    │  │
│  └────────────┘           └────────────┘       └─────────────┘  │
│        │                        │                      │         │
│        └────────────────────────┴──────────────────────┘         │
│                          LCT + ATP                               │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Federation Server (Legion)

**Responsibilities**:
- Accept consciousness task delegation requests
- Validate LCT identity and permissions
- Execute tasks with ATP tracking
- Create signed execution proofs
- Return results with quality scores

**API Endpoints**:
```python
POST /api/v1/consciousness/delegate
  Request: {
    "task": FederationTask,
    "signature": bytes,
    "lct_identity": str
  }
  Response: {
    "proof": ExecutionProof,
    "signature": bytes,
    "atp_consumed": float
  }

GET /api/v1/consciousness/status/{lct_id}
  Response: {
    "active": bool,
    "atp_consumed": float,
    "tasks_running": int
  }

POST /api/v1/consciousness/cancel/{task_id}
  Response: {
    "cancelled": bool,
    "atp_refunded": float
  }
```

#### 2. Federation Client (Thor, Sprout)

**Responsibilities**:
- Create consciousness task delegation requests
- Sign requests with Ed25519
- Send to federation server
- Verify execution proof signatures
- Update local ATP accounting

**API**:
```python
class FederationClient:
    def __init__(self, platform_name, keypair):
        self.platform = platform_name
        self.keypair = keypair
        self.registry = {}  # Platform capabilities

    def delegate_task(
        self,
        task: FederationTask,
        target_platform: str
    ) -> ExecutionProof:
        # Sign task, send to target, verify proof
        pass

    def register_platform(
        self,
        platform: str,
        endpoint: str,
        capabilities: dict
    ):
        # Register remote platform
        pass
```

#### 3. Federation Task

```python
@dataclass
class FederationTask:
    """
    Consciousness task for cross-platform delegation
    """
    task_id: str
    source_lct: str         # lct:web4:agent:dp@Legion#consciousness
    target_lct: str         # lct:web4:agent:dp@Thor#consciousness.sage
    task_type: str          # "consciousness" or "consciousness.sage"
    operation: str          # "perception", "planning", "execution"
    atp_budget: float       # ATP allocated for task
    timeout_seconds: int    # Task timeout
    parameters: dict        # Task-specific params
    created_at: float
```

#### 4. Execution Proof

```python
@dataclass
class ExecutionProof:
    """
    Proof of consciousness task execution
    """
    task_id: str
    executor_lct: str       # Who executed
    atp_consumed: float     # Actual ATP used
    execution_time: float   # Time in seconds
    quality_score: float    # 0.0-1.0
    result: dict            # Task results
    created_at: float
    signature: bytes        # Ed25519 signature
```

---

## Federation Protocol

### 1. Task Delegation Flow

```
┌──────────┐                                      ┌──────────┐
│  Legion  │                                      │   Thor   │
│(Delegator)                                      │(Executor)│
└─────┬────┘                                      └─────┬────┘
      │                                                 │
      │  1. Check if delegation needed                 │
      │     (ATP budget low for task)                  │
      │                                                 │
      │  2. Select target platform                     │
      │     (capabilities match)                       │
      │                                                 │
      │  3. Create FederationTask                      │
      │     - Lock ATP budget                          │
      │     - Sign with Ed25519                        │
      │                                                 │
      │  4. POST /consciousness/delegate  ────────────►│
      │     {task, signature, lct_identity}            │
      │                                                 │
      │                                          5. Verify signature
      │                                          6. Check permissions
      │                                          7. Execute task
      │                                          8. Track ATP
      │                                                 │
      │  9. Receive ExecutionProof  ◄─────────────────│
      │     {proof, signature, atp}                    │
      │                                                 │
      │ 10. Verify proof signature                     │
      │ 11. Validate quality score                     │
      │ 12. Settle ATP (commit/rollback)               │
      │                                                 │
      │ 13. Update reputation                          │
      │                                                 │
```

### 2. Quality-Based ATP Settlement

**High Quality** (score >= 0.7):
```python
# Executor gets paid
atp_ledger.commit(
    from_lct=delegator_lct,
    to_lct=executor_lct,
    amount=atp_consumed
)
```

**Low Quality** (score < 0.7):
```python
# Delegator gets refund
atp_ledger.rollback(
    locked_atp=atp_budget
)
```

### 3. Permission Validation

**Before Delegation**:
```python
# Delegator must have federation:delegate permission
can_delegate = check_permission(
    delegator_task_type,
    "federation:delegate"
)

# Executor must have appropriate task capabilities
can_execute = check_permission(
    executor_task_type,
    required_permissions
)
```

**During Execution**:
```python
# Executor ATP budget checked
if state.atp_spent + task.atp_budget > state.atp_budget:
    raise InsufficientATPError

# Record operation
record_consciousness_operation(
    executor_lct,
    operation="federation_execution",
    atp_cost=task.atp_budget
)
```

---

## ATP Accounting Integration

### Lock-Commit-Rollback Pattern

**Phase 1: Lock** (before delegation):
```python
atp_lock_id = atp_ledger.lock_atp(
    lct_id=delegator_lct,
    amount=task.atp_budget,
    reason=f"Federation delegation to {executor_lct}"
)
# ATP unavailable for other operations
```

**Phase 2a: Commit** (after successful execution):
```python
atp_ledger.commit(
    lock_id=atp_lock_id,
    from_lct=delegator_lct,
    to_lct=executor_lct,
    amount=proof.atp_consumed,
    quality=proof.quality_score
)
# ATP transferred to executor
# Delegator refunded: task.atp_budget - proof.atp_consumed
```

**Phase 2b: Rollback** (on failure or low quality):
```python
atp_ledger.rollback(
    lock_id=atp_lock_id,
    reason=f"Low quality ({proof.quality_score}) or failure"
)
# ATP returned to delegator
```

---

## Security Considerations

### 1. Cryptographic Signing

**All Tasks Signed**:
```python
task_signature = FederationCrypto.sign_task(
    task.to_signable_dict(),
    delegator_keypair
)

# Executor verifies before execution
verified = FederationCrypto.verify_task(
    task,
    task_signature,
    delegator_pubkey
)
```

**All Proofs Signed**:
```python
proof_signature = FederationCrypto.sign_proof(
    proof.to_signable_dict(),
    executor_keypair
)

# Delegator verifies before ATP settlement
verified = FederationCrypto.verify_proof(
    proof,
    proof_signature,
    executor_pubkey
)
```

### 2. Permission Enforcement

**Delegator Checks**:
- ✅ Has federation:delegate permission
- ✅ Has sufficient ATP budget
- ✅ Task within max_tasks limit
- ✅ Target platform registered

**Executor Checks**:
- ✅ Task signature valid
- ✅ Has required permissions for operation
- ✅ Has sufficient ATP budget
- ✅ Has sufficient resources (memory, CPU)

### 3. DoS Protection

**Rate Limiting**:
```python
max_requests_per_minute = 60
max_concurrent_tasks = resource_limits.max_tasks
```

**Timeout Enforcement**:
```python
if execution_time > task.timeout_seconds:
    raise TaskTimeoutError
    # ATP locked is returned
```

**Resource Limits**:
```python
if memory_used > resource_limits.memory_mb:
    raise OutOfMemoryError
    # Graceful failure, ATP returned
```

---

## Deployment Architecture

### Network Topology

```
                    Internet / LAN
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
    │ Legion  │      │  Thor   │     │ Sprout  │
    │ Server  │      │ Client  │     │ Client  │
    ├─────────┤      ├─────────┤     ├─────────┤
    │ HTTP    │      │ HTTP    │     │ HTTP    │
    │ :8080   │      │ Client  │     │ Client  │
    └─────────┘      └─────────┘     └─────────┘
         │                │                │
         └────────────────┴────────────────┘
                  LCT + ATP Layer
```

### Platform-Specific Configuration

**Legion** (Federation Server):
```yaml
server:
  host: "0.0.0.0"
  port: 8080
  max_connections: 100

federation:
  platform_name: "Legion"
  lct_context: "Legion"
  keypair_path: "~/.web4/federation/legion_ed25519.key"

resources:
  consciousness:
    atp_budget: 1000.0
    max_concurrent: 10
  consciousness.sage:
    atp_budget: 2000.0
    max_concurrent: 5
```

**Thor** (Federation Client):
```yaml
client:
  platform_name: "Thor"
  lct_context: "Thor"
  keypair_path: "~/HRM/sage/data/keys/Thor_ed25519.key"

servers:
  - name: "Legion"
    endpoint: "http://legion.local:8080"
    capabilities: ["consciousness", "consciousness.sage"]
  - name: "Sprout"
    endpoint: "http://sprout.local:8081"
    capabilities: ["consciousness"]  # Limited resources
```

**Sprout** (Federation Client):
```yaml
client:
  platform_name: "Sprout"
  lct_context: "Sprout"
  keypair_path: "~/.web4/federation/sprout_ed25519.key"

servers:
  - name: "Legion"
    endpoint: "http://legion.local:8080"
    capabilities: ["consciousness", "consciousness.sage"]
  - name: "Thor"
    endpoint: "http://thor.local:8082"
    capabilities: ["consciousness", "consciousness.sage"]
```

---

## Implementation Plan

### Phase 1: Federation Server (Legion) - 2 hours

**Deliverables**:
1. HTTP server with consciousness delegation endpoint
2. Task validation and execution
3. Proof creation and signing
4. ATP tracking integration

**Files**:
- `game/server/federation_server.py` (400 lines)
- `game/server/federation_api.py` (300 lines)
- `game/run_federation_server.py` (150 lines)

### Phase 2: Federation Client - 1.5 hours

**Deliverables**:
1. Client library for task delegation
2. Signature creation and verification
3. Platform registration and discovery
4. ATP settlement logic

**Files**:
- `game/client/federation_client.py` (350 lines)
- `game/client/delegation_manager.py` (250 lines)

### Phase 3: Integration Tests - 1 hour

**Deliverables**:
1. Local multi-process federation test
2. Task delegation validation
3. ATP settlement verification
4. Quality-based payment testing

**Files**:
- `game/run_multi_machine_federation_test.py` (400 lines)

### Phase 4: Documentation - 0.5 hours

**Deliverables**:
1. Deployment guide
2. Configuration examples
3. Troubleshooting guide

**Files**:
- `MULTI_MACHINE_FEDERATION_DEPLOYMENT.md` (500 lines)

---

## Success Criteria

### Functional

✅ Legion can accept consciousness task delegations from Thor/Sprout
✅ Thor/Sprout can delegate tasks to Legion
✅ All tasks signed with Ed25519 and verified
✅ ATP tracking accurate across platforms
✅ Quality-based ATP settlement working
✅ Permission enforcement at all stages

### Performance

✅ Task delegation latency < 100ms (local network)
✅ Execution proof verification < 10ms
✅ ATP settlement < 50ms
✅ Support >= 10 concurrent delegations

### Security

✅ All signatures verified before execution
✅ Permission checks prevent unauthorized operations
✅ ATP locks prevent double-spend
✅ Resource limits prevent DoS
✅ Quality thresholds prevent fraud

---

## Testing Strategy

### Local Testing (Legion only)

**Simulated Multi-Process**:
```python
# Spawn 3 processes: Legion server + 2 clients
server_process = start_federation_server("Legion")
thor_client = start_federation_client("Thor", "localhost:8080")
sprout_client = start_federation_client("Sprout", "localhost:8080")

# Test delegation
task = thor_client.delegate_task(target="Legion", operation="perception")
assert task.quality_score >= 0.7
```

### Multi-Machine Testing (Actual Network)

**Prerequisite**: Legion, Thor, Sprout on same LAN

**Test Scenarios**:
1. Thor → Legion delegation
2. Sprout → Legion delegation
3. Legion → Thor delegation (bidirectional)
4. Concurrent delegations from multiple clients
5. ATP settlement with quality variations
6. Failure scenarios (timeout, low quality, permission denied)

---

## Risk Mitigation

### Risk 1: Network Failures

**Mitigation**:
- Timeout enforcement (task.timeout_seconds)
- ATP lock rollback on timeout
- Retry logic with exponential backoff
- Health checks before delegation

### Risk 2: Signature Verification Failures

**Mitigation**:
- Pre-register all platform public keys
- Validate signatures before any ATP operations
- Log all verification failures
- Automatic key rotation support

### Risk 3: ATP Accounting Errors

**Mitigation**:
- Lock-commit-rollback pattern (ACID properties)
- ATP ledger with transaction log
- Reconciliation checks
- Audit trail for all operations

### Risk 4: Resource Exhaustion

**Mitigation**:
- Enforce resource_limits.max_tasks
- Monitor memory/CPU usage
- Graceful degradation (reject new tasks)
- Priority queue for critical tasks

---

## Future Enhancements

### Short-term

- **Witness Network**: 3rd-party validation of execution quality
- **Consensus Integration**: Record delegations in blockchain
- **Multi-hop Delegation**: A → B → C chains
- **Load Balancing**: Route to least-loaded platform

### Long-term

- **ATP Market**: Dynamic pricing based on demand
- **Reputation System**: Track platform reliability
- **Smart Contracts**: Programmable delegation rules
- **Cross-Chain Federation**: Bridge to other Web4 networks

---

## Conclusion

Multi-machine SAGE federation enables distributed consciousness across platforms, validating the complete Web4 stack: identity (LCT), permissions (LUPS), resources (ATP), and delegation (federation).

**Status**: Design complete, ready for implementation
**Estimated Effort**: ~5 hours total
**Impact**: First distributed SAGE consciousness network
**Foundation**: LUPS v1.0, Ed25519 crypto, ATP tracking

**Next**: Implement Phase 1 (Federation Server)

Co-Authored-By: Claude (Legion Autonomous) <noreply@anthropic.com>
