# Web4 Society Specification

## Version: 1.0.0
## Date: January 17, 2025
## Status: Foundational Concept

---

## 1. Definition of Society

### 1.1 Core Definition

A **Society** in Web4 is a self-governing collective of LCT-bearing entities that maintains:
- Shared laws (governance rules)
- Shared ledger (immutable record)
- Shared economy (ATP/ADP token pool)
- Shared identity (society LCT)

### 1.2 Minimum Requirements

For a collective to constitute a Society, it MUST have:

#### 1.2.1 Law Oracle
- **Definition**: Codified rules governing entity behavior and resource allocation
- **Requirements**:
  - At least one foundational law (can be "all decisions by consensus")
  - Amendment mechanism defined in law
  - Enforcement mechanism (even if voluntary)
  - Published and accessible to all citizens

#### 1.2.2 Ledger
- **Definition**: Immutable record of society events and state
- **Minimum Records**:
  - Citizenship events (join/leave/suspend/reinstate)
  - Law changes (proposal/ratification/amendment)
  - Economic events (ATP/ADP allocations)
  - Witness attestations (trust building)

#### 1.2.3 Treasury
- **Definition**: Society-managed ATP/ADP token pool
- **Requirements**:
  - Initial ADP allocation (can be zero)
  - Allocation mechanism defined in law
  - Energy accounting (ATP in/out tracking)

#### 1.2.4 Society LCT
- **Definition**: The society's own Linked Context Token
- **Purpose**:
  - Represents society as entity
  - Enables inter-society relationships
  - Holds society-level trust tensors

### 1.3 Formation Process

```
1. Genesis Event
   - Founding entities agree on initial laws
   - Society LCT is minted
   - Ledger is initialized

2. Bootstrap Phase
   - Initial citizens recorded
   - Treasury allocated (if any)
   - First law ratified

3. Operational Phase
   - Society begins accepting citizens
   - Economic activity commences
   - Trust relationships form
```

---

## 2. Citizenship

### 2.1 Definition

**Citizenship** is a witnessed relationship between an entity (via its LCT) and a society (via its society LCT), recorded on the society's ledger.

### 2.2 Citizenship Properties

#### 2.2.1 Multi-Society Citizenship
- Entities MAY be citizens of multiple societies
- No exclusive citizenship requirement
- Each citizenship is independent

#### 2.2.2 Citizenship Rights
Defined by society law, but typically include:
- Participation in governance
- Access to society resources (ATP allocation)
- Recognition by other citizens
- Protection under society laws

#### 2.2.3 Citizenship Obligations
Defined by society law, but typically include:
- Adherence to society laws
- Contribution to society goals
- Witness participation
- Resource contribution (optional)

### 2.3 Citizenship Lifecycle

```
Application → Review → Acceptance → Active Citizenship
                ↓           ↓              ↓
            Rejection   Provisional    Suspension
                          Status           ↓
                                      Reinstatement
                                           or
                                      Termination
```

### 2.4 Citizenship Record Structure

```json
{
  "event_type": "citizenship_granted",
  "entity_lct": "lct-agent-alice-12345",
  "society_lct": "lct-society-web4dev-67890",
  "timestamp": 1737142857,
  "witness_lcts": ["lct-1", "lct-2", "lct-3"],
  "rights": ["vote", "propose", "allocate"],
  "obligations": ["witness", "contribute"],
  "status": "active"
}
```

---

## 3. Fractal Nature

### 3.1 Society Fractals

Societies can be citizens of other societies, creating fractal hierarchies:

```
Universe Society
    ├── Regional Society (citizen of Universe)
    │      ├── City Society (citizen of Regional)
    │      │      └── Neighborhood Society (citizen of City)
    │      └── Industrial Society (citizen of Regional)
    └── Global Trade Society (citizen of Universe)
```

### 3.2 Fractal Properties

#### 3.2.1 Inheritance
- Child societies MAY inherit base laws from parent
- Inheritance is defined at incorporation
- Local laws can extend but not contradict inherited laws

#### 3.2.2 Recursive Citizenship
- If Society A is citizen of Society B
- And Entity X is citizen of Society A
- Then X has indirect relationship with B
- This creates trust propagation paths

#### 3.2.3 Economic Fractals
- Parent societies can allocate ATP to child societies
- Child societies manage their own sub-allocations
- Energy flows follow citizenship paths

### 3.3 Fractal Citizenship

An entity's complete citizenship portfolio forms a fractal tree:

```
Entity (LCT-123)
    ├── Direct: Development Society
    │      └── Indirect: Web4 Global Society
    ├── Direct: Testing Guild
    │      ├── Indirect: Quality Alliance
    │      └── Indirect: Web4 Global Society
    └── Direct: Local Community
           └── Indirect: Regional Federation
```

---

## 4. Ledger Types and Requirements

### 4.1 Ledger Classification

#### 4.1.1 Confined Ledger
- **Access**: Citizens only
- **Validation**: Internal consensus
- **Use Case**: Private societies, development teams
- **Trust Model**: Mutual trust among citizens

