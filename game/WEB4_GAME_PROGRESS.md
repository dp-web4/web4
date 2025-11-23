# Web4 Game – Progress Log (v0)

This document summarizes the current implementation status of the Web4 society simulation game under `web4/game`.

It is intentionally high-level and public-safe, focused on structure and intent rather than internal/private details.

---

## 1. Directory and Design Artifacts

- `web4/game/README.md`
  - High-level concept and MVP scope for the Web4 society simulation.
  - Describes agents, societies, economy, and MRH/LCT context at a conceptual level.

- `web4/game/design/WEB4_GAME_DESIGN.md`
  - Draft design spec with:
    - Entities and data model (Agent, Society, Resource, World, MRH/LCT context).
    - Micro and macro game loops.
    - Phased implementation plan (Phase 0–3).

---

## 2. Engine: Core Models (v0)

**File:** `web4/game/engine/models.py`

- `Agent`
  - Fields:
    - `agent_lct: str` – canonical agent LCT (e.g. `lct:web4:agent:alice`).
    - `name: str` – display name.
    - `trust_axes: Dict[str, Dict[str, float]]` – T3-like trust tensor structure, typically:
      - `{"T3": {"talent", "training", "temperament", "composite"}}`.
    - `capabilities: Dict[str, float]` – capability scores (e.g. witnessing skill).
    - `resources: Dict[str, float]` – balances (e.g. `{"ATP": 100.0}`).
    - `memberships: List[str]` – society LCTs the agent belongs to.
    - `roles: List[str]` – role tags such as `"role:web4:auditor"`, `"role:web4:treasurer"`, etc.

- `Society`
  - Fields:
    - `society_lct: str` – canonical society LCT (e.g. `lct:web4:society:home-root`).
    - `name: str` – display name.
    - `treasury: Dict[str, float]` – resource balances (e.g. `{"ATP": 1000.0}`).
    - `members: List[str]` – member agent LCTs.
    - `policies: Dict[str, str]` – simple policy configuration (admission, governance, etc.).
    - **Per-society blockchain (microchain) state:**
      - `block_interval_seconds: int` – target interval between blocks (default 15, tick-based for now).
      - `last_block_time: float` – last block seal time (in simulated ticks).
      - `pending_events: List[Dict[str, Any]]` – events waiting to be sealed.
      - `blocks: List[Dict[str, Any]]` – sealed blocks (index, timestamp, events, etc.).

- `ContextEdge`
  - Represents a simple MRH/LCT context edge:
    - `subject`, `predicate`, `object`, `mrh: Dict[str, str]`.

- `World`
  - Fields:
    - `agents: Dict[str, Agent]` – keyed by `agent_lct`.
    - `societies: Dict[str, Society]` – keyed by `society_lct`.
    - `tick: int` – global simulation tick counter.
    - `context_edges: List[ContextEdge]` – in-world MRH/LCT context edges.
  - Methods:
    - `add_agent`, `add_society`, `get_agent`, `get_society`.
    - `add_context_edge(subject, predicate, object, mrh)` – append a context edge to `context_edges`.

- Helpers:
  - `make_agent_lct(local_id: str) -> str` – returns `"lct:web4:agent:{local_id}"`.
  - `make_society_lct(local_id: str) -> str` – returns `"lct:web4:society:{local_id}"`.

---

## 3. Engine: Simulation Loop

**File:** `web4/game/engine/sim_loop.py`

- `tick_world(world: World) -> None`
  - Increments `world.tick`.
  - Calls `_agent_step` for each agent and `_society_step` for each society.

- `_agent_step(world, agent)`
  - Currently:
    - Records MRH/LCT context edges for each membership:
      - `agent_lct --web4:participantIn--> society_lct` with a coarse MRH profile:
        - `{ "deltaR": "local", "deltaT": "session", "deltaC": "agent-scale" }`.
  - Placeholder for future per-agent behavior (decisions, tasks, etc.).

