# Web4 Society Specification

## Version: 1.0.0
## Date: 2026-05-30
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
  - Economic events (treasury deposits/allocations/reclaims)
  - Metabolic state transitions (per `SOCIETY_METABOLIC_STATES.md`)
  - Formation events (genesis/bootstrap/operational/incorporation)
- **Note**: Witnesses participate in every recorded event via the per-entry `witnesses` field; they are participants, not a separate event category. The canonical enumeration of recorded event types and their minimum field-sets is given in §4.2.1.

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
  - Holds society-level T3 (trust) and V3 (value) tensors (see `t3-v3-tensors.md` and §5.3)

#### 1.2.5 Operational-Minimum Cross-Reference

The four-element minimum above is the *conceptual* minimum a society must satisfy. The *operational* minimum — what a deployment instantiates to function as a full participant in cross-society interactions — is refined along the role-structural axis by two sister specs:

- **`web4-society-authority-law.md` §3.1** requires an **Authority Role LCT** and a **Quorum Policy** (alongside the Law Oracle and Immutable Record listed in §1.2.1–§1.2.2). The Authority Role refines §1.2.1's "enforcement mechanism" into a specific role-bearing entity. The Quorum Policy is the table of **witness/attestation requirements per action type**, defined by the Law Oracle role (SAL §5.3; quorum policy assignment per SAL §5.4) — it specifies which witnesses must co-sign which classes of ledger entry, not a governance decision rule.
- **`society-roles.md` §2** enumerates **seven base-mandatory roles** — Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, and Citizen — that every Web4-compliant society MUST have filled (a single entity MAY fill several, down to a solo founder filling all seven). The Treasurer role is the role-bearing counterpart to §1.2.3's Treasury; the Sovereign role is the role-bearing counterpart to §1.2.4's Society LCT.

A society implementer satisfying §1.2.1–§1.2.4 alone has met the conceptual minimum but not the operational minimum. Conformance to the operational minimum is **not protocol-enforced**: `inter-society-protocol.md` §6.2 defines *semantic viability* (internal differentiation, witnessing capacity, externally grounded ATP referent) as GUIDANCE, and ISP §6.3 is explicit that the Web4 protocol does not adjudicate whether a society is "real enough" — viability is discovered socially through first-contact outcomes (ISP §3). The SDK's `validate_minimum_viable` is a *voluntary* conformance check covering the role-structural side of those criteria. SAL §3.1 governs the authority-binding semantics.

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

### 1.4 Operational Modes (Metabolic States)

A society in the Operational Phase does not run at a single fixed activity level. Web4 defines eight **metabolic states** (Active, Rest, Sleep, Hibernation, Torpor, Estivation, Dreaming, Molting) that modulate consensus participation, witness duty cycles, ATP/ADP flow, trust-tensor updates, and citizenship acceptance based on activity demand, resource availability, and operational conditions. The metabolic-state subsystem is normative for societies running long-lived operations; it determines which transactions a society accepts at a given time, what its instantaneous energy cost is, and what trust effects (update rate, decay rate, temporary penalty) apply during the current state.

The full normative definition — including state characteristics, transition rules, configuration schema, trust adjustments, and economic implications — is given in `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md`. Implementations of this Society Specification MUST also conform to the metabolic-states specification for any society that intends to operate beyond a single bootstrap window.

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

**Note on `Rejection`**: Rejection is a non-record outcome — no `CitizenshipRecord` is created on the ledger and no status is assigned. The canonical SDK `CitizenshipStatus` enum contains only `APPLIED`, `PROVISIONAL`, `ACTIVE`, `SUSPENDED`, and `TERMINATED` (no `REJECTED` value); a rejected application leaves the ledger unchanged. The other branches in the diagram (`Provisional`, `Suspension`, `Reinstatement`, `Termination`) correspond to recorded status transitions.

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

Participatory ledgers inherit their validator set from the parent ledger (see §3.2.1 on inheritance and §4.1.2 for the Witnessed-ledger validator pattern). The absence of an explicit `validators` field in this JSON is intentional: validation authority is delegated to the parent, not enumerated locally.

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
     "action": "deposit|allocate|reclaim",
     "amount": "...",
     "token_type": "ATP",
     "recipient_lct": "...",
     "purpose": "..."
   }
   ```

   The treasury-level economic vocabulary is **deposit** (tokens flow into the pool), **allocate** (tokens flow from the pool to a citizen), and **reclaim** (tokens flow back to the pool). ATP-cycle state transitions (charge / discharge) operate at the R6/cycle layer per `atp-adp-cycle.md` §2 and are recorded separately on R6 transactions, not as treasury-level economic events.

4. **Metabolic State Transitions** (per `SOCIETY_METABOLIC_STATES.md`)
   ```json
   {
     "type": "metabolic",
     "action": "transition",
     "data": {
       "from": "active|rest|sleep|hibernation|torpor|estivation|dreaming|molting",
       "to":   "active|rest|sleep|hibernation|torpor|estivation|dreaming|molting"
     },
     "witnesses": ["..."],
     "timestamp": "..."
   }
   ```

5. **Formation Events** (phase transitions and incorporation)
   ```json
   {
     "type": "formation",
     "action": "genesis|bootstrap|operational|incorporate_child|incorporated_by",
     "data": {
       "founders": ["..."],
       "name": "..."
     },
     "witnesses": ["..."],
     "timestamp": "..."
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

Core inter-society primitives — including the cross-society envelope, reputation propagation, and witnessing across federation boundaries — are normatively defined in `mcp-protocol.md` §7 (MCP as the inter-society interface) and `inter-society-protocol.md`. The bullet list below enumerates further extensions beyond what those documents currently specify normatively:

- Treaty mechanisms (formal bilateral or multilateral society-to-society agreements with on-ledger ratification)
- Resource sharing agreements (cross-society ATP allocation pools or shared treasury sub-partitions)
- Reputation portability (mechanisms beyond `mcp-protocol.md §7.4`'s reputation envelopes — e.g. trust-tensor migration on citizenship transfer)

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