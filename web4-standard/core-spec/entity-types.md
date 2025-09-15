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
| **Society** | Delegative entity with authority to issue citizenship and bind law | Nation, platform, network, organization | Delegative |
| **Organization** | Collective entities representing groups | Companies, DAOs, communities | Delegative |
| **Role** | First-class entities representing functions or positions | Citizen, Authority, Auditor, Witness | Delegative |
| **Task** | Specific work units or objectives | Data processing job, verification task | Responsive |
| **Resource** | Data, services, or assets | Databases, APIs, compute resources | Responsive |
| **Device** | Physical or virtual hardware | IoT sensors, servers, vehicles | Responsive/Agentic |
| **Service** | Software services and applications | Web services, microservices | Responsive |
| **Oracle** | External data providers | Price feeds, Law Oracle, weather data | Responsive/Delegative |
| **Accumulator** | Broadcast listeners and recorders | Presence validators, history indexers | Responsive |
| **Dictionary** | Semantic bridges between domains | Medical-legal translator, tech-common interpreter | Responsive |
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

### 3.1 The Citizen Role: Universal Birth Certificate

#### Fundamental Principle
**Every entity begins with the "citizen" role** - a broad role representing participation in its general context. This first citizen role pairing, made at LCT creation, serves as the entity's **birth certificate** in Web4.

#### Citizen Role Characteristics
- **Universal**: Every entity has citizen role in some context
- **Contextual**: Human citizen of nation, AI citizen of platform, device citizen of network
- **Foundational**: Provides base rights and responsibilities
- **Immutable**: Birth certificate pairing cannot be revoked
- **Inherited**: Carries context from creating/binding entity

#### Birth Certificate Structure (SAL-compliant)
```json
{
  "@context": ["https://web4.io/contexts/sal.jsonld"],
  "type": "Web4BirthCertificate",
  "entity": "lct:web4:entity:...",
  "citizenRole": "lct:web4:role:citizen:...",
  "society": "lct:web4:society:...",
  "lawOracle": "lct:web4:oracle:law:...",
  "lawVersion": "v1.2.0",
  "birthTimestamp": "2025-09-14T12:00:00Z",
  "witnesses": ["lct:web4:witness1", "lct:web4:witness2"],
  "genesisBlock": "block:12345",
  "initialRights": ["exist", "interact", "accumulate_reputation"],
  "initialResponsibilities": ["abide_law", "respect_quorum"],
  "ledgerProof": "hash:sha256:...",
  "parentEntity": "lct:web4:parent:..."
}
```

### 3.2 The Role Revolution

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

### 3.3 Role Hierarchy: From Citizen to Specialist

#### Role Evolution Path
Entities typically progress through role hierarchies:

1. **Citizen** (birth) → Base participation rights
2. **Participant** → Active engagement in specific domain
3. **Contributor** → Proven value creation
4. **Specialist** → Domain expertise roles (surgeon, engineer, analyst)
5. **Authority** → Governance and oversight roles

#### Role-Agent Pairing

When an agent takes on a role beyond citizen:

1. **Prerequisite Check**: Verify citizen role exists (birth certificate)
2. **Pairing Established**: Agent's LCT pairs with new Role's LCT
3. **Context Transfer**: Role's permissions and scope transfer to agent
4. **Performance Tracking**: Actions tracked against both LCTs
5. **Reputation Impact**: Performance affects both reputations
6. **Pairing Termination**: Clean handoff when role assignment ends

Note: Citizen role pairing is permanent and cannot be terminated.

This creates a transparent, reputation-based labor market where:
- Roles with strong reputations attract capable agents
- Agents with proven performance access better roles
- Performance history is verifiable and portable

## 4. SAL-Specific Roles

### 4.1 Society Role
A **Society** is a delegative entity with special capabilities:
- Issues citizenship (birth certificates) to new entities
- Maintains a Law Oracle that publishes machine-readable laws
- Operates or binds to an immutable ledger for record-keeping
- Can be a citizen of other societies (fractal membership)

### 4.2 Authority Role
The **Authority** role within a society:
- Scoped delegation powers (finance, safety, membership)
- Can create sub-authorities with limited scope
- Must publish scope and limits as machine-readable policy
- Emergency powers if defined by law

### 4.3 Law Oracle Role
A specialized oracle that:
- Publishes versioned law datasets (norms, procedures, interpretations)
- Signs interpretations and precedents
- Answers compliance queries with proof transcripts
- Maps laws to R6 action grammar

### 4.4 Witness Role (Enhanced)
Beyond basic witnessing:
- Co-signs ledger entries for SAL-critical events
- Maintains immutable record via timestamping
- Participates in quorum requirements
- Provides availability proofs

