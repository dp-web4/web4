# Web4 Presence Protocol Specification

**Version**: 1
**Status**: Draft — captures Hestia 0.0.3+ with the policy engine wired.
**Companion**: [`mcp-protocol.md`](./mcp-protocol.md) — the *outward* MCP that societies use to engage each other. This spec is the *inward* MCP that the **presence layer** of a Web4 entity exposes to its **cognition layer** (agentic orchestrator).
**Changelog**: [`presence-protocol-CHANGELOG.md`](./presence-protocol-CHANGELOG.md)

---

## 1. Scope

This spec covers the protocol an agentic orchestrator (SAGE, Claude
Code, Cursor, OpenClaw, custom agent) speaks to the **presence
layer** of a Web4 entity. The presence layer is the social face of
the entity: it holds identity (LCT), the credential vault, the
witness chain, the trust state, and the policy engine. Two
implementations exist:

- **Hestia** — software-encrypted vault, passphrase-derived seal.
  Consumer tier, portable. AGPL-3.0-or-later. Reference
  implementation.
- **Hardbound** — hardware-bound vault (TPM 2.0 / YubiKey / Secure
  Enclave). Manufactured at the embedded tier or licensed to
  institutions. Private; same wire protocol.

Both implementations expose this protocol identically. Conformance
to this spec is what makes an implementation a Web4 presence layer.

### 1.1 Inward vs. outward MCP

The Web4 equation `MCP + RDF + LCT + T3/V3*MRH + ATP/ADP` has two
distinct MCP surfaces:

- **Outward MCP** — society ↔ society, specified in
  [`mcp-protocol.md`](./mcp-protocol.md). The presence layer acts
  as the MCP server for inbound cross-society R6/R7 actions.
- **Inward MCP** — presence ↔ orchestrator, this spec. The
  presence layer acts as the MCP server for the cognition driving
  the entity from within.

A single Hestia/Hardbound process serves both surfaces. They are
distinct logical endpoints; today they share a transport (HTTP /
StreamableHTTP).

### 1.2 What the orchestrator gets

A conforming implementation provides:

1. **Identity** — a Soft LCT for the orchestrator's session
   (Hestia) or a hardware-attested LCT (Hardbound).
2. **R6/R7 lifecycle** — `begin_action` → `record_outcome` with
   the chain position assigned at begin time.
3. **Vault access** — read/write credentials gated by scope and
   per-plugin allow-lists.
4. **Witness chain** — query and append hash-linked entries; one
   per outcome by default.
5. **Trust state** — per-plugin T3/V3 tensors that evolve with
   outcomes.
6. **Policy** — pre-action allow/deny/warn decisions backed by a real
   engine (since v1). Four built-in presets (`permissive`, `safety`,
   `strict`, `audit-only`); user overrides + custom rules layered on
   top. Active preset stored inside the vault. See §3.4 for the
   query shape.
7. **Shared context** — read-only access to cross-agent shared
   state surfaced by the user (a small key/value namespace).

---

## 2. Versioning

This protocol is versioned with a single integer `protocolVersion`.

- **v0** — initial capture. 8 tools, 6 resource URIs, default-allow
  policy stub.
- **v1** — policy engine wired: `hestia_query_policy` returns real
  decisions from a rule-based engine with 4 built-in presets. The
  response shape gains `ruleId`, `ruleName`, and `constraints` fields
  (back-compat: `policyId` retained as alias of `ruleId`). Vault
  schema extended (v1 → v2) to store the active preset, per-rule
  overrides, and custom rules alongside credentials. `vault_set`
  audit chain entry is now emitted on credential writes.
- Bumps follow the rule: **any change to the wire shape of a tool's
  input or output, addition/removal of tools or resources, or
  change to error code semantics, requires a version bump.**
  Exception: **optional additive fields** (new keys that older readers
  can safely ignore) are back-compatible and do NOT trigger a bump.
  `status`/`nextPollMs` (output, v1 back-compat addition) and
  `synthetic` (input, v1 back-compat addition) were both added under
  this exception. Removals, renames, type changes, or new required
  fields always bump.

