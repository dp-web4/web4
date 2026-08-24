# Web4 Community Hub — Sprint Plan

**Companion to:** `PRD.md`
**Date:** 2026-06-07

> **STATUS as of 2026-06:** The MVP (Sprints 0–6) shipped, and substantial V2 work has since shipped on top of it (encrypt-at-rest, machine-enforced hub law, sealed member channels, EUDI/`did:web4`, Sovereign Council, operator web UI + admission queue, plugin seam). This document remains an accurate record of the MVP build. For everything after the MVP, see `docs/V2-V3-ARCHITECTURE.md` and the README.

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
  - `add_member(member_spec)` — adds to ledger; requires LCT-signed envelope from a role-holder authorized to add members per hub law
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
- `docs/HUB-LAW.md` — template + guidance for writing hub law that the Sovereign signs
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

> **STATUS as of 2026-06: these triggers have FIRED.** V2 work is underway and much of it has shipped. See `docs/V2-V3-ARCHITECTURE.md` for current state. Annotations below mark what each trigger produced.

After Sprint 6 ships, MVP is in pilot. V2 work starts when one of these triggers fires:

- **Pilot chapter requests web UI** (likely first ask — CLI suffices for the organizer but members want a browser surface) — **FIRED:** operator/admin web UI shipped (`/admin` dashboard + write-capable operator plane on `127.0.0.1:8772`).
- **Second chapter wants to federate** (triggers inter-society protocol implementation) — **FIRED (in part):** inter-society primitives shipped — `find_members`, `request_intro`/`respond_intro`, `did:web4`/EUDI, `/.well-known/web4-hub.json` discovery. Central Overlay aggregation still future.
- **Pilot chapter wants T3 attestation by witnesses** (triggers reputation pipeline beyond raw skill declarations) — **FIRED (in part):** constellation attestation (hub-side verify + challenge/present) shipped; the full T3-accrual reputation pipeline is still future.
- **Partner lab asks for programmatic engagement** (triggers cross-society MCP federation work) — partly addressed by sealed channels + intros + EUDI credentials.
- **A deployment's central operator asks for cross-chapter observability** (triggers Central Overlay phase) — still future.

Each trigger defines its own sprint stack. V2 planning is deferred until a trigger fires; sprint-planning-in-advance for hypothetical V2 work is drift.

---

## F-series: the federated-hub PRD sprints

> The maintained north star is `PRD_HUB_V2_FEDERATED.md` (merged #698, all five design questions
> ratified). F-series sprints execute its ordered plan. Unlike the V2 triggers above, these are not
> hypothetical: Phase 0 was ratified as gating (Q5), so planning it is not drift.

### Sprint F0 — the gating hygiene (PRD Phase 0: R7a, R7b, R7c)

Three items, parallelizable. R7a is the critical path: the reputation seam (hestia's ~9.5k queued
deltas) stays closed until it is green.

**Current status (2026-08-23): Phase 0 is not complete.** R7a landed in #703. R7b core landed in #706,
with witnessed sponsor-vouch completion tracked separately in #707. R7c is **partial**: ratified-artifact
visibility/self-reporting landed in #708, while deploy-closure protection remains #709 and still gates
completion. R7d availability parity remains not started in the maintained federated PRD.

**F0.1 — R7a: degraded-verdict recording + delta classification.**
- A `DegradedEvent` record: class (`infra` vs `conduct`), source (`locked-refusal` |
  `signer-unreachable` | `peer-unreachable` | `gate-timeout`), timestamp, context — recorded
  append-only. The existing type-level distinctions (`LockedSigner` refusals, `SignError::Transport`)
  become recorded events, not just returned errors.
- Every reputation delta carries a conduct-vs-infra class; infra never scores as conduct.
- **Exit = PRD criterion 7**: kill the hestia callback (and a federation peer, once one exists)
  mid-session → every failure lands as a recorded degraded event, distinguishable from conduct
  denies; zero conduct-class deltas emitted from the window; the seam-opening test replays queued
  deltas and proves the classifier separates the classes.

**F0.2 — R7b: asserted-asker admission law.**
- Law section: witness vouches count only toward identities resolved from the authoritative record;
  a self-asserted binding collects no peer factors. Enforced in admission scoring.
- **Exit = PRD criterion 8**: differential test — the self-asserted twin of a resolved identity
  accumulates zero peer factors.

**F0.3 — R7c: ratified-digest closure + operator surface.**

**Status: partial.** The ratified-artifact manifest, running-digest self-reporting and operator
visibility portion landed in #708. The deploy path itself is **not yet inside the protected closure**:
#709 still carries unit/ExecStart, deploy scripts, staged artifact and manifest write protection.
Until that lands, F0.3 and Phase 0 must not be described as complete.

- Supervisor-owned ratified-digest manifest (extends hub-watch `self_fingerprint`); running hub
  self-reports its executing digest; operator surface shows per-seat `current`/`stale`/`unknown`;
  deploy path (unit, scripts, binary path) joins the gate-protected closure.
- **Exit = PRD criterion 9**: staging an unratified binary flips the seat to `stale` without
  needing a restart to notice; a closure write from a gated session is refused and escalatable.

**Restart discipline:** F0.1 + F0.2 daemon changes batch onto one branch and go live as **one dark
binary → one ignition**. Never two restarts where one will do (the vault relocks on every restart).

**Seam-opening decision (HUB seat, dp-delegated 2026-08-13): staged.** When F0.1 is green, the same
ignition opens `reputation_emit` in **classify-and-record mode** — queued deltas are ingested,
classified conduct-vs-infra, and visible on the operator surface, but applied to no tensor. After one
observation window in which the classification distribution is reviewed and looks sane, application
turns on. Observe before actuate: the fail-closed+warn default applied to the merit arc itself. Any
anomaly in the window (implausible conduct/infra ratio, deltas that classify as neither, volume
mismatch vs hestia's queue) holds application and escalates to dp.

### Sprint F1 — R4 design (roles-as-entities), doc before code

The entity-model decisions — role-LCT minting, charter as the policy-action vocabulary, the
institutional tensor with occupant-attributed sub-dimensions (merit never transfers between
occupants), migration of the founding seven with no legacy fork, and the distinct-identity
role-filling binding (#698 R5 semantics) — land as a design PR for adversarial review BEFORE
implementation sprints are cut. Cheap to review, expensive to get wrong in code.

### Parallel — AIC pilot track

Requires live-now features only; independent of F0/F1. dp's outreach (presentation artifact exists);
then one chapter, one quarter. Pilot feedback steers R4/R2 priorities — consistent with the V2
trigger discipline above: real triggers over pre-planned hypotheticals. Note the head start: R1
composes on already-shipped primitives (`find_members`, intros, `did:web4`/EUDI, `/.well-known`
discovery), not greenfield.
