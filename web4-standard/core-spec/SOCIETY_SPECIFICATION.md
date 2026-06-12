# Web4 Society Specification

## Version: 1.0.0
## Date: 2026-06-12
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
  - Citizenship events (apply/grant/provisional grant/suspend/reinstate/terminate)
  - Law changes (proposal/ratification/amendment/repeal)
  - Economic events (treasury deposits/allocations/reclaims; pool-supply mints/slashes)
  - Metabolic state transitions (per `SOCIETY_METABOLIC_STATES.md`)
  - Formation events (genesis/bootstrap/operational/incorporation/secession/dissolution)
- **Note**: Witnesses participate in every recorded event via the per-entry `witnesses` field; they are participants, not a separate event category. §4.2.1 gives the canonical enumeration of *society-lifecycle* event types and their minimum field-sets. It is not the ledger's complete storage obligation: `web4-society-authority-law.md` §3.4 additionally requires the society's Immutable Record to store **Birth Certificates**, **role pairings**, **delegations**, **law dataset digests**, **witness attestations**, and **auditor adjustments** as SAL record classes in their own right — the per-entry `witnesses` field does not substitute for SAL §3.4's standalone witness-attestation record class.

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
  - Enables inter-society relationships (the LCT's standards-facing interop projection is a `did:web4` identifier — see `did-web4-method.md`)
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

Genesis does not require multiple founders: `inter-society-protocol.md` §2.1 defines the self-bootstrapped (solo-founder) genesis procedure and its SHALL-level requirements — founder LCT, society keypair, published charter, treasury initialization, and society-LCT minting with ≥3 birth witnesses (which MAY be under the founder's control at genesis). The solo founder fills all seven base-mandatory roles (`society-roles.md` §2), constituting a "society-of-one" for bootstrap purposes (ISP §6.3).

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

**Note on `Rejection`**: Rejection is a non-record outcome — the rejection itself creates no ledger event and assigns no status. The canonical SDK `CitizenshipStatus` enum contains only `APPLIED`, `PROVISIONAL`, `ACTIVE`, `SUSPENDED`, and `TERMINATED` (no `REJECTED` value); a rejected application's prior `apply` event (§4.2.1) remains the entity's most recent citizenship event, with no further transition recorded. The other branches in the diagram (`Provisional`, `Suspension`, `Reinstatement`, `Termination`) correspond to recorded status transitions per the §4.2.1 action-to-status mapping.

### 2.4 Citizenship Record Structure

A citizenship grant is recorded as the canonical citizenship event of §4.2.1 (envelope `{type, action, data, witnesses, timestamp}`), with the society's rights/obligations payload carried under `data`:

```json
{
  "type": "citizenship",
  "action": "grant",
  "data": {
    "entity_lct": "...",
    "society_lct": "...",
    "rights": ["vote", "propose", "allocate"],
    "obligations": ["witness", "contribute"],
    "law_reference": "citizenship_law_v1"
  },
  "witnesses": ["...", "...", "..."],
  "timestamp": "..."
}
```

The entity's *current status* (Applied / Provisional / Active / Suspended / Terminated, per §2.3) is not stored on the event; it is derived state, determined by the most recent citizenship event's `action` (see the action-to-status mapping in §4.2.1). Implementations MAY maintain a separate state-record projection (e.g. the SDK's `CitizenshipRecord`) computed from these events; the ledger event above is the normative record.

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

Every event uses the common envelope `{type, action, data, witnesses, timestamp}` (mirroring the SDK's `LedgerEntry`): `type` and `action` classify the event, event-specific payload fields live under `data`, and `witnesses` + `timestamp` carry the provenance that §4.2.2's amendment machinery depends on. The field-sets shown are minimums; societies MAY extend `data`.

Every ledger MUST record:

1. **Citizenship Events**
   ```json
   {
     "type": "citizenship",
     "action": "apply|grant|provisional_grant|suspend|reinstate|terminate",
     "data": {
       "entity_lct": "...",
       "law_reference": "citizenship_law_v1"
     },
     "witnesses": ["..."],
     "timestamp": "..."
   }
   ```

   Action-to-status mapping (statuses per §2.3): `apply` → Applied, `provisional_grant` → Provisional, `grant` and `reinstate` → Active, `suspend` → Suspended, `terminate` → Terminated. (`terminate` replaces the `revoke` action of earlier drafts — Termination is the recorded status it produces.) Rejection produces no event (§2.3 Note).

2. **Law Change Events**
   ```json
   {
     "type": "law_change",
     "action": "propose|ratify|amend|repeal",
     "data": {
       "law_id": "...",
       "change_description": "...",
       "voting_record": {...},
       "effective_date": "..."
     },
     "witnesses": ["..."],
     "timestamp": "..."
   }
   ```

   Law changes are SAL-critical events (`sal.law.update` per `web4-society-authority-law.md` §3.4) and MUST carry witness co-signatures per the society's Quorum Policy (SAL §5.4).

3. **Economic Events**
   ```json
   {
     "type": "economic",
     "action": "deposit|allocate|reclaim|mint|slash",
     "data": {
       "amount": "...",
       "token_type": "ATP|ADP",
       "recipient_lct": "...",
       "purpose": "..."
     },
     "witnesses": ["..."],
     "timestamp": "..."
   }
   ```

   The treasury-flow vocabulary is **deposit** (tokens flow into the pool), **allocate** (tokens flow from the pool to a citizen), and **reclaim** (tokens flow back to the pool). The pool-supply vocabulary is **mint** (new tokens created by the society's monetary authority — minting occurs in the ADP state per `atp-adp-cycle.md` §2.1) and **slash** (supply destroyed per `atp-adp-cycle.md` §2.4); both are witnessed, ledger-recorded events that change total supply rather than move existing tokens. ATP-cycle state transitions operate at the cycle layer per `atp-adp-cycle.md` §2: **discharge** is recorded on the R6 transaction that spends the ATP (§2.3), while **charging** is recorded as a standalone value-creation event (§2.2) — neither is a treasury-level economic event.

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

5. **Formation Events** (phase transitions, incorporation, secession, dissolution)
   ```json
   {
     "type": "formation",
     "action": "genesis|bootstrap|operational|incorporate_child|incorporated_by|secede|dissolve",
     "data": {
       "founders": ["..."],
       "name": "..."
     },
     "witnesses": ["..."],
     "timestamp": "..."
   }
   ```

   `secede` and `dissolve` record the SHALL-required constituent-secession and federation-dissolution events of `inter-society-protocol.md` §5.1–§5.2 (intent-to-secede and departure on the constituent's and federation's ledgers; ratified dissolution on the federation's ledger).

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
     "law_reference": "amendment_law_v2"
   }
   ```

3. **Maintain Provenance Chain**
   ```json
   {
     "amendment_context": {
       "proposed_by": "...",
       "witnesses": ["...", "..."],
       "voting_record": {...},
       "ratified_timestamp": "...",
       "block_height": 12345
     }
   }
   ```

### 4.3 Immutability with Corrections

The ledger maintains immutability while allowing corrections:

```
Block N:   [Original Entry: "Alice's allocation is 100 ATP"]
Block N+1: [Amendment: "Correction - Alice's allocation is 90 ATP, 10 ATP was calculation error"]
Block N+2: [Context: "Approved by 3/5 validators per Amendment Law §2.3"]

Query Result: Alice's allocation is 90 ATP (amended at block N+1, original: 100 ATP)
```

(The example uses allocation vocabulary deliberately: ATP is society-allocated, not entity-owned — see `atp-adp-cycle.md` on non-accumulation and §4.2.1's allocate/reclaim treasury flows.)

---

## 5. Implementation Considerations

### 5.1 Society Bootstrap

A minimal bootstrap society — the *conceptual* minimum of §1.2, distinct from both the operational minimum of §1.2.5 and ISP §6.2's "minimum viable *semantic* society" — can be:
- 2 entities agreeing to form society (or 1 solo founder, per the self-bootstrapped genesis path in §1.3)
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
- **Ledger**: Witnessed (distributed — constituent societies act as one another's external witnesses; the apex society has no parent, so the Participatory type of §4.1.3, which delegates validation to a parent ledger, is structurally unavailable)
- **Economy**: ATP generation rights allocation

---

## 7. Future Considerations

### 7.1 Cross-Society Protocols

Core inter-society primitives — including the cross-society envelope, reputation propagation, and witnessing across federation boundaries — are normatively defined in `mcp-protocol.md` §7 (MCP as the inter-society interface) and `inter-society-protocol.md`. The bullet list below enumerates further extensions beyond what those documents currently specify normatively:

- Treaty mechanisms (formal bilateral or multilateral society-to-society agreements with on-ledger ratification)
- Resource sharing agreements (cross-society ATP allocation pools or shared treasury sub-partitions)
- Reputation portability (mechanisms beyond the signed reputation objects of `mcp-protocol.md` §7.3 and the §7.5 reputation-propagation rules — e.g. trust-tensor migration on citizenship transfer)

### 7.2 Society Mergers and Splits

Constituent secession and federation dissolution — including treasury distribution and citizenship-membership updates on exit — are normatively specified in `inter-society-protocol.md` §5 and recorded via §4.2.1's `secede`/`dissolve` formation events. The bullets below enumerate extensions beyond that coverage:

- Forking mechanisms (a society dividing into successor societies, outside the federation secession/dissolution cases)
- Asset division (formulas beyond ISP §5.2's pro-rata-by-contribution default)
- Citizenship migration (automatic re-homing of citizens, beyond the LCT membership updates ISP §5 specifies)

### 7.3 Dispute Resolution

Intra-society dispute resolution is carried by the Mediator role (`society-roles.md` §4.1; context-mandatory for Court/Arbitration societies per its §3), and ISP §5.1 provides for charter-specified mediation during secession notice periods. The bullets below enumerate what remains unspecified:

- Inter-society courts
- Arbitration protocols
- Enforcement mechanisms

---

*"A society is not just a group - it's a living entity with laws as DNA, ledger as memory, and citizens as cells."*