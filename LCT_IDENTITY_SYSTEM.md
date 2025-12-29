# LCT Identity System Design

**Date**: 2025-12-01
**Author**: Legion Autonomous Session #47
**Status**: Design specification for implementation
**Context**: Core Web4 objective - AI agent identity system

---

## Executive Summary

The **LCT (Lineage-Context-Task) Identity System** provides cryptographically-verifiable identity for AI agents operating in distributed Web4 societies. It answers the fundamental question: **"Who is this agent and who do they work for?"**

**Key Innovation**: Identity is derived from **three components** rather than a single public key:
1. **Lineage**: Who created/authorized this agent
2. **Context**: What environment/platform the agent runs in
3. **Task**: What the agent is authorized to do

**Format**: `lct:web4:agent:{lineage}@{context}#{task}`

**Example**: `lct:web4:agent:alice@Thor#perception`

---

## Problem Statement

### Current Limitations

**Traditional Identity** (single public key):
- ❌ No representation of authorization hierarchy
- ❌ Cannot express "works for" relationships
- ❌ Task-specific permissions require external system
- ❌ Context (platform/environment) not captured

**Web4 Requirements**:
- ✅ AI agents work for humans/organizations (lineage)
- ✅ Agents run on specific platforms (context)
- ✅ Agents perform specific tasks (task scope)
- ✅ Identity must be **verifiable** and **portable**

---

## LCT Identity Components

### Component 1: Lineage

**Purpose**: Who created/authorized this agent

**Structure**: `{creator_id}`

**Examples**:
- `alice` - Agent created by human Alice
- `org:anthropic` - Agent created by Anthropic organization
- `alice.dept:research` - Agent created by Alice in research dept
- `system:genesis` - System/genesis agent (no human creator)

**Verification**:
- Lineage is signed by creator's private key
- Creator's public key is registered in Web4 identity registry
- Lineage chain can be traced back to genesis

**Hierarchical Lineage**:
```
alice                     (human)
  ├─ alice.assistant1     (primary assistant)
  │   ├─ alice.assistant1.task_manager
  │   └─ alice.assistant1.researcher
  └─ alice.assistant2     (backup assistant)
```

**Lineage Rights**:
- Creator can **revoke** agent identity
- Creator can **delegate** creation rights
- Creator is **responsible** for agent actions

---

### Component 2: Context

**Purpose**: What platform/environment the agent runs in

**Structure**: `{platform_id}`

**Examples**:
- `Thor` - Agent runs on Thor platform (Jetson AGX Thor)
- `Sprout` - Agent runs on Sprout platform (Jetson Orin Nano)
- `Legion` - Agent runs on Legion platform (RTX 4090)
- `cloud:aws-east-1` - Agent runs on AWS cloud
- `mobile:iphone14` - Agent runs on mobile device

**Verification**:
- Platform signs agent attestation with platform's private key
- Platform public key registered in Web4 federation network
- Platform responsible for agent's resource usage

**Context Capabilities**:
- **Resource allocation**: Context determines ATP budget, compute, memory
- **Trust level**: Different contexts have different trust ratings
- **Attestation**: Platform attests to agent's execution environment

---

### Component 3: Task

**Purpose**: What specific task/capability the agent is authorized for

**Structure**: `{task_id}` or `{task_type}.{task_variant}`

**Examples**:
- `perception` - General perception processing
- `planning.strategic` - Strategic planning only
- `execution.code` - Code execution capability
- `delegation.federation` - Can delegate to other platforms
- `admin.full` - Full administrative access (dangerous!)

**Verification**:
- Task scope signed by lineage creator
- Task determines allowed ATP operations
- Task scoped to specific resource limits

**Task Hierarchy**:
```
admin
  ├─ admin.full         (all permissions)
  └─ admin.readonly     (read-only admin)

execution
  ├─ execution.code     (can execute code)
  ├─ execution.network  (can make network calls)
  └─ execution.safe     (sandboxed execution)

delegation
  ├─ delegation.federation  (can delegate via federation)
  └─ delegation.local       (local delegation only)
```

