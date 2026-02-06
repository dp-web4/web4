# ACT Framework Quick Reference
## Fast lookup for key components

### Module Locations

**Blockchain Modules** (`/implementation/ledger/x/`)
```
lctmanager/       → Identity registration & management
pairing/          → Agent pairing & delegation
pairingqueue/     → Queue management & offline ops
trusttensor/      → Trust scoring & attribution
energycycle/      → ATP/ADP economy & budgets
mrh/              → Context boundary management
componentregistry → Component tracking
societytodo/      → Governance & tasks
```

**Python Tools** (`/implementation/`)
```
sprout_autonomous_agent.py       → Autonomous agent executor (1433 lines)
trust_coordinator.py             → Trust aggregation & consensus
federation_trust_transfer.py     → Cross-society trust
genesis_atp_adp_manager.py       → ATP pool management
genesis_blockchain.py            → Blockchain integration
genesis_crypto.py                → Cryptographic utilities
genesis_witness.py               → Witness coordination
```

**Specifications** (`/core-spec/`)
```
human-lct-binding.md    → LCT creation & binding ceremony
agent-pairing.md        → Agent pairing & revocation
permission-model.md     → Permissions & constraints
ui-requirements.md      → User interface spec
```

### Key Data Structures

#### LCT Identity
```python
@dataclass
class LCTIdentity:
    lct_id: str           # Format: lct://society:role:agent_id@network
    public_key: str       # Ed25519
    hardware_hash: str    # TPM binding (placeholder currently)
    role: str             # "citizen" | "validator" | "coordinator"
```

#### Permission Specification
```python
Permission(
    scope="financial.transfer",        # Category
    action="send",                     # Action
    constraints={
        "max_per_tx": 100,             # Value limit
        "daily_limit": 1000,
        "rate_limit": "10/hour",       # Rate limit
        "expires_at": "2025-12-31"     # Temporal
    }
)
```

#### Trust Update
```python
@dataclass
class TrustUpdate:
    agent_lct: str    # Who observed
    expert_id: int    # Which expert
    context: str      # What context
    quality: float    # [0, 1] quality score
    timestamp: int    # Unix time
    signature: str    # Cryptographic signature
```

#### ATP/ADP States
```
ATP = "atp"    # Charged, available for work
ADP = "adp"    # Discharged, awaiting recharge
```

### Core Flows

#### 1. Creating an Agent
```
Human LCT
    ↓ [Sign pairing certificate]
Agent keypair generation (X25519)
    ↓ [Diffie-Hellman exchange]
Derive shared secret & session keys
    ↓ [Create certificate]
Register on blockchain (lctmanager module)
    ↓ [Broadcast to network]
Agent LCT created ✓
```

#### 2. Delegating to Agent
```
Agent receives task from federation_inbox
    ↓ [Parse markdown task file]
Check resource constraints (temp, memory, ATP)
    ↓ [Fail if exceeded]
Check delegation permissions (query pairing module)
    ↓ [Fail if insufficient]
Execute task locally
    ↓ [Create proof-of-agency]
Record to blockchain & write report to federation_outbox
```

#### 3. Trust Consensus
```
Agent observes expert quality
    ↓ [Create TrustUpdate + sign]
Broadcast to society
    ↓ [All validators receive]
Byzantine consensus (need 2f+1 witnesses)
    ↓ [Aggregate via median]
Update aggregated trust
    ↓ [Publish to ledger]
Trust state updated ✓
```

### REST API Endpoints

**LCT Manager**
```
GET    /cosmos/lctmanager/v1/lct/{lct_id}
GET    /cosmos/lctmanager/v1/society/{society_id}/lcts
POST   /cosmos/lctmanager/v1/register_lct
```

**Pairing**
```
GET    /cosmos/pairing/v1/pairing/{pairing_id}
POST   /cosmos/pairing/v1/create_pairing
POST   /cosmos/pairing/v1/revoke_pairing
```

**Energy Cycle**
```
GET    /cosmos/energycycle/v1/balance/{agent_lct}
POST   /cosmos/energycycle/v1/discharge
POST   /cosmos/energycycle/v1/recharge
```

**Trust Tensor**
```
GET    /cosmos/trusttensor/v1/trust/{expert_id}/{context}
POST   /cosmos/trusttensor/v1/update_trust
```

### Configuration Files

