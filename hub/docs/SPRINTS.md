# Web4 Community Hub — Sprint Plan

**Companion to:** `PRD.md`
**Date:** 2026-06-07

Sprints are **capability-defined**, not calendar-defined. Each sprint produces a verifiable milestone — a thing that builds, runs, and demonstrates a specific capability. Pace is set by the work, not by weeks. Each sprint's exit criteria must be met before the next sprint starts.

The whole sprint plan is one stack of seven sprints (Sprint 0 through Sprint 6). After Sprint 6, MVP is shippable.

---

## Sprint 0 — Scaffold

**Goal:** repo structure exists; binary builds; the project has somewhere for sprint 1 to start.

**Deliverables:**
- `web4/hub/` Cargo workspace
- `hub-lib/` library crate (society logic — empty stub)
- `hub-daemon/` binary crate (main.rs prints version, exits cleanly)
- `Cargo.toml` workspace manifest with path dependencies on `web4-core` and `web4-trust-core`
- `README.md` pointing at PRD + SPRINTS
- `docs/PRD.md` + `docs/SPRINTS.md` (this document)
- `.gitignore` (target/, *.log, etc.)
- License header convention applied (AGPL-3.0-or-later)

**Exit criteria:**
- `cd web4/hub && cargo build --release` succeeds
- `./target/release/hub --version` prints version + exits 0
- `cargo test` passes (even if zero tests — the wiring runs)
- README + PRD + SPRINTS committed

**Lands as one commit:** `hub: sprint 0 scaffold (PRD + sprint plan + Cargo workspace)`

---

## Sprint 1 — Society instantiation

**Goal:** `hub init` produces a chapter directory with a signed founding charter and the 7 roles wired with sensible defaults.

**Deliverables:**
- `hub-lib::society::Society` struct: name, founding date, Sovereign LCT, role state (HashMap<Role, Vec<Member>>)
- `hub-lib::charter::Charter` struct + signing via `web4-core` LCT API
- `hub-lib::roles::Role` enum: Sovereign, LawOracle, PolicyEntity, Treasurer, Administrator, Archivist, Citizen
- `hub init <chapter-name> --sovereign-lct <path>` CLI subcommand
- Initial chapter directory layout: `<chapter-dir>/{config.toml, charter.json, ledger.jsonl}` (ledger empty)
- Idempotency: re-running `hub init` on an existing chapter dir reports state without overwriting

**Tests:**
- Instantiate → re-read → verify Sovereign signature on charter
- Idempotency: second `init` call doesn't corrupt the first
- All 7 roles present after instantiation; Sovereign filled, others marked unfilled

**Exit criteria:**
- `hub init test-chapter --sovereign-lct ./test_keys/sovereign.json` creates a working chapter dir
- Charter signature round-trip verified by web4-core's verifier
- Tests pass

---

## Sprint 2 — Chapter ledger

**Goal:** witnessed event ledger lands behind `hub-lib` API and persists to file.

**Deliverables:**
- `hub-lib::ledger::Ledger` wrapping `web4-core`'s `LocalLedger`
- Event types: `MemberAdded`, `MemberRemoved`, `RoleAssigned`, `EventRecorded`, `CharterAmended`
- Each event carries: actor LCT, timestamp, payload, signature, prev-entry hash
- Persistence: append-only JSONL at `<chapter-dir>/ledger.jsonl`
- Chain verifier: reuses `web4-core`'s verifier — no hub-specific verification code

**Tests:**
- Write 10 events of mixed types, read back, verify chain integrity
- Tamper test: modify a middle entry, verifier rejects
- Restart recovery: process crash mid-write doesn't corrupt the chain

**Exit criteria:**
- `hub record-event <event>` writes a signed entry to the ledger
- `web4-core verify <ledger>` (existing tool) validates the chain
- Tests pass

---

## Sprint 3 — MCP server

**Goal:** MCP server exposes the core tool set; act-recording calls require LCT-signed envelopes per Web4 cross-society binding spec.

**Deliverables:**
- `hub-daemon::mcp` module — MCP server bound to configurable port (default 8770)
- Tools implemented:
  - `list_members()` — returns chapter member list with public profile fields
  - `find_skill(query)` — searches member skill declarations
  - `query_chapter()` — returns chapter identity + role-fill state + recent events summary
  - `record_event(event_spec)` — writes to ledger; requires LCT-signed envelope
  - `add_member(member_spec)` — adds to ledger; requires LCT-signed envelope from a role-holder authorized to add members per chapter law
  - `assign_role(role, member)` — assigns role; requires consent step (assignee LCT signs acceptance) + Sovereign or Administrator authorization
