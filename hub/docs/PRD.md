# AIC Hub — Product Requirements Document

**Version:** 0.1 (Draft)
**Date:** 2026-06-07
**Owner:** Metalinxx Inc.
**Status:** Pre-build (sprint 0 scaffold lands alongside this document)
**License:** AGPL-3.0-or-later (inherits web4 root)
**Repo location:** `web4/hub/` (new Cargo workspace, sibling to `web4/web4-core/` and `web4/web4-trust-core/`)

---

## 1. Background

Build an MVP of a Web4 community-hub package: generic open-source infrastructure for trust-native community governance. First deployment target: a large-scale, volunteer-driven non-profit community concerned about concentration of power in AI infrastructure. The MVP turns the design intent into demonstrable software.

The hub package is not specific to any single community by design. Any community willing to operate as a Web4 society can deploy it.

This document is **the PRD** — what gets built, what doesn't, why, and how we'll know we're done. The sprint plan lives in `SPRINTS.md`.

## 2. Problem

Distributed communities at scale face three structural problems the existing Slack/Discord/Substack stack can't solve:

1. **Cross-chapter discovery is invisible.** A member in NYC has no programmatic way to find a relevant collaborator in Nairobi. A million-member community can't programmatically answer "who knows medical-imaging RAG and is willing to mentor?"

2. **Reputation doesn't travel.** A member who runs three excellent demo nights in Lisbon has no portable credential they can carry to Berlin. Slack-message-count is not reputation.

3. **Volunteer organizers reinvent operational primitives every month.** Event ops, attendance, member onboarding — each chapter rebuilds from scratch. The bottleneck is organizer time, not enthusiasm.

The Web4 society pattern — fractal, anti-hierarchical, federation-by-consent — is shaped to address all three. This MVP operationalizes the pattern for the chapter scale (the first scale; member and central scales come later).

## 3. Solution shape

A single-binary Rust daemon that implements a minimum-viable Web4 society:

- **7-role state**: Sovereign, Law-Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen
- **Founding charter** signed by Sovereign LCT
- **Append-only witnessed event ledger**, file-persisted
- **MCP server** as the I/O membrane (per Web4 canonical equation: MCP is *the* outward-facing surface, not an optional accessory)
- **Admin CLI** for chapter operators (parallel to MCP for human use)
- **Docker compose** deployment (`docker compose up` brings up the daemon)

Uses `web4-core` and `web4-trust-core` directly as Rust path dependencies. **Does not reimplement** LCT, T3/V3, MRH, ATP, R6 primitives — those are inherited from the canonical implementations.

Inheritance discipline matters because (per `CLAUDE.md`): web4 is in *development* phase, and reimplementing primitives with a `hub_` prefix would be drift, not progress.

## 4. In scope (MVP)

| Capability | Description |
|---|---|
| **Society instantiation** | `hub init <name>` creates a new chapter society. Generates initial config, fills the 7 roles with sensible defaults (solo founder wears multiple hats), produces a founding charter signed by the Sovereign LCT. |
| **Chapter ledger** | Append-only JSONL witnessed event log per chapter. Reuses `web4-core`'s `LocalLedger` pattern. Every consequential action lands as a signed event. |
| **MCP server** | Exposes a minimum set of tools: `list_members`, `find_skill`, `record_event`, `query_chapter`, `add_member`, `assign_role`. Binds to a configurable port. The MCP server *is* the programmatic surface. |
| **Admin CLI** | Subcommands paralleling MCP tools, plus operator-only ops (`hub init`, `hub serve`, `hub status`). Lets a chapter operator manage the hub without writing MCP clients. |
| **Docker deployment** | `Dockerfile` + `docker-compose.yml`. One `chapter.toml` config specifies chapter name + Sovereign LCT path. `docker compose up` brings up the daemon listening on configured port. |
| **Documentation** | README + chapter-organizer quickstart. A volunteer organizer can deploy and run their first event from docs alone. |

## 5. Out of scope (V2+)

These are deliberately deferred. Each is real but not MVP.