The daemon advertises its `protocolVersion` in the
[`hestia_connect`](#31-hestia_connect) response. SDKs MUST expose a
`PROTOCOL_VERSION` constant matching the version they implement.
SDKs SHOULD emit a warning on connect if their version differs
from the daemon's; they SHOULD NOT refuse the session — forward
compatibility is preferred over hard failure.

Implementations MAY support older protocol versions concurrently
via content negotiation, but this is not required for v0.

---

## 3. Tool surface

All tool calls follow standard MCP JSON-RPC semantics. Wire casing
is split by surface and is fixed by the JSON Schemas in
`web4-standard/schemas/presence-protocol/` (normative — see §7):

- **Tool input arguments are `snake_case`** (`plugin_id`,
  `host_agent`, `action_id`, …), as the input schemas require.
- **Tool output and all §5 type-catalog shapes are `camelCase`**
  (`sessionId`, `softLct`, `protocolVersion`, …).
- **§4 resource bodies follow the casing of what they return** —
  there is no single blanket rule, because the six resources return
  different kinds of payload:
  - `hestia://society/state` returns an **ad-hoc `snake_case`** stats
    object (`sovereign_lct`, `chain_length`, …) — it is *not* a §5
    type-catalog struct; its casing is bound by vector P0-009.
  - `hestia://context/shared` is an **opaque** user-owned JSON
    namespace with no casing mandate.
  - The other four resources return §5 type-catalog structs and so
    carry the same **`camelCase`** keys: `witness/recent` →
    `WitnessEntry` (`chainPosition`, …; bound by vector P0-010),
    `session/own` → `Session`, `society/trust/{plugin_id}` →
    `TrustState`, `vault/{name}` → `VaultEntry`.

Timestamps are ISO-8601 UTC strings. UUIDs are RFC 4122 v4 hex
with dashes. Session IDs are UUIDs.

The eight tools below MUST be implemented by a conforming
presence layer.

### 3.1 `hestia_connect`

Establish a plugin session and receive a Soft LCT.

**Input:**
```json
{
  "plugin_id": "claude-code",
  "plugin_version": "1.0.0",
  "host_agent": "claude-code",
  "host_agent_version": "1.0.0",
  "requested_role": "citizen",
  "protocol_version": 1,
  "synthetic": false
}
```
`plugin_id` and `host_agent` are REQUIRED. Others are OPTIONAL.

`synthetic` (OPTIONAL, default `false`) declares the calling client as
a test harness, fuzzer, or other non-orchestrator workload. The
presence layer SHOULD still witness the session (chain entries remain
authoritative), but SHOULD exclude synthetic plugins from
operator-facing aggregations (dashboards, trust roll-ups) by default.
This is a self-declaration: implementations MAY honor it without
verification. Once a plugin_id has been observed with `synthetic:
true`, the presence layer MAY treat all subsequent activity from the
same plugin_id as synthetic for the lifetime of that record.
(**Not yet conformed** — no JSON Schema, no conformance vector, no
CHANGELOG entry. Tracked in §8 drift table. See C5 audit P2.)

**Output:**
```json
{
  "sessionId": "97a3-...",
  "softLct": "lct:web4:session:abc123",
  "assignedRole": "citizen",
  "protocolVersion": 1
}
```

**Errors:**
- `hestia.invalid_role` (v1+) — the requested role is not available to plugins; v0 daemons MAY emit `hestia.internal_error` instead (see §6.1)
- `hestia.internal_error` — connection setup failed

### 3.2 `hestia_begin_action`

Begin tracking an R6/R7 action. The presence layer records the
intent, assigns a chain position, and returns an action handle the
orchestrator carries through `record_outcome` and `query_policy`.

**Input:**
```json
{
  "tool_name": "Bash",
  "target": "echo hello",
  "parameters": { "command": "echo hello" },
  "atp_stake": 8.0,
  "session_id": "97a3-..."
}
```
`tool_name` REQUIRED. `target`, `parameters`, `atp_stake`,
`session_id` OPTIONAL. `session_id` is recommended whenever the
caller has it; it disambiguates concurrent plugins driving the
same daemon.

**Output:**
```json
{
  "actionId": "ae27-...",
  "startedAt": "2026-05-16T15:45:13.633Z",
  "chainPosition": 12
}
```

**Errors:** `hestia.internal_error`.

### 3.3 `hestia_record_outcome`

Submit the outcome of a previously-begun action. The presence
layer appends an `outcome` chain entry and evolves the calling
plugin's trust state.

**Input:**
```json
{
  "action_id": "ae27-...",
  "success": true,
  "magnitude": 0.5,
  "error": null,
  "result": { "exit_code": 0 },
  "session_id": "97a3-..."
}
```
`action_id` and `success` REQUIRED. `magnitude` in `[0,1]`; if
omitted, the daemon SHOULD default to 0.5. `error` MUST be present
on failure outcomes, OPTIONAL on success. `result` is an
implementation-defined object.

**Output:**
```json
{
  "witnessEntryHash": "abc...",
  "updatedTrustState": { /* TrustState — see §5 */ }
}
```

**Errors:** `hestia.action_not_found`, `hestia.internal_error`.

### 3.4 `hestia_query_policy`

Query the policy engine for an allow/deny/warn decision on a
pending action. Backed by a real rule engine since v1 (was a
default-allow stub in v0).

**Input:**
```json
{
  "action_id": "ae27-...",
  "context": { "user_active": true },
  "session_id": "97a3-..."
}
```
`action_id` REQUIRED.

**Output (v1):**
```json
{
  "decision": "allow",
  "reason": "Matched rule: Allow read-only tools",
  "ruleId": "allow-read-tools",
  "ruleName": "Allow read-only tools",
  "policyId": "allow-read-tools",
  "enforced": true,
  "constraints": [
    "policy:policy:abc123...",
    "decision:allow",
    "rule:allow-read-tools"
  ],
  "status": "decided",
  "nextPollMs": null
}
```

`decision` is one of `"allow"`, `"deny"`, `"warn"`. `ruleId` MAY be
`null` (default-policy path); when set, it's a stable rule identifier
the orchestrator can log. `ruleName` is a human-readable label
(`null` on default-policy paths). `policyId` is an alias of `ruleId`
kept for v0 SDK back-compat — new code SHOULD read `ruleId`.
`constraints` is an audit-trail-friendly list of `policy:`, `decision:`,
`rule:` namespaced strings, always at least three entries when present.

#### 3.4.1 The "wait" protocol (`status` + `nextPollMs`)

`status` is one of:

- `"decided"` (default) — the verdict is final; the orchestrator can act on `decision`.
- `"evaluating"` — the engine is **here** but still working on a verdict
  (e.g. it has invoked an LLM-backed reviewer or is awaiting an external
  attestation). The orchestrator SHOULD wait `nextPollMs` milliseconds
  and then re-query with the same `action_id`.

When `status == "evaluating"`, `decision` carries the engine's *current
tentative* verdict (usually the default policy) and `nextPollMs` is the
suggested wait. Orchestrators SHOULD bound their total re-poll budget
(recommended: 5 seconds total, 3 polls max) and fall back to a local
heuristic if the engine never settles to `"decided"`.

A v1 daemon with a synchronous rule engine always returns
`status: "decided"` and `nextPollMs: null`. The `"evaluating"` status
is reserved for future v1.x engines that consult an LLM-backed policy
entity or external attestation service; orchestrator implementations
MUST support both branches today so the protocol stays back-compatible
when those engines arrive.

**Errors:** `hestia.action_not_found`, `hestia.policy_denied` (v1+;
when deny is enforced — v0 daemons MAY emit `hestia.internal_error`
instead, see §6.1), `hestia.internal_error`.

### 3.5 `hestia_vault_get`

Request a credential from the vault.

**Input:**
```json
{
  "name": "anthropic_key",
  "scope": ["infer"],
  "reason": "user is invoking the agent",
  "session_id": "97a3-..."
}
```
`name` REQUIRED. `scope` and `reason` OPTIONAL but RECOMMENDED.
`session_id` is used to resolve the caller's `plugin_id` against
the credential's allow-list.

**Output:**
```json
{
  "value": "sk-...",
  "approvalToken": null
}
```
`approvalToken` is reserved for v1+ flows that require user
interactive approval; in v0 it's always `null`.

**Errors:**
- `hestia.vault_not_found` — credential not in vault
- `hestia.vault_scope_mismatch` — caller is not in `allowed_consumers` or scope doesn't match
- `hestia.vault_denied` — interactive approval refused (reserved for v1+)
- `hestia.internal_error`

### 3.6 `hestia_vault_set`

Store or upsert a credential. v0 has no interactive approval —
the caller can write without prompt. v1+ MAY add approval flow.

**Input:**
```json
{
  "name": "anthropic_key",
  "value": "sk-...",
  "scope": ["infer"],
  "tags": ["llm"],
  "allowed_consumers": ["claude-code", "openclaw"]
}
```
`name` and `value` REQUIRED.

**Output:**
```json
{
  "stored": true,
  "entryId": "uuid-of-vault-entry"
}
```

Side effect: appends a `vault_set` entry to the witness chain (the
credential name is recorded; the value is NOT).

**Errors:** `hestia.internal_error`.

### 3.7 `hestia_query_history`

Query the witness chain.

**Input:**
```json
{
  "filter": {
    "tool_name": "Bash",
    "target_pattern": "/etc/*",
    "since": "2026-05-01T00:00:00Z",
    "limit": 50,
    "outcome": "success"
  }
}
```
All fields OPTIONAL. `limit` defaults to 50, max 500. `outcome` is
one of `"success"`, `"failure"`, `"abandoned"`.

**Output:**
```json
{
  "entries": [ /* WitnessEntry — see §5 */ ],
  "hasMore": false
}
```

Entries are returned **newest first**. `hasMore` indicates the
window was truncated by `limit`.

**Errors:** `hestia.internal_error`.

### 3.8 `hestia_request_witness`

Append a custom event to the witness chain. Plugins use this for
events that don't fit the R6/R7 action lifecycle (e.g.
"user_observed_outcome", "plugin_internal_milestone").

