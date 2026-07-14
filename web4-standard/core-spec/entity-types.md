# Web4 Entity Types Specification

This document defines the complete taxonomy of entity types in Web4 and their behavioral characteristics. Every entity in Web4 has an LCT (Linked Context Token) that serves as its verifiable footprint in the digital realm.

## Notation

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) when, and only when, they appear in all capitals, as shown here.

## 1. Core Concept: Entities with Presence

In Web4, an **entity** is anything that can manifest presence—anything that can be paired with an LCT. This revolutionary expansion moves beyond traditional notions of users or accounts to recognize that many things have presence and agency in the information age.

## 2. Entity Type Taxonomy

### 2.1 Primary Entity Types

The following entity types are recognized in Web4:

| Entity Type | Description | Examples | Mode | Energy Pattern |
|-------------|-------------|----------|------|----------------|
| **Human** | Individual persons participating in Web4 | End users, developers, administrators | Agentic | Active |
| **AI** | Artificial intelligence agents with autonomous capabilities | Chatbots, analysis engines, autonomous agents | Agentic | Active |
| **Society** | Delegative entity with authority to issue citizenship and bind law | Nation, platform, network, organization | Delegative | Active (via citizens) |
| **Organization** | Collective entities representing groups | Companies, DAOs, communities | Delegative | Active (via members) |
| **Role** | First-class entities representing functions or positions | Citizen, Authority, Auditor, Witness | Delegative | Active (via paired agents) |
| **Task** | Specific work units or objectives | Data processing job, verification task | Responsive | Active (when R6-capable) |
| **Resource** | Data, services, or assets | Databases, APIs, compute resources | Responsive | Passive |
| **Device** | Physical or virtual hardware | IoT sensors, servers, vehicles | Responsive/Agentic | Active or Passive |
| **Service** | Software services and applications | Web services, microservices | Responsive | Active (can process R6) |
| **Oracle** | External data providers | Price feeds, Law Oracle, weather data | Responsive/Delegative | Active (delivers results) |
| **Accumulator** | Broadcast listeners and recorders | Presence validators, history indexers | Responsive | Passive (stores data) |
| **Dictionary** | Living semantic bridges managing compression-trust | Medical-legal translator, AI model bridges, cultural interpreters | Responsive/Agentic | Active (translates) |
| **Hybrid** | Entities combining multiple types | Human-AI teams, cyborg systems | Agentic/Responsive/Delegative | Active |
| **Policy** | Governance rules as living entities with IRP-backed evaluation | Enterprise safety rules, access policies, compliance frameworks | Responsive/Delegative | Active |
| **Infrastructure** | Physical passive resources | Buildings, roads, machinery, tools | None | Passive |

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

### 2.3 Energy Metabolism Patterns

In addition to behavioral modes, entities are classified by their **energy metabolism** in R6 transactions:

#### Active Resources
- **Definition**: Entities capable of expending energy to produce new resources (ATP discharge capable)
- **Characteristics**: Can process R6 transactions, deliver results, earn reputation
- **R6 Capability**: Can complete full R6 cycle autonomously or through delegation
- **Energy Flow**:
  ```
  ATP (charged) → R6 Work → ADP (discharged)
      ↓
  ADP returns to pool
      ↓
  Reputation updates propagate up fractal chain
      ↓
  ADP available for recharging
  ```
- **Examples**:
  - Agentic entities (Human, AI, autonomous Device)
  - Delegative entities when filled (Organization via members, Role via paired agent)
  - R6-capable Responsive entities (Oracle, Dictionary, Service)
- **Key Property**: ADP returns to pool, enabling reputation updates

#### Passive Resources
- **Definition**: Infrastructure utilized by Active Resources but incapable of R6 processing
- **Characteristics**: Cannot deliver results, requires maintenance energy, reputation from utilization
- **R6 Capability**: Cannot process R6 transactions
- **Energy Flow**:
  ```
  ATP (charged) → Maintenance → ADP (discharged)
      ↓
  ADP CONSUMED (permanently, via maintenance)
      ↓
  NO reputation updates
      ↓
  Only utilization metrics updated
  ```
