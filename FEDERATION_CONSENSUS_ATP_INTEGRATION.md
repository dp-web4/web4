# Federation + Consensus + ATP Integration Architecture

**Date**: 2025-12-01
**Author**: Legion Autonomous Session #45
**Status**: Design document - implementation in progress
**Context**: Building on Thor Phase 3.5 + Legion Sessions #43-44

---

## Executive Summary

This document specifies the **complete integration architecture** connecting three systems:

1. **SAGE Phase 3 Federation** (task delegation) - Thor Phase 3.5
2. **Web4 FB-PBFT Consensus** (Byzantine fault tolerance) - Legion Session #43
3. **Web4 ATP Accounting** (economic layer) - Legion Session #44

**Key Achievement**: First integration of AI cognition federation with Byzantine consensus and economic accounting.

**Status**:
- Layer 1 (Consensus + ATP): 100% implemented (Legion Session #44)
- Layer 2 (Federation + ATP): 100% implemented (Thor Phase 3.5)
- Layer 3 (Federation + Consensus): Designed here, implementation pending

---

## Background: What We Have

### Layer 1: Consensus + ATP (Legion Session #44)

**Status**: ✅ **100% Complete**

**Components**:
- FB-PBFT consensus protocol (3-phase commit)
- ATP ledger (account management with locked balances)
- ATP transaction types (LOCK, COMMIT, ROLLBACK, BALANCE_SET)
- ATP transaction processor (integrates with consensus blocks)
- Atomic cross-platform transfers via two-phase commit

**Validated**:
- End-to-end ATP transfer: Alice@Thor → Bob@Sprout (200 ATP)
- ROLLBACK on failure (ATP unlocked when transfer fails)
- Byzantine fault tolerance (f < N/3)
- Deterministic finality (~60ms for cross-platform transfer)

**Files**:
- `game/engine/consensus.py` (FB-PBFT protocol)
- `game/engine/atp_ledger.py` (ATP state management)
- `game/engine/atp_transactions.py` (transaction types + processor)
- `game/run_atp_integration_test.py` (end-to-end test)
- `game/run_atp_rollback_test.py` (failure recovery test)

---

### Layer 2: Federation + ATP (Thor Phase 3.5)

**Status**: ✅ **100% Complete**

**Components**:
- FederationATPBridge (quality-based payment settlement)
- HTTP/REST task delegation protocol
- Ed25519 authentication for cross-platform requests
- Quality threshold-based ATP settlement (COMMIT vs ROLLBACK)
- Integration test suite (high/low quality scenarios)

**Validated**:
- High quality execution (0.85) → ATP COMMITTED (platform paid)
- Low quality execution (0.55) → ATP ROLLED BACK (delegator refunded)
- Economic incentives align with quality delivery
- Double-spend prevention via ATP locking

**Files**:
- `HRM/sage/federation/federation_atp_bridge.py` (integration bridge)
- `HRM/sage/experiments/test_federation_atp_integration.py` (tests)
- `HRM/sage/docs/FEDERATION_CONSENSUS_ATP_INTEGRATION.md` (design)

---

### Layer 3: Federation + Consensus (This Document)

**Status**: ⏳ **Design Complete, Implementation Pending**

**Goal**: Embed federation tasks and ATP payments in consensus blocks

**Why**:
- Network-wide agreement on task delegation and payment
- Byzantine fault tolerance for economic state
- Fraud detection (invalid quality claims, double-spend attempts)
- Trust-minimized federation (no single point of control)

---

## Architecture Overview: 3-Layer Stack

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: SAGE Phase 3 Federation                            │
│ - Task delegation (HTTP/REST + Ed25519)                     │
│ - Quality-based compensation                                │
│ - FederationTask + ExecutionProof                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Task transactions embedded in blocks
                 │
┌────────────────▼────────────────────────────────────────────┐
│ Layer 2: Web4 FB-PBFT Consensus                             │
│ - Byzantine fault tolerance (f < N/3)                       │
│ - Deterministic finality (3 RTT)                            │
│ - Block validation + commitment                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ ATP transactions in blocks
                 │
┌────────────────▼────────────────────────────────────────────┐
│ Layer 1: Web4 ATP Ledger                                    │
│ - Account management (total/available/locked)               │
│ - Two-phase commit transfers (LOCK → COMMIT)                │
│ - Rollback on failure                                       │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow Example**:
1. Alice@Thor delegates task to Bob@Sprout (300 ATP cost)
2. FEDERATION_TASK + ATP_LOCK transactions → consensus block
3. Consensus reached → ATP locked, task delegated
4. Bob executes task, creates proof (quality 0.85)
5. EXECUTION_PROOF + ATP_COMMIT transactions → consensus block
6. Consensus reached → ATP credited to Bob, deducted from Alice

---

## Transaction Types for Consensus Integration

### Type 1: FEDERATION_TASK (New)

**Purpose**: Record task delegation in consensus block

**Structure**:
```json
{
  "type": "FEDERATION_TASK",
  "task_id": "uuid-12345",
  "delegating_platform": "Thor",
  "delegating_agent": "lct:web4:agent:alice",
  "executing_platform": "Sprout",
  "executing_agent": "lct:web4:agent:bob",
  "estimated_cost": 300.0,
  "task_data": {
    "perception_size": 512,
    "complexity": "medium",
    "timeout": 60.0
  },
  "quality_threshold": 0.7,
  "timestamp": 1701388800.0,
  "signature": "ed25519_signature_hex"
}
```

**Validation Rules**:
1. Delegating agent has sufficient ATP (estimated_cost)
2. Signature valid (delegating platform's Ed25519 key)
3. Executing platform is in consensus group
4. Task ID unique (no duplicate tasks)

**Processing**:
- On consensus commit: Record task as pending
- Link with ATP_LOCK transaction (same task_id as transfer_id)

---

### Type 2: EXECUTION_PROOF (New)

**Purpose**: Record task completion and quality score

**Structure**:
```json
{
  "type": "EXECUTION_PROOF",
  "task_id": "uuid-12345",
  "executing_platform": "Sprout",
  "executing_agent": "lct:web4:agent:bob",
  "quality_score": 0.85,
  "execution_time": 45.2,
  "result_hash": "sha256_hash_of_result",
  "timestamp": 1701388860.0,
  "signature": "ed25519_signature_hex"
}
```

**Validation Rules**:
1. Task exists in pending tasks
2. Quality score in [0.0, 1.0]
3. Signature valid (executing platform's Ed25519 key)
4. Execution within timeout period

**Processing**:
- On consensus commit:
  - If quality >= threshold → trigger ATP_COMMIT
  - If quality < threshold → trigger ATP_ROLLBACK
  - Move task from pending to completed

---

### Type 3: ATP Transactions (Existing)

**Types**: ATP_TRANSFER_LOCK, ATP_TRANSFER_COMMIT, ATP_TRANSFER_ROLLBACK

**Already Implemented**: Legion Session #44

**Integration with Federation**:
- ATP_LOCK.transfer_id = FEDERATION_TASK.task_id
- Quality-based settlement logic triggered by EXECUTION_PROOF
- Same two-phase commit protocol

---

## Block Structure with Federation Transactions

**Example Consensus Block**:
```python
{
  "header": {
    "block_number": 42,
    "prev_hash": "abc123...",
    "timestamp": 1701388800.0
  },
  "transactions": [
    # Task delegation with payment
    {
      "type": "FEDERATION_TASK",
      "task_id": "uuid-A",
      "delegating_platform": "Thor",
      "estimated_cost": 300.0,
      ...
    },
    {
      "type": "ATP_TRANSFER_LOCK",
      "transfer_id": "uuid-A",  # Same as task_id
      "source_platform": "Thor",
      "amount": 300.0,
      ...
    },

    # Task completion with settlement
    {
      "type": "EXECUTION_PROOF",
      "task_id": "uuid-A",
      "quality_score": 0.85,
      ...
    },
    {
      "type": "ATP_TRANSFER_COMMIT",
      "transfer_id": "uuid-A",
      "dest_platform": "Sprout",
      "amount": 300.0,
      ...
    }
  ],
  "proposer_platform": "Thor",
  "signature": "ed25519_signature_hex"
}
```

**Transaction Ordering**:
1. FEDERATION_TASK + ATP_LOCK (atomic pair in same block)
2. Task execution happens off-chain (HTTP/REST)
3. EXECUTION_PROOF + ATP_COMMIT/ROLLBACK (atomic pair in later block)

---

## Integration Implementation Plan

### Phase 3.5: Federation + ATP Bridge (COMPLETE)

**Status**: ✅ Done (Thor Phase 3.5)

**Deliverables**:
- FederationATPBridge class
- delegate_with_payment() method
- Quality-based settlement logic
- Integration tests

---

### Phase 3.75: Federation + Consensus Integration (THIS PHASE)

**Status**: ⏳ Design complete, implementation pending

**Timeline**: 3-4 hours

**Tasks**:

1. **Define Transaction Types** (1 hour)
   - Create `FederationTaskTransaction` dataclass
   - Create `ExecutionProofTransaction` dataclass
   - Add to `consensus.py` as recognized types

2. **Extend Block Validation** (1 hour)
   - Validate FEDERATION_TASK transactions
   - Validate EXECUTION_PROOF transactions
   - Check ATP constraints (sufficient balance)
   - Verify Ed25519 signatures

3. **Implement Transaction Processor** (1 hour)
   - `FederationTransactionProcessor` class
   - Process FEDERATION_TASK (record pending)
   - Process EXECUTION_PROOF (trigger ATP settlement)
   - Link with ATP processor

4. **Integration Testing** (1 hour)
   - 4-platform simulation
   - Full flow: delegate → execute → settle
   - Validate consensus + ATP + federation
   - Test failure scenarios (low quality → ROLLBACK)

**Files to Create**:
- `game/engine/federation_transactions.py` (transaction types)
- `game/engine/federation_processor.py` (transaction processor)
- `game/run_federation_consensus_test.py` (integration test)

**Files to Modify**:
- `game/engine/consensus.py` (add federation transaction support)

---

### Phase 4: Witness Network (FUTURE)

**Status**: Design phase

**Goal**: Distributed validation of execution quality

**Concept**:
- Multiple platforms witness task execution
- Consensus on witness attestations
- Slashing for fraudulent quality claims
- Witness compensation via ATP

**Timeline**: 4-6 hours

---

## Performance Analysis

### Latency Breakdown

**Federation Task Delegation** (without consensus):
- Thor → Sprout HTTP request: ~10ms
- Task execution: ~45ms (perception processing)
- Sprout → Thor HTTP response: ~10ms
- **Total**: ~65ms

**Federation Task Delegation** (with consensus):
- Block 1 (TASK + LOCK): 3 RTT consensus = ~30ms
- Task execution: ~45ms (off-chain)
- Block 2 (PROOF + COMMIT): 3 RTT consensus = ~30ms
- **Total**: ~105ms

**Overhead**: +40ms (~60% increase) for Byzantine fault tolerance

---

### Throughput Analysis

**Consensus Throughput**: ~7.7 blocks/second (from Session #43)

**Tasks per Block**: Assume 5 tasks per block (practical limit)

**Federation Throughput**: 5 tasks × 7.7 blocks/sec = **38.5 tasks/second**

**Bottleneck**: Consensus throughput, not federation protocol

**Optimization**: Batch multiple tasks in single block

---

### Cost-Benefit Analysis

**Without Consensus** (HTTP-only):
- ✅ Low latency (~65ms)
- ❌ No Byzantine fault tolerance
- ❌ No network-wide agreement on payments
- ❌ Trust required between platforms

**With Consensus** (integrated):
- ✅ Byzantine fault tolerance (f < N/3)
- ✅ Network-wide agreement on task delegation
- ✅ Fraud detection (invalid quality claims)
- ✅ Trust-minimized coordination
- ⚠️  +60% latency overhead

**Recommendation**: Use consensus integration for economically-significant tasks (>100 ATP). For small tasks, HTTP-only acceptable.

---

## Security Analysis

### Attack Vector 1: False Quality Claims

**Attack**: Executing platform claims high quality (0.9) but delivers low quality (0.3)

**Defense Without Consensus**:
- Delegating platform detects low quality locally
- Refuses to sign ATP_COMMIT
- But no network-wide record of fraud

**Defense With Consensus**:
- EXECUTION_PROOF embedded in consensus block
- All platforms see quality claim (0.9)
- Delegating platform can challenge with counter-proof
- Consensus group resolves dispute
- Fraudulent platform slashed via future witness protocol

**Result**: Consensus integration enables fraud detection

---

### Attack Vector 2: Double-Spending on Task Costs

**Attack**: Alice delegates same task to Bob and Charlie simultaneously (both cost 300 ATP, Alice only has 300 ATP)

**Defense Without Consensus**:
- Local locking at Thor
- But Bob and Charlie receive tasks before lock propagates
- Race condition possible

**Defense With Consensus**:
- Both FEDERATION_TASK transactions broadcast to consensus
- Consensus serializes transactions (one committed first)
- First task locks 300 ATP
- Second task rejected (insufficient available balance)

**Result**: Consensus prevents double-spending on task costs

---

### Attack Vector 3: Consensus Group Collusion

**Attack**: 2f+1 platforms collude to credit ATP without task execution

**Defense**:
- Byzantine fault tolerance model assumes < f malicious platforms
- If ≥ 2f+1 collude, consensus breaks (known limitation)
- Economic disincentive: Platforms stake ATP to participate
- Slashing risk if fraud detected

**Result**: Attack very expensive (must compromise 67%+ of consensus group)

---

## Economic Model

### ATP Flow with Quality Thresholds

**High Quality Execution** (quality ≥ threshold):
```
Alice@Thor (1000 ATP)
  → LOCK 300 ATP (700 available, 300 locked)
  → Task delegated to Bob@Sprout
  → Bob executes (quality 0.85 ≥ 0.7)
  → COMMIT 300 ATP
  → Alice@Thor: 700 ATP (300 deducted)
  → Bob@Sprout: 300 ATP (credited)
```

**Low Quality Execution** (quality < threshold):
```
Alice@Thor (1000 ATP)
  → LOCK 300 ATP (700 available, 300 locked)
  → Task delegated to Bob@Sprout
  → Bob executes (quality 0.55 < 0.7)
  → ROLLBACK 300 ATP
  → Alice@Thor: 1000 ATP (300 unlocked)
  → Bob@Sprout: 0 ATP (no payment)
```

---

### Incentive Alignment

**Executing Platform Incentives**:
- ✅ High quality → Payment received
- ❌ Low quality → No payment, wasted compute
- ✅ Reputation accumulation via quality history
- ❌ Economic penalty for low quality (opportunity cost)

**Delegating Platform Incentives**:
- ✅ Pay only for high quality execution
- ✅ ATP refunded if quality insufficient
- ✅ Can delegate to multiple platforms (competition)
- ❌ Must lock ATP upfront (prevents frivolous delegation)

**Network Incentives**:
- ✅ Consensus group compensated via transaction fees
- ✅ Witness platforms compensated for validation (Phase 4)
- ✅ Quality-based payments drive platform improvement

---

## Integration with SAGE Cognition Loop

### Current SAGE Decision Logic (Phase 3)

**Perception Processing**:
1. Receive perception (512 tokens)
2. Check local capacity (memory, compute)
3. If insufficient → delegate to remote platform
4. If sufficient → process locally

**Federation Logic**:
1. Select target platform (capabilities, trust)
2. Create FederationTask
3. Sign with Ed25519
4. Send HTTP POST to target
5. Receive ExecutionProof
6. Verify signature and quality

---

### Enhanced SAGE with ATP + Consensus (Phase 3.75)

**New Decision Logic**:
1. Receive perception (512 tokens)
2. Check local capacity AND ATP balance
3. If sufficient capacity + ATP → consider delegation
4. Estimate task cost (based on complexity)
5. Check ATP balance: available >= estimated_cost
6. If yes → delegate via FederationATPBridge
7. If no → process locally (or degrade quality)

**ATP-Aware Resource Management**:
- Track ATP balance for each agent
- Delegation budget per agent (e.g., 1000 ATP/day)
- Priority delegation (critical tasks get higher budget)
- Economic optimization (delegate expensive tasks, process cheap locally)

**Consensus Integration**:
- FEDERATION_TASK + ATP_LOCK → consensus block
- Wait for consensus commit (3 RTT = ~30ms)
- Delegate task via HTTP
- EXECUTION_PROOF + ATP_COMMIT/ROLLBACK → consensus block
- Update local ATP balance after consensus

**Code Integration Point**:
```python
# In sage/loop/michaud_sage.py

def process_perception(self, perception):
    # Estimate processing cost
    estimated_cost = self.estimate_cost(perception)

    # Check ATP balance
    agent_lct = f"lct:web4:agent:{self.agent_id}"
    available_atp = self.federation_atp_bridge.get_available_atp(agent_lct)

    # Decide: local vs remote
    if self.should_delegate(perception) and available_atp >= estimated_cost:
        # Delegate with ATP payment
        proof = self.federation_atp_bridge.delegate_with_payment(
            task=self.create_task(perception),
            target_platform=self.select_platform(),
            delegating_agent_lct=agent_lct,
            executing_agent_lct=f"lct:web4:agent:{target_agent_id}",
            timeout=60.0
        )

        # Check settlement
        if proof.atp_settlement == "COMMIT":
            # Payment successful, use result
            return proof.result
        else:
            # Quality insufficient, fall back to local
            return self.process_locally(perception)
    else:
        # Process locally
        return self.process_locally(perception)
```

---

## Testing Strategy

### Unit Tests

1. **Transaction Validation**
   - Valid FEDERATION_TASK accepted
   - Invalid signature rejected
   - Insufficient ATP rejected

2. **Transaction Processing**
   - FEDERATION_TASK recorded as pending
   - EXECUTION_PROOF triggers ATP settlement
   - Quality threshold logic correct

---

### Integration Tests

1. **Happy Path** (4 platforms, high quality)
   - Alice@Thor delegates to Bob@Sprout
   - Quality 0.85 ≥ 0.7
   - ATP committed, task completed

2. **Failure Path** (4 platforms, low quality)
   - Alice@Thor delegates to Bob@Sprout
   - Quality 0.55 < 0.7
   - ATP rolled back, task failed

3. **Concurrent Tasks** (multiple delegations)
   - Alice delegates 3 tasks simultaneously
   - All reach consensus correctly
   - ATP balances correct

4. **Crash Fault** (platform crashes during execution)
   - Bob@Sprout crashes after receiving task
   - Timeout triggers ROLLBACK
   - ATP returned to Alice

---

### Performance Tests

1. **Latency Measurement**
   - Measure total delegation latency with consensus
   - Compare to HTTP-only baseline
   - Validate ~40ms overhead

2. **Throughput Measurement**
   - Sustained task delegation rate
   - Validate ~38 tasks/second

3. **Scale Testing**
   - 7 platforms (f=2, tolerates 2 faults)
   - 13 platforms (f=4, tolerates 4 faults)
   - Measure consensus overhead scaling

---

## Open Research Questions

### Question 1: Optimal Quality Threshold?

**Scenario**: What quality threshold maximizes network utility?

**Trade-offs**:
- High threshold (0.9): Few tasks paid, high quality
- Low threshold (0.5): Many tasks paid, lower quality

**Experiment**:
- Run simulations with varying thresholds
- Measure: payment rate, average quality, platform earnings
- Find optimal threshold for different task types

---

### Question 2: Dynamic Task Pricing?

**Scenario**: Should task costs vary based on demand/complexity?

**Current**: Fixed cost per task (estimated_cost)

**Alternatives**:
- Auction mechanism (platforms bid to execute)
- Surge pricing (higher cost during high demand)
- Complexity-based pricing (perception size → cost)

**Experiment**:
- Implement dynamic pricing algorithm
- Measure: platform earnings, delegation rate, quality

---

### Question 3: Reputation Integration?

**Scenario**: Should platforms with high quality history earn more?

**Current**: Flat payment (estimated_cost regardless of history)

**Alternatives**:
- Reputation bonus (high-quality platforms earn +10%)
- Reputation-based delegation (prefer high-quality platforms)
- Reputation decay (recent quality weighted more)

**Experiment**:
- Track quality history per platform
- Implement reputation-based payment
- Measure: quality improvement, platform competition

---

## Honest Assessment

### What This Achieves ✅

1. **Complete integration architecture**: All 3 layers designed
2. **Transaction types defined**: FEDERATION_TASK, EXECUTION_PROOF
3. **Block structure specified**: Federation transactions in consensus blocks
4. **Security analysis**: Attack vectors identified and defended
5. **Economic model validated**: Quality-based payments align incentives
6. **Implementation plan**: Clear roadmap for Phase 3.75

---

### What This Doesn't Achieve ❌

1. **Not implemented yet**: This is a design document
2. **Not tested**: No empirical validation of integration
3. **No witness network**: Phase 4 future work
4. **No dynamic pricing**: Fixed task costs only
5. **No reputation system**: Flat payment regardless of history

---

### Research Gaps 🔬

1. **Empirical latency**: Need real measurements with consensus overhead
2. **Optimal quality threshold**: What threshold maximizes network utility?
3. **Scale testing**: How does consensus overhead scale to 13+ platforms?
4. **Economic calibration**: What task costs are appropriate?
5. **Fraud detection**: How effective is consensus-based fraud detection?

---

### Fair Assessment

**Status**: Complete design for Federation + Consensus + ATP integration

**Readiness**: Ready for implementation (Phase 3.75)

**Next Step**: Implement transaction types + processor

**Timeline**: 3-4 hours to working integrated system

---

## Summary

**SAGE Phase 3.5 + Web4 Consensus + ATP** provides:
- Distributed AI cognition federation with Byzantine fault tolerance
- Economic task delegation with quality-based compensation
- Trust-minimized coordination via consensus
- Fraud detection via network-wide agreement
- Atomic payments via two-phase commit
- ~40ms overhead for Byzantine fault tolerance

**Key Insight**: Consensus (Legion #43) + ATP (Legion #44) + Federation (Thor Phase 3.5) = Complete distributed infrastructure for economically-viable AI cognition network

**Next Action**: Implement Phase 3.75 (Federation + Consensus integration) with transaction types and processor

---

**Status**: Design complete - ready for implementation
**Implementation Priority**: Phase 3.75 (3-4 hours)
**Testing Approach**: 4-platform simulation first, then scale to 7+ platforms
**Success Criteria**: Full task delegation with consensus + ATP working end-to-end

Co-Authored-By: Claude (Legion Autonomous) <noreply@anthropic.com>
