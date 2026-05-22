# Society Roles Specification

**Status**: Core Specification v0.1.0 (DRAFT)
**Date**: 2026-05-13
**Category**: Society Structure
**Extends**: `SOCIETY_SPECIFICATION.md` (single-society structural requirements)
**Companion to**: `entity-types.md` (taxonomy of entities that can fill roles), `inter-society-protocol.md` (inter-society interactions)

## Abstract

This specification enumerates the **roles** a Web4-compliant society MUST or MAY define within its governance structure. It establishes three tiers — base-mandatory, context-mandatory, and optional — and lists example entity types from `entity-types.md` that can fill each role.

The complementary structure is symmetric: `entity-types.md` lists entity types with example roles each can fill; this document lists roles with example entities each can be filled by. The two documents together specify the role↔entity mapping that defines Web4 society structure.

## Notation

Key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in this document are to be interpreted as described in RFC 2119.

## 1. Three Tiers of Roles

### 1.1 Base-mandatory

Roles that MUST be filled for any Web4 society to function at all. A society without any of these is not operational — it cannot mint ATP, cannot record events, cannot make decisions, cannot have members.

Other societies establish and maintain trust in a society by auditing that its base-mandatory roles are filled, are operating, and are producing the expected outputs (ledger writes from Archivist, ATP movements from Treasurer, policy decisions from Policy-Entity, etc.).

### 1.2 Context-mandatory

Roles that become mandatory based on the society's **outward-facing role** in the larger Web4 ecosystem. Examples:

- Society acts as **Banker** in fractal society → MUST have Auditor + Recovery-Authority internally
- Society acts as **Notary / Witness-Service** → MUST have Witness internally
- Society acts as **Court / Arbitration-Service** → MUST have Mediator + Auditor
- Society acts as **Federation-Member** → MUST have Diplomat role
- Society acts as **Standards-Body** → MUST have Auditor + Validator
- Society acts as **Cooperative** → MUST have Membership-Authority + Governance-Council
- Society acts as **Custodian-of-Records** → MUST have Archivist with redundancy + Auditor

See §3 for the full illustrative table of context-mandatory mappings.

Context-mandatory roles are determined by the society's claimed outward role plus the auditing standards of the societies it interacts with. A society claiming to act as Banker but lacking Recovery-Authority would be downgraded in T3 trust by other societies that audit the role.

The specific outward-role → required-inward-role mappings are themselves society-sovereign — different fractal societies may set different auditing standards for the same outward role. The Web4 standard does not normatively specify these mappings; it specifies the *property* that outward role implies inward structure, and provides example mappings as informative guidance.

### 1.3 Optional

Roles a society MAY define when its needs warrant, but that are not required for basic function or for the society's outward role. The list below is illustrative, not exhaustive — societies MAY define new roles as needed and SHOULD document them in their charter.

## 2. Base-Mandatory Roles

Every Web4-compliant society MUST have these seven roles filled. A single entity MAY fill multiple roles in a small society (e.g., a solo founder fills Sovereign + Treasurer + Administrator + Archivist + Citizen simultaneously). The roles must exist; how many entities fill them is per-society scale.

### 2.1 Sovereign

**Function**: Final authority for charter amendment and identity-of-last-resort. Without this, no agent of change exists for the society.

**Corporate analogue**: CEO / Founder / Board Chair

**Authority scope**:
- Ratifies charter amendments per the charter's own amendment mechanism
- Holds ultimate identity-recovery authority if no Recovery-Authority is defined
- Speaks for the society in extraordinary inter-society circumstances (war, dissolution, secession)

**Example filling entities**: Human, AI, Organization, Society (a founding society of a federation), Federation (when sovereignty is itself collective)

