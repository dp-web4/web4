# Web4 Community Hub

> Minimum-viable Web4 society for a community chapter.

> **Status — reference proof-of-concept.** This crate is the open reference POC.
> Production and advanced development continue in a separate private repository;
> features may land here later behind stable plugin interfaces.

A single-binary Rust daemon (~6 MB) that turns a community chapter into a sovereign Web4 society — 7 roles, signed founding charter, append-only witnessed ledger, and a multi-surface API: a small MCP `/tools/*` convenience surface, a full REST `/v1` API, a sealed member↔hub channel, and an operator admin web GUI — all driven by the same admin CLI and Docker deployment. First deployment target: a pilot community chapter. Any community willing to operate as a Web4 society can use the same software.

## Witnessed law

The hub does **not** dictate how a society runs — it makes *whatever law the society adopts* auditable, and enforces adherence to it. This is the Web4 posture (see the [root README](../README.md), "Law is witnessed, not dictated") at society scale:

- **Signed, machine-readable law.** A society's rules — admission, role authority, thresholds, what escalates — are a law the PolicyEntity gate evaluates before every consequential act. It is **inspectable by anyone** (`GET /v1/hubs/:id/law`), *including while the hub's vault is locked*: the rules are public even when the hub can't yet act on them.
- **Changeable only with authority, and witnessed.** Amending the law requires unlock + signing and lands as a `LawAmended` event on the **append-only, hash-chained, witnessed ledger** — alongside every membership, role, skill, and intro act. You cannot quietly change the rules.
- **Fail-closed secrets.** The Sovereign key is encrypted at rest; the daemon never silently writes a plaintext key (an empty passphrase is allowed but must be *explicit*). A hub whose vault is locked **degrades to a read-only no-LCT surface** rather than running ungoverned.
- **Governed startup (shipped).** Unlocking a hub is itself an auditable, governed act — automatable or human-gated per the society's own law, but always recorded. Locked-mode ships today, and so does the **generic tier-2 M-of-N unlock seam** (`POST /v1/hubs/:id/unlock/challenge` + `/unlock/attest`): the hub mints the challenge, ledgers every step, and defers the quorum decision to an optional private verifier (`HUB_UNLOCK_VERIFIER`). With no verifier installed, tier-2 unlock reports N/A (501) and the hub runs unaffected — the novel quorum logic is pluggable, the seam is public. *Convenience is policy; the audit trail is not.*

We don't mandate the policy. We insist that whatever the policy is, is followed verifiably.

## Current status

**MVP complete (Sprints 0-6).** Buildable, runnable, documented for chapter organizers. Pilot-ready.

| Sprint | Capability | Status |
|---|---|---|
| 0 | Workspace scaffold + PRD + sprint plan | ✓ |
| 1 | Society instantiation (7 roles + signed charter) | ✓ |
| 2 | Chapter ledger (hash-chained signed event log) | ✓ |
| 3 | HTTP surface — small MCP `/tools/*` convenience set + full REST `/v1` API + sealed member channel | ✓ |
| 4 | Admin CLI + operator admin web GUI | ✓ |
| 5 | Docker package + first-chapter demo scripts | ✓ (Docker untested on dev machine; first operator with Docker should report) |
| 6 | Pilot-organizer docs + polish | ✓ |

## What this is

- **Web4 society shell** — uses `web4-core` + `web4-trust-core` directly; no reimplementation of LCT / T3/V3 / MRH / ATP / R6 primitives
- **AGPL-3.0-or-later** — patent grant per web4 root `PATENTS.md`; any community can fork
- **Single binary, single config file** — `docker compose up` deploys; chapter organizer needs no DevOps experience
- **Local-first, encrypted at rest** — chapter data stays in the chapter's directory; no telemetry, no vendor data extraction. The SQLCipher state store, the identity vault, and the ledger are all encrypted on disk with a key derived from the vault passphrase, held in memory only after ignition

## Extending the hub (plugin seam)

The hub is **open-core**: the daemon owns the hard parts — authenticating the
caller, gating by chapter law, bounding results to the caller's tier, and sealing
the response — and tools plug in behind that. The generic seam lives in the
[`hub-plugin`](hub-plugin/) crate:

- `ToolPlugin` — implement `name()` + `handle(ctx, args)`; the core runs your
  handler only after `gate → handle → scope`.
