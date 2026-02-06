# Web4 Engine, 4-Life Website, and Whitepaper Consistency Report

**Date**: November 24, 2025  
**Author**: Cascade (AI assistant)

This document summarizes consistency checks between:

- The **Web4 whitepaper / standard** (as reviewed in `WHITEPAPER_REVIEW_SUMMARY.md` and `WHITEPAPER_DISCREPANCIES.md`)
- The **Web4 society game engine** under `web4/game`
- The **4-Life website** under `/4-life`

It focuses on **inconsistencies, ambiguities, and open questions**. It does **not** implement fixes; it is an input to future design and implementation passes.

### Current Status (Honest Posture)

- **What this is**: A research-stage consistency review between the Web4 standard, the `/game` simulation sandbox, and the 4-Life website copy.
- **What works**: The engine and site broadly align on LCTs, simplified MRH, T3-like trust, R6-lite envelopes, and hardware-bound root LCTs as design intent. The `/game` engine runs concrete demos (treasury abuse, two-society federation) that exercise these ideas at research scale.
- **What is missing**: Full MRH architecture, V3 tensors, ATP/ADP metabolism, complete R6 envelopes, explicit witnessing/broadcast primitives, and production-grade threat modeling/cryptographic hardening. Several concepts are intentionally "v0" or "-lite" compared to the whitepaper.
- **How to evaluate fairly**: Treat this as a **research prototype + consistency map**, not a production implementation. The purpose is to surface gaps honestly so code, docs, and website can converge iteratively.
- **Where to look for security assumptions**: See `THREAT_MODEL_GAME.md` for a focused, research-stage threat model covering `/web4/game` microchains, MRH-aware policies, and the hardware binding MVP.

---

## 1. Scope and Positioning

### Observed

- **Whitepaper**: Describes a broad Web4 architecture: LCTs, ATP/ADP cycles, T3/V3 tensors, memory as temporal sensor, blockchain typology, witnesses, etc.
- **Original codebase (demo store)**: Implements a **commerce delegation / agent authorization** system.
- **New game engine (`web4/game`)**: Implements **societies, per-society microchains, MRH edges, simple T3-like trust, roles, and cross-society policies** as a **simulation sandbox**.
- **4-Life website**: Presents 4-Life as a **simulation-first gateway into Web4 societies** and states that engine pieces that behave well under stress may graduate into the Web4 standard.

### Inconsistency / Tension

There are effectively **multiple embodiments of Web4**:

- Vision-level whitepaper
- Agent authorization demo
- Web4 society game / 4-Life

The relationships between these are not yet clearly described in a single place.

### Open Questions

1. Should we **explicitly position** the Web4 society game as a **primary current testbed** in the whitepaper and/or a top-level "Current Implementations" section?
2. Should the whitepaper and website share a small **"Current Status"** table listing:
   - Agent authorization demo (commerce vertical)
   - Web4 society game (4-Life)

---

## 2. LCT Definition and Representation

### Whitepaper / Intent

- **LCT** = **Linked Context Token**, **non-fungible token** that **lives on a society's blockchain**.
- Each LCT carries **MRH** (what happened, with whom, under which roles) and **T3/V3** views.
- LCTs are connected via **RDF-like graph edges**.

### Engine

- `Agent.agent_lct: str`, `Society.society_lct: str`, and helper functions like `make_agent_lct` and `make_society_lct` generate **namespaced LCT strings**.
- Events on a society's **microchain** reference these LCT strings.
- MRH and T3 are tracked in **associated structures**:
  - `trust_axes` on `Agent` and `Society` (T3-like trust vectors)
  - `ContextEdge` instances with an `mrh` dict per edge
- There is **no first-class `LCT` object** in the game engine that bundles ID, MRH, T3/V3, and graph links into a single durable entity.

### 4-Life Website

- Web4 explainer page now correctly defines LCT as:
  - **Linked context token**, **non-fungible**, **lives on a society's blockchain**
  - Embedded in a specific society's **MRH and chain**, not free-floating
  - Linked by **RDF-like graph edges** (examples given)

### Inconsistency

- Conceptually: LCT = **NFT on chain with MRH/T3/V3 attached**.
- Implementation: LCT = **string identifier**, with MRH and T3 stored in **nearby** structures (events, trust maps, context edges).

### Open Questions

1. Do we want to introduce a **v0 `LCT` dataclass** in the game to more closely match the conceptual model (ID + owning society + MRH/T3/V3 summaries)?
2. Or do we treat the simulation as **"LCT-lite"** and label that explicitly in docs/website until the representation is upgraded?

---

## 3. MRH (Memory, Reputation, History)

### Whitepaper

- MRH is a rich **temporal sensing / memory architecture**, with ideas like dual memory, SNARC signals, and multi-chain typology.

### Engine