### 4.5 Auditor Role
Invokable role with special powers:
- Traverses society's MRH graph
- Validates and adjusts T3/V3 tensors of direct citizens
- Must provide evidence-based audit transcripts
- Adjustments written to immutable ledger with witness quorum

#### Auditor Adjustment Policy
```json
{
  "type": "Web4AuditRequest",
  "society": "lct:web4:society:...",
  "targets": ["lct:web4:citizen:..."],
  "scope": ["context:data_analysis"],
  "basis": ["hash:evidence1", "hash:evidence2"],
  "proposed": {
    "t3": {"temperament": -0.02},
    "v3": {"veracity": -0.03}
  },
  "rateLimits": "per_law_oracle",
  "appealPath": "defined_by_law"
}
```

## 5. Entity Lifecycle

### 5.1 Entity Creation and Birth Certificate (SAL-compliant)

When an entity enters Web4:

1. **Society Selection**: Entity must be born into a society context
2. **LCT Generation**: Unique LCT created and cryptographically bound
3. **Entity Type Declaration**: Immutable type assignment
4. **Citizen Role Pairing**: Automatic pairing with society's citizen role
5. **Birth Certificate Recording**: Written to society's immutable ledger
6. **Witness Quorum**: Required witnesses co-sign the birth event
7. **Law Oracle Binding**: Current law version recorded in certificate
8. **Initial Binding**: For delegative entities, binding to parent/creator
9. **MRH Initialization**: Citizen role pre-populated in paired array
10. **Ledger Proof**: Inclusion proof from immutable record

#### Birth Certificate Process
```python
def create_entity_with_birth_certificate(entity_type, context, parent=None):
    # Generate entity LCT
    entity_lct = generate_lct(entity_type)
    
    # Determine citizen role for context
    citizen_role = get_citizen_role_for_context(context)
    
    # Create birth certificate pairing
    birth_cert = {
        "entity_lct": entity_lct.id,
        "citizen_role": citizen_role.id,
        "context": context,
        "birth_timestamp": now(),
        "parent_entity": parent.id if parent else None,
        "birth_witness": collect_witnesses()
    }
    
    # Establish permanent citizen pairing
    entity_lct.mrh.paired.append({
        "lct_id": citizen_role.id,
        "pairing_type": "birth_certificate",
        "permanent": True,
        "timestamp": birth_cert["birth_timestamp"]
    })
    
    # Record in blockchain
    record_birth_certificate(birth_cert)
    
    return entity_lct, birth_cert
```

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

#### Citizen Role (Special Case)
- **Automatically pairs**: With every new entity at creation
- **Cannot be revoked**: Permanent birth certificate pairing
- **Provides base rights**: Exist, interact, accumulate reputation
- **Context-specific**: Nation-citizen, platform-citizen, network-citizen

#### Other Roles
- **Can be bound to**: Organizations, parent roles
- **Can bind**: Sub-roles, specific tasks
- **Can pair with**: Agents (human or AI) to perform the role
- **Can witness**: Performance of paired agents
- **Cannot**: Act autonomously without a paired agent
- **Require**: Citizen role as prerequisite

## 6. Implementation Requirements

### 6.1 Entity Type Validation

Implementations MUST:
- Validate entity type at LCT creation
- Enforce interaction rules based on entity types
- Prevent invalid mode behaviors (e.g., responsive entity initiating)

### 6.2 Role Management

Implementations MUST:
- Support role LCTs as first-class entities
- Automatically create citizen role pairing at entity birth
- Maintain immutable birth certificate records
- Track performance history within role LCTs
- Enable role-agent pairing with proper permission transfer
- Calculate reputation impacts for both role and agent
- Verify citizen role exists before other role assignments

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

## 10. Citizen Role Examples

### 10.1 Context-Specific Citizens

Different contexts define different citizen roles:

| Context | Citizen Role | Base Rights | Base Responsibilities |
|---------|--------------|-------------|----------------------|
| Nation | National Citizen | Vote, access services | Pay taxes, follow laws |
| Platform | Platform Citizen | Create content, interact | Follow ToS, respect others |
| Network | Network Citizen | Send/receive data | Maintain node, relay traffic |
| Organization | Member Citizen | Participate, propose | Contribute, uphold values |
| Ecosystem | Ecosystem Citizen | Use resources | Sustain balance |

### 10.2 Birth Certificate as Proof of Origin

The birth certificate provides:
- **Provenance**: Where and when entity originated
- **Legitimacy**: Proper creation process followed
- **Context**: Initial environment and constraints
- **Inheritance**: Rights/responsibilities from parent
- **Witnesses**: Who validated the birth

## 11. Future Extensions

Potential entity types under consideration:
- **Contract**: Smart contracts as entities
- **Content**: Documents/media with their own LCTs
- **Workflow**: Process definitions as entities
- **Community**: Collective intelligence entities
- **Citizen Subtypes**: Specialized citizen roles for different contexts