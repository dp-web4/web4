# AIC Hub

> Minimum-viable Web4 society for a community chapter.

A single-binary Rust daemon that turns a community chapter into a sovereign Web4 society — 7 roles, signed founding charter, append-only witnessed ledger, MCP server, admin CLI, Docker compose deployment. First deployment target: a pilot AIC chapter. Any community willing to operate as a Web4 society can use the same software.

## Current status

**Sprint 0** — scaffold landing. Workspace builds, binary prints version, no functionality yet.

Subsequent sprints (Sprint 1 → Sprint 6) wire in society instantiation, ledger, MCP server, admin CLI, Docker deployment, and pilot-organizer documentation. See `docs/SPRINTS.md`.

## What this is

- **Web4 society shell** — uses `web4-core` + `web4-trust-core` directly; does not reimplement LCT / T3/V3 / MRH / ATP / R6 primitives
- **AGPL-3.0-or-later** — patent grant per web4 root `PATENTS.md`; AIC (or any community) can fork
- **Single binary, single config file** — `docker compose up` deploys; chapter organizer needs no DevOps experience

## What this isn't (MVP scope)

- Not a Member Presence Toolkit (Hestia multi-hub plugin — separate package, V2)
- Not the AIC-Central Overlay layer (cross-chapter federation, global skill graph — V2 / Phase 3)
- Not a public web UI for members (admin CLI is the MVP surface; UI is V2)
- Not Slack-integrated (deferred until pilot empirically defines the coexistence requirements)
- Not ACT-anchored (local file ledger for MVP; ACT anchoring is V2)
- Not Hardbound-policy-integrated (chapter law is text in MVP; full enforcement requires resolving Hardbound's canonical Web4 alignment debt first)

See `docs/PRD.md` §5 for full out-of-scope rationale.

## Read first

| Doc | Purpose |
|-----|---------|
| [`docs/PRD.md`](docs/PRD.md) | Formal PRD — problem, solution, scope, requirements, acceptance criteria, risks |
| [`docs/SPRINTS.md`](docs/SPRINTS.md) | Sprint 0 → Sprint 6 plan, capability-defined milestones |

## Build (Sprint 0)

```bash
cd web4/hub
cargo build --release
./target/release/hub --version
```

Subcommands land sprint-by-sprint. Sprint 0 surface is `--version` and `--help`.

## License

AGPL-3.0-or-later. See [`LICENSE`](../LICENSE) at the web4 root.

Commercial licensing available for organizations that need non-AGPL terms — contact `dp@metalinxx.io`.