```json
{
  "type": "confined",
  "access": "citizens_only",
  "validators": ["citizen_lct_1", "citizen_lct_2"],
  "visibility": "private"
}
```

#### 4.1.2 Witnessed Ledger
- **Access**: Citizens + at least one external witness
- **Validation**: Mixed internal/external
- **Use Case**: Semi-public societies, trade groups
- **Trust Model**: External verification

```json
{
  "type": "witnessed",
  "access": "citizens_plus_witnesses",
  "validators": ["citizen_lct_1", "external_witness_lct"],
  "visibility": "restricted"
}
```

#### 4.1.3 Participatory Ledger
- **Access**: Participates in parent society ledger
- **Validation**: Parent society consensus
- **Use Case**: Subsidiary societies, local chapters
- **Trust Model**: Inherited from parent

```json
{
  "type": "participatory",
  "access": "via_parent_society",
  "parent_ledger": "parent_society_ledger_id",
  "visibility": "as_per_parent"
}
```

### 4.2 Ledger Requirements

#### 4.2.1 Minimum Recording Requirements

Every ledger MUST record:

1. **Citizenship Events**
   ```json
   {
     "type": "citizenship_event",
     "action": "grant|revoke|suspend|reinstate",
     "entity_lct": "...",
     "timestamp": "...",
     "witnesses": ["..."],
     "law_reference": "citizenship_law_v1"
   }
   ```

2. **Law Change Events**
   ```json
   {
     "type": "law_change",
     "action": "propose|ratify|amend|repeal",
     "law_id": "...",
     "change_description": "...",
     "voting_record": {...},
     "effective_date": "..."
   }
   ```

3. **Economic Events**
   ```json
   {
     "type": "economic_event",
     "action": "allocate|charge|discharge",
     "amount": "...",
     "token_type": "ATP|ADP",
     "recipient_lct": "...",
     "purpose": "..."
   }
   ```

#### 4.2.2 Amendment Mechanism

All ledgers MUST support law-driven amendments that:

1. **Preserve Original Entry**
   ```json
   {
     "entry_id": "original-123",
     "status": "superseded",
     "superseded_by": "amendment-456",
     "original_data": {...}
   }
   ```

2. **Record Amendment**
   ```json
   {
     "entry_id": "amendment-456",
     "amends": "original-123",
     "amendment_type": "correction|clarification|expansion",
     "new_data": {...},
     "reason": "...",
     "law_authorization": "amendment_law_v2"
   }
   ```

3. **Maintain Provenance Chain**
   ```json
   {
     "amendment_context": {
       "proposed_by": "lct-entity-789",
       "witnessed_by": ["lct-1", "lct-2"],
       "voting_record": {...},
       "ratified_timestamp": "...",
       "block_height": 12345
     }
   }
   ```

### 4.3 Immutability with Corrections

The ledger maintains immutability while allowing corrections:

```
Block N:   [Original Entry: "Alice owns 100 ATP"]
Block N+1: [Amendment: "Correction - Alice owns 90 ATP, 10 ATP was calculation error"]
Block N+2: [Context: "Approved by 3/5 validators per Amendment Law §2.3"]

Query Result: Alice owns 90 ATP (amended at block N+1, original: 100 ATP)
```

---

## 5. Implementation Considerations

### 5.1 Society Bootstrap

Minimum viable society can be:
- 2 entities agreeing to form society
- 1 simple law: "all decisions unanimous"
- Confined ledger between them
- Zero initial treasury

### 5.2 Scaling Patterns

As societies grow:
1. Laws become more complex
2. Ledger transitions: Confined → Witnessed → Participatory
3. Sub-societies form and incorporate
4. Economic complexity increases

### 5.3 Trust Building

Society-level trust tensors (T3) are calculated from:
- Citizen behavior aggregation
- Inter-society interactions
- Economic efficiency
- Law compliance rates

---

## 6. Society Examples

### 6.1 Development Team Society
- **Citizens**: 5 developers
- **Laws**: Code review requirements, merge policies
- **Ledger**: Confined (team only)
- **Economy**: ATP for features completed

### 6.2 Regional Trade Society
- **Citizens**: 50 businesses + 10 logistics providers
- **Laws**: Trade standards, dispute resolution
- **Ledger**: Witnessed (external auditors)
- **Economy**: ATP for successful trades

### 6.3 Global Web4 Society
- **Citizens**: All Web4 societies (fractal)
- **Laws**: Core Web4 principles only
- **Ledger**: Participatory (distributed)
- **Economy**: ATP generation rights allocation

---

## 7. Future Considerations

### 7.1 Cross-Society Protocols
- Treaty mechanisms
- Resource sharing agreements
- Reputation portability

### 7.2 Society Mergers and Splits
- Forking mechanisms
- Asset division
- Citizenship migration

### 7.3 Dispute Resolution
- Inter-society courts
- Arbitration protocols
- Enforcement mechanisms

---

*"A society is not just a group - it's a living entity with laws as DNA, ledger as memory, and citizens as cells."*