- `_society_step(world, society)`
  - Implements minimal microblock sealing logic:
    - Uses `world.tick` as a simple time base.
    - If `society.pending_events` is non-empty and
      `current_time - last_block_time >= block_interval_seconds`,
      then creates a new block:
      - `{"index", "society_lct", "timestamp", "events"}`
      - Appends it to `society.blocks`.
      - Clears `pending_events`.
      - Updates `last_block_time`.
  - Placeholder for future policy/economy logic.

- `run_world(world: World, steps: int) -> World`
  - Convenience helper to run multiple ticks in sequence.

---

## 4. Engine: Audit Helpers

**File:** `web4/game/engine/audit.py`

- `make_r6_envelope(interaction_type, justification, constraints)`
  - Creates a minimal R6-style envelope for events, with:
    - `interaction_type` (e.g. `"audit"`).
    - `justification` – human-readable reason.
    - `constraints` – additional structure (e.g. MRH, fields).

- `request_audit(world, society, auditor_lct, target_lct, scope, reason, atp_allocation)`
  - Appends an `audit_request` event to `society.pending_events`:
    - Includes:
      - `auditor_lct`, `target_lct`.
      - `scope` (fields and MRH profile).
      - `reason` and `atp_allocation`.
      - `r6` envelope (with interaction type `"audit"`).
      - `world_tick` at the time of request.
  - ATP enforcement is not yet implemented; this is a structural stub to keep the chain auditable.

---

## 5. Engine: Bootstrap Scenario

**File:** `web4/game/engine/scenarios.py`

- `bootstrap_home_society_world() -> World`
  - Creates a minimal "home society" world:
    - Root society:
      - LCT: `make_society_lct("home-root")`.
      - Name: `"Home Society"`.
      - Treasury: e.g. `{"ATP": 1000.0}`.
      - Simple policies: `{"admission": "open", "governance": "simple-majority"}`.
    - Agent `Alice`:
      - LCT: `lct:web4:agent:alice`.
      - Higher temperament trust.
      - Capabilities: `{"witness_general": 0.7}`.
      - Resources: `{"ATP": 100.0}`.
      - Membership: `[root_society_lct]`.
      - Roles: e.g. `"role:web4:auditor"`, `"role:web4:law_oracle"`.
    - Agent `Bob`:
      - LCT: `lct:web4:agent:bob`.
      - Higher talent, lower temperament trust.
      - Capabilities: `{"witness_general": 0.4}`.
      - Resources: `{"ATP": 80.0}`.
      - Membership: `[root_society_lct]`.
      - Roles: e.g. `"role:web4:treasurer"`.
  - Membership links are recorded both in `Society.members` and as MRH/LCT context edges during simulation ticks.

---

## 6. CLI Demo: Bootstrap World and Microblocks

**File:** `web4/game/run_bootstrap_demo.py`

- Behavior (intended):
  - Construct `bootstrap_home_society_world()`.
  - Issue a sample `audit_request` from Alice (auditor) targeting Bob with:
    - Scoped MRH and fields (e.g., composite trust and ATP balance).
  - Run the world for a fixed number of ticks (e.g. 20).
  - Print:
    - Final `world.tick`.
    - Societies and their sealed blocks, including `audit_request` events with R6 envelopes.
    - MRH/LCT context edges (agent–society `web4:participantIn` relationships and their MRH profiles).

This provides a minimal, end-to-end demonstration of:

- Per-society microchains.
- MRH/LCT context tracking.
- Agent roles (auditor, treasurer, law oracle).
- R6-wrapped, ATP-backed audit requests recorded on-chain.

---

## 7. Next Directions (Not Yet Implemented)

- Enforce ATP deductions and balances for audit requests and other actions.
- Add role-aware policies (only agents with `role:web4:auditor` can initiate audits).
- Extend event types (membership changes, treasury transfers, role assignments).
- Wire the in-memory structures to a hardware-bound root LCT and real signing/hashing for production-like bootstrap kits.
- Build a small web UI to visualize societies, trust, MRH context, and chain state.
