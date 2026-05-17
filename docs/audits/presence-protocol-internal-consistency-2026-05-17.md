# presence-protocol.md Internal-Consistency Audit

**Date**: 2026-05-17
**Auditor**: autonomous web4 session (legion, Sprint 54+ candidate **C5**)
**Subject**: `web4-standard/core-spec/presence-protocol.md` (648 lines, 9 sections), v1
**Companion artifacts cross-checked**: `presence-protocol-CHANGELOG.md`,
`web4-standard/schemas/presence-protocol/{v0,v1}/`,
`web4-standard/testing/conformance/presence-protocol-conformance.json`
**Scope**: Internal consistency only — contradictions, normative/illustrative
conflicts, type-catalog vs tool-surface drift, and spec↔conformance-artifact
seams **within this spec and the artifacts it points to**. This audit does NOT
compare the spec to any SDK or daemon implementation (those live in other
repos) and does **not** patch the spec, schemas, CHANGELOG, or vectors.
Remediation is a separate reviewable follow-up, exactly as the C2
mcp-protocol audit fed PRs #200/#201/#203.

**Trigger**: The operator landed `presence-protocol.md` (v0→v1) plus schemas
and conformance vectors directly on `main` in a 2026-05-16 burst
(`d7867704`…`66d7c3b5`). The 2026-05-15 C2 audit established
internal-consistency review as a standing Development-phase deliverable; this
is the same instrument applied to the newest, freshly-landed Draft spec
(§1: "Status: Draft"; §8: "the discipline is only as good as the honesty
about where it isn't yet held"). No prior consistency review of this spec
exists.

---

## Methodology

Full end-to-end read of the spec, then cross-check of every documented input
example and type against the JSON Schemas and conformance vectors the spec
normatively names in §7. Each finding records: location(s), the passages in
tension, why it is an *internal* inconsistency (not merely an omission), and a
recommended resolution direction. Severity:

| Sev | Meaning |
|-----|---------|
| **HIGH** | A conformant implementation cannot satisfy the document as written, OR a normative passage contradicts the conformance artifacts the spec itself binds. |
| **MEDIUM** | Normative guidance is self-contradicting or ambiguous enough that two good-faith implementations would diverge, OR a canonical reference (type catalog) lags the surface it documents. |
| **LOW** | Maintainability / link / narrative-completeness hazard; not a blocking contradiction today. |

**Headline**: The spec's central thesis is *protocol discipline* (CHANGELOG
"discipline rule"; §8 honesty table; §7 conformance). Two HIGH findings strike
that thesis directly: (P1) the one normative statement about input wire
casing is contradicted by every input example **and** every input JSON Schema;
(P2) the spec's most recent change (`synthetic`, `66d7c3b5`) violates the
spec's own stated completion-discipline rule — no schema, no conformance
vector, no CHANGELOG entry — while the *sibling* back-compat change
(`status`/`nextPollMs`) followed it fully. The discipline is asymmetrically
held, and the spec does not yet say so.

---

## Findings Summary

