# Web4 Entity Relationship Mechanisms

This document provides the formal specifications for the four core entity relationship mechanisms in Web4: BINDING, PAIRING, WITNESSING, and BROADCAST. These mechanisms are the foundation of Web4's unique approach to building trust and enabling secure, decentralized interactions.

## Interaction Framework: R6 Actions

While these four mechanisms establish relationships, actual interactions between entities are structured through the R6 Action Framework. Every meaningful interaction can be expressed as an R6 action that:
- Tracks intent through Request
- Validates permissions through Role
- Consumes Resources (ATP)
- Produces measurable Results
- Updates T3/V3 tensors based on performance
- Creates References for future learning

See `web4-r6-framework.md` for complete R6 specification.




## 1. BINDING (Permanent Identity Attachment)

BINDING is the process of creating a permanent, unforgeable link between a Web4 entity and its digital identity, represented by a Lineage and Capability Token (LCT). This is the foundational act of creating a new Web4 entity.

### 1.1. ABNF Specification

```abnf
binding-request = binding-version SP entity-type SP public-key SP hardware-id
binding-response = binding-version SP lct-id SP binding-proof
binding-version = "BIND/1.0"
entity-type = "HUMAN" / "AI" / "ORGANIZATION" / "ROLE" / "TASK" / "RESOURCE" / "DEVICE" / "SERVICE" / "ORACLE" / "HYBRID"
hardware-id = 64*64HEXDIG  ; SHA-256 of hardware characteristics
binding-proof = signature over (entity-type / public-key / hardware-id / timestamp)
```

### 1.2. State Machine

```mermaid
stateDiagram-v2
    [*] --> Unbound
    Unbound --> Binding: initiate_binding
    Binding --> Bound: binding_confirmed + update_MRH
    Bound --> Revoked: binding_revoked + remove_from_MRH
    Revoked --> [*]
```

### 1.3. MRH Impact

When a BINDING is established:
1. Parent LCT adds child to its `mrh.bound` array with type="child"
2. Child LCT adds parent to its `mrh.bound` array with type="parent"
3. Both LCTs update `mrh.last_updated` timestamp
4. Trust context begins flowing between bound entities




## 2. PAIRING (Authorized Operational Relationships)

PAIRING is the process of establishing an authorized, operational relationship between two already-bound Web4 entities. This allows them to communicate securely and perform actions based on a mutually agreed-upon context and set of rules.

### Special Case: Role-Agent Pairing

When an agentic entity (human or AI) pairs with a role entity, the pairing creates a delegation relationship where:
- The agent temporarily assumes the role's permissions and responsibilities
- Actions taken by the agent are contextualized by the role's scope
- Performance metrics accumulate to both the agent's and role's reputation
- The role maintains a history of all agents who have performed it

### 2.1. ABNF Specification

```abnf
pairing-request = pairing-version SP lct-a SP lct-b SP context SP rules
pairing-response = pairing-version SP session-id SP key-half-a SP key-half-b
pairing-version = "PAIR/1.0"
context = quoted-string  ; "energy-management", "data-exchange", etc.
rules = "{" rule-list "}"
key-half-a = base64(32-bytes)  ; For symmetric key derivation
key-half-b = base64(32-bytes)
```

### 2.2. State Machine

```mermaid
stateDiagram-v2
    [*] --> Unpaired
    Unpaired --> Pairing: initiate_pairing
    Pairing --> Paired: pairing_complete + add_to_MRH
    Paired --> Active: session_established
    Active --> Active: exchange_messages
    Active --> Paired: session_closed
    Paired --> Unpaired: pairing_revoked + remove_from_MRH
```

### 2.3. MRH Impact

When a PAIRING is established:
1. Both LCTs add each other to their `mrh.paired` arrays
2. Include pairing context (e.g., "energy-mgmt", "role-performance") and session_id
3. Update `mrh.last_updated` on both LCTs
4. Entities enter each other's relevancy horizons for the pairing context

For Role-Agent pairings specifically:
1. Role LCT adds agent to its current performers list
2. Agent LCT adds role to its active roles
3. Role's permission set becomes available to agent
4. Performance tracking begins for reputation calculation

