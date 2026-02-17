# Web4 Entity Relationship Guide

## Overview

Web4 defines four fundamental mechanisms for entities to relate and interact. Each mechanism serves a specific purpose and creates different trust dynamics.

## The Four Mechanisms

### 1. BINDING - Permanent Identity Attachment

**Purpose**: Create an unforgeable, permanent link between entities, typically establishing parent-child hierarchies.

**Key Characteristics:**
- Permanent and irreversible (except through revocation)
- Creates hierarchical relationships
- Hardware anchoring possible via EAT tokens
- Both entities' MRH updated with binding

**When to Use:**
- Creating organizational hierarchies
- Establishing device ownership
- Defining role inheritance
- Anchoring virtual entities to physical hardware

**Example Flow:**
```
Organization creates Role:
1. Organization generates Role LCT
2. BINDING established (Organization → Role)
3. Role inherits organizational context
4. Both MRHs updated with relationship
```

**Implementation:**
```json
// Binding Request
{
  "version": "BIND/1.0",
  "entity_type": "role",
  "public_key": "mb64:...",
  "hardware_id": "sha256:...",
  "parent_lct": "lct:web4:org:..."
}

// MRH Update (both entities)
{
  "mrh": {
    "bound": [
      {
        "lct_id": "lct:web4:...",
        "type": "parent|child",
        "ts": "2025-01-11T15:00:00Z"
      }
    ]
  }
}
```

### 2. PAIRING - Authorized Operational Relationships

**Purpose**: Establish temporary, context-specific operational relationships between peers.

**Three Pairing Modes:**

#### Direct Pairing (Peer-to-Peer)
- Entities negotiate directly without intermediary
- Each generates half of session key
- Lowest latency, highest privacy
- Best for: Low-risk, trusted entities

#### Witnessed Pairing (Notarized)
- Third entity observes and attests
- Creates permanent pairing record
- Adds external validation
- Best for: Legal compliance, dispute resolution

#### Authorized Pairing (Mediated)
- Authority handles entire process
- Authority generates and distributes keys
- Enables transparent policy compliance
- Best for: High-risk, enterprise, role assignments

**Key Characteristics:**
- Bidirectional authorization required (except in authorized mode)
- Context-specific (e.g., "energy-mgmt", "data-exchange")
- Symmetric key derivation for secure communication
- Session-based with explicit lifecycle

**When to Use:**
- Agent taking on a role
- Peer-to-peer collaboration
- Service consumption
- Resource sharing

**Special Case - Role-Agent Pairing:**
When an agent pairs with a role:
- Agent temporarily assumes role's permissions
- Performance tracked against both entities
- Creates delegation relationship
- History maintained in role's LCT

**Example Flow:**
```
Human pairs with Developer Role:
1. Human requests pairing with Role
2. Role validates Human capabilities
3. Pairing established with context
4. Permissions transfer to Human
5. Performance tracking begins
```

**Implementation Examples:**

```json
// Direct Pairing Request
{
  "version": "PAIR/1.0",
  "mode": "DIRECT",
  "lct_a": "lct:web4:human:...",
  "lct_b": "lct:web4:ai:...",
  "context": "collaboration",
  "rules": {
    "permissions": ["read", "write"],
    "duration": 86400
  }
}

// Witnessed Pairing Request
{
  "version": "PAIR/1.0",
  "mode": "WITNESSED",
  "lct_a": "lct:web4:org:...",
  "lct_b": "lct:web4:service:...",
  "witness": "lct:web4:oracle:notary",
  "context": "service_agreement",
  "rules": {
    "sla": "99.9%",
    "audit_trail": true
  }
}

// Authorized Pairing Request
{
  "version": "PAIR/1.0",
  "mode": "AUTHORIZED",
  "lct_a": "lct:web4:human:...",
  "lct_b": "lct:web4:role:cfo",
  "authority": "lct:web4:org:hr",
  "context": "role_assignment",
  "rules": {
    "clearance": "executive",
    "permissions": ["approve:budgets"],
    "audit_required": true
  }
}
```

### 3. WITNESSING - Trust Building Through Observation

**Purpose**: Build trust through accumulated observations and attestations.

