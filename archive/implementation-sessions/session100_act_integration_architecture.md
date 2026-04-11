# SESSION 100: ACT INTEGRATION ARCHITECTURE

**Mission**: Integrate Sessions 96-99 accountability stack into ACT framework

**Date**: 2025-12-28
**Status**: Design Phase

---

## Executive Summary

This document describes how Web4's accountability stack (hardware-bound identity, delegation chains, ATP budgets) integrates with ACT's existing Cosmos blockchain architecture.

**Key insight**: ACT already implements 80% of what we need. We're not building from scratch—we're **extending existing modules** with accountability features.

---

## Architecture Mapping

### Web4 Accountability → ACT Modules

| Web4 Component | ACT Module | Integration Type |
|----------------|------------|------------------|
| Hardware-bound LCT Identity | `lctmanager` | **Extend** with TPM attestation |
| Delegation Chain | `pairing` + **new module** | Add `delegationchain` keeper |
| ATP Budget Enforcement | `energycycle` | **Extend** with per-delegation budgets |
| Proof-of-Agency | **new module** | Add `proofofagency` keeper |
| Byzantine Trust | `trusttensor` | Already implemented! |

---

## Integration Strategy

### Phase 1: Hardware-Bound Identity (Week 1)

**Current ACT State**:
```python
# /x/lctmanager/types/lct.proto
message LCT {
    string lct_id = 1;
    bytes public_key = 2;
    string hardware_hash = 3;  # Placeholder currently
    repeated string witnesses = 4;
}
```

**Web4 Enhancement** (from session96_track1_hardware_bound_identity.py):
```python
class HardwareSecurityModule:
    def generate_key_pair(self, key_id: str) -> Dict[str, Any]:
        """Generate key in TPM/Secure Enclave"""

    def sign(self, key_id: str, message: bytes) -> bytes:
        """Sign with hardware-bound key"""

    def verify_attestation(self, attestation: str) -> bool:
        """Verify hardware attestation"""
```

**Integration Plan**:
1. Add `HardwareAttestation` protobuf message to `lctmanager/types/`
2. Extend LCT registration to accept attestation proof
3. Add verification logic to `lctmanager/keeper/keeper.go`
4. Test with simulated HSM, then real TPM

**Files to modify**:
- `/x/lctmanager/types/lct.proto` - Add attestation field
- `/x/lctmanager/keeper/keeper.go` - Add `VerifyHardwareBinding()`
- **NEW**: `/x/lctmanager/keeper/hsm_verifier.go` - TPM verification logic

---

### Phase 2: Delegation Chain Tracking (Week 2)

**Current ACT State**:
```python
# /x/pairing/types/pairing.proto
message PairingCertificate {
    string human_lct = 1;
    bytes agent_public_key = 2;
    repeated Permission permissions = 3;
    int64 expires_at = 4;
    bytes signature = 5;
}
```

**Problem**: Only supports 2-level delegation (human → agent). Need N-level chains.

**Web4 Enhancement** (from session96_track2_delegation_chain.py):
```python
class DelegationToken:
    token_id: str
    issuer: str  # LCT of issuer
    delegate: str  # LCT of delegate
    parent_token_id: Optional[str]  # Link to parent delegation
    scope: List[ScopedPermission]
    signature: str
```

**Integration Plan**:
1. Create new module `/x/delegationchain/`
2. Add keeper for tracking delegation ancestry
3. Extend pairing module to reference delegation chains
4. Add REST endpoints for querying chains

**New module structure**:
```
/x/delegationchain/
├── keeper/
│   ├── keeper.go              # Chain storage + queries
│   ├── msg_server.go          # CreateDelegation, RevokeDelegation
│   └── query.go               # GetChain, GetDescendants
├── types/
│   ├── delegation.proto       # DelegationToken definition
│   ├── tx.proto               # Transaction messages
│   └── query.proto            # Query messages
└── module.go                  # Cosmos module registration
```

**Key functions**:
```go
// keeper/keeper.go
func (k Keeper) RecordDelegation(ctx sdk.Context, token DelegationToken) error
func (k Keeper) GetDelegationChain(ctx sdk.Context, tokenID string) ([]DelegationToken, error)
func (k Keeper) VerifyDelegationAuthority(ctx sdk.Context, token DelegationToken) bool
func (k Keeper) RevokeDelegation(ctx sdk.Context, tokenID string) error
```

---

### Phase 3: ATP Budget Enforcement (Week 3)

**Current ACT State**:
```python
# /implementation/genesis_atp_adp_manager.py
pool = {
    'entities': {
        'lct:web4:genesis:genesis_queen': {
            'atp_balance': 30000,
            'adp_balance': 0,
            'daily_recharge': 3000
        }
    }
}
```