**Input:**
```json
{
  "event_type": "user_observed_outcome",
  "event_data": { "observed_by": "user", "tag": "good" }
}
```
`event_type` REQUIRED.

**Output:**
```json
{ "witnessEntryHash": "abc..." }
```

**Errors:** `hestia.internal_error`.

---

## 4. Resource surface

The presence layer exposes six resource URIs (4 fixed + 2
parameterized) via MCP's `resources/read`.

### 4.1 Fixed resources

| URI | Returns |
|---|---|
| `hestia://context/shared` | Cross-agent shared key/value namespace, JSON object. Read-only in v0. |
| `hestia://society/state` | Society identity macro stats: `sovereign_lct`, `chain_length`, `session_count`, `vault_entries`, `known_plugins`. |
| `hestia://witness/recent` | Most recent N (≤ 50) chain entries. JSON object `{"entries": [...]}`. Newest first. |
| `hestia://session/own` | This session's record (Session struct from §5). |

### 4.2 Parameterized resources

| URI pattern | Returns |
|---|---|
| `hestia://society/trust/{plugin_id}` | The TrustState (§5) for the named plugin. |
| `hestia://vault/{name}` | A VaultEntry (§5) **with `secret` redacted** — metadata only. |

All resource bodies are JSON, mime type `application/json`.

