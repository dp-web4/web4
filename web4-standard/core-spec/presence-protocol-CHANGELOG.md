# Presence Protocol — CHANGELOG

This file tracks every protocol version bump. The PR introducing a
bump MUST add an entry here with the bump number, what changed, and
which implementations were updated in the same commit/PR.

The discipline rule: **a protocol change is not complete until this
file is updated, all conforming SDKs are updated, and the
conformance test vectors reflect the new shape.** See
`shared-context/protocol-discipline/PR_CHECKLIST.md` for the PR
checklist that enforces this.

---

## v1 — 2026-05-16 — Policy engine + vault schema v2

The first **real test of the discipline**: a protocol version bump
driven by a feature landing in the daemon. All artifacts updated in
one coordinated change.

**What changed**

- **`hestia_query_policy` returns real decisions.** Engine ported
  from `claude-code/plugins/web4-governance/governance/`. Evaluates a
  pending action against the active preset's rules using glob/regex
  pattern matchers, command pattern matchers (with positive and
  negative match), time-window gating, and per-rule rate limits.
- **`PolicyResult` shape extended:**
    - New: `ruleId` — stable rule identifier (`"deny-destructive-commands"`)
    - New: `ruleName` — human-readable rule name
    - New: `constraints` — audit-trail constraint list (`policy:`,
      `decision:`, `rule:` namespaced)
    - Kept: `policyId` — now an alias of `ruleId` for v0 back-compat
- **Vault schema v1 → v2.** Adds a `policy` section alongside `entries`
  with `active_preset`, `overrides`, `custom_rules`. v1 vaults
  deserialize transparently (the field is `#[serde(default)]`); on
  next save, the file becomes v2.
- **Four built-in presets**: `permissive`, `safety`, `strict`,
  `audit-only`. `safety` is the default for new vaults. Configurable
  via the new `hestia policy {show|set|test}` CLI subcommand.
- **`vault_set` chain audit.** Daemon now appends a `vault_set` event
  to the witness chain whenever a credential is added or replaced
  (credential name only — the secret value is never written to the
  chain). Was technically present in v0 but not documented.

**Implementations updated in this PR**

- ☑ Hestia daemon — `dp-web4/hestia` `core/` crate (0.0.2 → **0.0.3**)
- ☑ TypeScript SDK — `@hestia-tools/plugin-sdk` (0.0.2 → 0.0.3)
- ☑ Python SDK — `hestia-plugin-sdk` (local, still pre-publish)
- ☑ Rust SDK — `hestia-plugin-sdk` (local, still pre-publish)
- ☑ `hardbound-pak` Rust/Python/TS (all three, 0.0.1 → 0.0.2)
- ☑ Spec, CHANGELOG, schemas, conformance vectors

**Not yet implemented at v1 (deferred to v2+)**

- Pre-action policy denial at `hestia_begin_action` time. Today the
  orchestrator must explicitly call `hestia_query_policy` between
  `begin_action` and the actual tool execution. Auto-evaluation at
  `begin_action` lands when we've seen enough real traffic to know
  the right defaults.
- Interactive vault approval flow. `approvalToken` in `vault_get`
  response is still always `null`.
- Hardbound parity. Hardbound continues to expose the (now-v1)
  trait surface from `hardbound-pak`; an actual Hardbound
  implementation is its own private workstream.

---

## v0 — 2026-05-16 — Initial capture

Captures the actual current state of the Hestia daemon's inward MCP
surface as of 2026-05-16. No new features; this version exists to
freeze a baseline and start enforcing the discipline.

**Tools (8):** `hestia_connect`, `hestia_begin_action`,
`hestia_record_outcome`, `hestia_query_policy`,
`hestia_vault_get`, `hestia_vault_set`, `hestia_query_history`,
`hestia_request_witness`.

**Resources (6):** `hestia://context/shared`,
`hestia://society/state`, `hestia://witness/recent`,
`hestia://session/own`, `hestia://society/trust/{plugin_id}`,
`hestia://vault/{name}`.