| # | Location | Sev | One-line |
|---|----------|-----|----------|
| P1 | §3 (101–103) ↔ §3.1–§3.8 examples ↔ all input schemas; §5 (429–431) | **HIGH** | §3 normatively states tool **input** is camelCase; every input example and every input JSON Schema is snake_case (`plugin_id`, `action_id`, …). Outputs *are* camelCase. The normative casing rule for input is false as written. |
| P2 | §3.1 (121, 126–134) ↔ schemas ↔ CHANGELOG discipline rule | **HIGH** | `synthetic` (added `66d7c3b5`) appears in **zero** schemas, **zero** conformance vectors, **zero** CHANGELOG entries — a self-violation of the CHANGELOG's own "a protocol change is not complete until…" rule. Asymmetric with `status`/`nextPollMs`, which followed the rule fully. |
| P3 | §7 (591–617) ↔ §3 (101–103) | MED | §7 Conformance is a flat MUST-list pointing back to "the documented shapes in §3" — which are self-contradictory (P1). The JSON *Schemas* directory is never normatively bound by the spec (only the vectors JSON is). No normative tiebreaker exists for the casing contradiction. |
| P4 | §3.1 output (137–143) ↔ §2 (73–88) ↔ conformance JSON | MED | §3.1 output example shows `"protocolVersion": 0` (stale v0 artifact) while §2 declares v1 current and the conformance vectors are `protocolVersion: 1` / `specVersion: presence-protocol v1`. |
| P5 | §5.4 (470–489) ↔ §3.4 (230–247) ↔ v1 schema | MED | §5.4 PolicyResult — the canonical type-catalog entry — omits `status` and `nextPollMs` that §3.4's v1 output and `v1/tools/hestia_query_policy.schema.json` both carry; §5.4 prose also never documents `enforced`. The type catalog lags the tool surface it defines. |
| P6 | §4.1 (411–414) ↔ §5 (429–431) ↔ §8 (631) | MED | §4.1's `hestia://society/state` field list is entirely snake_case (`sovereign_lct`, `chain_length`, `session_count`, `vault_entries`, `known_plugins`), contradicting §5's "all wire shapes camelCase" mandate. §8's drift table flags only a *different* field (`trust_states_known`) that §4.1 doesn't list, reconciling none of the five. |
| P7 | §2 (87) | LOW | Link text **"tool/connect"** and anchor `#31-tool-connect` for the connect tool, whose actual name is `hestia_connect` (§3.1) — wrong tool name + non-resolving in-doc anchor. |
| P8 | §2 (73–84) ↔ §3.1 `synthetic` ↔ §2 bump rule (83–84) | LOW | §2's v0/v1 version narrative never mentions `synthetic`; §2's bump rule ("any change to the wire shape of a tool's input … requires a version bump") gives no exception for optional additive input fields, yet `synthetic` (and `status`/`nextPollMs`) were added without a bump. The additive-field exception is applied but unstated. |
| P9 | §3.1 Errors (146–148) ↔ §6.1 (573–587) | LOW | §3.1 lists `hestia.invalid_role` as a plain error; §6.1 marks it `(v1+)` "reserved … v0 daemons MAY emit `hestia.internal_error` instead". The per-tool error list omits the reservation caveat the registry attaches. |
| P10 | §9 (635–648) ↔ CHANGELOG v1 (36–72) | MED | §9 "Open work" lists policy engine + vault v2 as pending; CHANGELOG documents both as shipped in v1. Two of three §9 items are stale. |
| P11 | §8 drift row 3 (629) ↔ CHANGELOG v1 | MED | Drift table says error codes `policy_denied`/`vault_denied`/`invalid_role` will be emitted "when the policy engine lands in v1" — v1 has landed; drift status is indeterminate (resolved or stale). |
| P12 | P1-003 vector name ↔ vector content | LOW | Vector claims to test "v1 protocolVersion bumped on connect" but only reads `hestia://society/state` resource; does not verify `protocolVersion: 1` in a connect response. |
| P13 | §3.4.1 (257–278) ↔ conformance vectors | LOW | `status`/`nextPollMs` fields (wait protocol) have no conformance test coverage. Spec mandates orchestrators MUST support both branches "today." |

**2 HIGH · 6 MEDIUM · 5 LOW.**

---

## Detailed Findings

### P1 — Normative input-casing rule contradicts every input example and every input schema (HIGH)

- **§3, lines 101–103**: "The wire format for tool input arguments is
  **camelCase** JSON; tool output is also camelCase."
- **Every §3 input example** uses snake_case: `plugin_id`, `host_agent`,
  `requested_role`, `protocol_version`, `synthetic` (§3.1); `tool_name`,
  `atp_stake`, `session_id` (§3.2); `action_id`, `success` (§3.3);
  `event_type`, `event_data` (§3.8); `target_pattern` (§3.7); etc.
- **Every input JSON Schema** confirms snake_case is the *contract*, not a
  typo: `v0/tools/hestia_connect.schema.json` `$defs.input.required` =
  `["plugin_id", "host_agent"]`; `v1/tools/hestia_query_policy.schema.json`
  `$defs.input.required` = `["action_id"]`.