- `PluginCtx` — the capabilities the core *lends* a plugin (sign as the hub LCT,
  read projected state, send a sealed payload to a peer). Deliberately generic —
  the seam never names a specific tool.
- `PluginRegistry::dispatch` — the canonical `gate → handle → scope` path, the
  same contract as the daemon's channel dispatch.

This is the keystone of the split: the public core ships the seam, and any
operator can add their own (or proprietary) handlers without forking the hub.

## What this isn't (MVP scope)

- Not a Member Presence Toolkit (Hestia multi-hub plugin — separate package, V2)
- Not the Central Overlay layer (cross-chapter federation, global skill graph — V2)
- Not a *member-facing* public web UI — that's still out of scope. (An **operator/admin web GUI does ship**: a read-only dashboard at `/admin` on the fleet port, plus a write-capable operator plane — admit/deny admissions, add/re-key/remove members — at `/admin/joins` and `/admin/manage`, bound to 127.0.0.1 only on the admin port, default 8772.)
- Not Slack-integrated (deferred until pilot empirically defines coexistence requirements)
- Not ACT-anchored (ledger persists to a local `file` backend or a SQLCipher-encrypted `sqlite` backend; ACT anchoring is V2)
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

**Vault / unlock-first reality.** A sealed hub boots **locked** — every endpoint returns 503 except the unlock path — and is ignited with `hub unlock` (which presents the passphrase once and never stores it). CLI acts that touch the vault (`gen-lct`, `init`, …) resolve the passphrase from `HUB_PASSPHRASE` or a TTY prompt (an empty value is allowed but must be explicit). See [`docs/QUICKSTART.md`](docs/QUICKSTART.md) and [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

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
cargo test --release              # → the full suite should pass
```

## CLI surface

Run `hub --help` for the authoritative list. Highlights:

```
# Identity & vault
hub gen-lct <path> [--entity-type T]                 Generate a fresh LCT + keypair
hub seal-identity <path>                             Encrypt a plaintext identity file in place
hub export-public-identity <hub-dir>                 Write the clear tier-0 public-identity.json
hub rotate-passphrase <hub-dir>                      Re-key the vault to an operator-chosen passphrase
hub unlock [--port N]                                Ignite a locked, running hub (stub-console plugin)

# Society lifecycle
hub init <name> --sovereign-lct <path> [--storage file|sqlite]
                                                    Bootstrap a chapter society
hub status <hub-dir>                                 Chapter summary
hub migrate <hub-dir> --to file|sqlite              Migrate the storage backend
hub serve <hub-dir> [--port N] [--bind addr] [--admin-port N]
                                                    Run the HTTP server (REST + MCP + admin)
hub verify-ledger <hub-dir>                          Verify the chain end-to-end

# Members, roles, events, skills
hub add-member <hub-dir> <lct-id> [--name]          Add a member
hub remove-member <hub-dir> <lct-id> [--reason]     Remove a member
hub assign-role <hub-dir> <role> <member-lct-id>    Assign a role (role LCT is society-managed)
hub set-member-key <hub-dir> <member-lct-id> <pubkey-hex>
                                                    Pin/rotate a member's channel public key
hub record-event <hub-dir> <kind> <title> [--attended-by lct1,lct2,...]
                                                    Record a chapter event
hub declare-skill <hub-dir> <member-lct> <skill>    Declare a skill for a member
hub set-profile <hub-dir> <member-lct> KEY=VALUE... Update member profile fields

# Law
hub init-law [output] [--force]                     Write a starter chapter-law template
hub set-law <hub-dir> <yaml> [--diff-summary ...]   Set/amend chapter law (ledgers LawAmended)
hub get-law <hub-dir>                                Print the current chapter law

# Sovereign Council (V2-9)
hub council add <hub-dir> <member-lct-id> --pubkey HEX [--name]   Admit a co-Sovereign
hub council remove <hub-dir> <member-lct-id> [--kind] [--reason]  Remove a holder
hub council set-threshold <hub-dir> <m>             Set the M-of-N threshold
hub council show <hub-dir>                           Show council state

# Paired channels (V2 PAIRED-CHANNELS) — see docs/PAIRED-CHANNELS.md
hub envelope-sign --identity P --nonce N --payload JSON          Build a SignedEnvelope for REST
hub pair-generate-ephemeral                          Fresh X25519 ephemeral keypair (forward secrecy)
hub pair-encrypt / pair-decrypt ...                  Seal/open a pair-message body

# Query
hub query members <hub-dir>                          List members
hub query skill <hub-dir> <query>                    Find members by skill (substring)
hub query chapter <hub-dir>                          Chapter identity + role fill
```

## HTTP surface (when `hub serve` is running)

### MCP `/tools/*` — convenience subset

A small, unauthenticated localhost convenience surface — **not** the full API; the
REST `/v1` API below is the canonical write path.

```
GET  /tools                       Tool catalog
GET  /tools/query_hub             Hub identity + role-fill + recent events
                                  (/tools/query_chapter is a back-compat alias)
GET  /tools/list_members          Current member projection
GET  /tools/find_skill?q=...      Skill substring match
POST /tools/add_member            { member_lct_id, name? }
POST /tools/assign_role           { role, member_lct_id }  (role_lct_id optional; society-managed)
POST /tools/record_event          { event_kind, title, attended_by?, held_at? }
POST /tools/declare_skill         { member_lct_id, skill }
```

### REST `/v1` API — the full surface

```
GET  /.well-known/web4-hub.json                       Tier-0 discovery (did:web4, pubkey, founder)
GET  /v1/hubs/:id/law                                 Public chapter law (readable while locked)
POST /v1/auth/challenge                               Mint an envelope-signing nonce
POST /v1/hubs/:id/events                              Submit a signed, law-gated act
GET  /v1/hubs/:id/state                               Projected state (tier-scoped)
POST /v1/hubs/:id/unlock                              Tier-1 passphrase ignition (127.0.0.1)
POST /v1/hubs/:id/unlock/challenge | /unlock/attest   Tier-2 M-of-N unlock seam (501 w/o verifier)
POST /v1/hubs/:id/members/join                        Member admission request → law gate → queue
POST /v1/hubs/:id/channel                             Sealed member↔hub channel (see below)
*    /v1/hubs/:id/council/{propose,sign,proposals}    Sovereign Council proposal flow
*    /v1/hubs/:id/pairs/...                            Paired member↔member channels
*    /v1/hubs/:id/{credential,vp/request,vp/response} EUDI / OID4VC (see below)
```

### Operator admin web GUI (admin port, default 8772, 127.0.0.1-only)

Read-only dashboard at `/admin` (overview, members, roles, ledger, law, council,
pairs) plus a write-capable operator plane: the admission queue at `/admin/joins`
(Admit/Deny live, no restart) and member management at `/admin/manage`
(add / re-key / remove), backed by the `/admin/api/*` endpoints.

### Member admission flow

An external entity calls `request_citizenship` (or `POST /v1/hubs/:id/members/join`).
The chapter-law gate evaluates it: **Allow** admits immediately, **Deny** rejects (403),
**Escalate** parks the request in the operator admission queue (202), where an operator
Admits or Denies it live from `/admin/joins`.

### Sealed member↔hub channel

`POST /v1/hubs/:id/channel` carries a sealed, authenticated request whose inner tool is
one of: `find_members`, `request_intro` / `list_intros` / `respond_intro`,
`notifications` (drains the per-citizen sealed mailbox), `referenced_act`, and
`constellation_challenge` / `present_constellation` (assurance-tier bindings). The same
`gate → handle → scope` contract as the [plugin seam](#extending-the-hub-plugin-seam)
applies to every channel tool.

### Paired channels, Council & EUDI

- **Paired member↔member channels** — request / confirm / revoke pairs and exchange
  end-to-end-sealed messages (X25519 + ChaCha20-Poly1305, optional forward secrecy).
  See [`docs/PAIRED-CHANNELS.md`](docs/PAIRED-CHANNELS.md).
- **Sovereign Council** — propose / sign / threshold M-of-N governance over council-gated
  acts (data model + management ship now; threshold enforcement is Phase 2).
- **EUDI / OID4VC** — the hub issues membership credentials (OID4VCI, SD-JWT-VC) and
  verifies presentations (OID4VP) as a relying party, anchored to its `did:web4` identity.
  See [`docs/V2-V3-ARCHITECTURE.md`](docs/V2-V3-ARCHITECTURE.md).

## License

AGPL-3.0-or-later. See [`LICENSE`](../LICENSE) at the web4 root.

Commercial licensing available from Metalinxx Inc. for organizations that need non-AGPL terms — inquire via the [project repository](https://github.com/dp-web4/web4).