- Implements a **simplified MRH model**:
  - Per-society **microchain** (`Society.blocks`) containing events.
  - In-memory **MRH/LCT context edges** (`World.context_edges` of `ContextEdge(subject, predicate, object, mrh)`), used by policies and UI.
- No dual-memory architecture or SNARC processing; this is intentionally minimal.

### 4-Life Website

- Describes MRH as:
  - "Per-society microchain plus an in-memory MRH/LCT context graph."
- This matches the current engine behavior.

### Inconsistency

- There is a **large gap** between this simplified MRH and the **full whitepaper MRH vision**, but **website ↔ engine** are consistent.

### Open Questions

1. Should the Web4 explainer explicitly call this a **"simplified MRH model"** and point to the whitepaper for the full design?

---

## 4. T3 / V3 Trust and Valence

### Whitepaper

- Defines **T3** (talent, training, temperament) and **V3** (valuation, veracity, validity).
- Earlier review documented that these were **not implemented** in the older codebase.

### Engine

- Implements a **T3-like trust structure**:
  - `Agent.trust_axes["T3"]` and `Society.trust_axes["T3"]` contain `talent`, `training`, `temperament`, and `composite`.
  - `update_society_trust` in `society_trust.py` updates the society-level composite based on recent chain events.
- **V3** is **not implemented** in the game engine.

### 4-Life Website

- Explainer describes **T3/V3** generically.
- States that **agents and societies carry T3-like trust vectors** that drive policies.

### Inconsistency

- Game engine: **T3 implemented, V3 absent**.
- Website: Mentions both T3 and V3 as core concepts, without clarifying which are present in the current engine.

### Open Questions

1. Should we add a minimal **V3 stub** in the game (even if unused initially) for symmetry?
2. Alternatively, should the website be updated to say explicitly: **"In this engine, we currently use T3; V3 is reserved for later layers"**?

---

## 5. ATP / ADP

### Whitepaper

- Presents ATP/ADP as a **metabolic energy/value cycle**, not just a balance.

### Engine

- Uses simple **numeric ATP balances** in `Society.treasury` and `Agent.resources`, e.g. `{"ATP": 1000.0}`.
- Treasury helpers debit/credit ATP values.
- There is **no explicit ADP representation** and no full metabolic conversion cycle.

### 4-Life Website

- Explainer describes ATP/ADP as:
  - "Accounting units for scarce resources" (time, attention, compute, authority).
  - Explicitly *not* a coin.
  - Used to frame treasury and budget policies.

### Inconsistency

- Current engine only implements **ATP-like balances**; ADP and the full ATP/ADP cycle are conceptual only.

### Open Questions

1. Should we rename or annotate these as **"ATP-like points"** in engine and site copy until ADP and conversion semantics are implemented?
2. Do we want to avoid mentioning **ADP** in public-facing docs until there is at least a stub in the engine?

---

## 6. R6 Interaction Envelopes

### Whitepaper

- R6 is a structured envelope describing participants, roles, context, expectations, etc.

### Engine

- `make_r6_envelope(interaction_type, justification, constraints)` returns a **minimal dict**:
  - `{"interaction_type", "justification", "constraints"}`
- This is attached to many events:
  - Role binding/pairing/revocation
  - Treasury operations
  - Audit requests
  - Cross-society policy events

### 4-Life Website

- Explainer describes R6 as:
  - A "minimal, structured envelope" for interactions.
  - Used so different societies can parse "what kind of interaction is this".

### Inconsistency

- Conceptually, R6 in the whitepaper is richer than the current **three-field implementation**.
- Practically, **engine and site** are aligned on R6 as a **minimal v0 envelope**.

### Open Questions

1. Should we define and document a **"v0 R6 schema"** in the engine (e.g. code + doc) and explicitly label it as **incomplete vs the full spec**?

---

## 7. Pairing Types and Roles

### Intent / Whitepaper

