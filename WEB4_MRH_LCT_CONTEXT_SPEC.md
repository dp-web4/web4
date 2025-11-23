# Web4 MRH + LCT Context Specification

**Status:** Draft (experimental)

This document specifies how Web4 associates **Markov Relevancy Horizons (MRH)** with **Linked Context Tokens (LCTs)** using a small, RDF-like context model.

It is intended to complement, not replace, the core LCT specification in `web4-standard/implementation/act_deployment/LCT_SPECIFICATION.md`.

---

## 1. Terminology

- **LCT** – Linked Context Token, an identity primitive bound to a public key, as defined in the LCT specification.
- **MRH** – Markov Relevancy Horizon, a triple `(ΔR, ΔT, ΔC)` from Synchronism:
  - `ΔR`: spatial extent.
  - `ΔT`: temporal extent.
  - `ΔC`: complexity extent.
- **MRH profile** – a discretized representation of MRH suitable for implementation.
- **Context triple** – a record `(subject, predicate, object, mrh?)` describing a typed relationship between LCTs, optionally scoped by MRH.

---

## 2. MRH profiles

### 2.1 Discretization

Web4 implementations SHOULD represent MRH using **discrete profiles** rather than raw real-valued `(ΔR, ΔT, ΔC)` tuples.

A recommended initial discretization is:

- **Spatial extent (ΔR):**
  - `local`
  - `regional`
  - `global`
- **Temporal extent (ΔT):**
  - `ephemeral` (seconds to minutes)
  - `session` (minutes to hours)
  - `day` (hours to a day)
  - `epoch` (days to months or longer)
- **Complexity extent (ΔC):**
  - `simple` (single interaction, low-dimensional state)
  - `agent-scale` (multi-step behavior by a single agent)
  - `society-scale` (multi-agent, policy/treasury-level behavior)

Implementations MAY define additional or alternative bins, but SHOULD document the mapping between their bins and the underlying `(ΔR, ΔT, ΔC)` interpretation.

### 2.2 MRH profile object

An MRH profile is represented as a JSON-like object:

```json
{
  "deltaR": "local|regional|global",
  "deltaT": "ephemeral|session|day|epoch",
  "deltaC": "simple|agent-scale|society-scale"
}
```

Implementations MAY extend this with additional fields but MUST preserve the above semantics.

---

## 3. LCT MRH metadata

### 3.1 Optional MRH section on LCTs

The core LCT definition remains unchanged. This specification adds an **optional MRH metadata section** that can be associated with an LCT.

An example LCT record with MRH metadata might include:

```json
{
  "lct": "lct:web4:society:demo-agent",
  "mrh": {
    "defaultProfile": {
      "deltaR": "local",
      "deltaT": "session",
      "deltaC": "agent-scale"
    }
  }
}
```

Semantics:

- `defaultProfile` describes the **horizon in which statements about this LCT are intended to hold by default**.
- Implementations MAY support multiple profiles per LCT for different classes of statements, but that is out of scope for this initial draft.

### 3.2 Interpretation

Clients interpreting an LCT with MRH metadata SHOULD:

- Treat associated identity, trust, and obligation statements as **horizon-relative** to the MRH profile.
- Avoid assuming that statements automatically generalize beyond the declared profile (e.g., from `agent-scale` to `society-scale`).

---

## 4. LCT context triples

### 4.1 Data model

A **context triple** links LCTs (or an LCT and a literal) with an optional MRH profile:

```json
{
  "subject": "lct:web4:society:demo-agent",
  "predicate": "web4:relevantTo",
  "object": "lct:web4:society:demo-store",
  "mrh": {
    "deltaR": "local",
    "deltaT": "session",
    "deltaC": "agent-scale"
  }
}
```

Fields:

- `subject` – REQUIRED. An LCT URI.
- `predicate` – REQUIRED. A string in the `web4:` vocabulary (see below).
- `object` – REQUIRED. Either:
  - Another LCT URI, or
  - A literal value (e.g., string, number, or structured object).