**Problem**: ATP tracking exists, but no per-delegation budget limits.

**Web4 Enhancement** (from session96_track3_atp_resource_limits.py):
```python
class BudgetedDelegationToken:
    # Delegation info
    token_id: str
    issuer: str
    delegate: str

    # ATP budget
    atp_budget: float
    atp_consumed: float
    atp_locked: float  # For pending transactions

    @property
    def atp_available(self) -> float:
        return self.atp_budget - self.atp_consumed - self.atp_locked
```

**Integration Plan**:
1. Extend `energycycle` module with `DelegationBudget` type
2. Link budgets to delegation chains (from Phase 2)
3. Add pre-transaction budget checks
4. Implement lock-commit-rollback for ATP operations

**Files to modify**:
- `/x/energycycle/types/budget.proto` - Add `DelegationBudget` message
- `/x/energycycle/keeper/keeper.go` - Add `CheckBudget()`, `LockATP()`, `CommitATP()`
- `/x/energycycle/keeper/msg_server.go` - Add budget enforcement to all ATP operations

**New types**:
```protobuf
// energycycle/types/budget.proto
message DelegationBudget {
    string delegation_id = 1;
    string delegate_lct = 2;
    int64 total_budget = 3;
    int64 consumed = 4;
    int64 locked = 5;
    int64 daily_limit = 6;
    int64 monthly_limit = 7;
}

message BudgetAlert {
    string delegation_id = 1;
    AlertLevel level = 2;  # WARNING_80 | CRITICAL_90 | EXHAUSTED_100
    int64 budget_allocated = 3;
    int64 budget_consumed = 4;
    int64 timestamp = 5;
}
```

**Budget enforcement flow**:
```go
// Before any ATP transaction
func (k Keeper) EnforceAtpBudget(ctx sdk.Context, delegationID string, amount int64) error {
    budget := k.GetDelegationBudget(ctx, delegationID)
    if budget.consumed + budget.locked + amount > budget.total_budget {
        return ErrBudgetExhausted
    }

    // Lock ATP for transaction
    budget.locked += amount
    k.SetDelegationBudget(ctx, budget)

    return nil
}

// After successful transaction
func (k Keeper) CommitAtpSpend(ctx sdk.Context, delegationID string, amount int64) error {
    budget := k.GetDelegationBudget(ctx, delegationID)
    budget.locked -= amount
    budget.consumed += amount

    // Check alert thresholds
    if budget.consumed >= int64(float64(budget.total_budget) * 0.80) {
        k.EmitBudgetAlert(ctx, budget, ALERT_WARNING_80)
    }

    k.SetDelegationBudget(ctx, budget)
    return nil
}
```

---

### Phase 4: Proof-of-Agency (Week 4)

**Current ACT State**:
- Agents write task reports to `federation_outbox/*.md`
- No cryptographic proof-of-agency
- No human approval workflow

**Web4 Enhancement**:
```python
class ProofOfAgency:
    agent_lct: str
    human_lct: str
    action: str
    action_hash: str
    delegation_chain_id: str
    agent_signature: str
    human_approval: Optional[str]
    timestamp: str
```

**Integration Plan**:
1. Create new module `/x/proofofagency/`
2. Record every agent action on-chain with signatures
3. Add human approval workflow
4. Create audit log viewer

**New module structure**:
```
/x/proofofagency/
├── keeper/
│   ├── keeper.go              # Proof storage
│   ├── msg_server.go          # RecordProof, ApproveAction
│   └── query.go               # GetProofs, GetAuditLog
├── types/
│   ├── proof.proto            # ProofOfAgency definition
│   └── audit.proto            # Audit log types
└── module.go
```

**Key types**:
```protobuf
// proofofagency/types/proof.proto
message ProofOfAgency {
    string proof_id = 1;
    string agent_lct = 2;
    string human_lct = 3;
    string action_description = 4;
    bytes action_hash = 5;
    string delegation_chain_id = 6;
    bytes agent_signature = 7;
    bytes human_approval = 8;  # Optional
    int64 timestamp = 9;
    ApprovalStatus status = 10;
}

enum ApprovalStatus {
    PENDING = 0;
    APPROVED = 1;
    REJECTED = 2;
    AUTO_APPROVED = 3;  # Within delegation scope
}
```