**Error codes (10):** `not_connected`, `session_expired`,
`policy_denied`, `vault_denied`, `vault_not_found`,
`vault_scope_mismatch`, `action_not_found`, `invalid_role`,
`unknown_tool`, `internal_error`.

**Error envelope:** Mechanism A — `_hestia_error` in tool result
structured content. See spec §6.

**Implementations at v0:**
- Hestia daemon — `dp-web4/hestia` `core/` crate at `0.0.2` (live)
- TypeScript SDK — `@hestia-tools/plugin-sdk` `0.0.2` on npm
- Python SDK — `hestia-plugin-sdk` local-only (not published yet)
- Rust SDK — `hestia-plugin-sdk` local-only (not published yet)
- Hardbound — parity not yet implemented (tracked separately)

**Known drift (resolved in 1a-4 of the discipline pass):**
- `PROTOCOL_VERSION = 0` constant exists in Rust SDK only; missing
  in TS and Python SDKs.
- `TrustState` is missing `entityId`, `successCount`, `successRate`
  fields in all three SDKs (daemon emits them; SDKs ignore).
- Daemon's `hestia://society/state` returns `trust_states_known`
  in snake_case — should be `trustStatesKnown` for consistency
  (deferred to v1).

**Not yet implemented at v0 (reserved fields):**
- `hestia_query_policy` returns default-allow for every action.
  Real policy engine arrives in v1.
- `approvalToken` in vault_get response is always `null`.
  Interactive vault approval arrives in v1.
- Error codes `policy_denied`, `vault_denied`, `invalid_role` are
  reserved in the registry but the v0 daemon emits
  `internal_error` for these conditions instead.

---

## Upcoming (planned)

### v1 — policy engine + vault schema v2

Expected changes:

- **`hestia_query_policy` returns a real decision.** Engine
  ported from `claude-code/plugins/web4-governance/governance/`.
  Four built-in presets: `permissive`, `safety`, `strict`,
  `audit-only`. Wire shape extends to include `ruleName` and
  `constraints` fields per the Python `PolicyEvaluation`.
- **`hestia_begin_action` evaluates policy before assigning a
  chain position.** A pre-action `deny` short-circuits — no chain
  entry is appended and the response carries the policy reason.
- **Daemon emits `policy_denied` errors** in the cases where v0
  emitted `internal_error`.
- **Vault state extended.** Schema v1 → v2 adds `policy` section
  alongside `entries`. Same vault file, larger payload. Auto-
  migration on first open of a v1 vault.
- **`trust_states_known` → `trustStatesKnown`** in
  `hestia://society/state` (case fix).

Will require simultaneous bump of:
- Hestia daemon (`hestia` crate on crates.io)
- TypeScript SDK (`@hestia-tools/plugin-sdk` on npm)
- Python SDK (`hestia-plugin-sdk` on PyPI — first publish under
  this name)
- Rust SDK (`hestia-plugin-sdk` on crates.io — first publish)
- `hardbound-pak` `PolicyDecision` trait to add `rule_name` +
  `constraints`
- Hardbound private repo to consume the new shape
- Test vectors at
  `web4-standard/testing/conformance/presence-protocol-conformance.json`

---

## Process

A protocol change PR must:

1. Open this file and add the new version section above
   "Upcoming (planned)".
2. Describe every shape change in the entry.
3. List which artifacts ship the same change in the PR.
4. Update the spec (`presence-protocol.md`) to reflect the new
   version.
5. Update the JSON Schemas at `web4-standard/schemas/presence-protocol/`.
6. Update the conformance vectors at
   `web4-standard/testing/conformance/presence-protocol-conformance.json`.
7. Update each SDK's `PROTOCOL_VERSION` constant.
8. File a Hardbound parity ticket (since that repo is private) or,
   if same author, include Hardbound updates in the same PR.

See `shared-context/protocol-discipline/PR_CHECKLIST.md` for the
copy-pasteable checklist.