- **Outputs *are* camelCase** (verified): `sessionId`, `softLct`,
  `assignedRole`, `protocolVersion`, `actionId`, `chainPosition`,
  `witnessEntryHash`. The output half of the §3 sentence is correct.
- **§5, lines 429–431** compounds it: "All wire shapes use **camelCase keys**
  regardless of the source language's native convention." Tool inputs are
  wire shapes; this is overbroad — true for outputs and the §5 type catalog,
  false for tool inputs.

**Why internal**: This is not an omission. The spec makes a normative claim
about input casing and then contradicts it in 8 of 8 tool examples *and* in
the conformance schemas §7 obliges implementations to honor. An implementer
who believes the prose ships camelCase inputs; one who copies the examples
ships snake_case. They cannot interoperate, and the prose-follower fails the
schemas.

**Recommended resolution**: Rewrite §3 lines 101–103 to state the actual
split — **tool input arguments are snake_case; tool output and all §5 type
shapes are camelCase** — and narrow §5's "all wire shapes" to "all output and
type-catalog shapes." (Resolution only; out of scope here.)

---

### P2 — `synthetic` violates the spec's own completion-discipline rule (HIGH)

- **§3.1, line 121** input example includes `"synthetic": false`; **lines
  126–134** give it normative SHOULD/MAY semantics (witness yes, exclude from
  operator aggregations, self-declared, sticky per `plugin_id`). Added by
  commit `66d7c3b5` ("presence-protocol §3.1: add optional `synthetic` flag").
- **CHANGELOG discipline rule** (top of `presence-protocol-CHANGELOG.md`):
  "a protocol change is not complete until this file is updated, all
  conforming SDKs are updated, and the conformance test vectors reflect the
  new shape." The CHANGELOG `Process` section repeats it as 8 mandatory PR
  steps (update CHANGELOG, schemas, conformance vectors, …).
- **Verified**: `grep -rl synthetic` across `schemas/presence-protocol/`,
  `presence-protocol-conformance.json`, and `presence-protocol-CHANGELOG.md`
  returns **nothing** (exit 1). `synthetic` exists only in the spec body.
- **Structural gap (stronger than "one missing file")**: the *only*
  `hestia_connect` schema is `v0/tools/hestia_connect.schema.json`; the v1
  schema directory contains a single file (`hestia_query_policy.schema.json`)
  — there is **no v1 `hestia_connect` schema at all**, so a v1-era input
  field addition has no schema home even in principle. The v0 connect schema
  predates `synthetic` and admits it only via `additionalProperties: true`
  (i.e. unmodeled).