---

## 5. Type catalog

The type-catalog shapes below — and all tool **output** shapes —
use **camelCase keys** regardless of the source language's native
convention. Languages map to their native casing via serializer
hints. This camelCase rule does **not** extend to tool *input*
arguments, which are `snake_case` per §3 and the bound input
schemas. For §4 resource bodies the casing is per-resource (see the
split in §3): a resource that returns one of these §5 structs carries
its `camelCase` keys (e.g. `witness/recent` → `WitnessEntry`,
`session/own` → `Session`), while the ad-hoc `society/state` stats
object is `snake_case` (bound by vector P0-009) and `context/shared`
is opaque.

### 5.1 Session

```json
{
  "sessionId": "uuid",
  "pluginId": "claude-code",
  "pluginVersion": "1.0.0",
  "hostAgent": "claude-code",
  "hostAgentVersion": "1.0.0",
  "assignedRole": "citizen",
  "softLct": "lct:web4:session:abc",
  "connectedAt": "2026-05-16T15:45:13.633Z"
}
```

### 5.2 R6Action

```json
{
  "actionId": "uuid",
  "toolName": "Bash",
  "startedAt": "2026-05-16T15:45:13.633Z",
  "chainPosition": 12
}
```

### 5.3 Outcome (orchestrator → presence)

```json
{
  "success": true,
  "magnitude": 0.5,
  "error": null,
  "result": { /* opaque object */ }
}
```

### 5.4 PolicyResult / PolicyDecision