- **Examples**:
  - Infrastructure (buildings, roads, machinery)
  - Storage resources (databases, file systems)
  - Non-autonomous devices (sensors, actuators)
  - Accumulators (passive data collection)
- **Key Property**: ADP consumed (permanently destroyed via maintenance), no reputation updates. This routine maintenance discharge is distinct from the punitive, authority-executed *slashing* of `atp-adp-cycle.md` §2.4 (evidence-gated destruction of ATP for law violations).
- **Reputation Metric**: Utilization frequency × effectiveness by Active Resources

#### The Efficiency Forcing Function

This creates automatic optimization pressure:

**Active Resources compete on:**
- Quality of results delivered
- Efficiency of energy use
- Reputation from successful R6 completions

**Passive Resources compete on:**
- How frequently Active Resources utilize them
- How effectively they support R6 transactions
- Energy cost vs. value provided

**Natural Selection Emerges:**
- Well-utilized infrastructure gets maintained (receives ATP allocation)
- Disused infrastructure degrades (no ATP allocation)
- System self-optimizes without governance

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

#### Birth Certificate Structure (SAL-aligned superset)
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
  "witnesses": ["lct:web4:witness:1", "lct:web4:witness:2"],
  "genesisBlock": "block:12345",
  "rights": ["presence", "interact", "accumulate_reputation"],
  "obligations": ["abide_law", "respect_quorum"],
  "ledgerProof": "hash:sha256:...",
  "parentEntity": "lct:web4:parent:..."
}
```

> **Note (field provenance)**: The fields `entity` through `obligations` match the
> canonical `Web4BirthCertificate` defined in `web4-society-authority-law.md` §2.2 —
> in particular the rights/obligations keys are `rights`/`obligations` (SAL canonical),
> not `initialRights`/`initialResponsibilities`. `ledgerProof` and `parentEntity` are
> entity-types **extensions** beyond the SAL §2.2 canonical set; whether they belong in
> the canonical certificate is an **open design question** (tracked as C23-H1, "canonical
> BirthCertificate shape"). This structure is therefore a SAL-aligned *superset*, not a
> verbatim copy of SAL §2.2.

### 3.2 The Role Revolution

Traditional roles are static job descriptions. In Web4, a role becomes a living entity that:

- **Defines** its own requirements and boundaries
- **Accumulates** history of who has filled it  
- **Maintains** reputation based on past performance
- **Evolves** based on changing needs and patterns

### 3.3 Role LCT Structure

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

### 3.4 Role Hierarchy: From Citizen to Specialist

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

### 3.5 Example Roles per Entity Type

The companion `society-roles.md` specification enumerates society roles (base-mandatory, context-mandatory, optional) with example entities for each. This subsection provides the symmetric dual: for each primary entity type, example roles that entity type can fill. The mapping is illustrative — any entity type that meets a role's behavioral requirements MAY fill that role.

| Entity Type | Example Roles It Can Fill |
|---|---|
| **Human** | Sovereign, Treasurer, Administrator, Archivist, Policy-Entity, Citizen, Witness, Auditor, Mediator, Diplomat, Recovery-Authority, Architect, Agent, Client |
| **AI** | Policy-Entity, Treasurer, Administrator, Archivist, Validator, Witness, Auditor, Mediator, Architect, Oracle, Dictionary, Agent |
| **Society** | Sovereign (in federation), Law Oracle (specialized law-publishing society), Treasurer (a treasury-services society), Witness (a witness-services society), Mediator (an arbitration society), Governance-Council, Recovery-Authority |
| **Organization** | Sovereign, Treasurer, Administrator, Membership-Authority, Governance-Council, Auditor, Steward |
| **Role** | (Role itself is an entity type; roles are first-class. Roles fill roles in a degenerate sense — see §3.2, "The Role Revolution," above.) |
| **Task** | (Tasks are work units, not role-fillers; they are operated on by roles, not held by them.) |
| **Resource** | (Resources are operated on by roles; do not fill roles themselves.) |
| **Device** | Validator (hardware-attested), Oracle (sensor-based), Recovery-Authority (TPM-bound recovery), Witness (attestation device) |
| **Service** | Policy-Entity (rules engine), Validator, Administrator, Oracle, Dictionary, Archivist |
| **Oracle** | Law Oracle, Policy-Entity (when policy is itself an oracle), Validator, Witness (specialized attestation oracle) |
| **Accumulator** | Archivist (specialized for accumulation), Witness (broadcast observer) |
| **Dictionary** | Dictionary role, Policy-Entity (when policy involves semantic translation) |
| **Hybrid** | Any role (the strength of hybrids is role flexibility — Human-AI teams can fill almost any role with complementary strengths) |
| **Policy** | Policy-Entity (the canonical filling), Validator, Mediator |
| **Infrastructure** | (Infrastructure is passive; supports role-filling entities but does not fill roles itself.) |

Where an entity type appears for multiple roles, the choice of which role to use it for is per-society design. A single Human entity might fill Sovereign + Treasurer + Archivist simultaneously in a small society, with separate role-LCT pairings making the accountability explicit per role.

For the role-LCT pairing mechanics see §3.4, "Role-Agent Pairing," above; for the LCT structures these pairings reference see `LCT-linked-context-token.md`; for the full role taxonomy with audit implications see `society-roles.md`.

## 4. SAL-Specific Roles

> **See also**: `society-roles.md` for the full society-roles taxonomy (base-mandatory, context-mandatory, optional) with fractal-composability semantics. The roles enumerated below are the SAL-specific subset; the broader taxonomy in `society-roles.md` includes additional functional roles (Policy-Entity, Treasurer, Administrator, Archivist, etc.) that are base-mandatory for every Web4 society.
>
> **Note (subsection count vs role count; SAL roles vs base-mandatory roles)**: §4 has eight subsections, but §4.1 (Society) describes an *entity-type context* (§2.1), **not** a role an entity fills — so there are **seven** SAL-specific roles below (Authority, Law Oracle, Witness, Auditor, Agent, Client, Effector) plus the Society context that hosts them. These seven roles are a *different set* from the **base-mandatory** roles defined in `society-roles.md` §2 (Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen) — the two sets overlap only on **Law Oracle**. The canonical home of the base-mandatory role list is **`society-roles.md` §2** (resolved per `SOCIETY_SPECIFICATION.md` §1.2.5 / C51, which attributes the base-mandatory roles to that section); the remaining open item is only the role-*name* reconciliation (SAL "Authority Role" vs society-roles "Sovereign"), not the list's home.

### 4.1 Society (entity-type capabilities)
**Society** is an *entity type* (§2.1), not a role an entity fills — it is included here because the SAL-specific roles below are hosted *within* a society and depend on these capabilities. A **Society** is a delegative entity with:
- Issues citizenship (birth certificates) to new entities
- Maintains a Law Oracle that publishes machine-readable laws
- Operates or binds to an immutable ledger for record-keeping
- Can be a citizen of other societies (fractal membership)

The society's apex *role* (the one an entity actually fills) is the **Authority Role** / "Sovereign" — see §4.2.

### 4.2 Authority Role
The **Authority** role within a society:
- Scoped delegation powers (finance, safety, membership)
- Can create sub-authorities with limited scope
- Must publish scope and limits as machine-readable policy
- Emergency powers if defined by law

> **Note (scope)**: "Authority Role" as described here denotes a **scoped** delegation
> (finance/safety/membership) operating *beneath* the society's root authority — the
> sub-authority position in SAL's delegation tree (`web4-society-authority-law.md` §3.3,
> `authorityRole web4:delegatesTo subAuthorityRole`). It is **not** the root of the
> delegation tree; SAL §3.1 names the *root* "Authority Role" LCT, and `society-roles.md`
> §2.1 names the society's final/root authority **"Sovereign"**. The canonical *home* of
> the base-mandatory role list is settled — `society-roles.md` §2, per
> `SOCIETY_SPECIFICATION.md` §1.2.5 / C51 (formerly C25-H1) — so what remains open is only
> reconciling the role *name* across these specs (SAL "Authority Role" vs society-roles
> "Sovereign"); this note fixes only the scoped-vs-root reading.

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
- Can validate agency delegations and their execution

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

### 4.6 Agent Role (AGY)
Specialized role for delegated authority:
- Acts on behalf of a Client entity within scoped constraints
- Requires proof-of-agency for all actions
- Cannot impersonate Client unless explicitly allowed
- Accrues own T3/V3 for execution quality
- Bound by grant scope, caps, and temporal limits

### 4.7 Client Role (AGY)
Principal entity in agency delegation:
- Delegates authority to Agent entities
- Defines scope, caps, and constraints for delegation
- Can revoke grants immediately
- Shares reduced/indirect liability per law policy
- Maintains ultimate responsibility for delegated actions

#### Agency Grant Structure (AGY)
```json
{
  "type": "Web4AgencyGrant",
  "grantId": "agy:...",
  "client": "lct:web4:entity:CLIENT",
  "agent": "lct:web4:entity:AGENT",
  "society": "lct:web4:society:ROOT",
  "lawHash": "sha256-...",
  "scope": {
    "contexts": ["finance:payments", "docs:sign"],
    "mrhSelectors": ["web4://org/finance/*"],
    "r6Caps": {
      "rules": ["LAW-ATP-LIMIT"],
      "resourceCaps": {"max_atp": 25},
      "roleImpersonation": false
    },
    "methods": ["create", "update", "approve"],
    "delegatable": false,
    "witnessLevel": 2,
    "trustCaps": {
      "t3.min": {"temperament": 0.7},
      "v3.floor": {"veracity": 0.9}
    }
  },
  "duration": {
    "notBefore": "2025-09-15T00:00:00Z",
    "expiresAt": "2025-12-31T23:59:59Z"
  },
  "witnesses": ["lct:web4:witness:A"],
  "signatures": [...]
}
```

### 4.8 Effector Role

The **Effector** is the Auditor's (§4.5) response-side sibling. Where the
Auditor operates on the *recognition* side — validating and adjusting T3/V3
tensors — the Effector operates on the *response* side: it enacts the
society's graded responses to witnessed violations, acts that interfere with a
target's ability to act. It is the named role dp's ratified framing requires:
*kinetic authority is a defined role within society, filled by actor entities
in accordance with law; it is always R7, and R7 is definitive as to all the
particulars.*

*Provenance (informative):* this role lands W4IP N2
(`proposals/W4IP-DRAFT-2026-07-13-governance-immune-enforcement.md`) against
the response vocabulary ratified in `hub-law-schema.md` ("Response
vocabulary", web4 `87377c3`). The W4IP draft itself remains non-normative;
this section is the normative expression of its N2 item.

Invokable role with special powers:
- Enacts only the ratified response vocabulary of `hub-law-schema.md`:
  `notice | quarantine | correct | rehabilitate`, plus the kinetic class
  (`slash | suspend | revoke | terminate | halt`) — which remains
  **parse-don't-enact** per that section: an Effector MUST NOT enact a
  kinetic rung until that rung's enactment is individually ratified and
  implemented
- Acts **only via R7**: every enactment's Reference binds the recognition
  evidence that licenses it — witnessed deltas under the Coercive/Extractive
  Behavior Rules category (`reputation-computation.md` §4). No recognition
  evidence, no act.
- Its own acts pass the same gate as anyone's — **RWOA + S + V + F** as
  specified in `hub-law-schema.md` (F-a forfeiture predicate, F-b
  proportionality bound). An effector acting without evidence fails its own
  gate; autoimmunity is unauthorized action, already prohibited.
- Reputation-bearing: accrues own T3/V3 for enactment quality
- Enactments written to immutable ledger with witness quorum
- Reversible rungs carry appeal path and adjudication/cool-down bounds
  (`appealPath: defined_by_law`)
- Fractally delegable through the SAL delegation tree
  (`web4-society-authority-law.md` §3.3, §5.6)

Web4 defines the role's *shape*; who fills it, its thresholds, and when it
acts are each society's law — content, not mechanism.

#### Effector Enactment Request
```json
{
  "type": "Web4EffectorEnactment",
  "society": "lct:web4:society:...",
  "target": "lct:web4:citizen:...",
  "response": "quarantine",
  "consequenceClass": "reversible",
  "recognitionEvidence": ["hash:delta1", "hash:delta2"],
  "lawRule": "QUARANTINE-ON-AGENCY-OVERRIDE",
  "proportionalityBasis": "hash:violation-magnitude-assessment",
  "witnesses": ["lct:web4:witness:A"],
  "rateLimits": "per_law_oracle",
  "appealPath": "defined_by_law"
}
```

`recognitionEvidence` satisfies F-a (the R7 Reference binding);
`proportionalityBasis` records the F-b bound; `lawRule` cites the `responses:`
rule (`hub-law-schema.md` YAML surface) licensing the enactment.

## 5. Entity Lifecycle

### 5.1 Entity Creation and Birth Certificate

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

> **Note**: The pseudocode below is **illustrative and abbreviated** — it sketches the
> creation flow, not the normative on-ledger certificate shape. The `birth_cert` dict
> shows only a subset of fields and omits SAL-required elements (law-oracle digest,
> genesis block reference, rights/obligations). For the **normative** certificate
> structure see §3.1 above and the canonical `Web4BirthCertificate` in
> `web4-society-authority-law.md` §2.1–§2.2.

```python
def create_entity_with_birth_certificate(entity_type, context, parent=None):
    # Generate entity LCT
    entity_lct = generate_lct(entity_type)
    
    # Determine citizen role for context
    citizen_role = get_citizen_role_for_context(context)
    
    # Create birth certificate pairing (illustrative subset — see §3.1 / SAL §2.2 for normative shape)
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
    
    # Record in immutable ledger
    record_birth_certificate(birth_cert)
    
    return entity_lct, birth_cert