**Notes**:
- In autocratic societies, Sovereign is a single entity
- In democratic societies, Sovereign may be a Governance-Council (which is then mandatory for that society's structure)
- In federated societies, Sovereign is typically the collective of constituent societies acting under the federation's charter

### 2.2 Law Oracle

**Function**: Publishes machine-readable laws (norms, procedures, interpretations); signs interpretations and precedents; answers compliance queries with proof transcripts; maps laws to R6/R7 action grammar.

**Corporate analogue**: Published statutes + court precedents (the corpus juris itself, not the lawyer)

**Authority scope**:
- Publishes versioned law datasets
- Signs interpretations (which become precedent)
- Provides authoritative answers to compliance queries
- Does NOT make per-action approve/deny decisions (that is the Policy-Entity's role)

**Example filling entities**: Oracle (entity type), Service, Society (specialized law-publishing society), AI (when laws are algorithmically derived)

**Notes**:
- The Law Oracle is a *publisher of facts about the law*, not a *decision-maker about specific actions*
- This separation enables performance optimization (Policy-Entity caches; Law Oracle is slow authoritative source)
- This separation also enables accountability (Policy-Entity decisions are auditable; Law Oracle interpretations are versioned)

### 2.3 Policy-Entity

**Function**: Takes specific R6/R7 action requests, consults Law Oracle, evaluates against role-context-resource constraints, returns approve/deny/escalate with reasoning. Operates the per-action policy decision hot path.

**Corporate analogue**: General Counsel / Chief Compliance Officer (interprets the law for specific situations, doesn't write the law)

**Authority scope**:
- Receives R6/R7 requests from Administrators / Agents / Citizens
- Consults Law Oracle for authoritative law text
- Evaluates the request against the law in the current MRH context
- Returns signed decision: approve / deny / escalate (to HITL / Sovereign / Governance-Council)
- Decisions themselves are ledger artifacts; Policy-Entity's own T3/V3 evolves based on outcomes

**Example filling entities**: Policy (entity type, IRP-backed evaluation), AI (LLM-as-policy-evaluator), Human (manual approver for high-stakes), Society (compliance department as society), Hybrid (Human-with-AI-advisor)

**Notes**:
- This is the per-action policy evaluation function that enterprise implementations realize operationally
- A society MAY have multiple Policy-Entities at different MRH scopes (Compliance-Officer-for-Finance, Compliance-Officer-for-HR, etc.); the parent Policy-Entity delegates per scope
- Distinct from Law Oracle for performance, accountability, and architectural separation

### 2.4 Treasurer

**Function**: Operates the Treasury — mints ATP per the society's reification policy, allocates per society's law, accounts for ATP/ADP movements, settles inter-society exchanges.

**Corporate analogue**: CFO / Chief Financial Officer

**Authority scope**:
- Holds the keys (literal or delegated) for ATP minting
- Executes allocations per Law Oracle's published allocation rules
- Records ATP movements to the ledger (or instructs the Archivist to record)
- Negotiates exchange rates with peer society Treasurers at inter-society contact
- Reports treasury state per society's transparency policy

**Example filling entities**: Human, AI, Society (a treasury-services society), Organization, Hybrid

**Notes**:
- Treasury (the resource pool) is structural; Treasurer (the role) is functional. The pool exists in the ledger; the role does the operations on it.
- In societies with sensitive treasury operations, Treasurer should be paired with Auditor for accountability

### 2.5 Administrator

**Function**: Operational execution. Ensures the day-to-day mechanics work — citizen administration, R6/R7 dispatch routing, infrastructure liveness, scheduled jobs.

**Corporate analogue**: COO / Chief Operations Officer

**Authority scope**:
- Routes incoming R6/R7 requests to appropriate Policy-Entity / executor
- Manages citizen lifecycle events (admit, suspend, reinstate, exit) under Law Oracle constraints
- Operates infrastructure (or supervises it) — ledger writes commit, monitor daemons fire, alerts deliver
- Coordinates scheduled tasks (audit cadence, charter review periods, etc.)

**Example filling entities**: Human, AI, Society, Organization, Hybrid

**Notes**:
- In small societies, Administrator overlaps heavily with Sovereign
- In large societies, Administrator is typically a multi-entity organization
- Administrator does NOT make policy decisions (that's Policy-Entity's role) and does NOT make charter decisions (that's Sovereign's role); Administrator executes

### 2.6 Archivist

**Function**: Maintains ledger writes, history, retention; the role that actually writes to the ledger and ensures records are preserved per society's policy.

**Corporate analogue**: Corporate Secretary / Records Manager / Chief Information Officer (records side)

**Authority scope**:
- Writes entries to the society's ledger (or commits Treasurer/Policy-Entity entries through the Archivist for chain integrity)
- Maintains the cryptographic chain of the ledger
- Enforces retention policy (per society's law and any applicable external compliance)
- Provides historical query capability to authorized requesters
- Coordinates with Auditor (when present) for periodic review access

**Example filling entities**: Human, AI, Accumulator (entity type), Service, Society, Organization

**Notes**:
- The Archivist is the role that operationally writes the ledger that Witness signs and Auditor reviews
- For high-stakes societies, Archivist redundancy (multiple entities filling the role) is typical for availability

### 2.7 Citizen

**Function**: Basic membership role. At least one Citizen must exist for the society to have members; the Citizen role is the foundation upon which all other roles are built (a Treasurer is a Citizen first, then additionally a Treasurer).

**Corporate analogue**: Member / Employee / Participant (depending on society type)

**Authority scope**:
- Rights and obligations as defined by society's charter
- May propose actions, file disputes, vote (if society's governance includes voting)
- May be paired with additional roles (Treasurer, Witness, etc.) through the role-LCT-pairing mechanism

**Example filling entities**: Human, AI, Organization, Society (when one society is citizen of another in fractal nesting), any Agentic or Delegative entity

**Notes**:
- Citizenship is universal across Web4 entities; the citizen-role mechanics are detailed in `entity-types.md` §3.1
- Every entity in a Web4 society holds Citizen as its base role; additional roles are paired on top

## 3. Context-Mandatory Roles

These become mandatory based on the society's outward-facing role. Each row gives an illustrative outward role + the inward roles it typically forces. Specific mappings are society-sovereign; this table is informative.

| Outward role | Context-mandatory inward roles | Why |
|---|---|---|
| **Banker** (holds resources for others) | Auditor, Recovery-Authority | Custodianship requires audit trail + recovery from compromise |
| **Notary / Witness-Service** | Witness | The service IS attestation; can't provide it without the role |
| **Court / Arbitration-Service** | Mediator, Auditor | Decisions must be impartially mediated + auditable |
| **Standards-Body** | Auditor, Validator | Standards conformance requires verification |
| **Cooperative** (member-owned, member-governed) | Membership-Authority, Governance-Council | Member control mechanism must exist |
| **Custodian-of-Records** | Archivist (with redundancy), Auditor | Records must survive single-point failure + be auditable |
| **Federation-Member** (participates in higher-order society) | Diplomat | Inter-society representation required |
| **Public-Service-Provider** | Auditor, Validator | Public accountability requires verification + audit |
| **Recovery-Service** (for other societies' LCT recovery) | Recovery-Authority, Auditor | Recovery operations themselves need oversight |

A society audited by peers will be evaluated against the context-mandatory roles expected for its claimed outward role. Missing required inward roles result in T3 trust downgrade or refused federation.

## 4. Optional Roles

The following are commonly defined when needed. The list is illustrative, not exhaustive — societies MAY define new roles as their needs evolve and SHOULD document them in their charter.

### 4.1 Trust / Accountability

#### Witness

**Function**: Neutral attester for transactions; signs ledger entries to provide independent confirmation.

**Note**: At federation depth, Witness becomes structurally necessary even when optional at single-society level. See `inter-society-protocol.md` §4.6 for inter-society resource-measurement attestation (where the Witness role operates at the resource-attestation layer).

**Example filling entities**: Human, AI, Society (a witness-services society), Oracle (specialized for witnessing)

#### Auditor

**Function**: Periodic compliance / treasury / record review. Distinct from Witness in scope (audits patterns; witnesses attest events) and cadence (audits periodic; witnessing per-transaction).

**Example filling entities**: Human, AI, Society, Organization

#### Mediator

**Function**: Internal dispute resolution between citizens. Different from Auditor (which reviews) and Validator (which gates) — Mediator resolves disagreement after the fact.

**Example filling entities**: Human, AI, Society (an arbitration society), Hybrid

#### Validator

**Function**: Pre-commit action verification — gates an action before it executes/commits to the ledger. Different from Witness (which records after) and Auditor (which reviews periodically).

**Example filling entities**: AI, Service, Society, Oracle

### 4.2 Inter-Society

#### Diplomat / Federation-Representative

**Function**: Represents society in inter-society negotiations (first-contact protocol, federation formation, ongoing federation participation).

**Example filling entities**: Human, AI, Society (a diplomatic society), Organization

#### Agent (AGY)

**Function**: Specialized role for delegated authority; acts on behalf of a Client entity within scoped constraints. See `entity-types.md` §4.6.

**Example filling entities**: Human, AI, Service, Hybrid

#### Client (AGY)

**Function**: Principal entity in agency delegation. See `entity-types.md` §4.7.

**Example filling entities**: Human, AI, Organization, Society

### 4.3 Governance

#### Authority

**Function**: Scoped delegation powers (finance, safety, membership, etc.). Can create sub-authorities with limited scope. See `entity-types.md` §4.2.

**Example filling entities**: Human, AI, Organization, Society

#### Membership-Authority

**Function**: Controls admission of new citizens. Distinct from Sovereign when citizenship is open or large-scale (Sovereign doesn't gate every join).

**Example filling entities**: Human, AI, Service, Society

#### Governance-Council

**Function**: Collective body for charter amendments. Distinct from Sovereign when amendments require deliberation rather than unilateral decision.

**Example filling entities**: Society (the council is itself a society of members), Federation, Organization

#### Recovery-Authority

**Function**: Controls re-issuance of compromised LCTs. Essential for high-value societies where LCT compromise is real risk.

**Example filling entities**: Human, Society (a recovery-services society), Hybrid (Human-with-hardware-attestation)

### 4.4 Technical / Operational

#### Architect

**Function**: Technical direction for societies with significant technical surface. Maintains the technical decisions documented in the charter.

**Corporate analogue**: CTO / Chief Architect

**Example filling entities**: Human, AI, Society, Hybrid

#### Oracle (non-Law)

**Function**: External data provider for the society — price feeds, weather data, hardware attestation results, etc. See `entity-types.md` Oracle entity type.

**Example filling entities**: Oracle (entity type), Service, Device, Hybrid

#### Dictionary

**Function**: Living semantic bridges managing compression-trust between vocabularies. See `entity-types.md` Dictionary entity type.

**Example filling entities**: Dictionary (entity type), AI, Society, Hybrid

#### Steward

**Function**: Custodian of resources external to ATP — physical assets, IP rights, equipment that isn't fully reified into ATP. Optional; for societies that hold non-fungible resources.

**Example filling entities**: Human, Organization, Society

## 5. Fractal Composability

A normative property of every role defined in this specification:

> A role MAY be filled by any of:
> - A single entity (Human, AI, Service, Device, etc.)
> - A society (the role's responsibilities are discharged by the filling society's own operations)
> - A federation of societies (the role is discharged by inter-society arrangement)
>
> Role authority binds to the **role LCT**, not to the filling entity's LCT. When the filling entity changes, the role's history and authority continue uninterrupted; only the binding rotates per the role-LCT-rotation procedure.

This matches how corporations actually scale: a small startup's "CFO" is one human; a Fortune 500's "CFO" is supported by an entire Finance department which is itself a structured organization. The position is durable; the filling changes.

For Web4 specifically, this enables:

| Society scale | Role-filling pattern |
|---|---|
| Solo founder | One entity (human) fills 6+ of 7 base-mandatory roles |
| Small team (~5-20 members) | Each role typically one entity; some entities wear multiple hats |
| Medium organization (~50-500) | Each role is one team / sub-organization |
| Large enterprise (~1000+) | Each role is a sub-society; the society itself is a federation of role-societies |
| Federation | Shared roles (e.g., shared Treasurer for shared currency) are filled by federation-level sub-societies |

### 5.1 Multi-Hat Pattern (small societies)

A single human entity in a solo society can hold:
- Citizen role (base membership)
- Sovereign role (charter authority)
- Law Oracle role (law publishing; possibly minimal — one foundational law per charter)
- Treasurer role (ATP ops)
- Administrator role (execution)
- Archivist role (ledger writes)
- Policy-Entity role (per-action decisions; possibly with AI-assist)

This is structurally valid. The role-LCT pairing makes each hat-wearing explicit so accountability for actions remains traceable to the specific role even when one entity wears many.

### 5.2 Role-as-Society Pattern (large societies)

In a large enterprise society, the "Treasurer" role's LCT is held by a sub-society (e.g., "Finance Society") that has its own internal structure (its own Sovereign, Law Oracle, etc.). When the role acts, the action is signed by the Finance Society's society-LCT, with internal accountability handled within Finance Society.

### 5.3 Role-as-Federation Pattern (very large societies)

In federation contexts, a single role can be filled by a federation of sub-societies. Example: a multinational corporation's Treasurer might be a federation of regional Finance Societies (US-Finance, EU-Finance, APAC-Finance), each handling its region's ATP operations, federated under a shared charter that handles cross-region transactions.

## 6. Audit Implications

Other societies audit the role structure to establish and maintain trust. The audit attends to:

1. **Are all base-mandatory roles filled?** — A society missing any base-mandatory role is non-operational.
2. **Are the right context-mandatory roles filled for the society's claimed outward role?** — A self-described Banker without Auditor + Recovery-Authority is making claims it can't structurally back.
3. **Are role-LCT pairings current and witnessed?** (per `LCT-linked-context-token.md` witnessing requirements) — Stale pairings (filling entity left but role-LCT still binds to them) are an audit failure.
4. **Are roles' actions consistent with their authority scope?** — A Treasurer making policy decisions, or a Policy-Entity making charter amendments, indicates role-confusion.
5. **For societies with optional roles defined**: do the role's operations match the charter's description of the role's authority?

T3 trust scores for the society as a whole (in inter-society contexts) are derived in part from this audit.

## 7. Relationship to Other Specs

| Spec | Relationship |
|---|---|
| `SOCIETY_SPECIFICATION.md` | Specifies structural requirements (Law Oracle, Ledger, Treasury, Society LCT); this spec specifies the roles that operate on those structures |
| `entity-types.md` | Lists entity types with example roles each can fill; this spec lists roles with example entities each can be filled by (the symmetric dual) |
| `inter-society-protocol.md` | Inter-society interactions reference the Diplomat role (§2.2 federation genesis). This spec's §6.2 defines semantic viability criteria that constrain role composition. ATP measurement witnessing (§4.6) involves the Witness role at the resource attestation layer. Bidirectional dependency. |
| `mcp-protocol.md` | MCP actions consume the role taxonomy directly: Policy-Entity signs action decisions (§7.3), Witness co-signs high-consequence actions (§7.5), Archivist persists audit bundles (§7.3), Treasurer negotiates exchange rates (§7.7). |
| `web4-society-authority-law.md` | The SAL spec defines Citizen, Authority, Law Oracle, Witness, and Auditor from the Society–Authority–Law perspective with detailed normative requirements (birth certificates, delegation chains, ledger interfaces, audit transcripts). This spec provides the role taxonomy; SAL provides the operational protocol for a subset of those roles. |
| `r6-framework.md` | R6 actions are dispatched through Administrator, evaluated by Policy-Entity, witnessed by Witness, recorded by Archivist |
| `r7-framework.md` | R7 actions add Reputation back-propagation through the same role chain |
| `LCT-linked-context-token.md` | Each role has its own role-LCT; filling entities are paired with the role-LCT |
| `t3-v3-tensors.md` | Each (entity, role) pair has its own T3/V3 tensors; a single entity has different trust scores for different roles |

## 8. Future Work

The following remain open for v0.2+:

- **Role-LCT pairing protocol** — operational mechanics of pairing an entity to a role-LCT, rotating, suspending, and revoking. Currently implied by LCT spec; deserves explicit treatment.
- **Cross-role conflict resolution** — when a single entity holds multiple roles and their authorities conflict (Treasurer who is also Auditor: can they audit their own treasury operations?). Likely society-policy not protocol, but worth documenting patterns.
- **Role-specific T3/V3 sub-dimensions** — Treasurer-Talent and Witness-Talent are different specialized capabilities; the spec could enumerate sub-dimensions per role.
- **Role-deprecation lifecycle** — when a society removes a role from its charter, what happens to entities currently filling it? Their other roles continue; the deprecated role's authority is wound down.
- **Standardized context-mandatory mappings** — per §3, specific outward-role → required-inward-role mappings are society-sovereign. A future spec MAY establish standard mappings that the fleet collectively endorses, raising auditability.

## 9. Acknowledgments

This specification was substantially shaped by 2026-05-13 dialogue with dp on corporate-structure parallels and the role-of-roles within fractal societies. Particular acknowledgment for the context-mandatory framing: the idea that a society's outward-facing role determines its inward role requirements, and that this constraint is auditable. The Web4 model becomes substantially more concrete when the role taxonomy is made explicit.
