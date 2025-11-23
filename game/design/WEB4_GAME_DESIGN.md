# Web4 Game Design (Draft)

**Status:** Draft, evolving

This document elaborates the design of the Web4 society simulation game. It is a living specification that will be refined as we implement and learn from the system.

---

## 1. Goals

- Provide a **playable simulation** of Web4 societies that remains faithful to the standards.
- Enable **both humans and AI agents** to:
  - Found societies.
  - Join and leave societies.
  - Broadcast witnessing and production capabilities.
  - Build reputation and attract resources.
- Serve as a **test harness** for:
  - LCTs and MRH/RDF context graphs.
  - T3/V3 trust tensors and policies.
  - ATP/ADP-style economics.
  - Memory lightchains and witnessing.
  - ACT-style societies and treasuries (on-chain or simulated).

---

## 2. Entities and Data Model (v0)

### 2.1 Agent

- Fields (v0):
  - `agent_lct`: unique Linked Context Token.
  - `name`: display name.
  - `trust`: T3 tensor view, later extended to V3.
  - `capabilities`: structured description of what the agent can do (witness types, skills).
  - `resources`: balances (ATP, tokens, simple goods).
  - `memberships`: list of societies and roles.

### 2.2 Society

- Fields (v0):
  - `society_lct`: unique LCT.
  - `name`: display name.
  - `treasury`: balances and resource pools.
  - `members`: agent and society members, with roles.
  - `policies`: simplified law/policy representation (admission, allocation, governance).

### 2.3 Resource / Economy

- Types (v0):
  - `work_unit`: generic unit of labor.
  - `infrastructure`: simple assets providing ongoing capacity.
  - `knowledge_artifact`: documents or models.
- Economies:
  - Per-agent and per-society ATP/ADP budgets.
  - Task offers and bounties.

### 2.4 Knowledge / MRH Context

- Representation:
  - LCT context graph with nodes = agents, societies, roles, resources.
  - Predicates like `web4:participantIn`, `web4:relevantTo`, `web4:delegatedFrom`, `web4:governs`.
  - MRH profiles attached to edges (discretized `(ΔR, ΔT, ΔC)`).

---

## 3. Game Loops

### 3.1 Micro Loop (per tick)

For each **agent**:

- Observe:
  - Current societies, tasks, and broadcast capabilities.
  - Personal resources and trust.
- Decide actions:
  - Found a new society.
  - Apply to join an existing society.
  - Propose or accept tasks.
  - Perform work and witness events.

For each **society**:

- Evaluate:
  - Membership requests.
  - Outstanding task proposals.
  - Treasury status and budgets.
- Act:
  - Accept/reject members.
  - Award tasks and pay for completed work.
  - Update trust and MRH context edges.

### 3.2 Macro Loop (per epoch)

- Assess:
  - Health and growth of societies.
  - Distribution of trust and resources.
- Adapt:
  - Allow societies to change policies.
  - Enable splits, mergers, or alliances.

---

## 4. MVP Implementation Plan

### 4.1 Engine (v0)

- `engine/models.py`
  - `Agent`, `Society`, `Resource`, `World` dataclasses.
- `engine/sim_loop.py`
  - Tick loop that updates the world state.
  - Simple scheduler for agent and society actions.

### 4.2 API

- `api/app.py` (or integrate into existing FastAPI app):
  - Endpoints to:
    - Inspect world state (agents, societies, tasks).
    - Trigger ticks/epochs.
    - Submit human player actions.

### 4.3 UI

- `ui/` (v0):
  - Minimal dashboards showing:
    - Societies and members.
    - Agent trust and resources.
    - MRH/LCT context graphs (starting from server-rendered lists, later richer visualizations).

---

## 5. Phasing

- **Phase 0: Design + Skeleton (this doc)**
  - Create directory structure and high-level design.

- **Phase 1: Minimal World + CLI/Test Harness**
  - Implement `World`, `Agent`, `Society` models and a simple tick loop.
  - Drive it via tests or a CLI before building UI.

- **Phase 2: Web API + Basic UI**
  - Add FastAPI endpoints and a small web UI.
  - Visualize societies, trust, and MRH context.

- **Phase 3: Deeper Web4 Integration**
  - Plug in real T3Tracker, LCTContextGraph, memory lightchains, and ACT-like treasuries.

This design will be refined as we implement and observe emergent behavior.