- **Member Presence Toolkit (Hestia multi-hub extension)**: separate package. Members read the hub via MCP in MVP; the per-member portable-identity layer comes in a follow-on.
- **AIC-Central Overlay**: cross-chapter federation, global skill graph, partner-lab programmatic aggregation. Phase 3 in the inventory doc. MVP is one chapter.
- **Public web UI for members**: admin CLI + chapter README is the MVP surface. Web UI is V2 (likely Tauri or Leptos to stay Rust-aligned, but format TBD).
- **Slack bot integration**: deferred until one chapter is running and Slack-coexistence requirements are empirical, not designed. Concrete > speculative.
- **ACT-anchored ledger**: MVP uses local file ledger. ACT anchoring is V2 — useful for tamper-evidence at federation scale but not needed for a single chapter.
- **Hardbound policy engine integration**: MVP encodes chapter law as text (Sovereign-signed but not machine-enforced). Full policy enforcement is V2 — and requires resolving the Hardbound canonical Web4 alignment debt (per `CANONICAL_AUDIT.md` 2026-01-31).
- **Federation between chapters**: inter-society protocol exists in spec; MVP doesn't exercise it. V2.
- **Skill attestation by chapter witnesses (T3 accrual)**: MVP records skill *declarations*; T3 attestation chain is V2.

## 6. Users + use cases

| User | What they do with MVP |
|---|---|
| **Chapter organizer** | Deploys the hub for their chapter. Runs `hub init`, configures Sovereign LCT, brings up the daemon, adds initial members + roles, records first event. Operates via CLI. |
| **Chapter member** | Read-only access via MCP queries in MVP — can find members by skill, see chapter events, check chapter state. Future Hestia plugin makes this richer; for MVP, MCP is the surface. |
| **AI tool (Claude, Cursor, etc.)** | Calls chapter MCP to query members and events. With proper LCT-side configuration, can record actions taken on behalf of a member. |
| **Future pilot AIC organizer (out of MVP scope, but informs design)** | Reviews MVP, identifies what's missing for their chapter's actual operations, drives V2 priorities. |

## 7. Functional requirements

### FR1 — Society instantiation
- `hub init <chapter-name> --sovereign-lct <path>` creates a chapter directory containing config, charter, empty ledger
- Charter is plain text + structured metadata (chapter name, founding date, Sovereign LCT public key, role-fill placeholders)
- Charter is signed by the Sovereign LCT; signature verifiable via web4-core
- Idempotent: re-running on an existing chapter dir reports state without overwriting

