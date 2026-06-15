# Web4 Community Hub

> Minimum-viable Web4 society for a community chapter.

> **Status — reference proof-of-concept.** This crate is the open reference POC.
> Production and advanced development continue in a separate private repository;
> features may land here later behind stable plugin interfaces.

A single-binary Rust daemon (~6 MB) that turns a community chapter into a sovereign Web4 society — 7 roles, signed founding charter, append-only witnessed ledger, MCP HTTP server, admin CLI, Docker deployment. First deployment target: a pilot community chapter. Any community willing to operate as a Web4 society can use the same software.

## Witnessed law

The hub does **not** dictate how a society runs — it makes *whatever law the society adopts* auditable, and enforces adherence to it. This is the Web4 posture (see the [root README](../README.md), "Law is witnessed, not dictated") at society scale:

- **Signed, machine-readable law.** A society's rules — admission, role authority, thresholds, what escalates — are a law the PolicyEntity gate evaluates before every consequential act. It is **inspectable by anyone** (`GET /v1/hubs/:id/law`), *including while the hub's vault is locked*: the rules are public even when the hub can't yet act on them.
- **Changeable only with authority, and witnessed.** Amending the law requires unlock + signing and lands as a `LawAmended` event on the **append-only, hash-chained, witnessed ledger** — alongside every membership, role, skill, and intro act. You cannot quietly change the rules.
- **Fail-closed secrets.** The Sovereign key is encrypted at rest; the daemon never silently writes a plaintext key (an empty passphrase is allowed but must be *explicit*). A hub whose vault is locked **degrades to a read-only no-LCT surface** rather than running ungoverned.
- **Governed startup (design posture).** Unlocking a hub is itself meant to be an auditable, governed act — automatable or human-gated per the society's own law, but always recorded. Locked-mode ships today; the witnessed M-of-N / hardware-bound unlock is the roadmap. *Convenience is policy; the audit trail is not.*

We don't mandate the policy. We insist that whatever the policy is, is followed verifiably.

## Current status

**MVP complete (Sprints 0-6).** Buildable, runnable, documented for chapter organizers. Pilot-ready.

| Sprint | Capability | Status |
|---|---|---|
| 0 | Workspace scaffold + PRD + sprint plan | ✓ |
| 1 | Society instantiation (7 roles + signed charter) | ✓ |
| 2 | Chapter ledger (hash-chained signed event log) | ✓ |
| 3 | MCP HTTP server (`/tools/*` for all operations) | ✓ |
| 4 | Admin CLI parity via HubSession | ✓ |
| 5 | Docker package + first-chapter demo scripts | ✓ (Docker untested on dev machine; first operator with Docker should report) |
| 6 | Pilot-organizer docs + polish | ✓ |

## What this is

- **Web4 society shell** — uses `web4-core` + `web4-trust-core` directly; no reimplementation of LCT / T3/V3 / MRH / ATP / R6 primitives
- **AGPL-3.0-or-later** — patent grant per web4 root `PATENTS.md`; any community can fork
- **Single binary, single config file** — `docker compose up` deploys; chapter organizer needs no DevOps experience
- **Local-first** — chapter data stays in the chapter's directory; no telemetry, no vendor data extraction

## What this isn't (MVP scope)

- Not a Member Presence Toolkit (Hestia multi-hub plugin — separate package, V2)
- Not the Central Overlay layer (cross-chapter federation, global skill graph — V2)
- Not a public web UI for members (admin CLI + MCP is the MVP surface)
- Not Slack-integrated (deferred until pilot empirically defines coexistence requirements)
- Not ACT-anchored (local file ledger for MVP; ACT anchoring is V2)
- Not Hardbound-policy-integrated (chapter law is text; full enforcement requires resolving Hardbound's canonical Web4 alignment debt)

See `docs/PRD.md` §5 for full out-of-scope rationale.

## Quick start

```bash
# Build
cd web4/hub
cargo build --release

# 5-minute demo
HUB=$PWD/target/release/hub bash examples/first-chapter.sh
```

Or, with Docker (untested on dev machine; first operator with Docker, please report):

```bash
cd web4/hub
bash examples/first-chapter-docker.sh
```

Read `docs/QUICKSTART.md` for the chapter-organizer onboarding walkthrough.

## Read first

| Doc | Purpose |
|-----|---------|
| [`docs/QUICKSTART.md`](docs/QUICKSTART.md) | Chapter-organizer onboarding (5-min deploy, 30-min first event) |
| [`docs/PRD.md`](docs/PRD.md) | Formal PRD — problem, solution, scope, requirements, risks |
| [`docs/SPRINTS.md`](docs/SPRINTS.md) | Sprint 0 → 6 plan, exit criteria each |
| [`docs/CHAPTER-LAW.md`](docs/CHAPTER-LAW.md) | Template + guidance for writing chapter law |
| [`docs/ROLES.md`](docs/ROLES.md) | The 7 Web4 society roles, how to fill them |
| [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) | Common errors + recovery |

## Build (Sprint 0 onwards)

```bash
cd web4/hub
cargo build --release
./target/release/hub --version    # → hub 0.1.0-alpha.0
./target/release/hub --help       # → list of subcommands
cargo test --release              # → 30 tests should pass
```

## CLI surface

```
hub gen-lct <path>                                  Generate a fresh LCT + keypair
hub init <name> --sovereign-lct <path>              Bootstrap a chapter society
hub status <chapter-dir>                            Chapter summary
hub add-member <chapter-dir> <lct-id> [--name]      Add a member
hub remove-member <chapter-dir> <lct-id>            Remove a member
hub assign-role <chapter-dir> <role> <role-lct> <member-lct>
                                                    Assign a role
hub record-event <chapter-dir> <kind> <title> [--attended-by lct1,lct2,...]
                                                    Record a chapter event
hub declare-skill <chapter-dir> <member-lct> <skill>
                                                    Declare a skill for a member
hub query members <chapter-dir>                     List members
hub query skill <chapter-dir> <query>               Find members by skill (substring)
hub query chapter <chapter-dir>                     Chapter identity + role fill
hub serve <chapter-dir> [--port N] [--bind addr]    Run MCP HTTP server
hub verify-ledger <chapter-dir>                     Verify the chain end-to-end
```

## MCP HTTP endpoints (when `hub serve` is running)

```
GET  /tools                       Tool catalog
GET  /tools/query_chapter         Chapter identity + role-fill snapshot
GET  /tools/list_members          Current member projection
GET  /tools/find_skill?q=...      Skill substring match
POST /tools/add_member            { member_lct_id, name? }
POST /tools/assign_role           { role, role_lct_id, member_lct_id }
POST /tools/record_event          { event_kind, title, attended_by?, held_at? }
POST /tools/declare_skill         { member_lct_id, skill }
```

## License

AGPL-3.0-or-later. See [`LICENSE`](../LICENSE) at the web4 root.

Commercial licensing available from Metalinxx Inc. for organizations that need non-AGPL terms — inquire via the [project repository](https://github.com/dp-web4/web4).