```

### 5.2 Entity Evolution

Throughout its existence:

- **Relationship Building**: Accumulating bindings, pairings, witness attestations
- **Reputation Development**: T3/V3 tensors evolve through interactions
- **Context Expansion**: MRH grows as entity engages with others
- **Role Performance**: For agents, building history across multiple roles

### 5.3 Entity Termination

When an entity ceases to exist:

- **LCT Marking**: Status changed to "void" or "slashed"
- **Relationship Cleanup**: Removed from all MRH arrays
- **Historical Preservation**: Past interactions remain in ledger
- **Reputation Finalization**: Final state preserved for reference

## 6. Entity Interactions

### 6.1 Valid Interaction Patterns

Not all entity types can interact in all ways:

| Interaction | Valid Between | Example |
|-------------|---------------|---------|
| **Binding** | Parent → Child entities | Organization → Role, Role → Task |
| **Pairing** | Peer entities | Human ↔ AI, Agent ↔ Role |
| **Witnessing** | Any → Any | Oracle → Task, AI → Human |
| **Delegation** | Delegative → Agentic | Role → Human, Organization → AI |

### 6.2 Role-Specific Interactions

Roles have unique interaction patterns:

#### Citizen Role (Special Case)
- **Automatically pairs**: With every new entity at creation
- **Cannot be revoked**: Permanent birth certificate pairing
- **Provides base rights**: Presence, interact, accumulate reputation
- **Context-specific**: Nation-citizen, platform-citizen, network-citizen

#### Other Roles
- **Can be bound to**: Organizations, parent roles
- **Can bind**: Sub-roles, specific tasks
- **Can pair with**: Agents (human or AI) to perform the role
- **Can witness**: Performance of paired agents
- **Cannot**: Act autonomously without a paired agent
- **Require**: Citizen role as prerequisite

## 7. Implementation Requirements

### 7.1 Entity Type Validation

Implementations MUST:
- Validate entity type at LCT creation
- Enforce interaction rules based on entity types
- Prevent invalid mode behaviors (e.g., responsive entity initiating)

### 7.2 Role Management

Implementations MUST:
- Support role LCTs as first-class entities
- Automatically create citizen role pairing at entity birth
- Maintain immutable birth certificate records
- Track performance history within role LCTs
- Enable role-agent pairing with proper permission transfer
- Calculate reputation impacts for both role and agent
- Verify citizen role exists before other role assignments

### 7.3 Entity Discovery

Implementations SHOULD:
- Provide entity type filtering in discovery
- Support role matching based on requirements
- Enable reputation-based sorting
- Facilitate capability-requirement matching

## 8. Security Considerations

### 8.1 Entity Type Immutability

Once declared, an entity's type MUST NOT change. This prevents:
- Privilege escalation through type mutation
- Bypassing interaction restrictions
- Reputation gaming through type switching

### 8.2 Role Authority Limits

Role permissions MUST be:
- Clearly scoped and bounded
- Revocable by binding authority
- Tracked in all delegated actions
- Limited by parent entity permissions

## 9. Privacy Considerations

- Entity types themselves are public
- Role definitions are public to enable matching
- Performance histories may be selectively disclosed
- Agent-role pairings visible only to relevant parties

## 10. Specialized Entity: Dictionary

### 10.1 Dictionary Role
Dictionaries are first-class entities that serve as living semantic bridges:

- **Translate** between domains, models, and cultures
- **Manage** compression-trust relationships
- **Evolve** through community feedback and usage
- **Build** reputation through successful translations
- **Track** confidence and semantic degradation

### 10.2 Dictionary LCT Structure
```json
{
  "entity_type": "dictionary",
  "dictionary_spec": {
    "source_domain": "medical",
    "target_domain": "legal",
    "bidirectional": true,
    "coverage": {
      "terms": 15000,
      "concepts": 3200
    }
  },
  "compression_profile": {
    "average_ratio": 12.5,
    "lossy_threshold": 0.02,
    "context_required": "moderate"
  },
  "trust_requirements": {
    "minimum_t3": {
      "talent": 0.8,
      "training": 0.9,
      "temperament": 0.85
    },
    "stake_required": 100
  },
  "evolution": {
    "learning_rate": 0.001,
    "update_frequency": "daily",
    "community_edits": true
  }
}
```

### 10.3 Dictionary Trust Building
Dictionaries earn trust through:
- Translation accuracy and consistency
- Successful witness attestations
- Community validation and curation
- Low semantic degradation rates
- Handling of edge cases and ambiguity

### 10.4 Compression-Trust Principle
**All meaningful communication is compression plus trust across shared or sufficiently aligned latent fields.**

Dictionaries manage this by:
- Building trust → Enabling higher compression
- Tracking degradation → Maintaining quality
- Facilitating alignment → Bridging latent spaces
- Evolving continuously → Adapting to drift

For complete specification, see [dictionary-entities.md](dictionary-entities.md).

## 11. Specialized Entity: Accumulators

### 11.1 Accumulator Role
Accumulators are specialized responsive entities that provide passive witnessing services:

- **Listen** to public broadcasts without acknowledgment
- **Record** broadcast events with cryptographic integrity
- **Index** by broadcaster, type, timestamp
- **Query** interface for presence validation

### 11.2 Accumulator LCT Structure
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

### 11.3 Accumulator Trust
Accumulator reliability measured by:
- Uptime and availability
- Query response accuracy
- Storage commitment honoring
- Non-selective recording (no censorship)

## 12. Citizen Role Examples

### 12.1 Context-Specific Citizens

Different contexts define different citizen roles:

| Context | Citizen Role | Base Rights | Base Responsibilities |
|---------|--------------|-------------|----------------------|
| Nation | National Citizen | Vote, access services | Pay taxes, follow laws |
| Platform | Platform Citizen | Create content, interact | Follow ToS, respect others |
| Network | Network Citizen | Send/receive data | Maintain node, relay traffic |
| Organization | Member Citizen | Participate, propose | Contribute, uphold values |
| Ecosystem | Ecosystem Citizen | Use resources | Sustain balance |

### 12.2 Birth Certificate as Proof of Origin

The birth certificate provides:
- **Provenance**: Where and when entity originated
- **Legitimacy**: Proper creation process followed
- **Context**: Initial environment and constraints
- **Inheritance**: Rights/responsibilities from parent
- **Witnesses**: Who validated the birth

## 13. Specialized Entity: Policy

### 13.1 Policy Role
Policy entities are first-class participants in the trust network that represent governance rules with their own LCT, witnessing history, and hash-tracked versioning:

- **Evaluate** proposed actions against configurable rule sets
- **Witness** member actions (allow/deny/warn decisions)
- **Evolve** through versioned updates (changing policy = new entity)
- **Build** trust through evaluation accuracy and convergence quality
- **Integrate** with SAGE's IRP plugin architecture via PolicyGate

### 13.2 Policy Entity Characteristics

| Property | Value |
|----------|-------|
| Mode | Responsive/Delegative |
| Energy Pattern | Active |
| LCT Format | `policy:<name>:<version>:<hash>` |
| Immutability | Policy config is immutable once registered; updates create new entities |

### 13.3 PolicyGate: IRP-Backed Evaluation

When integrated with SAGE's IRP stack, PolicyEntity gains a runtime implementation (PolicyGate) that follows the IRP contract:

- **Energy function**: `PolicyEntity.evaluate()` output as compliance score (0 = compliant, >0 = violation)
- **Convergence**: Iterative refinement of actions toward policy compliance
- **Trust metrics**: Same convergence-based trust as all IRP plugins
- **ATP budgeting**: Policy evaluation participates in metabolic resource allocation
- **Fractal self-similarity**: PolicyEntity is itself a specialized SAGE stack — a "plugin of plugins." The IRP contract operates at three nested scales (consciousness loop → policy evaluation → LLM advisory), validating the abstraction as scale-invariant

### 13.4 Accountability Frames

Policy evaluation includes an accountability frame reflecting the agent's metabolic context:

| Frame | Metabolic States | Meaning |
|-------|-----------------|---------|
| Normal | WAKE, FOCUS | Standard accountability — agent chose this outcome |
| Degraded | REST, DREAM | Reduced capabilities acknowledged |
| Duress | CRISIS | Fight-or-flight — consequences beyond agent's control |

CRISIS mode changes the **accountability equation**, not policy strictness. Both freeze (halt effectors) and fight (proceed with best action) are valid responses under duress. The audit trail records the duress context alongside the decision.

### 13.5 Policy Trust Building

Policy entities earn trust through:
- Evaluation consistency and accuracy
- Convergence quality when used as IRP plugin
- Successful witness attestations from teams
- Low false-positive/false-negative rates
- Appropriate handling of edge cases and trust boundaries

For implementation details, see the design decision: `docs/history/design_decisions/POLICY-ENTITY-REPOSITIONING.md`

## 14. Future Extensions

Potential entity types under consideration:
- **Contract**: Smart contracts as entities
- **Content**: Documents/media with their own LCTs
- **Workflow**: Process definitions as entities
- **Community**: Collective intelligence entities
- **Citizen Subtypes**: Specialized citizen roles for different contexts