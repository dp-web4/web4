# Web4 Entity Types Specification

This document defines the complete taxonomy of entity types in Web4 and their behavioral characteristics. Every entity in Web4 has an LCT (Linked Context Token) that serves as its unforgeable footprint in the digital realm.

## 1. Core Concept: Entities with Presence

In Web4, an **entity** is anything that can manifest presence—anything that can be paired with an LCT. This revolutionary expansion moves beyond traditional notions of users or accounts to recognize that many things have presence and agency in the information age.

## 2. Entity Type Taxonomy

### 2.1 Primary Entity Types

The following entity types are recognized in Web4:

| Entity Type | Description | Examples | Mode |
|-------------|-------------|----------|------|
| **Human** | Individual persons participating in Web4 | End users, developers, administrators | Agentic |
| **AI** | Artificial intelligence agents with autonomous capabilities | Chatbots, analysis engines, autonomous agents | Agentic |
| **Organization** | Collective entities representing groups | Companies, DAOs, communities | Delegative |
| **Role** | First-class entities representing functions or positions | Developer, Auditor, Energy Provider | Delegative |
| **Task** | Specific work units or objectives | Data processing job, verification task | Responsive |
| **Resource** | Data, services, or assets | Databases, APIs, compute resources | Responsive |
| **Device** | Physical or virtual hardware | IoT sensors, servers, vehicles | Responsive/Agentic |
| **Service** | Software services and applications | Web services, microservices | Responsive |
| **Oracle** | External data providers | Price feeds, weather data, event confirmers | Responsive |
| **Accumulator** | Broadcast listeners and recorders | Presence validators, history indexers | Responsive |
| **Hybrid** | Entities combining multiple types | Human-AI teams, cyborg systems | Mixed |

### 2.2 Entity Behavioral Modes

Entities exhibit three primary modes of existence:

#### Agentic Entities
- **Definition**: Entities that take initiative and make autonomous decisions
- **Characteristics**: Self-directed, goal-seeking, adaptive
- **Examples**: Humans, AI agents, autonomous devices
- **LCT Behavior**: Actively initiate bindings and pairings

#### Responsive Entities  
- **Definition**: Entities that react to external stimuli predictably
- **Characteristics**: Reactive, deterministic, state-based
- **Examples**: Sensors, APIs, databases, tasks
- **LCT Behavior**: Accept pairings but don't initiate

#### Delegative Entities
- **Definition**: Entities that authorize others to act on their behalf
- **Characteristics**: Define scope, grant permissions, establish boundaries
- **Examples**: Organizations, governance structures, **roles**
- **LCT Behavior**: Create authorization chains through binding

## 3. Roles as First-Class Entities

One of Web4's most radical innovations is treating roles not as labels but as entities with their own presence and LCTs.

### 3.1 The Role Revolution

Traditional roles are static job descriptions. In Web4, a role becomes a living entity that:

- **Defines** its own requirements and boundaries
- **Accumulates** history of who has filled it  
- **Maintains** reputation based on past performance
- **Evolves** based on changing needs and patterns

### 3.2 Role LCT Structure

Each Role LCT contains:

```json
{
  "lct_id": "lct:web4:role:...",
  "entity_type": "role",
  "binding": {
    "entity_type": "role",
    "public_key": "mb64:...",
    "created_at": "2025-01-11T15:00:00Z",
    "binding_proof": "cose:..."
  },
  "role_definition": {
    "purpose": "What this role exists to accomplish",
    "permissions": ["capability:read", "capability:write", "capability:audit"],
    "requirements": {
      "knowledge": ["domain expertise", "tool proficiency"],
      "capabilities": ["analysis", "reporting"],
      "temperament": ["reliable", "detail-oriented"]
    },
    "scope": {
      "domain": "specific area of responsibility",
      "boundaries": "limits of authority"
    }
  },
  "performance_history": [
    {
      "performer_lct": "lct:web4:agent:...",
      "period": {"start": "...", "end": "..."},
      "t3_scores": {...},
      "v3_outcomes": {...},
      "reputation_impact": 0.85
    }
  ],
  "mrh": {
    "bound": [], // Organizations or parent roles
    "paired": [], // Current agents performing this role
    "witnessing": [] // Performance validators
  }
}
```

### 3.3 Role-Agent Pairing

When an agent (human or AI) takes on a role:

1. **Pairing Established**: Agent's LCT pairs with Role's LCT
2. **Context Transfer**: Role's permissions and scope transfer to agent
3. **Performance Tracking**: Actions tracked against both LCTs
4. **Reputation Impact**: Performance affects both reputations
5. **Pairing Termination**: Clean handoff when role assignment ends