```json
{
  "decision": "allow",
  "reason": "...",
  "ruleId": "deny-destructive-commands",
  "ruleName": "Block destructive shell commands",
  "policyId": "deny-destructive-commands",
  "enforced": true,
  "constraints": [
    "policy:policy:<hex>",
    "decision:deny",
    "rule:deny-destructive-commands"
  ],
  "status": "decided",
  "nextPollMs": null
}
```
`decision` is one of `"allow"`, `"deny"`, `"warn"`. `ruleId` and
`ruleName` are `null` on default-policy decisions. `policyId` is
the v0 alias of `ruleId` retained for back-compat. `enforced` is
`true` when the policy engine actively blocked or allowed the
action (vs. a default pass-through). `status` and `nextPollMs`
support the wait protocol (§3.4.1): synchronous engines always
return `"decided"` / `null`.

### 5.5 TrustState

```json
{
  "entityId": "plugin:claude-code",
  "t3": { "talent": 0.61, "training": 0.78, "temperament": 0.65 },
  "v3": { "valuation": 0.5, "veracity": 0.51, "validity": 0.5 },
  "level": "medium",
  "actionCount": 81,
  "successCount": 75,
  "successRate": 0.926,
  "daysSinceLast": 0.001
}
```

`level` is one of `"low"`, `"medium_low"`, `"medium"`,
`"medium_high"`, `"high"` (the categorical `TrustLevel` from
web4-trust-core).

### 5.6 WitnessEntry

```json
{
  "hash": "sha256-hex",
  "prevHash": "sha256-hex",
  "timestamp": "2026-05-16T15:45:13.633Z",
  "eventType": "outcome",
  "eventData": { /* opaque object */ },
  "signerLct": "lct:web4:hestia:sovereign:...",
  "chainPosition": 12
}
```

`eventType` is conventionally one of `"session_started"`,
`"outcome"`, `"vault_set"`, plus any custom types submitted via
`hestia_request_witness`.

### 5.7 VaultEntry (metadata only — `secret` redacted on the wire)

```json
{
  "id": "uuid",
  "name": "anthropic_key",
  "scope": ["infer"],
  "tags": ["llm"],
  "allowedConsumers": ["claude-code"],
  "createdAt": "2026-05-16T15:45:13.633Z"
}
```

The `secret` field exists in storage but is NEVER returned through
`resources/read`. The only way to retrieve a secret value is via
`hestia_vault_get`, which goes through scope + consumer checks.

---

## 6. Error envelope (Mechanism A)

MCP's standard error path (JSON-RPC `error.code` + `error.data`)
is unreliable across SDK runtimes: the official Python MCP SDK
strips `data` on error normalization, so typed error context is
lost. To survive that, the presence layer embeds typed errors in
the *success* path with a sentinel envelope:

```json
{
  "_hestia_error": {
    "code": "hestia.vault_not_found",
    "message": "Credential 'anthropic_key' not found in vault.",
    "data": { "name": "anthropic_key" }
  }
}
```

When a SDK sees `_hestia_error` in a tool result's structured
content, it MUST raise the typed exception with the embedded
code, message, and data. The tool call itself is reported as
successful by the MCP runtime; the application-level error is
inside the envelope. This is **Mechanism A** from ADR-0005.

### 6.1 Error code registry

| Code | Origin | Semantics |
|---|---|---|
| `hestia.not_connected` | SDK | Method called before `connect()` |
| `hestia.session_expired` | SDK / daemon | Session no longer valid |
| `hestia.policy_denied` | daemon (v1+) | Policy engine denied the action |
| `hestia.vault_denied` | daemon (v1+) | Interactive vault approval refused |
| `hestia.vault_not_found` | daemon | Credential name not in vault |
| `hestia.vault_scope_mismatch` | daemon | Caller not in allowed_consumers or scope mismatch |
| `hestia.action_not_found` | daemon | No in-flight action with that `action_id` |
| `hestia.invalid_role` | daemon (v1+) | Requested role not available to plugins |
| `hestia.unknown_tool` | daemon | Tool name not in §3 |
| `hestia.internal_error` | daemon | Catch-all; the `message` field carries detail |

Codes marked `(v1+)` are reserved — SDKs MAY map them, but v0
daemons MAY emit `hestia.internal_error` instead until v1 lands.

---

## 7. Conformance

A conforming presence layer implementation MUST:

1. Implement all 8 tools in §3 with the documented input and
   output shapes.
2. Implement all 6 resource URIs in §4.
3. Use the `_hestia_error` envelope (§6) for all typed errors.
4. Advertise `protocolVersion` in `hestia_connect` response.
5. Pass the conformance test vectors at
   `web4-standard/testing/conformance/presence-protocol-conformance.json`.