- Auth model: read-only tools unauthenticated by default; act-recording tools require signed envelope; configurable per chapter

**Tests:**
- Each tool round-trip via MCP client
- Act-recording tool without signed envelope → rejected
- Act-recording tool with valid envelope → the act lands in the ledger

**Exit criteria:**
- `hub serve` brings up the MCP server
- An MCP client can list, query, find, and (with proper signing) record/add/assign
- Tests pass

---

## Sprint 4 — Admin CLI parity

**Goal:** chapter operator can do everything via CLI that an MCP client can do. CLI and MCP share the same primitives.

**Deliverables:**
- Subcommands: `hub status`, `hub add-member`, `hub assign-role`, `hub record-event`, `hub query <subcommand>`
- CLI authenticates by reading operator LCT from configured path (`hub` looks for `~/.hub/operator.lct.json` by default, overridable)
- All CLI commands write via the same `hub-lib` primitives MCP uses (no duplicate code paths)

**Tests:**
- Run a scripted "first day of a chapter" scenario: instantiate → add 5 members → assign roles → record 2 events → query members by skill
- All operations succeed; ledger end-state matches expected; chain verifies

**Exit criteria:**
- Operator scenario script runs to completion
- Same end-state reachable via MCP (parity test)
- Tests pass

---

## Sprint 5 — Docker + integration demo

**Goal:** chapter organizer can deploy via `docker compose up`. End-to-end demo runs.

**Deliverables:**
- `Dockerfile` — multi-stage build producing single-binary image
- `docker-compose.yml` — mounts chapter dir + config + LCT key as volumes; exposes MCP port
- `chapter.toml.example` — minimal config (chapter name, port, Sovereign LCT path, ledger dir)
- Integration test: spin up via `docker compose up`, exercise MCP tools from outside container, verify ledger state in mounted volume
- Demo script (`examples/first-chapter.sh`) — does the "first day" scenario from outside the container

**Tests:**
- Container builds, starts, serves MCP, responds to tools
- State persists across container restart (ledger mounted volume)
- Demo script completes end-to-end

**Exit criteria:**
- A fresh Linux/Mac machine with Docker can run the demo script and have a working chapter hub in under 30 minutes
- Image size under 50 MB
- Tests pass

---

## Sprint 6 — Pilot-organizer documentation + polish

**Goal:** a non-developer chapter organizer can deploy and operate their chapter from documentation alone.

**Deliverables:**
- `README.md` — what the hub is, who it's for, what it does today (links PRD for depth)
- `docs/QUICKSTART.md` — chapter-organizer onboarding (5 minutes → first deploy; 30 minutes → first event recorded)
- `docs/CHAPTER-LAW.md` — template + guidance for writing chapter law that the Sovereign signs
- `docs/ROLES.md` — role-fill guide (who does what, how to delegate when a chapter grows)
- `docs/TROUBLESHOOTING.md` — common errors + recovery
- Error message audit: every user-facing error explains what's wrong + how to fix
- Edge case audit: missing config, missing LCT, port in use, corrupted ledger recovery

**Tests:**
- Have a person not previously briefed on the project follow the QUICKSTART; observe where they stumble; fix
- Recovery from each documented failure mode works

**Exit criteria:**
- Pilot-ready: a chapter organizer can be handed the repo URL + chapter.toml template and get to a working hub independently
- Documentation passes the "could a volunteer organizer do this?" test
- MVP acceptance criteria from PRD §9 all met

---

## Post-MVP: triggers for V2

After Sprint 6 ships, MVP is in pilot. V2 work starts when one of these triggers fires:

- **Pilot chapter requests web UI** (likely first ask — CLI suffices for the organizer but members want a browser surface)
- **Second chapter wants to federate** (triggers inter-society protocol implementation)
- **Pilot chapter wants T3 attestation by witnesses** (triggers reputation pipeline beyond raw skill declarations)
- **Partner lab asks for programmatic engagement** (triggers cross-society MCP federation work)
- **A deployment's central operator asks for cross-chapter observability** (triggers Central Overlay phase)

Each trigger defines its own sprint stack. V2 planning is deferred until a trigger fires; sprint-planning-in-advance for hypothetical V2 work is drift.
