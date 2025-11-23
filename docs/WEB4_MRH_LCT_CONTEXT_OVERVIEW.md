# Web4 MRH–LCT Context Overview

## Purpose

This document summarizes how Web4 intends to use MRH (Markov Relevancy Horizon) together with Linked Context Tokens (LCTs), contrasts that vision with the current implementation, and outlines a pragmatic path forward.

It is a high-level, **public-facing** overview; detailed internal coordination lives in the private `private-context` repo.

---

## 1. MRH in Synchronism (brief recap)

Synchronism formalizes a Markov Relevancy Horizon as:

- **MRH = (ΔR, ΔT, ΔC)**
  - **ΔR** – spatial extent.
  - **ΔT** – temporal extent.
  - **ΔC** – complexity extent (accessible degrees of freedom).

Key ideas:

- **Horizon-relative truth** – each witness has its own horizon `H`, and the set of valid statements `Truth(H)` depends on that horizon.
- **Complexity as a dimension** – `ΔC` is a first-class axis, like space and time; different complexity bands expose different effective physics and emergent behavior.
- **Transformations between horizons** – moving from `H1` to `H2` requires explicit transformation `F: Truth(H1) → Truth(H2)`.

For Web4, MRH is the rigorous notion of a **context window** for identity, trust, and obligations.

---

## 2. Intended role of MRH in Web4 LCTs

Web4 defines **Linked Context Tokens (LCTs)** as unforgeable identity primitives bound to Ed25519 keys and used to represent agents, roles, societies, and resources.

The whitepaper vision (and related internal design notes) intend that:

- An LCT should **carry context**, not just identity.
- This context includes **Meaning / Relevance / Helpfulness (MRH)** in the Synchronism sense.
- MRH for an LCT is expressed as a structured **neighborhood of related LCTs**, not just a scalar score.

Concretely, the vision is that each LCT has an associated **RDF-like subgraph**:

- Nodes: LCTs (agents, societies, roles, resources, witnesses).
- Edges: typed predicates encoding contextual relationships, e.g.:
  - `(this_lct, web4:relevantTo, other_lct)`
  - `(this_lct, web4:helpsWith, resource_lct)`
  - `(this_lct, web4:withinHorizon, mrh_profile)`
- MRH metadata constrains the **horizon** in which these relationships are valid, using a discretized form of `(ΔR, ΔT, ΔC)`.

So in the intended design:

> **MRH for an LCT = its RDF-bound, horizon-scoped neighborhood in the Web4 trust / intent graph.**

---

## 3. Current implementation status

### 3.1 LCT specification

`web4-standard/implementation/act_deployment/LCT_SPECIFICATION.md` currently focuses on:

- LCT URI format and identifier derivation.
- Cryptographic binding to Ed25519 public keys.
- Usage in messaging, marketplaces, trust propagation, and energy (ATP/ADP) accounting.

Today, the spec **does not yet** define:

- An explicit MRH field or horizon profile on LCTs.
- An RDF or graph representation of LCT–LCT contextual links.
- A query interface for MRH-scoped neighborhoods.

### 3.2 Code-level usage

Across Web4 and ACT:

- LCTs appear mainly as **identifiers** (e.g. `society_lct`, `agent_lct`, role LCTs) in messages and events.
- Trust (T3) and ATP/ADP logic operate **per agent / per transaction**, without explicit MRH modeling.
- ACT events and keeper logic already produce **RDF-like tuples** (subject/predicate/object semantics), but:
  - They are not stored in a queryable RDF or graph store.
  - There is no standardized vocabulary for MRH predicates.

Net result: the system already emits many of the **raw relational facts** needed for MRH context graphs, but lacks a first-class MRH and RDF layer.

---

## 4. Gaps vs. the whitepaper vision

### 4.1 Conceptual gaps

- **No explicit MRH on identities**
  - LCTs lack any explicit `(ΔR, ΔT, ΔC)` or discretized horizon profile.
  - Statements about identity, trust, and law are effectively treated as **global**, not horizon-limited.

- **No MRH–trust coupling**
  - T3 trust scores are global scalars per agent.
  - There is no notion of “trusted at low complexity / short time horizons, not trusted at high complexity / long time horizons.”

- **Meaning/Relevance/Helpfulness is implicit**
  - MRH is present in narrative and design documents, but not as a typed data structure connected to LCTs.

### 4.2 Data-model gaps

- **Missing RDF context for LCTs**
  - No canonical triple representation of relational facts between LCTs.
  - No schema for predicates like `web4:relevantTo`, `web4:helpsWith`, `web4:withinHorizon`.

- **No MRH metadata section in LCT spec**
  - LCTs have identity, cryptographic, and energy semantics, but no **horizon semantics**.

### 4.3 API and enforcement gaps

- **No MRH-aware APIs**
  - Clients cannot query “the MRH context” or “neighbors within a given horizon” for an LCT.

- **No MRH-aware enforcement**
  - Policies (e.g. trust-gated purchases) are scalar thresholds on price and trust.
  - They do not adjust behavior based on complexity or horizon.

---

## 5. Proposed direction to close the gaps

The following is the high-level plan; details are in the dedicated MRH/LCT context spec file in the `web4` repository.

### 5.1 Add an MRH + RDF schema for LCTs (spec level)

- Define a **discretized MRH profile** for practical use, mapped to Synchronism’s `(ΔR, ΔT, ΔC)`.
- Define a minimal RDF-like model for LCT context:
  - `subject`: LCT URI.
  - `predicate`: `web4:*` vocabulary.
  - `object`: LCT URI or literal.
  - Optional attached MRH constraints.

### 5.2 Extend the LCT spec with optional MRH metadata

- Add an optional MRH section to the LCT spec, specifying how implementations may attach:
  - Horizon profile.
  - Context triples.

### 5.3 Implement a lightweight LCT context graph in Web4

- Introduce an in-process **LCT context graph** helper that:
  - Stores and queries triples between LCTs.
  - Supports simple MRH filters (by discretized horizon profile).
- Seed the graph using existing Web4 and ACT events (e.g., energy discharge events, settlement logs).

### 5.4 Make trust and policy MRH-aware over time

- Annotate trust metrics (e.g., T3 tensors) with MRH profiles.
- Adapt policies (like high-value purchase gates) to consider MRH context, not just global trust scores.

---

## 6. Relationship to private-context and Synchronism

- **Synchronism** provides the theoretical definition of MRH and the math behind `(ΔR, ΔT, ΔC)`.
- **Web4 public repo** houses:
  - The LCT spec.
  - The MRH/LCT context spec.
  - Public documentation like this overview.
- **private-context repo** hosts internal notes, research logs, and coordination documents that:
  - Track how these concepts are being implemented.
  - Capture design discussions and experiments that are not yet ready for publication.

This division keeps the public Web4 standard precise and focused, while enabling richer internal iteration in private-context.