### FR2 — Role state
- 7 roles defined per Web4 spec; each role has zero or more members
- Solo organizer wears all roles by default (founding-Sovereign placeholder for the other six)
- `hub assign-role <role> <member>` adds an assignee; consent step required (assignee's LCT signs acceptance)
- Role assignments land in the ledger as witnessed events

### FR3 — Event ledger
- Append-only JSONL at `<chapter-dir>/ledger.jsonl`
- Each entry: timestamp, actor LCT, action, payload, signature, prev-entry hash
- Verifier via web4-core's existing chain verifier — no new verifier code
- Events include: member added, member removed, role assigned, event recorded, charter amended

### FR4 — MCP server
- Listens on configurable port (default 8770; rationale: 8760 is sage-daemon, 8770 leaves room)
- Tools: `list_members`, `find_skill <query>`, `record_event <event>`, `query_chapter`, `add_member <member-spec>`, `assign_role <role> <member>`
- Each tool that mutates state requires LCT-signed envelope per Web4 MCP cross-society binding spec
- Read-only tools (list, find, query) are unauthenticated by default; configurable to require auth

### FR5 — Admin CLI
- Subcommands: `hub init`, `hub serve`, `hub status`, `hub add-member`, `hub assign-role`, `hub record-event`, `hub query`
- CLI writes to the same ledger via the same primitives MCP uses (single code path)
- CLI authenticates by reading operator LCT from configured path

### FR6 — Deployment
- `Dockerfile` produces a single-binary image (~20-30 MB)
- `docker-compose.yml` mounts chapter dir + config + LCT key as volumes
- `chapter.toml` minimal config: chapter name, port, Sovereign LCT path, ledger dir
- `docker compose up` brings up the daemon and MCP server

## 8. Non-functional requirements

| Aspect | Requirement |
|---|---|
| **Performance** | Single-chapter scale: hundreds of members, thousands of events per chapter. Not optimized for tens-of-thousands; that's a federation question. |
| **Security** | All consequential actions LCT-signed. No implicit cross-chapter trust (federation is opt-in, not in MVP). Ledger verifiable end-to-end. |
| **Deployment** | Linux + Mac via Docker. Single-binary fallback for direct install. Single config file per chapter. |
| **License** | AGPL-3.0-or-later (matches web4 root). Patent grant per web4 `PATENTS.md`. |
| **Language** | Rust. Alignment with web4-core / web4-trust-core / sage-rs. Single-binary deployment story matters more for chapter-organizer install than developer-iteration speed matters for MVP. |
| **Telemetry** | None. Zero phone-home, zero usage analytics, zero vendor-extracted data. |
| **Observability** | `tracing`-based logs; structured JSON output option for ops integration. |

## 9. Acceptance criteria (MVP done)

The MVP is shippable when **all** of these hold:

1. A clean machine can deploy a working chapter hub in under 30 minutes from `docker compose up`.
2. Chapter organizer can: instantiate a chapter, add members, assign roles, record events, query members by skill — all via CLI.
3. All consequential actions land in the ledger as LCT-signed entries.
4. MCP server responds to all FR4 tools; each mutating tool requires signed envelope.
5. Ledger is verifiable end-to-end using `web4-core`'s existing verifier (no hub-specific verifier).
6. Documentation walks a chapter organizer through "first day" — instantiate, configure, add 5 members, record 2 events, query.
7. Test suite covers: society instantiation, role assignment, event recording, ledger verification, MCP tool round-trips.
8. License headers + PATENTS.md reference in place per web4 root convention.

## 10. Risks + mitigations

| Risk | Mitigation |
|---|---|
| Hardbound canonical Web4 alignment debt (T3 dimensions misaligned per CANONICAL_AUDIT 2026-01-31) | MVP doesn't depend on Hardbound. Uses web4-core T3/V3 directly. If we integrate Hardbound later (V2), the alignment must be resolved first. |
| ACT/Society4 maturity (~65% per audit) | MVP doesn't depend on ACT. Local file ledger is the contract. ACT anchoring is layered on as it matures. |
| MCP server spec churn (cross-society binding spec is v0.1.3 DRAFT) | MVP implements the current draft. Spec changes propagate to hub through web4-standard refresh — same upgrade path the rest of the ecosystem follows. |
| Pilot chapter not identified before MVP completes | MVP development continues regardless; first-deployable state is the gating event. AIC engagement is parallel to MVP build. |
| Drift toward reimplementation (web4 CLAUDE.md flagged risk: re-doing CS primitives with `hub_` prefix) | Discipline check before each sprint: if a primitive exists in web4-core / web4-trust-core / web4-standard, use it. No `hub::LinkedContextToken`, no `hub::TrustTensor`, etc. |

## 11. Sprint plan reference

The detailed sprint breakdown lives in `SPRINTS.md` — Sprint 0 through Sprint 6, capability-defined (each sprint produces a verifiable milestone). No calendar dates; pace is set by the work, not by the calendar.

## 12. Open questions (carried from the AIC inventory doc)

These don't block MVP build but will influence V2 + pilot operations. They need AIC-side input when a pilot chapter is identified:

1. Pilot chapter selection criteria
2. Member opt-in model (default visibility for skill declarations)
3. Federation default reputation weight on T3 import (deferred to V2)
4. Slack-coexistence: is the chapter Slack constitutional?
5. AIC-central overlay timing + role-fill (deferred to Phase 3)
6. ATP issuance default policy template per chapter
7. Partner-lab engagement model (Citizen role vs peer-society federation)
8. Existing AIC member directory backward-compatibility (migration shape)

Full context: `private-context/proposals/2026-06-06-aic-hub-package/06-inventory-and-build-plan.md` §Open questions.

## 13. References

- AIC inventory + build plan: `private-context/proposals/2026-06-06-aic-hub-package/06-inventory-and-build-plan.md`
- Web4 canonical equation + ontology: `web4/CLAUDE.md`, `web4/STATUS.md`
- Web4 standard specs: `web4/web4-standard/core-spec/`
- Web4 core implementation (Rust + Python): `web4/web4-core/`, `web4/web4-trust-core/`
- Web4 MCP server reference: `web4/mcp-server/`, `web4/mcp-servers/`
- Existing Rust daemon precedent (different domain, same patterns): `SAGE/sage-rs/`