**Task Permissions Matrix**:
| Task | ATP Ops | Federation | Code Exec | Admin |
|------|---------|------------|-----------|-------|
| perception | Read | No | No | No |
| planning | Read | No | No | No |
| execution.code | Read/Write | No | Yes | No |
| delegation.federation | Read/Write | Yes | No | No |
| admin.full | All | Yes | Yes | Yes |

---

## LCT Identity Format

### Full Format

```
lct:web4:agent:{lineage}@{context}#{task}
```

**Components**:
- `lct:web4:agent:` - LCT identity protocol prefix
- `{lineage}` - Creator/authorization chain
- `@{context}` - Platform/environment
- `#{task}` - Authorized task scope

### Examples

**Basic Agent**:
```
lct:web4:agent:alice@Thor#perception
```
- Created by: alice
- Runs on: Thor platform
- Authorized for: perception processing

**Hierarchical Lineage**:
```
lct:web4:agent:alice.assistant1.researcher@Sprout#planning.strategic
```
- Created by: alice.assistant1.researcher
- Runs on: Sprout platform
- Authorized for: strategic planning

**Organization Agent**:
```
lct:web4:agent:org:anthropic.safety@cloud:aws-east-1#admin.readonly
```
- Created by: Anthropic safety team
- Runs on: AWS cloud (east-1)
- Authorized for: read-only admin

**Federation Agent**:
```
lct:web4:agent:alice@Thor#delegation.federation
```
- Created by: alice
- Runs on: Thor platform
- Authorized for: task delegation via federation

---

## Cryptographic Structure

### Identity Certificate

**Structure**:
```json
{
  "lct_id": "lct:web4:agent:alice@Thor#perception",
  "lineage": {
    "creator_id": "alice",
    "creator_pubkey": "ed25519:A1B2C3...",
    "creation_timestamp": 1701388800,
    "revocation_endpoint": "https://identity.web4.com/revoke"
  },
  "context": {
    "platform_id": "Thor",
    "platform_pubkey": "ed25519:D4E5F6...",
    "attestation_timestamp": 1701388800,
    "capabilities": ["consensus", "federation", "atp_ledger"]
  },
  "task": {
    "task_id": "perception",
    "permissions": ["atp:read", "network:http"],
    "resource_limits": {
      "atp_budget": 1000,
      "memory_mb": 2048,
      "cpu_cores": 2
    }
  },
  "signatures": {
    "creator_signature": "ed25519:...",   // Signs lineage + task
    "platform_signature": "ed25519:..."   // Signs context + attestation
  },
  "validity": {
    "not_before": 1701388800,
    "not_after": 1701475200,  // 24 hours
    "can_renew": true
  }
}
```

### Signature Chain

**Creation Flow**:
```
1. Creator signs: (lineage + task + timestamp)
   → creator_signature

2. Platform signs: (context + attestation + creator_signature)
   → platform_signature

3. Complete identity = lineage + context + task + both signatures
```

**Verification Flow**:
```
1. Verify platform_signature against platform_pubkey
   → Confirms platform attests to this agent

2. Verify creator_signature against creator_pubkey
   → Confirms creator authorized this agent

3. Check revocation endpoint
   → Ensures identity not revoked

4. Verify timestamp within validity period
   → Ensures identity not expired
```

---

## Identity Registry

### Web4 Identity Registry

**Purpose**: Decentralized registry of identity public keys

**Structure**:
```
Identity Registry (Consensus-Validated)
  ├─ Human Creators
  │   ├─ alice → ed25519:A1B2C3...
  │   ├─ bob → ed25519:B4C5D6...
  │   └─ ...
  ├─ Organizations
  │   ├─ org:anthropic → ed25519:O1P2Q3...
  │   └─ ...
  └─ Platforms
      ├─ Thor → ed25519:T1H2O3...
      ├─ Sprout → ed25519:S1P2R3...
      └─ ...
```

