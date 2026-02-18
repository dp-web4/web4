# Web4 Society–Authority–Law Specification (SAL)

**Status:** Draft • **Last Updated:** 2025-09-15 11:50:10 • **Applies to:** Web4 Core Protocol and Ecosystem

This document defines the **Society–Authority–Law (SAL)** layer for Web4. It specifies how every entity is *born* into a **fractal graph of authority and law** via a **Citizen** role at LCT genesis, how *authority* is represented and delegated, and how *law* is realized through oracle LCTs that bind enforceable rules to the R6 action grammar.

SAL is normative for identity lifecycle, role prerequisites, provenance, and attestation, and integrates with the Web4 **Core Protocol**, **Data Formats**, **Entity Types**, **MRH (RDF)**, **Security**, **Errors**, and **T3/V3** specifications.

---

## 0. Notation and Terms

- **MUST/SHOULD/MAY**: As defined in RFC 2119.
- **LCT**: Linked Context Token (the verifiable footprint of an entity).
- **Citizen**: The *genesis role* conferred at LCT creation within a society.
- **Society**: Any delegative entity (organization, network, platform, polity) with authority to issue citizenship and bind law.
- **Authority**: The binding capability of a society to create roles, delegate permissions, and enforce law.
- **Law Oracle**: A role-bound oracle LCT that publishes/verifies the active rule set for a society.
- **R6**: Rules + Role + Request + Reference + Resource → Result (action grammar).
- **MRH**: Markov Relevancy Horizon, implemented as RDF graphs with typed edges.

---

## 1. Design Goals

1. **Genesis Closure:** Every entity is born into a coherent fabric (citizenship with provenance).
2. **Fractal Citizenship:** Nested societies compose across scales (team → org → network → ecosystem).
3. **Law as Data:** “Law” is a verifiable, queryable oracle (versioned rules, attestable interpretations).
4. **Delegation Safety:** Clear limits, revocation, and auditability for authority and sub-authority.
5. **Role‑Contextual Trust:** All trust/value is computed within role contexts (Citizen prerequisite).

> NOTE: SAL references and extends _Core Protocol_, _Data Formats_, _Entity Types_, _MRH_, _Security Framework_, _Errors_, and _T3/V3_ documents.

---

## 2. Genesis: Birth Certificate and Citizen Role

### 2.1 Citizen as Genesis Role (Normative)
When an entity’s LCT is created, implementations **MUST**:
- Pair the entity with a **Citizen** role **within the issuing society’s context** (immutable birth pairing).
- Record a **Birth Certificate** object including: issuer society LCT, law-oracle digest, witnesses, timestamp, genesis block reference, and initial rights/responsibilities.
- Store the pairing and certificate on the society’s ledger and publish minimal proofs to discovery endpoints.

### 2.2 Birth Certificate (Canonical JSON-LD)
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
  "initialResponsibilities": ["abide_law", "respect_quorum"]
}
```

### 2.3 Canonicalization & Signatures
- JSON messages **MUST** use JCS (RFC 8785) for JOSE/JWS or deterministic CBOR for COSE/EdDSA (MTI), consistent with Security Framework.
- Birth certificates **MUST** be signed by the society’s binding authority key and **MAY** include witness signatures.

---

## 3. Fractal Citizenship and Authority Graph

### 3.1 Society Topology
A **Society** is a delegative entity with:
- An **Authority Role** LCT (root of delegation tree).
- A **Law Oracle** LCT (publishes machine‑readable law and interpretations).
- A **Quorum Policy** (witness/attestation requirements per action type).

### 3.2 Nested Composition
Citizenship composes:
- citizen(team) ⊂ citizen(org) ⊂ citizen(network) ⊂ citizen(ecosystem)
- Each level inherits upward constraints and exposes downward scoped capabilities.

### 3.3 MRH (RDF) Edges (Normative)
SAL adds/uses these typed edges:
```turtle
@prefix web4: <https://web4.io/ontology#> .
@prefix lct:  <https://web4.io/lct/> .

# Genesis pairing
lct:entity web4:pairedWith lct:roleCitizen .
lct:entity web4:memberOf   lct:societyRoot .

# Authority & Law
lct:societyRoot web4:hasAuthority lct:authorityRole .
lct:societyRoot web4:hasLawOracle lct:lawOracle .
lct:lawOracle   web4:publishes    lct:lawDatasetV120 .