- `mrh` – OPTIONAL. An MRH profile object.

### 4.2 Vocabulary (initial)

The following initial predicates are defined:

- `web4:relevantTo`
  - Indicates that the subject LCT is contextually relevant to the object LCT within the given MRH.
- `web4:helpsWith`
  - Indicates that the subject LCT is helpful for some activity or resource identified by the object.
- `web4:withinHorizon`
  - Explicitly binds a subject LCT (or statement about it) to a particular MRH profile.
- `web4:participantIn`
  - Indicates participation of an agent/role LCT in a society or process LCT.

Implementations MAY define additional predicates under the `web4:` namespace, but SHOULD document their semantics in the Web4 documentation.

### 4.3 Storage and transport

This specification is agnostic to storage backends. Implementations MAY:

- Store triples in a traditional RDF store.
- Store triples in JSON logs or key–value stores.
- Derive triples from existing events (e.g., ACT keeper events) and maintain an in-process graph.

The key requirement is that the **logical model** above is preserved.

---

## 5. Query behavior

This section specifies basic query patterns over LCT context triples. It does not prescribe a specific query language.

### 5.1 Neighborhood queries

Given an LCT `l`, an implementation SHOULD support retrieving its **context neighborhood**:

- Incoming and/or outgoing triples with `subject = l` or `object = l`.
- Optional filters by predicate and/or MRH profile.

Example (conceptual):

- `neighbors(l, predicate = "web4:relevantTo")`
- `neighbors(l, within_mrh = {"deltaC": "agent-scale"})`

### 5.2 MRH filtering

Implementations SHOULD provide a way to filter triples by MRH profile, using one of:

- Exact match (`deltaR`, `deltaT`, `deltaC` all equal).
- Range-like comparisons (e.g., `deltaC` no more complex than `agent-scale`).

The details of MRH comparison (e.g., partial orders between bins) are implementation-defined but SHOULD be documented.

---

## 6. Relationship to trust and policy

This specification does not standardize trust or policy behavior, but is designed to support:

- **MRH-annotated trust metrics**
  - Implementations MAY annotate trust scores (e.g., T3/V3 tensors) with MRH profiles indicating the horizon under which the scores were learned.
- **MRH-aware policy decisions**
  - Implementations MAY use MRH context to:
    - Restrict certain actions (e.g., high-complexity or long-horizon transactions) unless an agent has sufficient MRH-appropriate trust.
    - Tailor behavior to localized, short-horizon contexts.

Future versions of this spec MAY define standard patterns for MRH-aware trust aggregation and policy, once practical experience accumulates.

---

## 7. Backwards compatibility

- Existing LCTs and implementations that do not use MRH metadata or context triples remain valid.
- MRH metadata and context triples are **additive**:
  - Implementations can introduce them incrementally.
  - Systems that do not understand MRH can safely ignore the additional fields.

---

## 8. Security and privacy considerations

- MRH metadata and context triples can reveal **structural information** about relationships between LCTs.
- Implementations SHOULD:
  - Consider what contextual links are safe to expose publicly.
  - Use access control and redaction where necessary.
- This specification intentionally:
  - Keeps MRH profiles coarse-grained.
  - Avoids mandating disclosure of sensitive or fine-grained context.

---

## 9. Future work

Potential future extensions include:

- More detailed MRH models (e.g., continuous or hierarchical horizons).
- Standardization of MRH-aware trust representations.
- Standard APIs for querying LCT context graphs (e.g., SPARQL profiles or JSON-based query schemas).
- Integration guidance for:
  - On-chain modules (e.g., ACT keepers and treasuries).
  - Off-chain memory systems and temporal sensors.
  - Edge agents and cognition engines.

This draft is intended as a minimal, practical starting point that aligns Web4’s LCT implementation with the MRH concepts from Synchronism and leaves room for evolution as the ecosystem matures.