- Distinguishes **binding**, **pairing**, **witnessing**, and **broadcast** as different ways LCTs can be linked.
- Root LCT (typically a society's root) acts as an authority for some of these relationships.

### Engine

- `roles.py` implements:
  - `bind_role` → role LCT under a society namespace, bound to a subject; emits `role_binding` event + MRH/LCT edges.
  - `pair_role_with_lct` → `role_lct` paired with another LCT; emits `role_pairing` event + MRH/LCT edges.
  - `revoke_role` → emits `role_revocation`, updates `hasRole` to `hadRole` edges.
- Cross-society policies emit events like `federation_throttle` and `quarantine_request` but do not currently use explicit **"witness" or "broadcast"** event types.

### 4-Life Website

- Explainer includes a **"Pairing types between LCTs"** section with four concepts:
  - **Binding** (stable attachment from authority/root)
  - **Pairing** (flexible, time-bounded link)
  - **Witnessing** (attestations)
  - **Broadcast** (capability/status announcements)

### Inconsistencies

- Binding and pairing are **implemented** and described.
- Witnessing and broadcast are **described in the explainer** but only **implicitly present** in the engine (e.g. hub behaviors, cross-society policies) without named primitives.

### Open Questions

1. Should the game engine grow **explicit helper functions and event types** for `witness_event` and `broadcast_capability` to match the explainer?
2. Alternatively, should the explainer annotate witnessing and broadcast as **planned primitives** pending engine support?

---

## 8. Hardware-Bound Root LCTs
### Whitepaper / Intent
- A society's **root LCT** is intended to be **hardware-bound** (TPM, HSM, secure enclave), so that identity and evolving trust are anchored and attestable.
### Engine
- `hw_bootstrap.py` defines:
  - `HardwareIdentity` (public_key, fingerprint, hw_type)
  - `get_hardware_identity()` → returns a **stub** identity.
  - `derive_society_lct()` → derives a society LCT from hardware fingerprint.
  - `bootstrap_hardware_bound_world()` → creates a world whose root society LCT is derived from this stub identity and writes a simple genesis block.
- Microblock sealing in `sim_loop.py` uses deterministic header hashes and a
  placeholder `"stub-signature"`, with explicit TODOs to replace this with
  TPM- or enclave-backed signatures.
### 4-Life Website
- Home and how-it-works pages talk about **bootstrapping a hardware-bound
  home society** and a **hardware-bound root LCT**.
- Starter kit and explainer pages are more precise, stating that:
  - Hardware binding is **optional** today.
  - The current engine uses **stubbed hardware identities** and signatures.
  - The design intent is to move toward real attestation.
### Inconsistency
- High-level marketing copy (hero text, some how-it-works phrasing) implies
  hardware binding is fully present now.
- Engine and detailed pages accurately present it as **stubbed / in
  progress**.
### Open Questions
1. Should the hero and how-it-works copy be softened to: "designed for
  hardware-bound home societies; current builds use stubbed identities"?
2. Do we want explicit **versioning language** (e.g. "v0: stub hardware, v1:
  real attestation") in public docs?

---

## 9. Naming and Wording Alignment

### Observations

- **LCT naming**:
  - Whitepaper and current explainer: **Linked Context Token**.
  - Some older comments/docs still refer to "Local Context Ticket" or just
    "ticket".
- **"Lite" implementations**:
  - Several concepts are intentionally minimal in code compared to the
    whitepaper: LCT representation, MRH, T3/V3, ATP/ADP, R6, pairing types.
  - The website generally presents **full Web4 concepts** first and only in
    some places calls out that the engine is a **v0 sandbox**.

### Open Questions

1. Should all forward-facing docs (whitepaper site, 4-Life, game design docs)
  **standardize** on "Linked Context Token (LCT)" and avoid "ticket"?
2. Do we want a consistent vocabulary like **"LCT-lite"**, **"R6-lite"**,
  **"ATP-lite"** for v0 simulation implementations, or should we simply note
  that "this engine implements a minimal subset of the full design"?

---

## 10. Next Decisions Checklist

The following decisions will determine whether we adjust **code**, **docs**, or
**both** for each concept.

- **[ ] LCT representation**
  - **Option A:** Introduce a v0 `LCT` dataclass/record in the game engine.
  - **Option B:** Keep string IDs, but label the engine as **LCT-lite** and
    document the mapping clearly.

- **[ ] MRH description**
  - **Option A:** Add a short note in docs/site that the game uses a
    **simplified MRH model**.
  - **Option B:** Start implementing additional MRH features from the
    whitepaper (e.g., richer temporal summaries).

- **[ ] T3 / V3**
  - **Option A:** Add a minimal V3 stub to the engine for symmetry.
  - **Option B:** Update website copy to say the engine currently uses **T3
    only**, with V3 planned for later layers.

- **[ ] ATP / ADP**
  - **Option A:** Introduce an explicit ADP concept and simple ATP→ADP
    transitions.
  - **Option B:** Rephrase public docs to talk about **ATP-like budget
    points**, deferring ADP until needed.

- **[ ] R6 envelope shape**
  - **Option A:** Expand `make_r6_envelope` to a documented v0 schema that more
    closely matches the spec (including actor/subject/role fields).
  - **Option B:** Keep it minimal but explicitly label it **v0 R6** in docs and
    comments.

- **[ ] Pairing types (witnessing, broadcast)**
  - **Option A:** Add explicit `witness_event` / `broadcast_capability`
    helpers and event types in the engine.
  - **Option B:** Mark witnessing/broadcast in the explainer as **planned
    primitives** not yet implemented.

- **[ ] Hardware binding messaging**
  - **Option A:** Soften marketing copy to match the current stubbed state.
  - **Option B:** Keep current language and add an explicit **"v0, stubbed"
    disclaimer near the hero.

You can annotate this checklist directly in this file as we decide per-item
whether to evolve the code, adjust the docs, or both.
