# Web4 Role LCT Binding & Pairing (Draft)

**Status:** Draft, exploratory

This document sketches how **roles** within a Web4 society are represented and linked using Linked Context Tokens (LCTs), consistent with the existing LCT specification and the MRH/LCT context model.

The goal is to:

- Make role assignments **auditable and explicit**.
- Ensure the **root society LCT** acts as the authority for role bindings.
- Allow roles to be **paired** to other LCTs on an as-needed basis.
- Keep the design minimal and evolvable.

---

## 1. LCT Context

Existing LCT spec (summarized):

- LCTs are URI-like identifiers bound to public keys, e.g.:
  - `lct:web4:society:{id}` for societies.
  - `lct:web4:member:{id}` or similar for agents.
- LCTs are intended to be used as **nodes** in a context graph with typed edges (RDF-like triples):
  - `(subject_lct, predicate, object_lct)`.
- The MRH/LCT context spec adds MRH-aware edges with optional horizon profiles.

This draft focuses on how **roles** fit into that picture.

---

## 2. Role LCTs

### 2.1 Role LCT URI Shape (Proposal)

Roles are represented as LCTs under a society-specific namespace, for example:

- `lct:web4:role:{society_fragment}:{role_name}`
  - `society_fragment` is derived from the root society LCT.
  - `role_name` is a short identifier (e.g., `auditor`, `treasurer`, `law-oracle`).

Example:

- Society LCT: `lct:web4:society:home-root`
- Derived role LCTs:
  - `lct:web4:role:home-root:auditor`
  - `lct:web4:role:home-root:treasurer`
  - `lct:web4:role:home-root:law-oracle`

These role LCTs are **not** directly key-bound in v0; they are logical identifiers governed by the root society LCT.

---

## 3. Binding vs Pairing

We distinguish between **binding** and **pairing** relationships.

### 3.1 Binding (authoritative assignment)

Binding expresses that the root society LCT has **authoritatively assigned** a role LCT to a subject LCT.

- Semantic triple:
  - `(society_lct, web4:bindsRoleTo, subject_lct)` with additional details:
    - `role_lct`: the role being bound.
    - `scope`: optionally MRH and time bounds.

In MRH/LCT context terms, this can be represented as:

- Primary edge:
  - `subject_lct --web4:hasRole--> role_lct`
- Governance edge:
  - `society_lct --web4:bindsRole--> role_lct`

An audit trail for this binding should be recorded on the society's chain, e.g.:

```json
{
  "type": "role_binding",
  "society_lct": "lct:web4:society:home-root",
  "role_lct": "lct:web4:role:home-root:auditor",
  "subject_lct": "lct:web4:agent:alice",
  "mrh": {"deltaR": "local", "deltaT": "session", "deltaC": "agent-scale"},
  "reason": "founder assigned as initial auditor",
  "world_tick": 0
}
```

### 3.2 Pairing (contextual association)

Pairing expresses that, **for a given context**, a role or subject is associated with another LCT (resource, external society, external agent), under the authority of the root society.

Examples:

- Pair an internal auditor role with an external LCT representing an external auditor.
- Pair a treasurer role with a specific treasury pool or external account.

Semantic triple patterns:

- `role_lct --web4:pairedWith--> external_lct`
- `society_lct --web4:authorizesPairing--> (role_lct, external_lct)`

These pairings are:

- Recorded as events on the society chain.
- Reflected in the MRH/LCT context graph.
- Potentially time- and MRH-bounded.

---

## 4. Root LCT as Pairing Authority

The **root society LCT** is the **pairing authority**:

- All role LCTs are defined *within* the namespace of the root society.
- All bindings and pairings should be **authorized by the root LCT**, meaning:
  - There is a corresponding `role_binding` or `pairing` event on the society chain.
  - The event is signed or otherwise authenticated (future hardware binding).

In practice (v0, game engine):

- Role bindings and pairings are represented as structured events in `Society.pending_events` and later in `Society.blocks`.
- MRH/LCT context edges mirror these relationships for in-memory queries.

---

## 5. MRH-Aware Role Context

Bindings and pairings should include an MRH profile to encode the horizon within which the role is valid or relevant.

Recommended structure:

```json
{
  "mrh": {
    "deltaR": "local|regional|global",
    "deltaT": "ephemeral|session|day|epoch",
    "deltaC": "simple|agent-scale|society-scale"
  }
}
```

- Binding example:
  - Auditor role is valid at `agent-scale` and `session` horizons.
- Pairing example:
  - External auditor LCT paired for a specific `epoch` with `society-scale` complexity.

These MRH profiles can be used by policy modules to enforce need-to-know and scope limits during audits.

---

## 6. Engine-Level Representation (v0)

At the game engine level, we will:

- Provide helpers to construct role LCTs from a society LCT.
- Emit **role_binding** and **role_pairing** events into `pending_events`.
- Reflect these as MRH/LCT context edges in `World.context_edges`.

This keeps role semantics explicit and aligned with the broader LCT/MRH standards while remaining implementation-light.

Future iterations can refine:

- Exact URI schemes for role LCTs.
- Cryptographic binding between role LCTs and keys.
- On-chain enforcement of role constraints within ACT or other Web4-compliant ledgers.