**Usage in autonomous agent**:
```python
# /implementation/ledger/sprout_autonomous_agent.py
def execute_task(self, task: FederationTask) -> bool:
    # Generate proof before action
    proof = ProofOfAgency(
        agent_lct=self.lct_id,
        human_lct=self.paired_human_lct,
        action_description=task.title,
        action_hash=hashlib.sha256(task.to_json().encode()).hexdigest(),
        delegation_chain_id=self.delegation_token.token_id,
        agent_signature=self.sign_message(task.to_json()),
        timestamp=int(time.time())
    )

    # Record on blockchain
    blockchain.record_proof_of_agency(proof)

    # Execute task
    result = self._execute_task_internal(task)

    # Update proof with result
    blockchain.update_proof_result(proof.proof_id, result)

    return result
```

---

### Phase 5: Multi-Agent Integration (Week 5)

**Goal**: Test accountability stack in real multi-agent scenarios

**Test Scenarios**:

#### Scenario 1: Cooperative Delegation
```
Human (1000 ATP)
  └─ Coordinator SAGE (delegated 500 ATP, can sub-delegate)
        ├─ Worker Agent 1 (delegated 200 ATP, analysis)
        ├─ Worker Agent 2 (delegated 200 ATP, code generation)
        └─ Worker Agent 3 (delegated 100 ATP, testing)
```

**Success criteria**:
- Delegation chain tracks full ancestry
- ATP budgets enforced at each level
- Proof-of-agency for every action
- Budget exhaustion blocks further work
- Human can revoke any level and children are auto-revoked

#### Scenario 2: Budget Gaming Attack
```
Attacker attempts:
1. Create circular delegation (A→B→A)
2. Spend ATP then revoke to "refund"
3. Create many delegations to fragment tracking
4. Sub-delegate beyond authority
```

**Success criteria**:
- Circular delegation detected and rejected
- Revocation doesn't refund spent ATP
- Budget tracking accurate across many delegations
- Sub-delegation beyond authority rejected

#### Scenario 3: Cross-Network Settlement
```
Mainnet Agent (200 ATP) delegates to Testnet Agent (100 ATP equivalent)
  └─ Bridge converts: 200 mainnet ATP → 100 testnet ATP (0.5x rate)
  └─ Testnet agent completes work
  └─ Settlement: 50 testnet ATP → 25 mainnet ATP credited
```

**Success criteria**:
- Cross-network delegation recorded in both chains
- Exchange rate applied correctly
- Budget tracking synchronized
- Settlement finalizes after confirmations

#### Scenario 4: Dynamic Budget Optimization
```
SAGE with 1000 ATP, 3 workers:
- Worker A: 90% success rate, fast → allocated 400 ATP
- Worker B: 70% success rate, slow → allocated 200 ATP
- Worker C: 50% success rate, very slow → allocated 100 ATP
```

**Success criteria**:
- Budgets adjust based on performance metrics
- Efficient agents get more resources
- Poor performers get less
- Total budget conserved

---

## Implementation Tracker

### Week 1: Hardware-Bound Identity
- [ ] Add `HardwareAttestation` protobuf to lctmanager
- [ ] Implement `VerifyHardwareBinding()` in keeper
- [ ] Create HSM simulator for testing
- [ ] Test with 10 agents (5 hardware-bound, 5 software-bound)
- [ ] Measure: Identity creation time, attestation verification time

### Week 2: Delegation Chain
- [ ] Create `/x/delegationchain/` module
- [ ] Implement delegation token storage + queries
- [ ] Add ancestry tracking
- [ ] Implement revocation cascade (revoking parent revokes all children)
- [ ] Test: 5-level delegation chain (human → SAGE → coordinator → worker → sub-worker)

### Week 3: ATP Budget Enforcement
- [ ] Extend `energycycle` with `DelegationBudget`
- [ ] Add lock-commit-rollback for ATP operations
- [ ] Implement budget alerts (80%, 90%, 100%)
- [ ] Test: Budget exhaustion blocks transactions
- [ ] Measure: Budget check overhead (<1ms target)

### Week 4: Proof-of-Agency
- [ ] Create `/x/proofofagency/` module
- [ ] Integrate with autonomous agent execution
- [ ] Add human approval workflow
- [ ] Create audit log viewer
- [ ] Test: 100 actions, verify all have proofs

### Week 5: Multi-Agent Scenarios
- [ ] Implement Scenario 1 (Cooperative Delegation)
- [ ] Implement Scenario 2 (Budget Gaming Attack)
- [ ] Implement Scenario 3 (Cross-Network Settlement)
- [ ] Implement Scenario 4 (Dynamic Budget Optimization)
- [ ] Collect performance metrics
- [ ] Document security test results

---

## Success Metrics

### Performance Targets
- Identity creation: <200ms (hardware-bound)
- Delegation token creation: <50ms
- Budget check: <1ms
- Proof-of-agency creation: <10ms
- Query delegation chain (5 levels): <20ms