This creates a transparent, reputation-based labor market where:
- Roles with strong reputations attract capable agents
- Agents with proven performance access better roles
- Performance history is verifiable and portable

## 4. Entity Lifecycle

### 4.1 Entity Creation

When an entity enters Web4:

1. **LCT Generation**: Unique LCT created and cryptographically bound
2. **Entity Type Declaration**: Immutable type assignment
3. **Initial Binding**: For delegative entities, binding to parent/creator
4. **MRH Initialization**: Empty relationship arrays ready for population

### 4.2 Entity Evolution

Throughout its existence:

- **Relationship Building**: Accumulating bindings, pairings, witness attestations
- **Reputation Development**: T3/V3 tensors evolve through interactions
- **Context Expansion**: MRH grows as entity engages with others
- **Role Performance**: For agents, building history across multiple roles

### 4.3 Entity Termination

When an entity ceases to exist:

- **LCT Marking**: Status changed to "void" or "slashed"
- **Relationship Cleanup**: Removed from all MRH arrays
- **Historical Preservation**: Past interactions remain in ledger
- **Reputation Finalization**: Final state preserved for reference

## 5. Entity Interactions

### 5.1 Valid Interaction Patterns

Not all entity types can interact in all ways:

| Interaction | Valid Between | Example |
|-------------|---------------|---------|
| **Binding** | Parent → Child entities | Organization → Role, Role → Task |
| **Pairing** | Peer entities | Human ↔ AI, Agent ↔ Role |
| **Witnessing** | Any → Any | Oracle → Task, AI → Human |
| **Delegation** | Delegative → Agentic | Role → Human, Organization → AI |

### 5.2 Role-Specific Interactions

Roles have unique interaction patterns:

- **Can be bound to**: Organizations, parent roles
- **Can bind**: Sub-roles, specific tasks
- **Can pair with**: Agents (human or AI) to perform the role
- **Can witness**: Performance of paired agents
- **Cannot**: Act autonomously without a paired agent

## 6. Implementation Requirements

### 6.1 Entity Type Validation

Implementations MUST:
- Validate entity type at LCT creation
- Enforce interaction rules based on entity types
- Prevent invalid mode behaviors (e.g., responsive entity initiating)

### 6.2 Role Management

Implementations MUST:
- Support role LCTs as first-class entities
- Track performance history within role LCTs
- Enable role-agent pairing with proper permission transfer
- Calculate reputation impacts for both role and agent

### 6.3 Entity Discovery

Implementations SHOULD:
- Provide entity type filtering in discovery
- Support role matching based on requirements
- Enable reputation-based sorting
- Facilitate capability-requirement matching

## 7. Security Considerations

### 7.1 Entity Type Immutability

Once declared, an entity's type MUST NOT change. This prevents:
- Privilege escalation through type mutation
- Bypassing interaction restrictions
- Reputation gaming through type switching

### 7.2 Role Authority Limits

Role permissions MUST be:
- Clearly scoped and bounded
- Revocable by binding authority
- Tracked in all delegated actions
- Limited by parent entity permissions

## 8. Privacy Considerations

- Entity types themselves are public
- Role definitions are public to enable matching
- Performance histories may be selectively disclosed
- Agent-role pairings visible only to relevant parties

## 9. Specialized Entity: Accumulators

### 9.1 Accumulator Role
Accumulators are specialized responsive entities that provide passive witnessing services:

- **Listen** to public broadcasts without acknowledgment
- **Record** broadcast events with cryptographic integrity
- **Index** by broadcaster, type, timestamp
- **Query** interface for presence validation

### 9.2 Accumulator LCT Structure
```json
{
  "entity_type": "accumulator",
  "accumulator_config": {
    "listen_scope": ["ANNOUNCE", "HEARTBEAT", "CAPABILITY"],
    "retention_period": 2592000,  // 30 days in seconds
    "index_strategy": "entity_time_type",
    "query_interface": "web4://accumulator/query",
    "storage_commitment": "10GB"
  },
  "statistics": {
    "broadcasts_recorded": 1547823,
    "unique_entities": 4521,
    "queries_served": 89234,
    "uptime_percentage": 99.97
  }
}
```

### 9.3 Accumulator Trust
Accumulator reliability measured by:
- Uptime and availability
- Query response accuracy
- Storage commitment honoring
- Non-selective recording (no censorship)

## 10. Future Extensions

Potential entity types under consideration:
- **Contract**: Smart contracts as entities
- **Content**: Documents/media with their own LCTs
- **Workflow**: Process definitions as entities
- **Community**: Collective intelligence entities