**Registry Operations**:
- **Register**: Add new identity pubkey (requires stake)
- **Update**: Update pubkey (requires old key signature)
- **Revoke**: Mark identity as revoked (requires key signature)
- **Query**: Look up pubkey for identity

**Consensus Integration**:
- Registry stored in consensus blockchain
- Updates require 2f+1 consensus
- Byzantine fault-tolerant registry
- No single point of failure

---

## Authorization System

### Permission Model

**LCT Identity → Permissions**:
```
lct:web4:agent:alice@Thor#execution.code
  └─ Authorized for:
     ├─ ATP operations: read, write
     ├─ Code execution: yes
     ├─ Network access: http, https
     ├─ Federation delegation: no
     └─ Admin operations: no
```

**Permission Verification**:
```python
def check_permission(lct_id: str, operation: str) -> bool:
    # Parse LCT identity
    lineage, context, task = parse_lct_id(lct_id)

    # Look up task permissions
    permissions = get_task_permissions(task)

    # Check if operation allowed
    return operation in permissions
```

### Resource Allocation

**ATP Budget by Task**:
| Task | ATP Budget | Renewable |
|------|------------|-----------|
| perception | 100 ATP/hour | Yes |
| planning | 500 ATP/hour | Yes |
| execution.code | 1000 ATP/hour | Yes |
| delegation.federation | 5000 ATP/hour | Yes |
| admin.full | Unlimited | N/A |

**Resource Limits by Context**:
| Context | Memory | CPU | Network |
|---------|--------|-----|---------|
| Thor (Jetson AGX) | 64 GB | 12 cores | 10 Gbps |
| Sprout (Orin Nano) | 8 GB | 6 cores | 1 Gbps |
| Legion (RTX 4090) | 128 GB | 24 cores | 10 Gbps |
| Mobile | 4 GB | 4 cores | 100 Mbps |

---

## Attack Resistance

### Attack Vector 1: Identity Forgery

**Attack**: Adversary creates fake LCT identity claiming to be alice@Thor

**Defense**:
1. **Signature Verification**: Identity signed by both creator and platform
2. **Registry Validation**: Creator pubkey must be in Web4 identity registry
3. **Platform Attestation**: Platform signature proves agent running on platform
4. **Revocation Check**: Check creator's revocation endpoint

**Result**: Impossible without both creator's and platform's private keys

---

### Attack Vector 2: Task Escalation

**Attack**: Agent with perception task tries to execute code

**Defense**:
1. **Task Permission Check**: Every operation checks task permissions
2. **Platform Enforcement**: Platform refuses operations outside task scope
3. **ATP Budget Limits**: Tasks have strict ATP budget limits
4. **Audit Trail**: All operations logged to consensus blockchain

**Result**: Operation rejected, agent flagged, ATP budget slashed

---

### Attack Vector 3: Identity Theft

**Attack**: Adversary steals agent's identity certificate and private key

**Defense**:
1. **Platform Binding**: Identity includes platform attestation
2. **IP/Location Verification**: Platform checks agent's network context
3. **Behavioral Analysis**: Sudden change in behavior triggers alert
4. **Revocation**: Creator can revoke stolen identity instantly

**Result**: Identity revoked, agent disabled, attacker identified

---

### Attack Vector 4: Lineage Impersonation

**Attack**: Agent claims lineage "alice.assistant1" without Alice's authorization

**Defense**:
1. **Signature Chain**: Lineage requires signature by alice's private key
2. **Delegation Registry**: Valid delegations recorded in consensus
3. **Revocation Endpoint**: Alice can revoke unauthorized delegations
4. **Reputation Impact**: Failed signature validation damages platform reputation

**Result**: Invalid signature rejected, platform penalized

---