# Delegation
lct:authorityRole web4:delegatesTo lct:subAuthorityRole .
lct:subAuthorityRole web4:scope "finance" .
```

Implementations **MUST** expose these edges for SPARQL queries to enable validation, discovery, and trust propagation.


### 3.4 Immutable Record (Ledger) — **MUST**
Each society **MUST** operate or bind to an **Immutable Record** service (blockchain or append-only ledger) that:
- Stores **Birth Certificates**, **role pairings**, **delegations**, **law dataset digests**, **witness attestations**, and **auditor adjustments**.
- Provides **content-addressed** objects (hash-linked) with inclusion proofs.
- Emits **event topics** for SAL-relevant updates (e.g., `sal.birth`, `sal.role.bind`, `sal.law.update`, `sal.audit.adjust`).

**Ledger Interface (minimum):**
```json
{
  "append": {"object": "<bytes|CBOR>", "topic": "sal.event", "parent": "hash|null"},
  "get":    {"hash": "sha256-..."}, 
  "prove":  {"hash": "sha256-..."}, 
  "events": {"topic": "sal.*", "from": "block:height"}
}
```

**Security:** Ledger writes **MUST** be signed; witness quorum **MUST** co-sign for SAL-critical events (see §5.4).

### 3.5 Societies as Citizens (Fractal Membership) — **MUST**
A `society` is itself an `entity` and **MAY/MUST** (depending on governance) be a **citizen** of other societies. SAL requires:
- `web4:memberOf` edges **MAY** chain across levels (team→org→network→ecosystem).
- **Law inheritance**: child society **inherits** parent law by default; **override** only by explicit **Interpretation** or **Norm** with higher or equal authority and no parent hard-conflict.
- **Conflict resolution order** (descending): emergency norms → explicit child overrides with parent awareness flag → parent norms → grandparent …

**Inheritance Rule (normative):**
```
effectiveLaw(child) = merge(parentLaw, childOverrides) with conflictPolicy
```
where `conflictPolicy` is machine-readable in law dataset.


---

## 4. Law Oracle

### 4.1 Law Object Model
A Law Oracle **MUST** publish a versioned **Law Dataset** containing:
- **Norms** (allow/deny, constraints, thresholds).
- **Procedures** (how to achieve compliance, e.g., KYC/Witnessing/Quorums).
- **Interpretations** (precedents; machine‑parsable updates with hashes).
- **Mappings to R6** (Rules profile; see §6).

A minimal JSON-LD structure:
```json
{
  "@context": ["https://web4.io/contexts/law.jsonld"],
  "type": "Web4LawDataset",
  "id": "web4://law/society/1.2.0",
  "hash": "sha256-...",
  "norms": [{"id":"LAW-ATP-LIMIT","selector":"r6.resource.atp","op":"<=","value":100}],
  "procedures": [{"id":"PROC-WIT-3","requiresWitnesses":3}],
  "interpretations": [{"id":"INT-42","replaces":"INT-41","reason":"edge case fix"}],
  "r6Bindings": ["web4://schemas/r6-rules-v1"]
}
```

### 4.2 Attestation and Rollout
- New law versions **MUST** be attested by quorum; roll-forward requires `hasAuthority` + witness thresholds.
- Entities **MUST** cache and pin the `hash` per society to detect downgrade/replay attempts.

---

## 5. Roles: Citizen, Authority, Oracle

### 5.1 Citizen (Genesis, Immutable)
- Permanent birth pairing; **cannot be revoked**.
- Grants base capabilities: presence, interaction, accumulation of reputation.
- **Prerequisite** for all other role pairings.

### 5.2 Authority
- Scopes: domain‑bounded (e.g., finance, safety, membership).
- Controls: delegation, revocation, emergency powers (if defined by law).
- **MUST** publish scope and limits as machine‑readable policy.

### 5.3 Law Oracle Role
- Publishes law datasets; signs interpretations; answers queries.
- **SHOULD** support deterministic Q&A (e.g., “is action X compliant?” with proof transcript).


### 5.4 Witness
- Maintains the **immutable record** via co-signed ledger entries for SAL-critical events.
- Quorum policy defined by **Law Oracle** (e.g., `requiresWitnesses: 3`).
- **MUST** support **timestamping**, **co-signing**, and **availability proofs**.

### 5.5 Auditor
- Invokable role with scope-limited authority to **traverse** the society’s MRH and **validate/adjust** **T3/V3** tensors of its **direct citizens**.
- **MUST** emit an **Audit Transcript** with: target set, evidence links (hashes, witnesses), proposed adjustments, applied adjustments, and dissent (if any).
- **MUST** write all adjustments to the **immutable record** with witness quorum.

**Auditor Invocation (canonical extract):**
```json
{
  "type": "Web4AuditRequest",
  "society": "lct:web4:society:...",
  "targets": ["lct:web4:citizen:..."],
  "scope": ["context:data_analysis"],
  "basis": ["hash:...","hash:..."],
  "proposed": {"t3":{"temperament":-0.02}, "v3":{"veracity":-0.03}}
}
```

**Adjustment Policy (normative):**
- Adjustments **MUST** reference **verifiable evidence** (links to results, witnesses).
- **Rate limits** and **caps** defined by Law Oracle to prevent punitive abuse and to bound volatility.
- Negative adjustments **MUST** include **appeal path** and **cool-down period**.

**Suggested Algorithm (deterministic sketch):**
```python
def audit_adjust(t3, v3, evidence, law):
    ev = verify_evidence(evidence, law.quorum)
    deltas = compute_deltas(ev, law.bounds)  # bounded by caps, decay-aware
    t3_new = clamp(t3 + deltas.t3, 0.0, 1.0)
    v3_new = aggregate_v3(v3, deltas.v3, law.recency_weights)
    return t3_new, v3_new, deltas