A conforming SDK implementation MUST:

1. Expose a `PROTOCOL_VERSION` constant matching the spec version
   it implements.
2. Emit a warning (not a fatal error) on protocol-version
   mismatch at connect time.
3. Unwrap the `_hestia_error` envelope into a typed exception when
   present in tool results.
4. Pass the conformance test scenarios against a reference daemon.

**Precedence.** Where this document's prose and the JSON Schemas
at `web4-standard/schemas/presence-protocol/` (or the conformance
vectors bound in item 5) disagree about a wire shape — including
key casing — the Schemas and vectors are normative and the prose
is in error. The Schemas directory is normatively bound by this
clause, not only the vectors JSON.

Conformance does not require implementing the v0 policy engine
stub literally; an implementation MAY return real policy
decisions earlier than the spec mandates, provided the shape
matches §3.4 and §5.4.

---

## 8. Implementation drift (as of 2026-05-18)

Captured here because the discipline is only as good as the
honesty about where it isn't yet held.

| Drift | Where | Resolution |
|---|---|---|
| `PROTOCOL_VERSION` constant exists only in Rust SDK | TS, Python SDKs | Add to both — covered by `1a-4`. |
| `TrustState` is missing `entityId`, `successCount`, `successRate` in all SDKs | All 3 SDKs | Add fields — covered by `1a-4`. |
| ~~Error codes `policy_denied`, `invalid_role` referenced by SDKs but never emitted by daemon~~ | ~~Daemon~~ | **Resolved in v1.** The policy engine is wired (v1, 2026-05-16); these two codes are now emittable. §6.1 marks them `(v1+)`. |
| `vault_denied` referenced by SDKs but not yet emittable | Daemon | **Still pending.** Its only trigger — interactive vault approval refused (§6.1) — is deferred to v2+ (see §3.5/§3.6 and the CHANGELOG). Reserved in §6.1 as `(v1+)` so SDKs MAY map it, but no daemon can emit it until that approval flow ships. |
| `WitnessEntry.timestamp` is a string in SDK types but parsed as `chrono::DateTime` in Rust | Rust SDK | Internal — wire format is the string. No spec change. |
| Daemon's `hestia://society/state` resource returns `trust_states_known` (snake_case) | None — not drift | `society/state` is an **ad-hoc stats object** (not a §5 struct); its `snake_case` keys are bound by vector P0-009 (`sovereign_lct`, `chain_length`, …). **No rename:** the earlier camelCase aspiration contradicted that vector. This is resource-specific — the four §5-typed resource bodies (`witness/recent`, `session/own`, `society/trust/{plugin_id}`, `vault/{name}`) stay `camelCase`, as vector P0-010 (`entries[0].chainPosition`) and the `witness_entry`/`trust_state` schemas require. See the per-resource casing split in §3. |
| `synthetic` field in §3.1 `hestia_connect` input has no JSON Schema, no conformance vector, no CHANGELOG entry | Spec ↔ artifacts | Discipline gap (C5 audit P2). No v1 `hestia_connect` schema exists (only `v0/tools/hestia_connect.schema.json`); creating one is a structural prerequisite. Until then, `synthetic` is spec-documented but not artifact-conformed. |

---

## 9. Open work tracked elsewhere

### Completed in v1

- ~~**Policy engine**~~ — ported from `claude-code/plugins/web4-governance/`
  into Hestia core (v1, 2026-05-16). Four built-in presets; real
  rule-based evaluation. See CHANGELOG v1 entry.
- ~~**Policy state in vault**~~ — vault schema v1 → v2 shipped with
  `active_preset`, `overrides`, `custom_rules`. Same v1 protocol
  bump. See CHANGELOG v1 entry.

### Still pending

- **Hardbound parity** — implement this spec against a hardware-
  sealed vault (SealedVault trait from `hardbound-pak`). Same
  wire protocol; different storage backend.
- **Outward MCP cross-references** — once both protocols are
  stable, document the call graph from inward-MCP `record_outcome`
  into outward-MCP cross-society R7 actions.
- **`synthetic` discipline completion** — create a v1
  `hestia_connect` schema, add a conformance vector for `synthetic`,
  and add a CHANGELOG sub-entry. Prerequisite: the v1 schema
  directory currently has no `hestia_connect` schema (structural gap
  identified in C5 audit P2). Tracked in §8 drift table.