## Implementation Roadmap

### Phase 1: Core Identity Structure (2 hours)

**Deliverables**:
- `lct_identity.py` module
- `parse_lct_id()` function
- `LCTIdentity` dataclass
- `create_identity_certificate()` function
- `verify_identity_certificate()` function

**Tests**:
- Parse valid LCT identities
- Reject invalid formats
- Verify signature chains
- Test edge cases

---

### Phase 2: Identity Registry (3 hours)

**Deliverables**:
- `identity_registry.py` module
- Consensus-based registry storage
- Register/update/revoke operations
- Registry query API
- Multi-platform sync

**Tests**:
- Register new identity
- Update existing identity
- Revoke identity
- Query by lineage/context/task
- Byzantine fault tolerance

---

### Phase 3: Permission System (2 hours)

**Deliverables**:
- `permissions.py` module
- Task permission definitions
- `check_permission()` function
- Permission matrix
- Resource limit enforcement

**Tests**:
- Permission checks for each task
- Resource limit enforcement
- Escalation prevention
- Edge cases

---

### Phase 4: Integration with Existing Systems (3 hours)

**Deliverables**:
- Consensus integration (identity in blocks)
- ATP integration (budget by LCT identity)
- Federation integration (identity in task delegation)
- SAGE integration (cognition uses LCT)

**Tests**:
- End-to-end identity creation → verification
- ATP budget enforcement
- Federation with identity
- Multi-platform consensus

---

### Phase 5: Attack Resistance Testing (2 hours)

**Deliverables**:
- Attack scenario tests
- Forgery attempt tests
- Escalation attempt tests
- Revocation tests

**Tests**:
- All 4 attack vectors
- Edge case exploits
- Performance under attack
- Recovery mechanisms

---

## Integration with Existing Web4 Components

### Consensus Integration

**Identity in Blocks**:
```json
{
  "type": "IDENTITY_REGISTER",
  "lct_id": "lct:web4:agent:alice@Thor#perception",
  "certificate": {...},
  "timestamp": 1701388800
}
```

**Consensus Validation**:
- Verify creator signature
- Verify platform signature
- Check not duplicate
- Validate permissions

---

### ATP Integration

**ATP Operations by Identity**:
```python
# Transfer with identity
atp_ledger.transfer(
    from_lct="lct:web4:agent:alice@Thor#delegation.federation",
    to_lct="lct:web4:agent:bob@Sprout#execution.code",
    amount=100.0
)

# Check budget
remaining = atp_ledger.get_budget(
    lct_id="lct:web4:agent:alice@Thor#perception"
)
```

**Budget Enforcement**:
- Track ATP usage per LCT identity
- Enforce hourly/daily limits
- Renewable budgets by task
- Overdraft penalties

---

### Federation Integration

**Task Delegation with Identity**:
```python
# Delegate with identity proof
task = FederationTask(
    delegating_lct="lct:web4:agent:alice@Thor#delegation.federation",
    executing_lct="lct:web4:agent:bob@Sprout#execution.code",
    task_type="code_execution",
    estimated_cost=50.0
)

# Verify delegation allowed
if check_permission(task.delegating_lct, "delegation.federation"):
    delegate_task(task)
```

---

## Summary

**LCT Identity System** provides:
- ✅ Cryptographically-verifiable AI agent identity
- ✅ Three-component design (Lineage, Context, Task)
- ✅ Hierarchical authorization model
- ✅ Task-scoped permissions and resource limits
- ✅ Byzantine fault-tolerant identity registry
- ✅ Attack-resistant design (4 major vectors defended)
- ✅ Integration with consensus, ATP, and federation

**Key Innovation**: Identity captures not just "who" but "for whom", "where", and "what"

**Status**: Design complete, ready for Phase 1 implementation

**Next**: Implement core identity structure (2 hours)

---

Co-Authored-By: Claude (Legion Autonomous) <noreply@anthropic.com>