### 2.4. R6 Integration with Pairing

Once paired, entities interact through R6 actions:
- The pairing context defines available Rules
- The Role from pairing determines permissions
- Shared Resources become accessible
- Results affect both entities' T3/V3 tensors
- Failed actions may trigger pairing review




## 3. WITNESSING (Trust Building Through Observation)

WITNESSING is the process by which a Web4 entity observes and attests to the existence, actions, or state of another entity. This creates a verifiable record of interactions that builds trust over time and makes entities unforgeable through accumulated observation.

### 3.1. ABNF Specification

```abnf
witness-assertion = witness-version SP observer-lct SP observed-lct SP evidence
witness-version = "WTNS/1.0"
evidence = evidence-type SP evidence-data SP signature
evidence-type = "EXISTENCE" / "ACTION" / "STATE" / "TRANSITION"
; Creates bidirectional MRH tensor links
```

### 3.2. State Machine

```mermaid
stateDiagram-v2
    [*] --> Unwitnessed
    Unwitnessed --> Witnessing: observe_entity
    Witnessing --> Witnessed: evidence_recorded + update_both_MRHs
```

### 3.3. MRH Impact

When WITNESSING occurs:
1. Witnessed LCT adds witness to its `mrh.witnessing` array
2. Witness LCT may optionally track witnessed entities
3. Both update `mrh.last_updated`
4. Creates bidirectional awareness in relevancy horizons
5. Trust accumulates through repeated witnessing interactions

### 3.4. R6 Integration with Witnessing

Witnesses play a crucial role in R6 actions:
- Witnesses validate Result accuracy (affecting Veracity in V3)
- Quality witnesses assess output value (affecting Valuation)
- Time witnesses provide temporal ordering
- Failed witness validation can void Results
- Witness attestations become permanent References




## 4. BROADCAST (Unidirectional Discovery and Passive Witnessing)

BROADCAST is a unidirectional mechanism for an entity to announce its presence, capabilities, or status without requiring any prior relationship or acknowledgment. This is used for discovery, general network awareness, and enables a one-sided form of witnessing through accumulators.

### 4.1. ABNF Specification

```abnf
broadcast-message = broadcast-version SP sender-id SP message-type SP payload
broadcast-version = "CAST/1.0"
sender-id = entity-type ":" local-identifier
message-type = "ANNOUNCE" / "HEARTBEAT" / "CAPABILITY"
; No acknowledgment required, no relationship formed
```

### 4.2. State Machine

```mermaid
stateDiagram-v2
    [*] --> Broadcasting
    Broadcasting --> Broadcasting: send_broadcast
```

### 4.3. MRH Impact

BROADCAST is unique - it does NOT update MRH:
1. Broadcasting entity announces without creating relationships
2. Receiving entities MAY choose to initiate pairing based on broadcast
3. No MRH entries created until explicit relationship established
4. Enables discovery without commitment to relevancy horizon

### 4.4. Broadcast Accumulators

BROADCAST enables a one-sided form of witnessing through accumulators:

#### Accumulator Function
Accumulators are specialized entities that:
1. **Listen** for broadcasts without acknowledgment
2. **Record** broadcast history with timestamps and cryptographic proofs
3. **Index** broadcasts by entity, type, and time
4. **Respond** to queries about broadcast history

#### Lightweight Presence Validation
```abnf
accumulator-query = query-version SP entity-lct SP time-range
accumulator-response = query-version SP broadcast-count SP broadcast-history
broadcast-history = 1*(timestamp SP broadcast-hash SP signature)
```

#### Use Cases
- **Presence Proof**: Entity can query accumulators to prove consistent broadcasting
- **Liveness Validation**: Third parties can verify entity has been active
- **Historical Audit**: Broadcast patterns reveal operational consistency
- **Reputation Building**: Regular broadcasts accumulate as soft trust signal

#### Privacy Considerations
- Accumulators record public broadcasts only
- Broadcasters cannot control which accumulators listen
- Accumulator queries may be anonymous
- Broadcast content may be hashed rather than stored in full

This creates a lightweight, privacy-preserving mechanism for building presence reputation over time without requiring explicit relationships or mutual witnessing.