- **Asymmetry**: the sibling back-compat additive change
  (`status`/`nextPollMs`, commit `05338b0c`) followed the discipline fully —
  it has a CHANGELOG sub-entry ("2026-05-16 (later) — back-compat addition to
  v1"), is in `v1/tools/hestia_query_policy.schema.json`, and is reflected in
  the v1 conformance scenarios. `synthetic` received none of these.

**Why internal**: The spec's stated thesis (§8, §7, the CHANGELOG rule) is
that the discipline is enforced. Its most recent change demonstrably did not
follow the spec's own rule. This is the document contradicting its own
governing process, not an external implementation gap.

**Recommended resolution**: Either (a) complete the discipline for
`synthetic` — add a CHANGELOG sub-entry, a v1 `hestia_connect` schema (or
extend the bound schema), and a conformance scenario — or (b) if `synthetic`
is intentionally provisional, mark it explicitly in §3.1 as not-yet-conformed
and add it to §8's honest drift table. Silent partial landing is the one
outcome the spec's own rule forbids.

---

### P3 — No normative tiebreaker for the P1 casing contradiction (MEDIUM)

- **§7, lines 591–617**: "Conformance" is a flat MUST-list with **no
  subsections**. Item 1: "Implement all 8 tools in §3 with the documented
  input and output shapes." Item 5: "Pass the conformance test vectors at
  `…/presence-protocol-conformance.json`."
- §7 points conformance back at §3's "documented shapes" — which are
  self-contradictory per P1 — and binds only the conformance **vectors**
  JSON. The JSON **Schemas** directory
  (`web4-standard/schemas/presence-protocol/`) is referenced nowhere in the
  normative spec; the only statement that the harness "verifies shapes
  against the JSON Schemas" lives in the conformance JSON's own
  `description` field, not in the spec.

**Why internal**: When prose (camelCase input) and examples/schemas
(snake_case input) disagree, the spec offers no rule for which is normative.
The artifact that would settle it (the schemas) is never given normative
status by the spec itself. Two good-faith implementers resolve P1 in opposite
directions with equal textual justification.

**Recommended resolution**: Add one sentence to §7 establishing precedence —
e.g. "Where this document's prose and the JSON Schemas at
`web4-standard/schemas/presence-protocol/` disagree, the Schemas are
normative." That simultaneously fixes P1's ambiguity and binds the schema
directory the conformance JSON already depends on.

---

### P4 — §3.1 output example pinned to stale `protocolVersion: 0` (MEDIUM)

- **§3.1 output, lines 137–143**: `"protocolVersion": 0`.
- **§2, lines 73–88**: v1 is the current protocol; the daemon "advertises its
  `protocolVersion` in the `tool/connect` response."
- **Conformance JSON**: `"protocolVersion": 1`, `"specVersion":
  "presence-protocol v1"`, `"lastUpdated": "2026-05-16"`.

**Why internal**: The example contradicts the spec's own version declaration
and the conformance vectors the same spec binds. A reader copying the §3.1
output as a fixture asserts the wrong version.

**Recommended resolution**: Update the §3.1 output example to
`"protocolVersion": 1`, or annotate it as "value is the daemon's actual
version; shown as 0 only for the v0 baseline" if a version-agnostic example
is intended.

---

### P5 — §5.4 type catalog lags the §3.4 tool surface it defines (MEDIUM)

- **§3.4 v1 output, lines 230–247**, and `v1/tools/hestia_query_policy
  .schema.json` output both carry `status` (`"decided"|"evaluating"`) and
  `nextPollMs`.
- **§5.4 PolicyResult/PolicyDecision, lines 470–489** — the canonical "Type
  catalog" entry — shows only `decision, reason, ruleId, ruleName, policyId,
  enforced, constraints`. No `status`, no `nextPollMs`. The §5.4 prose
  (487–489) documents `decision`/`ruleId`/`ruleName`/`policyId` but never
  `enforced`.

**Why internal**: §5 is the spec's single source of truth for wire types
("Type catalog"). It is two fields behind the tool that emits the type and
behind the v1 schema. A consumer who builds a deserializer from §5.4 (the
designated canonical place) silently drops the wait-protocol fields.

**Recommended resolution**: Add `status` and `nextPollMs` to the §5.4
example and prose; add a one-line gloss for `enforced`. Cross-reference
§3.4.1 for the wait-protocol semantics.

---

### P6 — §4.1 resource fields are snake_case against §5's camelCase mandate; §8 reconciles a different field (MEDIUM)

- **§5, lines 429–431**: "All wire shapes use **camelCase keys**."
- **§4.1, line 412**: `hestia://society/state` returns `sovereign_lct`,
  `chain_length`, `session_count`, `vault_entries`, `known_plugins` — all
  snake_case. Resource bodies are JSON wire shapes (§4.1 line 423: "All
  resource bodies are JSON").
- **§8, line 631**: drift table flags only `trust_states_known` →
  `trustStatesKnown` — a field **not in §4.1's list at all** — and leaves the
  five fields §4.1 *does* list unreconciled.

**Why internal**: Three sections describe the same resource with mutually
inconsistent casing rules and even disjoint field sets (§4.1 lists
`known_plugins`; §8 names `trust_states_known`; neither lists the other).
§5's universal camelCase rule and §4.1's enumeration cannot both be right.

**Recommended resolution**: Decide the casing for resource bodies (either
exempt resource payloads from §5's camelCase rule, or camelCase them all),
then make §4.1, §5, and §8 agree on one field set and one casing.

---

### P7 — §2 connect link uses wrong tool name and a non-resolving anchor (LOW)

- **§2, line 87**: "advertises its `protocolVersion` in the
  [`tool/connect`](#31-tool-connect) response."
- The tool is `hestia_connect` (§3.1 heading). Link text "tool/connect" is
  not a name used anywhere else in the spec; the anchor `#31-tool-connect`
  will not resolve against a heading rendered as "3.1 `hestia_connect`".

**Recommended resolution**: Change link text to `hestia_connect` and the
anchor to the actual rendered slug of the §3.1 heading.

---

### P8 — §2 version narrative omits `synthetic`; the additive-field bump exception is applied but unstated (LOW)

- **§2, lines 73–84** enumerate exactly what v0 and v1 are; `synthetic` is
  absent from the narrative.
- **§2, lines 83–84** bump rule: "any change to the wire shape of a tool's
  input or output … requires a version bump." `synthetic` (input field) and
  `status`/`nextPollMs` (output fields) were all added with **no** bump. The
  CHANGELOG justifies the latter as a "forward-compatible addition," but §2's
  normative bump rule states no exception for optional additive fields.

**Why internal**: §2 is the normative versioning section. It states an
absolute bump rule, then the project (correctly) applies an unwritten
back-compat exception three times. The rule as written would have mandated
v2; the practice is v1-with-additions. The exception should be in §2, not
inferred from CHANGELOG prose.

**Recommended resolution**: Add to §2 an explicit clause: optional additive
fields that v0/older readers can ignore are back-compat and do **not** bump;
only removals, renames, type changes, or required-field additions bump. Then
list `synthetic` alongside `status`/`nextPollMs` as v1 back-compat additions.

---

### P9 — §3.1 error list omits the §6.1 reservation caveat (LOW)

- **§3.1, lines 146–148** lists `hestia.invalid_role` and
  `hestia.internal_error` as the tool's errors, unqualified.
- **§6.1, lines 573–587**: `invalid_role` is tagged `(v1+)` and the note
  (586–587) says reserved codes' "v0 daemons MAY emit `hestia.internal_error`
  instead until v1 lands."

**Why internal**: The per-tool error list presents a reserved/conditional
code as unconditional, contradicting the registry's own reservation status
for the same code.

**Recommended resolution**: Annotate `hestia.invalid_role` in §3.1 as
"(v1+; v0 daemons may emit `hestia.internal_error`)" to match §6.1, or add a
blanket note that §3 per-tool error lists are subject to §6.1 reservation
tags.

---

### P10 — §9 lists completed work as pending (MEDIUM)

- **§9, line 637**: "**Policy engine** — port from `claude-code/plugins/web4-governance/`
  into Hestia core; replaces the default-allow stub. Bumps protocol to v1."
- **§9, lines 640–642**: "**Policy state in vault** — vault schema v1 → v2
  … Same v1 protocol bump."
- **CHANGELOG v1** (lines 36–72): documents both as shipped — policy engine
  ported, vault schema v2 with `active_preset`/`overrides`/`custom_rules`,
  protocol bumped to v1, all SDKs updated, Hestia daemon 0.0.2→0.0.3.

Two of three §9 items are completed. A reader encountering §9 would believe the
policy engine hasn't been ported yet, contradicting the spec's own v1 status
and the CHANGELOG.

**Recommended resolution**: Move the two completed items into a "Completed"
subsection of §9 or remove them entirely (the CHANGELOG captures the history).
Retain the Hardbound parity and outward-MCP cross-reference items as genuinely
pending.

---

### P11 — §8 drift table stale after v1 landing (MEDIUM)

- **§8, row 3** (line 629): "Error codes `policy_denied`, `vault_denied`,
  `invalid_role` referenced by SDKs but never emitted by daemon" → Resolution:
  "Emit them when the policy engine lands in v1."
- **CHANGELOG v1**: v1 has landed. The policy engine is live. `hestia_query_policy`
  can now return `deny` with `enforced: true`.

The drift entry's resolution references a future event that has occurred. Either
(a) the error codes are now emitted by the v1 daemon (drift resolved — row
should be removed or marked done), or (b) the v1 daemon still doesn't emit
them (the resolution is stale and the drift persists with a different
remediation path). The entry as written is indeterminate.

**Recommended resolution**: Verify whether the v1 daemon now emits
`policy_denied` (expected, since the policy engine can deny). Update or remove
the row accordingly.

---

### P12 — P1-003 conformance vector doesn't test what it claims (LOW)

- **P1-003 name**: "v1 protocolVersion bumped on connect."
- **P1-003 actual test**: reads `hestia://society/state` and checks
  `sovereign_lct` starts with `lct:`. Does not call `hestia_connect` with
  `protocol_version: 1` and does not check `protocolVersion` in the response.

The vector passes trivially (it's a subset of P0-009) and does not verify the
claim in its name. A daemon returning `protocolVersion: 0` from `hestia_connect`
would still pass P1-003.

**Recommended resolution**: Either (a) add a `hestia_connect` step with
`protocol_version: 1` and a `fieldChecks` for `protocolVersion: 1`, or
(b) rename the vector to reflect what it actually tests.

---

### P13 — Wait protocol has no conformance test coverage (LOW)

- **§3.4.1** (lines 257–278): describes the "wait" protocol with `status`
  and `nextPollMs`. Mandates that "orchestrator implementations MUST support
  both branches today."
- **Conformance vectors**: P1-001 and P1-002 test `hestia_query_policy` but
  neither checks `status` or `nextPollMs`. The fields exist in the v1 schema
  but have zero vector coverage.

Since current v1 daemons always return `status: "decided"` and
`nextPollMs: null`, the absence is understandable. But the spec says
orchestrators MUST support both branches "today" — meaning conformance
should verify at least the default values.

**Recommended resolution**: Add a conformance vector (e.g. P1-004) verifying
`status: "decided"` and `nextPollMs: null` in v1 `query_policy` responses.

---

## Cross-Cutting Observation

P1, P2, P3, P6, and P8 are one theme: **the spec asserts disciplines
(camelCase everywhere; "a protocol change is not complete until…"; absolute
version-bump rule) that the spec and its artifacts do not yet uniformly
uphold.** P10, P11, and the stale §9 are a second theme: **the spec's
self-awareness sections (§8 drift, §9 open work) haven't been updated to
reflect v1's own landing.** This is exactly the gap §8 was created to track
honestly — but §8 currently records only one casing item and zero
discipline-process items.

The single highest-leverage remediation is **not** the individual edits
above; it is (a) one §7 precedence sentence binding the schemas (fixes
P1 ambiguity + P3), and (b) one honest pass extending §8 to cover the
`synthetic` discipline gap (P2), the resource-casing gap (P6), and the
post-v1 staleness (P10, P11) so the document's self-account matches
reality. The rest are localized cleanups.

## Suggested Remediation Grouping (for a future reviewable follow-up)

| Group | Findings | Shape |
|-------|----------|-------|
| **G1 — casing authority** | P1, P3, P6 | One §7 schema-precedence clause + §3/§5 input-casing correction + §4.1/§8 resource-casing reconciliation. Single coherent edit cluster. |
| **G2 — discipline honesty** | P2, P8, P10, P11 | Complete or explicitly mark `synthetic`; add §2 additive-field exception; extend §8 drift table; update §9 to reflect v1 completion. |
| **G3 — localized staleness** | P4, P5, P7, P9 | Independent one-spot fixes; safe to land together or piecemeal. |
| **G4 — conformance vector gaps** | P12, P13 | Fix misleading P1-003; add wait-protocol default-value vector. |

G1 and G2 are the load-bearing pair (they touch the spec's central
discipline thesis). G3 and G4 are mechanical. None require SDK or daemon
changes — all are spec/artifact-internal — so all are autonomous-pickable
for a remediation session once this audit is reviewed.