**Agent Config** (Python)
```python
federation_inbox: Path          # Where tasks arrive
federation_outbox: Path         # Where reports go
workspace: Path                 # Work directory
hrm_path: Path                  # HRM integration

max_file_size: int              # 100KB limit
max_concurrent_tasks: int       # 3 tasks max
memory_limit_mb: int            # 4GB limit
power_budget_watts: int         # 15W for Jetson

allowed_paths: List[str]        # Whitelist
forbidden_commands: List[str]   # Blacklist
```

**ATP Configuration** (Python)
```python
FEDERATION_TOTAL_ATP = 100000      # Total federation budget
SOCIETY_BASE_ATP = 20000           # Per society
DAILY_RECHARGE_ATP = 10000         # Daily regeneration
EMERGENCY_RESERVE_ATP = 5000       # Emergency fund
```

### Security Checklist

- [ ] Hardware binding verified (TPM quote)
- [ ] Witness attestations present (minimum 3)
- [ ] Permission inheritance enforced
- [ ] ATP budget limits checked
- [ ] Rate limits applied
- [ ] Signatures cryptographically valid
- [ ] Temperature/resource constraints met
- [ ] Delegation depth limits enforced
- [ ] Revocation propagated
- [ ] Audit log recorded

### Integration Checklist

**To add hardware binding**:
1. Add `HardwareBinding` protobuf to `lctmanager/types/`
2. Implement TPM verification in `lctmanager/keeper/`
3. Update `genesis_atp_adp_manager.py` to verify at startup

**To add delegation chains**:
1. Create `/x/delegationchain/` module
2. Add `DelegationLink` type with parent field
3. Implement keeper with chain traversal

**To add budget limits**:
1. Extend `energycycle/types/` with `DelegationBudget`
2. Add spending checks in `energycycle/keeper/`
3. Implement approval workflow in Python

**To add proof-of-agency**:
1. Create `/x/proofofagency/` module
2. Implement signing in Python agent
3. Add human approval notification

### Common Gotchas

⚠️ **Permission inheritance is checked at delegation time**
- Agent cannot do what human hasn't authorized
- Constraints are cumulative (most restrictive wins)

⚠️ **ATP is society-owned, not agent-owned**
- Agents draw from pool, not personal balance
- Must recharge for continued operation

⚠️ **Hardware binding currently uses static hashes**
- Not production-ready (vulnerable to copying)
- TPM integration required for real security

⚠️ **Trust consensus requires 2f+1 witnesses**
- With 3 agents, need all 3 to agree
- With 10 agents, 7+ need to agree

⚠️ **Federation messages are markdown files**
- Not encrypted in transit
- Sensitive data should use blockchain for encoding

### Debugging Tips

**Check agent state**:
```python
agent = SproutAutonomousAgent()
print(f"State: {agent.state}")
print(f"ATP: {agent.atp_balance}")
print(f"Tasks: {len(agent.tasks)}")
```

**Check blockchain status**:
```bash
# RPC endpoint
curl http://localhost:26657/status

# REST API
curl http://localhost:1317/cosmos/lctmanager/v1/lct/lct:test:alice

# Check specific module
curl http://localhost:1317/cosmos/energycycle/v1/balance/alice
```

**Debug permission checks**:
```python
# In agent before execution
permissions = entity.get_permissions_for_action(action)
for perm in permissions:
    is_valid = perm.is_valid_now()
    has_value = perm.check_value_limit(amount)
    under_rate = perm.check_rate_limit()
```

**Monitor trust consensus**:
```python
consensus = ByzantineConsensus(min_witnesses=3)
consensus.propose_update(trust_update_1)
consensus.propose_update(trust_update_2)
consensus.propose_update(trust_update_3)
# Now has consensus
value = consensus.get_consensus_value(consensus_key)
```

### Next Steps for Integration

1. **Read the specifications** (core-spec/*.md)
2. **Trace a task execution** (sprout_autonomous_agent.py)
3. **Understand blockchain structure** (ledger/x/*/types/)
4. **Run the demo society** (implementation/society/)
5. **Implement Phase 1 feature** (hardware binding)

### Resources

- **ACT Repository**: https://github.com/dp-web4/ACT
- **Web4 Specs**: https://github.com/dp-web4/web4
- **Cosmos SDK Docs**: https://docs.cosmos.network/
- **Tendermint Consensus**: https://tendermint.com/

---

**Last Updated**: 2025-12-28  
**Status**: Research/Learning Phase  
**Questions?** Check ACT_FRAMEWORK_EXPLORATION.md for detailed analysis