### Security Validation
- ✓ Sybil attack prevention (hardware binding required)
- ✓ Delegation forgery prevention (signature verification)
- ✓ ATP farming prevention (conservation law)
- ✓ Budget gaming prevention (atomic lock-commit-rollback)
- ✓ Circular delegation prevention (ancestry check)

### Integration Quality
- All existing ACT tests still pass
- No breaking changes to existing modules
- Clean separation of concerns
- Backward compatible with non-accountability agents

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     ACT BLOCKCHAIN                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  lctmanager (EXTENDED)                                 │  │
│  │  - LCT registration                                    │  │
│  │  + Hardware attestation verification (NEW)            │  │
│  │  + Binding strength tracking (NEW)                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  pairing (EXTENDED)                                    │  │
│  │  - Agent pairing certificates                          │  │
│  │  + Delegation chain references (NEW)                  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  delegationchain (NEW MODULE)                          │  │
│  │  + Delegation token storage                           │  │
│  │  + Ancestry tracking                                  │  │
│  │  + Revocation cascade                                 │  │
│  │  + Authority verification                             │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  energycycle (EXTENDED)                                │  │
│  │  - ATP/ADP balance tracking                            │  │
│  │  + Per-delegation budgets (NEW)                       │  │
│  │  + Lock-commit-rollback (NEW)                         │  │
│  │  + Budget alerts (NEW)                                │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  proofofagency (NEW MODULE)                            │  │
│  │  + Action recording                                   │  │
│  │  + Human approval workflow                            │  │
│  │  + Audit log                                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  trusttensor (EXISTING)                                │  │
│  │  - Byzantine consensus for trust                       │  │
│  │  - Already implements federation attestation!         │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              FEDERATION LAYER (Python)                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  SproutAutonomousAgent                                 │  │
│  │  - Task detection + execution                          │  │
│  │  + Proof-of-agency generation (NEW)                   │  │
│  │  + Budget checking (NEW)                              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  TrustCoordinator                                      │  │
│  │  - Byzantine consensus                                 │  │
│  │  - Trust updates                                       │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Extend vs. New Modules
**Decision**: Extend existing modules where possible, create new modules only when necessary.

**Rationale**:
- Hardware binding → Extend `lctmanager` (natural fit)
- Delegation chains → New `delegationchain` module (complex new state)
- ATP budgets → Extend `energycycle` (builds on existing ATP tracking)
- Proof-of-agency → New `proofofagency` module (new audit system)

### 2. Backward Compatibility
**Decision**: All accountability features are optional enhancements.

**Rationale**:
- Agents without hardware binding still work (lower trust)
- Delegations without budget limits still allowed (infinite budget)
- Proof-of-agency is opt-in per agent
- Existing ACT deployments unaffected

### 3. Performance First
**Decision**: Budget checks must be <1ms, identity operations <200ms.

**Rationale**:
- Accountability adds overhead
- Must not slow down agent operations
- Cache frequently accessed data
- Use indexes for chain queries

### 4. Security by Default
**Decision**: Default to strict enforcement, allow relaxation via config.

**Rationale**:
- Opt-in security rarely gets adopted
- Production systems need accountability by default
- Testing can disable features for speed

---

## Next Steps

1. **Design Review** (this document)
2. **Phase 1 Implementation** (hardware-bound identity)
3. **Phase 2 Implementation** (delegation chains)
4. **Phase 3 Implementation** (ATP budgets)
5. **Phase 4 Implementation** (proof-of-agency)
6. **Phase 5 Testing** (multi-agent scenarios)
7. **Documentation** (integration guide)
8. **WEB4-PROPOSAL-001 Update** (incorporate ACT findings)

---

## References

- ACT Framework Exploration: `/home/dp/ai-workspace/ACT_FRAMEWORK_EXPLORATION.md`
- Session 96 Track 1: `/home/dp/ai-workspace/web4/implementation/session96_track1_hardware_bound_identity.py`
- Session 96 Track 2: `/home/dp/ai-workspace/web4/implementation/session96_track2_delegation_chain.py`
- Session 96 Track 3: `/home/dp/ai-workspace/web4/implementation/session96_track3_atp_resource_limits.py`
- Sessions 96-100 Summary: `/home/dp/ai-workspace/private-context/moments/2025-12-28-sessions-96-100-research-arc-summary.md`
- WEB4-PROPOSAL-001: `/home/dp/ai-workspace/web4/proposals/WEB4-PROPOSAL-001-AI-AGENT-ACCOUNTABILITY-STACK.md`