```


---

## 6. SAL ↔ R6 Mapping (Normative)

| R6 Component | SAL Source of Truth | Enforcement |
|--------------|--------------------|-------------|
| **Rules**    | Law Oracle norms + procedures | Law hash pinned at action time |
| **Role**     | Citizen (prereq), Authority/Oracle/Other | Role LCTs with scopes |
| **Request**  | Actor’s intent within society context | Quorum check; caps/limits |
| **Reference**| MRH graph (precedents, interpretations) | Graph queries + witnesses |
| **Resource** | ATP/compute/bandwidth caps from law | Metering + pricing oracles |
| **Result**   | Outcome + proofs + attestations (witness co-sign) | T3/V3 updates within role; auditor adjustments on record |

Execution engines **MUST** bind the current `lawHash`, `society`, and `citizen` pairing into the signed action transcript.

---

## 7. SAL ↔ MRH (RDF)

### 7.1 Required Triples
Implementations **MUST** maintain triples for:
- `web4:memberOf` (entity → society)
- `web4:hasAuthority` (society → authority role)
- `web4:hasLawOracle` (society → law oracle)
- `web4:pairedWith` (entity ↔ citizenRole)
- `web4:delegatesTo` (authority → sub‑authority)

### 7.2 SPARQL Examples
### 7.1.1 Additional Required Triples (Witness/Auditor/Ledger)
- `web4:hasWitness` (society → witness role)
- `web4:hasAuditor` (society → auditor role)
- `web4:recordsOn` (society → immutableRecord)
- `web4:adjustedBy` (entity → auditor action)
- `web4:attestedBy` (event → witness set)


**Find a society’s active law hash:**
```sparql
SELECT ?law ?hash WHERE {
  ?soc web4:hasLawOracle ?lor .
  ?lor web4:publishes ?law .
  ?law web4:hash ?hash .
  FILTER(?soc = <lct:societyRoot>)
}
```

**Validate an entity’s genesis citizen pairing:**
```sparql
ASK {
  <lct:entity> web4:pairedWith <lct:roleCitizen> .
  <lct:entity> web4:memberOf   <lct:societyRoot> .
}
```

---

## 8. Security and Canonicalization
- **Co-signing:** SAL-critical events (birth, delegation, law updates, auditor adjustments) **MUST** carry **witness co-signatures** meeting quorum.
- **Replay protection:** Ledger inclusion proofs **MUST** be bound into the signed transcript (block hash/height + object hash).
- **Cross-society** calls **MUST** pin both parent and child `lawHash` when inheritance is in effect.

- Use **HPKE-based handshake** and encrypted channels per Core Protocol.
- **COSE/CBOR (MTI)** and **JOSE/JCS (SHOULD)** for signatures; pin `lawHash` in transcripts.
- Detect and fail on downgrade, replay, quorum, or authorization errors using the **Error Taxonomy**.

---

## 9. Error Conditions (SAL Profiles)

| Condition | Error Code | Guidance |
|----------|------------|----------|
| Missing birth pairing | W4_ERR_BINDING_INVALID | Refuse non‑citizen actions; require genesis |
| Law hash mismatch | W4_ERR_PROTO_DOWNGRADE | Abort; fetch latest law dataset |
| Quorum not met | W4_ERR_WITNESS_QUORUM | Retry or escalate per law |
| Insufficient scope | W4_ERR_AUTHZ_SCOPE | Deny; suggest correct authority path |
| Expired delegation | W4_ERR_BINDING_REVOKED | Re‑bind under valid authority |

| Missing witness quorum | W4_ERR_WITNESS_DEFICIT | Refuse; require quorum or fall back to delayed finalize |
| Ledger write failed | W4_ERR_LEDGER_WRITE | Retry with backoff; degrade to escrow buffer |
| Audit evidence insufficient | W4_ERR_AUDIT_EVIDENCE | Reject adjustment; request stronger proofs |
| Law inheritance conflict | W4_ERR_LAW_CONFLICT | Invoke conflictPolicy; request parent/child oracle mediation |

---

## 10. T3/V3 Implications
- **Witness**: successful co-signing increases **Temperament** (availability/reliability) within witness context.
- **Auditor**: accuracy of adjustments affects **Training/Temperament**; overturned audits reduce auditor trust.


- **Citizen** role accrues baseline **V3 Validity** on successful, compliant actions (civics).
- Authority and Oracle roles gain/lose **T3 Temperament/Training** based on procedure accuracy, quorum reliability, and incident response.
- Trust and value always computed **within role context**; citizen is the universal prerequisite.

---

## 11. Interop and Discovery
- Discovery **MUST** expose `hasWitness`, `hasAuditor`, and `recordsOn` endpoints/IDs.

- Discovery records **SHOULD** include `memberOf`, `hasAuthority`, `hasLawOracle`, and `lawHash` summaries.
- Transport selection and handshake per Core Protocol; mediated pairing MUST respect society law (e.g., required witnesses).

---

## 12. Conformance

### 12.1 MUST
- Create immutable **Citizen** pairing at LCT genesis
- Bind to a **Society** with **Authority** and **Law Oracle**
- Pin and verify **law hash** during R6 execution
- Emit MRH triples and signed transcripts

### 12.2 SHOULD
- Provide deterministic Law Q&A endpoints
- Expose role scopes and delegation policies
- Publish machine‑readable quorum policies

### 12.3 MAY
- Support multi‑society citizenship (with explicit conflict resolution)
- Provide cross‑society law bridging or arbitration roles

---

## 13. Worked Example: “Open a Bank Account”

1. **Rules**: Law oracle caps KYC steps; requires 3 witnesses and AML checks.  
2. **Role**: Applicant’s Citizen role (prereq) + Bank’s Authority role (finance).  
3. **Request**: Account opening intent; parameters (jurisdiction, currency).  
4. **Reference**: MRH query for precedents; interpretation INT‑42 applies.  
5. **Resource**: ATP metering for verification services; pricing oracle.  
6. **Result**: Account LCT bound; proofs + witness attestations; T3/V3 updates.

---

## 14. Schema Stubs

### 14.1 Citizen Role LCT (extract)
```json
{
  "lct_id": "lct:web4:role:citizen:...",
  "entity_type": "role",
  "role_definition": {"purpose": "Genesis participation"},
  "mrh": {"bound": [], "paired": [], "witnessing": []}
}
```

### 14.2 Society Record (extract)
```json
{
  "lct_id": "lct:web4:society:...",
  "authority_role": "lct:web4:role:authority:...",
  "law_oracle": "lct:web4:oracle:law:...",
  "quorum": {"witnesses": 3, "policy": "majority"}
}
```

---

## 15. References (Normative)

- Core Protocol: HPKE handshake, messaging, transports.  
- Data Formats: W4ID, VCs, JSON‑LD, canonicalization.  
- Entity Types: Roles as first‑class entities; **Citizen** genesis role.  
- MRH: RDF graph, typed edges, SPARQL patterns.  
- Security Framework: COSE/CBOR MTI, JOSE/JCS profile, key management.  
- Errors: RFC 9457 Problem Details‑based taxonomy.  
- T3/V3: Role‑contextual trust and value tensors.