**Key Characteristics:**
- Creates bidirectional awareness
- No prior relationship required
- Evidence-based trust accumulation
- Multiple witness types (time, audit, oracle, quality)

**When to Use:**
- Validating entity existence
- Confirming action completion
- Providing temporal ordering
- Quality assessment
- Building reputation

**Evidence Types:**
- **EXISTENCE**: Entity is present and active
- **ACTION**: Specific operation was performed
- **STATE**: Current condition verification
- **TRANSITION**: State change confirmation

**Example Flow:**
```
Task completion witnessing:
1. Task executes and produces result
2. Multiple witnesses observe execution
3. Each witness creates attestation
4. Task LCT accumulates witness marks
5. Trust score increases with witnesses
```

**Implementation:**
```json
// Witness Assertion
{
  "version": "WTNS/1.0",
  "observer": "lct:web4:oracle:...",
  "observed": "lct:web4:task:...",
  "evidence": {
    "type": "ACTION",
    "data": {
      "action": "data_processed",
      "timestamp": "2025-01-11T15:30:00Z",
      "hash": "sha256:..."
    },
    "signature": "cose:..."
  }
}

// MRH Update (both entities)
{
  "witnessing": [
    {
      "lct_id": "lct:web4:oracle:...",
      "role": "action_validator",
      "last_attestation": "2025-01-11T15:30:00Z"
    }
  ]
}
```

### 4. BROADCAST - Unidirectional Discovery

**Purpose**: Enable discovery and presence announcement without forming relationships.

**Key Characteristics:**
- No acknowledgment required
- No MRH updates
- Enables passive witnessing via accumulators
- Public announcements only

**When to Use:**
- Service discovery
- Capability announcements
- Heartbeat/liveness signals
- Public state updates

**Special Feature - Accumulator Witnessing:**
Accumulators listen to broadcasts and create queryable history:
- Lightweight presence validation
- No direct relationship needed
- Historical audit trails
- Privacy-preserving queries

**Example Flow:**
```
Service announces availability:
1. Service broadcasts capabilities
2. Accumulators record broadcast
3. Clients query accumulators
4. Clients initiate pairing if interested
5. No relationship until explicit pairing
```

**Implementation:**
```json
// Broadcast Message
{
  "version": "CAST/1.0",
  "sender_id": "service:energy_provider",
  "message_type": "CAPABILITY",
  "payload": {
    "services": ["energy:supply", "meter:read"],
    "location": "us-west-2",
    "availability": "24/7",
    "rate_atp": 5
  }
}

// Accumulator Query
{
  "query": "broadcasts_by_entity",
  "entity": "lct:web4:service:...",
  "time_range": {
    "start": "2025-01-11T00:00:00Z",
    "end": "2025-01-11T23:59:59Z"
  }
}

// Accumulator Response
{
  "broadcast_count": 144,
  "consistency_score": 0.99,
  "gaps": [],
  "presence_confirmed": true
}
```

## Relationship Lifecycle Management

### Creation Patterns

**Hierarchical (via BINDING):**
```
Organization → Department → Team → Role
```

**Operational (via PAIRING):**
```
Agent ↔ Role (delegation)
Peer ↔ Peer (collaboration)
Client ↔ Service (consumption)
```

**Trust (via WITNESSING):**
```
Oracle → Task (validation)
Accumulator → Broadcaster (presence)
Peer → Peer (reputation)
```

### Termination Patterns

**BINDING Termination:**
- Revocation propagates to children
- Historical record preserved
- MRH cleanup on both entities

**PAIRING Termination:**
- Session closed explicitly
- Timeout after inactivity
- Performance history finalized

**WITNESSING:**
- No explicit termination
- Trust decays over time without refresh
- Historical attestations permanent

**BROADCAST:**
- No relationships to terminate
- Accumulator history may expire

## Interaction Rules Matrix

