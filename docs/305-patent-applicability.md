# 305 Patent Family → Web4/Hardbound Applicability

## Purpose

This document maps the **305 patent family** (Metalinxx Inc.) to the **Web4 ontology** and **Hardbound enterprise implementation**. It exists so that web4 and hardbound sessions can understand the patent foundation without reading the patents themselves, and can design implementations that stay within — and build upon — the patented framework.

## Patent Family Overview

| Patent | Serial | Title | Status | Expires |
|--------|--------|-------|--------|---------|
| **US 11,477,027** (305) | 17/317,403 | Apparatus and Methods for Management of Controlled Objects | Issued 2022-10-18 | 2041-07-03 (adj. +53 days) |
| **US 12,278,913** (305CIP) | 17/710,759 | Apparatus and Methods for Management of Controlled Objects (Record Linking) | Issued 2025-01-14 | 2042-10-19 (adj. +526 days) |
| **305CON** | 19/178,619 | Continuation (same claims scope, different claim structure) | Pending | TBD |
| **305CIP2** | Not yet filed | Extension to Agentic Entities, T3/V3 Tensors, ATP/ADP | Draft stage | TBD |

**Assignee**: Metalinxx, Inc. (C-corp). Assignment recorded 2025-03-14.
**Inventor**: Dennis Palatov.
**Google Patents**: [US 11,477,027](https://patents.google.com/patent/US11477027B1) | [US 12,278,913](https://patents.google.com/patent/US12278913B2)

---

## Part 1: Issued Patents (305 + 305CIP) — The Foundation

### Critical Scope Difference Between the Two Issued Patents

Before diving into the terminology, understand this: **the two issued patents have very different claim scopes**.

**US 11,477,027 (305)** claims a **physical system** — Controlled Objects with electronic controllers, Pairing links, communications links to authentication controllers accessing blockchain databases. Claims require Product/Component/electronic controllers. 16 claims (2 independent: system claim + method-of-placing-into-use claim). Dependent claims specify electric vehicles, electric aircraft, and battery modules.

**US 12,278,913 (305CIP)** claims a **cryptographic association protocol** between any two *identifiable data records* managed by any two *Administrators* through any *Authentication Controller*. The physical object layer is **entirely optional** in the claims. 5 claims (1 independent method claim). The CIP introduces the Authorizer concept, Record Administrator, and a full PKI-mediated mutual association protocol.

**This means the 305CIP has dramatically broader applicability for Web4.** It covers the association of any two records — which could be LCT credentials, trust attestations, entity registrations, or any blockchain tokens — via a trusted intermediary that generates shared cryptographic material. Every MRH relationship, every LCT-to-LCT binding, every cross-society trust attestation is an instance of this patented protocol.

### Core Concept: Controlled Object Management System (COMS)

The patents define a **Controlled Object Management System (COMS 1000)** — a multi-domain system for managing the lifecycle of objects that have electronic controllers. The key insight is that an object's identity, capabilities, authorization, and trust are managed through **linked data records across multiple independent databases**, with **state transitions governed by certificates** issued by authentication controllers.

### Patent Terminology → Web4 Mapping

| Patent Term | Patent Definition | Web4 Equivalent | Notes |
|-------------|-------------------|-----------------|-------|
| **Controlled Object** | Physical object with Useful Function, having an electronic controller with control authority over Material Aspects | **Entity** (any of the 14+ types) | Patent scope is physical objects; 305CIP2 extends to all entities |
| **Electronic Controller** | Executes control program, has control authority over Material Aspects | **LCT binding + hardware anchor** | The controller IS the hardware presence. In Web4: TPM, secure element, FIDO2 key |
| **Useful Function** | The purpose and functionality for which the object is designed, manufactured, operated, and maintained | **Entity capabilities** (role-scoped) | Web4 adds role-contextuality: same entity, different useful functions per role |
| **Material Aspect** | Subset of Useful Function that, if restricted, restricts the function | **Scoped permissions** within role | The granular capabilities that can be individually authorized or restricted |
| **Authorizable Aspect** | Material Aspect subject to authorization, under controller authority | **PolicyGate-governed capabilities** | Things the system CAN control — e.g., an AI's access to external APIs |
| **Inherent Aspect** | Material Aspect critical to safety/integrity, NOT subject to authorization | **Hardcoded safety constraints** | Things that MUST work regardless of authorization state — emergency stop, data integrity |
| **Programmed State** | Subset of Useful Function embodied by controller execution, responsive to conditions | **Entity lifecycle state** | The patent defines 4 states (see below) |
| **Access Data** | Data to locate, identify, or transact with a Controlled Object | **LCT credential data** (lct_id, binding, public_key, hardware_anchor) | The identity primitive — how you find and verify an entity |
| **Use Data** | Authorization Data, expiration countdowns, historical records of Monitored Conditions | **T3/V3 tensors + MRH history** | The accumulated operational record |
| **Authorization Data** | Data received from Authentication Controller authorizing state transitions | **PolicyGate evaluation result** (PolicyEvaluation) | The trust verdict — approved/denied/conditional |
| **Authorization Certificate** | Affirmative certificate authorizing Material Aspects | **Signed attestation** (VerifiableCredential in hardbound) | The cryptographically signed proof of authorization |
| **Authentication Controller** | Accesses databases across domains, generates certificates | **Trust verification infrastructure** (W4ID + PolicyGate + witness network) | The system that evaluates trust and issues authorization |
| **Monitored Condition** | Condition monitored by electronic controller | **Observable state** in IRP consciousness loop | Sensor data, behavioral metrics, compliance status — inputs to trust evaluation |
| **Control Program** | Software executed by electronic controller | **Entity firmware/software** + PolicyGate policy model | The logic governing the entity's behavior |

### Programmed States → Entity Lifecycle

The patent defines four programmed states that map directly to Web4 entity lifecycle:

| Patent State | Patent Definition | Web4 Equivalent | Hardbound Implementation |
|--------------|-------------------|-----------------|-------------------------|
| **Passive** | All Material Aspects disabled/inhibited. Controller may be powered down. | **Uninitialized / Suspended** | Device registered but not active. No LCT binding yet, or binding revoked. |
| **Active** | At least one Material Aspect enabled, controlled responsive to Monitored Conditions. | **Active entity** in IRP loop | Device bound, LCT active, T3 tensor tracking, PolicyGate evaluating. |
| **Restricted Active** | Active, but some Material Aspects disabled/inhibited responsive to Authorization Data. Time/use countdown unless renewed. | **Degraded / Constrained** mode | Entity active but with reduced trust ceiling. PolicyGate restricting capabilities. CRISIS metabolic state. |
| **Unrestricted Active** | Active with affirmative Certificate authorizing substantially all Material Aspects. | **Fully trusted** | High T3 scores, full role permissions, all capabilities unlocked. |

**Key insight**: The patent's state model is a trust gradient, not a binary on/off. This directly maps to Web4's continuous T3 tensor (0.0→1.0) rather than discrete trust levels. A "Restricted Active" state is an entity with low T3 scores that still has partial capabilities — exactly how Web4 works.

### Pairing → Entity Binding

**Patent [71-72]**: "Pairing is the communicative or the communicative and physical coupling of two distinct identifiable Controlled Objects wherein the Useful Function of each is exercised substantially simultaneously responsive to a single Use Action by a User."

| Patent Concept | Web4 Equivalent | Example |
|----------------|-----------------|---------|
| **Pairing** (bidirectional) | **MRH Binding relationship** (permanent) | Device ↔ LCT hardware binding. Battery module ↔ vehicle. |
| **Pairing Event** | **Binding ceremony** (witnessed state transition) | Multi-device constellation creation. Birth certificate issuance. |
| **Pairing Certificate** | **Binding proof** (signed attestation) | W4ID binding proof with TPM attestation. |
| **Pairing Revocation** | **Binding termination** (with ledger record) | Device removal from constellation. LCT deactivation. |

**Critical patent detail**: Pairing creates mutual Access Data — each paired object records data about the other in its controller memory. In Web4 terms: when two entities bind, each stores the other's LCT reference in its MRH. The relationship is **bidirectional and attestable**.

### Association → Record Linking (305CIP)

**Patent [73]**: "Association is the data correspondence between an identifiable database record and an identifiable Controlled Object, or between two distinct identifiable database records."

This is the 305CIP's primary contribution — **linking records across databases and domains**.

| Patent Concept | Web4 Equivalent | Example |
|----------------|-----------------|---------|
| **Association** (bidirectional) | **MRH Pairing relationship** (session-based, mutual) | Two entities sharing data, mutual awareness |
| **Reference** (unidirectional) | **MRH Broadcast relationship** (one-way) | Public announcement, discovery beacon |
| **Cross-database Association** | **RDF triple linking** across contexts | Same entity referenced in Manufacture and Use databases = same LCT in different role contexts |
| **Record Administrator** | **Entity controller / LCT owner** | Computing resource with controlling access to a data record (can modify it) |
| **Authorizer** | **Delegation agent** | Controlled Object whose Useful Function is facilitating authorization of another object's state transitions |

**The patent explicitly anticipates RDF-like semantics**: records in different databases (domains) are linked by recording Access Data bidirectionally. This is exactly how MRH works — typed RDF edges connecting entities across contexts.

### 305CIP Cryptographic Association Protocol (Claim 1)

The 305CIP's independent claim describes a **full PKI-mediated mutual association protocol** — this is the patent foundation for every Web4 entity-to-entity relationship:

1. **First Administrator** generates Association Request (public key + encrypted request data)
2. Request submitted to **Authentication Controller** (trusted third party)
3. Authentication Controller **decrypts** request using first Administrator's public key
4. Authentication Controller **generates a private encryption key set** with portions for each record
5. Authentication Controller generates **Certificate** containing:
   - Access Data for both records (encrypted with Auth Controller's private key)
   - The first portion of the key set (encrypted with first Administrator's public key)
6. Certificate delivered; Administrator decrypts and stores
7. (Claim 2): Same process for the second Administrator with second Certificate
8. (Claim 3): Key set portions may be identical (symmetric communication)
9. (Claim 4): Subsequent secure messaging between Administrators using shared key set
10. (Claim 5): At least one record may be an NFT

**Web4 mapping**: This is the protocol for establishing any MRH relationship:
- Administrator = entity's LCT controller (the hardware-bound identity manager)
- Authentication Controller = witness network / trust verification infrastructure
- Private encryption key set = shared session material for bound entities
- Certificate = signed binding attestation (VerifiableCredential)
- The entire flow is: two entities request association → trusted authority verifies both → generates shared cryptographic material → both entities can now communicate securely

**This protocol covers**: LCT binding events, device constellation creation, role pairings, cross-society trust attestations, any two-party cryptographic handshake mediated by a trusted verifier.

### Domains → Life Cycle Facets

**Patent [75-77]**: Three life cycle facet categories, each containing multiple domains:

| Patent Category | Patent Domains (examples) | Web4 Equivalent |
|-----------------|---------------------------|-----------------|
| **Manufacture** | Product domain (vendors, suppliers, components) | **Creation context** — birth certificate, genesis block, manufacturing provenance |
| **Use** | Commerce domain (dealers, operators, consumers) | **Operational context** — active roles, transactions, pairings |
| **Compliance** | Federal domain (government agencies, regulators) | **Oversight context** — SAL governance, audit, policy compliance |

**Key insight**: The patent's multi-domain architecture is the structural precursor to Web4's SAL (Society-Authority-Law) framework:
- **Society** ≈ Use domains (where entities interact)
- **Authority** ≈ Compliance domains (who verifies and enforces)
- **Law** ≈ The rules governing transitions between domains

The patent also notes [77] that organizations can have departments in different domains — e.g., FAA's certification office (Compliance) vs. Air Traffic Organization (Use). This maps to Web4's concept of role-contextual identity: same organization, different T3 tensors per role.

### Access Data — The Connective Tissue

Access Data is the fundamental primitive connecting every element. It operates at three levels that map directly to Web4's identity hierarchy:

| Patent Layer | Patent Definition | Web4 Equivalent |
|--------------|-------------------|-----------------|
| **COAD** (Controlled Object Access Data) | Unique PIN + encryption keys stored in electronic controller memory | **LCT binding** (lct_id + public_key + hardware_anchor) |
| **RAD** (Record Access Data) | Unique identifier for each database record (Token/Wallet) | **MRH node identifiers** (RDF subject/object URIs) |
| **ACAD** (Authentication Controller Access Data) | URL/identifier of the authentication controller, stored in every object's memory | **Witness/Authority endpoint** (society authority URLs, trust oracle addresses) |

The Access Data architecture creates a **bidirectional lookup graph**: from any node (entity or record), you can traverse to any associated node by following stored Access Data. This is structurally identical to an RDF graph where every triple has a subject, predicate, and object — and you can traverse in any direction.

### Cross-Domain Transaction Mechanisms

The patent defines two inter-domain communication patterns that map to Web4's cross-society interactions:

| Patent Mechanism | Description | Web4 Equivalent |
|------------------|-------------|-----------------|
| **Administrative Change (810)** | Two-way communication requiring acknowledgment. Metadata in one database modified responsive to modification in associated record in another database. | **Witnessed state transition** — both parties update MRH, witnesses co-sign |
| **Administrative Notice (820)** | One-way communication, no acknowledgment required. Second database MAY modify responsive to changes. | **Broadcast event** — MRH Broadcast relationship, public announcement |

### Inter-Domain Transactions

**Patent [76]**: "Entities within one domain may from time to time transact with entities within another domain. Such transactions are referred to as inter-domain transactions herein."

This maps directly to **cross-society interactions** in Web4's SAL framework, and to **MRH graph traversal** when evaluating trust across contexts. The patent establishes the principle that trust must be re-evaluated at domain boundaries — you can't assume trust in one context transfers automatically to another.

### Entity Lifecycle (Patent FIG. 14 → Web4)

The patent defines the complete lifecycle, which maps to Web4 entity lifecycle:

| Phase | Patent Flow | Web4 Equivalent |
|-------|-------------|-----------------|
| **Manufacture** (Block 701) | Physical object manufactured. PIN assigned, COAD generated, control program stored. Tokens created in Manufacture and Compliance databases. | **Entity creation**: LCT minted, birth certificate issued, initial T3 tensor set, hardware binding established. |
| **Compliance** (Block 703-704) | Compliance entity verifies manufacture certifications, issues type certificate (airworthiness, manufacturer's certificate). Authorization Data recorded. | **Authority validation**: Compliance check against Society Law. Role eligibility verified. Initial trust attestation. |
| **Release to Use** (Block 705-707) | Use category Token created. Physical transfer to Use entity. Object enters Passive Programmed State. | **Activation**: Entity paired with operational role. LCT enters Active state. T3 tracking begins. |
| **Active Operation** (FIGS. 5-7) | Use Actions trigger Controllable Events. Certificate requests → Authentication Controller → Certificates. State transitions between Passive/Active/Restricted/Unrestricted. | **IRP consciousness loop**: Actions evaluated by PolicyGate. T3 updated per R6/R7 cycles. State transitions continuous. |
| **Suspension** (Block 885) | Safety recall, non-payment, airworthiness directive → Corrective action required. | **Degraded state**: CRISIS metabolic mode. Trust ceiling lowered. Capabilities restricted pending resolution. |
| **Retirement** (Block 715) | Physical removal from service. Authorization Data updated to reflect discontinuation. | **Entity deactivation**: LCT revoked or archived. MRH relationships terminated. Audit trail preserved. |

### 305 Claim Structure Summary (For Reference)

**US 11,477,027 — 16 Claims:**
- **Claim 1** (System): Authentication controller + first Controlled Object (Product) + second Controlled Object (Component) + Pairing link + communications link + Certificate request/response flow
- **Claim 11** (Method): Steps to place assembled Controlled Object into use across Manufacture → Compliance → Use domains with record creation and association at each step
- **Claims 2-4**: Internet connection, secure messaging on both links
- **Claim 5-7**: Blockchain/NFT embodiment with ledger recording
- **Claim 8**: Cross-domain Authorization Data
- **Claims 9-10, 12-15**: Electric vehicle and aircraft embodiments
- **Claim 16**: Association of Compliance record with Controlled Object

**US 12,278,913 — 5 Claims:**
- **Claim 1** (Method): Association of two identifiable data records via PKI-mediated protocol through Authentication Controller
- **Claim 2**: Bilateral — second Administrator also receives Certificate and key set portion
- **Claim 3**: Symmetric — key set portions may be identical
- **Claim 4**: Subsequent secure messaging using shared key set
- **Claim 5**: At least one record is an NFT

---

## Part 2: Hardware Binding — The Bridge

The patent's requirement that every Controlled Object has an **electronic controller** with **control authority** is the direct architectural ancestor of Web4/Hardbound's hardware binding requirement.

### Patent Architecture → Hardbound Implementation

| Patent Element | Hardbound Implementation | File |
|----------------|-------------------------|------|
| Electronic Controller (device with control program) | **Hardware anchor** (TPM 2.0, FIDO2, Secure Element) | `hardbound/src/core/multi-device-binding.ts` |
| Access Data (stored in controller memory) | **W4ID** (DID-like identifier derived from hardware key) | `hardbound/src/core/w4id.ts` |
| Control Program (executed by controller) | **PolicyGate** (Phi-4 Mini policy model) | `hardbound/src/policy-model/index.ts` |
| Authorization Certificate | **VerifiableCredential** (RFC 8785 JCS signed) | `hardbound/src/core/w4id.ts` |
| Monitored Conditions | **IRP sensor inputs** (SAGE consciousness loop) | `HRM/sage/` |
| Pairing (mutual Access Data exchange) | **Device Constellation** (multi-device binding) | `hardbound/src/core/multi-device-binding.ts` |

### Trust Ceilings

The patent's **Authorizable vs. Inherent Aspects** distinction maps to Hardbound's **trust ceiling** model:

```
Anchor-specific trust ceilings:
  Software alone:           0.40  (many Authorizable Aspects restricted)
  FIDO2 + Phone:            0.90  (most Authorizable Aspects available)
  FIDO2 + Phone + TPM:      0.95  (nearly all Authorizable Aspects available)
```

An entity's maximum achievable trust is bounded by its hardware binding quality — just as the patent constrains which Material Aspects are Authorizable based on the electronic controller's capabilities.

### The "Controller Authority" Principle

**Patent [78]**: "control authority being embodied by execution of a control program by the electronic controller"

This is the single most important sentence for Web4/Hardbound alignment. It establishes that **authority over an entity's capabilities is exercised through software running on hardware that is bound to that entity's identity**. This is exactly:

- **W4ID**: Identity derived from hardware key (Ed25519 on TPM)
- **PolicyGate**: Control program (Phi-4 Mini) executing on the bound device
- **LCT binding proof**: Cryptographic attestation that this specific hardware runs this specific control program for this specific entity

---

## Part 3: 305CIP2 Draft — The Extension to Web4

The 305CIP2 (not yet filed) explicitly extends the framework to **agentic entities** and introduces the full Web4 trust stack.

### New Concepts in 305CIP2

| 305CIP2 Concept | Definition | Web4 Spec Reference |
|-----------------|------------|---------------------|
| **Agentic Entity** | Any entity capable of autonomously initiating an action in response to its autonomous decision-making (AI, humans, organizations, DAOs) | `entity-types.md` — Agentic mode entities |
| **T3 Scale** | Talent, Training, Temperament — tensor characterizing entity capabilities, experience, and behavioral tendencies | `t3-v3-tensors.md` |
| **V3 Metric** | Valuation, Veracity, Validity — value assessment complement to T3 | `t3-v3-tensors.md` |
| **ATP/ADP Tokens** | Semi-fungible tokens in charged (ATP) and discharged (ADP) states, representing energy/resource allocation and value validation | `atp-adp-cycle.md` |
| **AIID** | AI Identifier — uniquely generated from timestamp, seed, model identifier | `entity-types.md` — AI entity type |
| **DIID** | Deployment Instance Identifier — distinguishes instances of same base model | Related to W4ID pairwise derivation |
| **Linked Control Token (LCT)** | Non-fungible blockchain token paired with at least one other identifiable data record | `LCT-linked-context-token.md` |

### T3 Mapping: Patent → Web4

The patent defines T3 as a **descriptor-based tensor** (not predetermined values). This is exactly how Web4 implements it:

**For Controlled Objects (battery modules — the Trojan horse):**

| T3 Dimension | Patent Definition | Battery Module Example | Web4 Generalization |
|--------------|-------------------|----------------------|---------------------|
| **Talent** | Design performance, manufacturer's reputation, certifications/approvals | Capacity (Ah), voltage range, max charge/discharge rates, cell type/chemistry | Natural aptitude for role. Inherent capabilities. What the entity CAN do. |
| **Training** | Maintenance, upgrades/mods, software/hardware updates, recalls | Software revision, validation testing, initial conditioning | Learned skills, accumulated experience. How the entity has been SHAPED. |
| **Temperament** | Operational history (both specific unit and batch/model), accidents/mishaps | State of health, charge history, overcharge/overdischarge/overtemp events, cycle count | Behavioral consistency, reliability. How the entity ACTUALLY BEHAVES. |

**For AI Systems:**

| T3 Dimension | 305CIP2 Definition | Web4 Implementation |
|--------------|--------------------|---------------------|
| **Talent** | Model architecture, computational capability, parameter count, specialized skills | Role-scoped: same AI has different Talent scores for "code review" vs "medical diagnosis" |
| **Training** | Training data provenance, dataset diversity, version history, retraining cycles | Accumulated through R6 actions: +0.02-0.05 for novel success |
| **Temperament** | Ethical guidelines compliance, behavioral metrics, safety protocol adherence, reliability | CRISIS mode changes accountability equation but Temperament continues tracking |

**Critical design alignment**: The patent establishes T3 as **role-contextual** through the domain structure. A battery module's T3 in the Manufacture domain (quality testing, certification) is different from its T3 in the Use domain (operational reliability, user satisfaction). Web4 formalizes this as: **T3 tensors exist only within role contexts. Same entity, different roles, different T3 values.**

### The Immune System Metaphor

From the T3/AI conversation, Dennis identified the key architectural role of T3 in controlled object ecosystems:

> "Critical incidents could trigger immediate trust level changes" — this is why LCT/T3 ecosystem would be a critical coherence mechanism.

The patent establishes the mechanism:
1. **Monitored Conditions** detect anomalies (Temperament tracking)
2. **Authentication Controller** re-evaluates authorization (PolicyGate)
3. **State transition** restricts capabilities (Restricted Active state)
4. **Cross-domain propagation** — incidents in one domain affect trust in others (inter-domain transactions)
5. **Population-level learning** — issues with similar entities affect trust across the batch/model (hierarchical trust)

Web4 implements this as: **Trust is not a side effect — it's the product.** Every R6 transaction produces reputation deltas. Critical incidents propagate through the MRH graph. PolicyGate responds in real-time.

---

## Part 4: Implementation Alignment

### What Web4/Hardbound Sessions Should Know

1. **Every LCT is a Controlled Object's digital twin.** The patent's Access Data (identity), Use Data (history), Authorization Data (trust), and Control Program (policy) map 1:1 to LCT structure (binding, MRH, T3/V3, PolicyGate).

2. **Programmed States are continuous, not discrete.** The four patent states (Passive → Active → Restricted Active → Unrestricted Active) map to the T3 tensor range (0.0 → 1.0). Don't implement them as enum values — they're regions on a continuous trust gradient.

3. **Pairing is bilateral and attestable.** When two entities bind, both must record the relationship in their MRH. This is not a reference/pointer — it's a mutual commitment with witnesses.

4. **Domains scope trust.** Trust earned in one domain does not automatically transfer. This is the patent foundation for Web4's role-contextual T3 tensors.

5. **The hardware anchor IS the electronic controller.** Hardbound's TPM/FIDO2/SE binding is not just a security feature — it's the realization of the patent's requirement that every entity has a controller with authority over its Material Aspects.

6. **Authorization requires cross-domain verification.** The Authentication Controller accesses databases across Manufacture, Use, AND Compliance domains before issuing certificates. PolicyGate should similarly check multiple contexts before approving actions.

7. **Revocation is recorded, not just executed.** The patent specifies that Pairing revocation may be recorded in a ledger. Every trust state change should be auditable.

### Architecture Checklist for Implementation

When implementing Web4/Hardbound features, verify alignment with the patent framework:

- [ ] Does the entity have a hardware-bound identity? (Electronic Controller requirement)
- [ ] Are capabilities scoped to roles? (Material Aspects are function-specific)
- [ ] Can individual capabilities be independently authorized/restricted? (Authorizable Aspects)
- [ ] Are safety-critical functions protected from authorization logic? (Inherent Aspects)
- [ ] Are state transitions governed by certificates from a verification authority? (Authentication Controller)
- [ ] Is trust evaluated across multiple domains before authorization? (Cross-domain verification)
- [ ] Are bindings bidirectional with mutual data exchange? (Pairing semantics)
- [ ] Are all state transitions recorded in an auditable ledger? (Ledger recording)
- [ ] Does trust degrade with inactivity or adverse events? (Restricted Active with countdown)
- [ ] Can the system respond to critical incidents with immediate trust adjustments? (Immune system)

---

## Part 5: Strategic Context

### The Battery Module Entry Point

The 305 family was originally filed for **modular battery management** — physical Controlled Objects with electronic controllers managing charge/discharge, authentication, and pairing. This is the pragmatic entry point:

1. **Battery modules** are the first Controlled Objects with real LCTs
2. **T3 for batteries** is concrete and measurable (capacity = Talent, testing = Training, reliability = Temperament)
3. **The framework is proven with physical objects** before extending to agentic entities
4. **305CIP2** extends the same framework to AI, humans, and organizations

This "under the radar" approach — building the trust infrastructure through practical battery management before revealing its applicability to AI governance — is deliberate strategy.

### Patent Coverage Analysis

| Web4/Hardbound Concept | Patent Coverage | Notes |
|------------------------|----------------|-------|
| Physical controlled objects + multi-domain management | **COVERED** (305) | System + method claims. EV, aircraft, battery module embodiments. |
| Cryptographic record association protocol | **COVERED** (305CIP) | Broadly claims ANY two identifiable data records via PKI/Auth Controller. This is the broadest coverage. |
| NFT/blockchain as identity record | **COVERED** (305 Claim 5, 305CIP Claim 5) | Dependent claims but explicitly covered. |
| Cross-domain authorization verification | **COVERED** (305 Claim 8) | Auth Data from second domain used in first domain. |
| Hardware-bound identity (electronic controller) | **COVERED** (305) | Core of Claim 1: electronic controller with control program executing authority. |
| Bilateral binding with mutual data exchange | **COVERED** (305 Pairing + 305CIP Association) | Pairing = physical, Association = data records. Both bidirectional. |
| Secure inter-entity communication | **COVERED** (305CIP Claim 4) | Post-association secure messaging using shared key set. |
| Authorizer delegation pattern | **COVERED** (305CIP) | Authorizer = entity whose function is facilitating another's state transitions. |
| Agentic entities (AI, humans, organizations) | **DRAFT** (305CIP2) | File CIP2 — extends to all entity types |
| T3 tensor trust metrics | **DRAFT** (305CIP2) | File CIP2 — tensor-based trust quantification |
| V3 value metrics | **DRAFT** (305CIP2) | File CIP2 — value assessment complement |
| ATP/ADP energy tokens | **DRAFT** (305CIP2) | File CIP2 — metabolic resource allocation |
| Role-contextual trust (same entity, different roles) | **IMPLIED** by domain structure | Consider making explicit in 305CIP2 |
| Multi-witness verification | **PARTIAL** (Auth Controller is single point) | 305CIP2 could add witness quorum semantics |
| Society/Authority/Law governance | **NOT COVERED** | Consider separate filing or inclusion in 305CIP2 |
| MRH as RDF graph | **NOT COVERED** | Implementation detail — patent uses "database records" which is broader |

### Filing Priority

The 305CIP2 is the critical bridge. It extends the issued patent's physical-object framework to cover the full Web4 entity taxonomy. Key claims to protect:

1. **T3 tensor integrated into LCT** for any entity type (not just physical objects)
2. **Dynamic T3 updates** responsive to real-time operational data
3. **V3 value assessment** as complement to T3 trust assessment
4. **ATP/ADP** semi-fungible tokens for metabolic resource allocation
5. **Cross-entity-type trust evaluation** (AI ↔ human ↔ organization interactions)

---

## References

### Patent Documents
- `305 - 17317403 controlled object/` — Original 305 filing documents
- `305CIP - 17710759 record link/` — 305CIP filing and office actions
- `305CIPCON/` — 305CIP continuation (305CON, serial 19/178,619)
- `305CIP2/` — Draft CIP2 materials (background, LCT expansion, T3 mapping, ChatGPT/Claude collaboration)

### Web4 Specifications
- `web4/web4-standard/core-spec/entity-types.md` — Entity taxonomy
- `web4/web4-standard/core-spec/t3-v3-tensors.md` — Trust/Value tensor spec
- `web4/web4-standard/core-spec/LCT-linked-context-token.md` — LCT structure
- `web4/web4-standard/core-spec/mrh-tensors.md` — MRH as RDF graph
- `web4/web4-standard/core-spec/reputation-computation.md` — R7 reputation deltas
- `web4/web4-standard/core-spec/multi-device-lct-binding.md` — Hardware binding protocol

### Hardbound Implementation
- `hardbound/src/core/w4id.ts` — W4ID/DID implementation
- `hardbound/src/core/types.ts` — Trust tensor types
- `hardbound/src/core/multi-device-binding.ts` — Device constellation
- `hardbound/src/policy-model/index.ts` — PolicyGate

### Key Conversations (in 305CIP2/)
- `T3 applied to CO.pdf` — Dennis's T3 → Controlled Object mapping
- `T3 and AI.pdf` — T3 as immune system for complex systems
- `Expanding Linked Control Tokens.pdf` — Full 305CIP2 draft specification
- `gpt outline.pdf` — ChatGPT CIP outline with LCT/T3/V3/ATP integration
- `background.txt` — 305CIP2 background section (agentic entities)