| From\To | Human | AI | Org | Role | Task | Resource | Device | Service | Oracle | Accumulator | Dictionary |
|---------|-------|----|-----|------|------|----------|--------|---------|--------|-------------|------------|
| **Human** | P,W | P,W | B,P | P | W | P,W | B,P,W | P,W | W | - | P,W |
| **AI** | P,W | P,W | B,P | P | W | P,W | B,P,W | P,W | W | - | P,W |
| **Organization** | B | B | P,W | B | B | B | B | B,P | W | - | B,P |
| **Role** | - | - | - | B | B | P | - | P | W | - | P |
| **Task** | - | - | - | - | W | P | - | P | W | - | P |
| **Resource** | - | - | - | - | - | W | P | P | W | - | - |
| **Device** | W | W | - | - | W | W | P,W | P,W | W | - | P |
| **Service** | - | - | - | - | - | - | - | P,W | W | - | P |
| **Oracle** | W | W | W | W | W | W | W | W | W | - | W |
| **Accumulator** | C | C | C | C | C | C | C | C | C | - | C |
| **Dictionary** | - | - | - | - | - | - | - | - | - | - | P |

**Legend:**
- B = BINDING (can bind)
- P = PAIRING (can pair)
- W = WITNESSING (can witness)
- C = BROADCAST collection (accumulator listens)
- \- = No direct interaction

## Best Practices

### 1. Relationship Selection
- Use BINDING for permanent hierarchies
- Use PAIRING for operational interactions
- Use WITNESSING for trust building
- Use BROADCAST for discovery

### 2. MRH Management
- Keep horizon_depth reasonable (default: 3)
- Prune stale relationships periodically
- Monitor MRH size for performance

### 3. Trust Building
- Seek diverse witnesses
- Accumulate attestations over time
- Verify witness reputation

### 4. Privacy Considerations
- BROADCAST is always public
- PAIRING can be private
- WITNESSING creates permanent record
- BINDING relationships visible in hierarchy

### 5. Performance Optimization
- Batch relationship updates
- Cache frequently accessed MRH data
- Use accumulators for lightweight validation
- Implement relationship timeouts

## Pairing Mode Decision Tree

```
Need to establish pairing?
├── High risk/value transaction?
│   └── YES → Use AUTHORIZED pairing
├── Legal/compliance requirements?
│   └── YES → Use WITNESSED pairing
├── Both entities well-trusted?
│   └── YES → Use DIRECT pairing
└── DEFAULT → Use WITNESSED pairing
```

## Common Patterns

### Pattern 1: Organization Onboarding
```
1. Create Organization LCT
2. BIND departments to organization
3. BIND roles to departments
4. Agents PAIR with roles (AUTHORIZED mode for executive roles)
5. WITNESS key operations
```

### Pattern 2: Service Discovery and Use
```
1. Service BROADCASTS capabilities
2. Accumulators record broadcasts
3. Client queries accumulators
4. Client initiates PAIRING
5. Service and client interact
6. Witnesses attest to service quality
```

### Pattern 3: Distributed Task Execution
```
1. Task created with requirements
2. Task BROADCASTS needs
3. Capable agents respond
4. PAIRING established with selected agent
5. Multiple oracles WITNESS execution
6. Results validated through attestations
```

### Pattern 4: Trust Network Formation
```
1. New entity joins network
2. Initial BROADCAST for discovery
3. Gradual WITNESSING accumulation
4. Trust score builds over time
5. Higher trust enables more PAIRINGS
6. Reputation becomes portable
```

## Security Considerations

### BINDING Security
- Verify parent authority before binding
- Implement revocation mechanisms
- Audit binding chains regularly

### PAIRING Security
- Validate context compatibility
- Enforce permission boundaries
- Monitor session activity

### WITNESSING Security
- Verify witness credentials
- Detect witness collusion
- Require witness diversity

### BROADCAST Security
- Sign all broadcasts
- Implement rate limiting
- Filter malicious content

## Troubleshooting

### Issue: Pairing Fails
- Check entity types compatibility
- Verify both entities' policies
- Ensure context alignment
- Validate signatures
- For witnessed: Check witness availability
- For authorized: Verify authority permissions

### Issue: Low Trust Score
- Increase witness diversity
- Ensure consistent broadcasting
- Verify attestation validity
- Check for negative witnesses

### Issue: MRH Overflow
- Increase horizon_depth carefully
- Implement relationship pruning
- Archive old relationships
- Optimize query patterns

### Issue: Accumulator Gaps
- Verify broadcast consistency
- Check network connectivity
- Ensure accumulator availability
- Implement redundant accumulators