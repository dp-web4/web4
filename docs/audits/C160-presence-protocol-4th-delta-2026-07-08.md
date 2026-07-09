# C160 — presence-protocol.md Fourth Delta Re-Audit

**Date**: 2026-07-08
**Auditor**: autonomous web4 session (legion, C-series **C160**, slot 205010)
**Subject**: `web4-standard/core-spec/presence-protocol.md` (722 lines, 9 sections), v1 Draft
**Baseline**: `docs/audits/C127-presence-protocol-3rd-delta-2026-07-02.md` (3rd delta). C127's sole net-new finding (C127-1, README schema-less-note incompleteness) was remediated in **#439** (`cf0d6cc5`, 2026-07-02) = **C128** (autonomous facet only; the cross-track schema-authoring facet was routed, not applied).
**Lineage**: C5 (`presence-protocol-internal-consistency-2026-05-17.md`, 13 findings) → C38 (#284/#285) → C88 (#379) → C89 (#380) → C127 (#—, audit) → **C128** (#439, remediation) → **C160** (this).
**Companion artifacts cross-checked**: `presence-protocol-CHANGELOG.md`; all **12** JSON Schemas under `web4-standard/schemas/presence-protocol/{v0/common,v0/tools,v1/tools}` + the schema-dir `README.md`; `web4-standard/testing/conformance/presence-protocol-conformance.json` (14 vectors, P0-001..P0-010 + P1-001..P1-004); filesystem ground-truth.
**Scope**: Internal-consistency 4th-delta re-audit. The spec is **byte-frozen** since C89; the only artifact that moved since C127 is the schema `README.md` (C128's remediation). So the primary new surface is **C128's own new prose** — verify the extended "known-gap ledger" is complete and every factual claim in it is true ([[feedback_remediation_introduced_regression]]). **§A** — regression-check C128 token-by-token, re-verify C89's 4 (C88) findings across 6 mirrors, 13/13 C5 + 5/5 C38, C88-5 INFO, and that C127-1's cross-track facet remains a standing carry. **§B** — fresh internal-consistency (spec ↔ 12 schemas ↔ README ↔ 14 vectors ↔ CHANGELOG), refute-by-default, primitive-clustered, 2-finder adversarial workflow + independent mechanical checks in lead context. Does NOT compare to SDK/daemon source (other repos). **Does NOT patch anything** — remediation is the next alternation turn (C161).
**Instrument**: 2 parallel refute-by-default finders (A = cross-artifact contradiction sweep across 6 lenses; B = ledger-completeness re-derivation + C89 six-mirror regression) + lead-context mechanical verification (jsonschema parse, `$ref` resolution, connect/vault_get/record_outcome/query_history output-shape extraction, vector-id sweep, schema-count at live HEAD). Per [[feedback_audit_workflow_adversarial_verify]] + [[feedback_auditor_blindspot_pattern]].

---

## Frozen-state ground truth

`git diff 0beb1b93 HEAD` over the presence artifact set is **empty except for `schemas/presence-protocol/README.md`** — the single file C128 touched (`+22 −5`). The spec, CHANGELOG, all 12 schema files, and the 14 conformance vectors are byte-stable ~15 days since C89. Inbound-carry surface is **CLEAN**: the only core-spec siblings that churned since C128 (`cf0d6cc5`) are reputation (C157 `5195465c`) and atp-adp (C151 `256ab51d`); neither mentions "presence" in its diff hunks, and no sibling routed a carry back here. As predicted by the rotation note, **no acp-born item (C158/C159) routes into presence.** This is the FROZEN-target-with-one-remediation-delta case: §A = verification of that delta + the standing findings; §B yield is the internal-blindspot / completeness surface.

---

## Headline

**C128 is a CLEAN remediation — the second consecutive clean presence remediation (after C89), and this time the property under test was completeness, not consistency.** C127-1 flagged that the schema-README's schema-less "exception Note" was an *incomplete* catalog (named only 2 of its schema-less artifacts). C128 rewrote it into a four-item "known-gap ledger" adding Session (§5.1) and VaultEntry (§5.7). The risk this delta was designed to catch: that the *new* ledger, claiming to be complete, is itself still incomplete — the exact defect-class C127-1 named, reintroduced by its own fix. **It is not.** An independent re-derivation of the complete schema-less set from ground truth — mapping every one of the 7 §5 structs *and* all 6 §4 resource bodies to its schema binding — yields exactly `{Session, R6Action, VaultEntry, society/state}`, identical to the README's four. The two traps are both handled correctly: **§5.3 Outcome is genuinely bound** (by `record_outcome` **input** `$defs`), and **§5.4 PolicyResult is genuinely bound** (by the v1 `query_policy` **output** schema), so their omission from the gap ledger is accurate, not a miss. Every other claim in the new prose is verified true against `$ref`s: `witness/recent`→WitnessEntry rides `query_history` output (`entries[].$ref` → `witness_entry.schema.json`); `society/trust`→TrustState rides `record_outcome` output (`updatedTrustState.$ref` → `trust_state.schema.json`); the connect reply is a distinct 4-field shape `{sessionId, softLct, assignedRole, protocolVersion}` (not a subset of the 8-field Session); `vault_get` returns `{value, approvalToken}`, not a VaultEntry.

**§B is the fourth consecutive near-clean presence delta by the contradiction lens.** Two refute-by-default finders across six cross-artifact lenses returned **zero surviving mutual-exclusivity findings** (~17 candidates raised and refuted, including the strongest — `enforced=true` on the default-allow path P1-002 vs §5.4's "default pass-through" gloss — demoted as under-specification, not mutual exclusion). **Zero net-new findings this delta.**

**§A: C128 ledger COMPLETE + all 6 factual claims TRUE (no regression — C128 is CLEAN) · C89 4/4 HELD across 6/6 mirrors (`vault_denied` uniformly v2+, no v1 leak) · 13/13 C5 + 5/5 C38 HELD · C88-5 R6Action still INFO · C127-1 cross-track facet STANDS as a routed carry.**
**§B: 2 finders, ~17 candidates → 0 confirmed contradictions, 0 net-new findings.**
**Documentation-hygiene note (not an artifact defect): schema count at live HEAD is 12, not the "13" stated in the C127 doc; C128's commit message already uses the correct 12.**

---

## §A — Delta Verification

### A.1 — C128 remediation regression check (the primary new surface)

C128 (`cf0d6cc5`) replaced the two-item schema-less Note with a four-item "known-gap ledger" (`schemas/presence-protocol/README.md` L43-64). Per [[feedback_remediation_introduced_regression]], every factual claim in the new prose was re-derived from ground truth, not inspected:

| C128 claim (README L43-64) | Ground-truth check | Verdict |
|---|---|---|
| "**four** spec-referenced artifacts have no JSON Schema … a known-gap ledger" | Independent re-derivation over 7 §5 structs + 6 §4 resource bodies (table A.1.1) = exactly `{society/state, R6Action, Session, VaultEntry}` | **COMPLETE — no C127-1 repeat** |
| `society/state` "ad-hoc stats object bound directly by conformance vector P0-009, not a §5 struct" | vector P0-009 present (`conformance.json`); `snake_case` per §4.1 L446 + §8 L694 | **TRUE** |
| §5.2 `R6Action` "documentary type catalog with no wire carrier (§8)" | `begin_action` output binds `{actionId, startedAt, chainPosition}` — omits `toolName`; no schema names R6Action | **TRUE** (C88-5 INFO) |
| `Session` (§5.1) schema-less; `hestia_connect` binds only the 4-field reply `{sessionId, softLct, assignedRole, protocolVersion}`, "not the full eight-field Session" | connect output `$defs.output` = exactly those 4, `additionalProperties:false`; §5.1 Session = 8 fields; `protocolVersion` is not even a Session field | **TRUE** |
| `VaultEntry` (§5.7) schema-less; `hestia_vault_get` returns `{value, approvalToken}`, "not a `VaultEntry`" | vault_get output `$defs.output` = `{value(req), approvalToken}`, `additionalProperties:false` | **TRUE** |
| Session + VaultEntry are "the only camelCase §5-typed resource bodies reached *solely* through `resources/read` — unlike `witness/recent`→`WitnessEntry` and `society/trust`→`TrustState`, which ride the `query_history`/`record_outcome` tool-output schemas" | `query_history` output `entries.items.$ref` → `witness_entry.schema.json` ✓; `record_outcome` output `updatedTrustState.$ref` → `trust_state.schema.json` ✓; `society/state`=snake_case (not §5-typed), `context/shared`=opaque | **TRUE** |

**A.1.1 — the ledger-completeness re-derivation** (the lens C127-1 introduced, re-run against C128's own list):

| §5 struct / §4 body | Bound? | By what |
|---|---|---|
| 5.1 Session (8 fields) | **NO** | connect output binds a distinct 4-field reply, not Session |
| 5.2 R6Action | **NO** | documentary; begin_action output omits `toolName` |
| 5.3 Outcome | **YES** | `record_outcome` **input** `$defs` constrains `{success, magnitude, error, result}` (+ `action_id`, `session_id`) |
| 5.4 PolicyResult (9 fields) | **YES** | v1 `query_policy` output schema binds all 9 |
| 5.5 TrustState | **YES** | `trust_state.schema.json` (+ record_outcome output `$ref`) |
| 5.6 WitnessEntry | **YES** | `witness_entry.schema.json` (+ query_history output `$ref`) |
| 5.7 VaultEntry | **NO** | vault_get → `{value, approvalToken}`; vault_set → `{stored, entryId}` |
| §4 context/shared | n/a | spec declares it opaque (no shape to author) — defensibly excluded |
| §4 society/state | schema NO / vector YES | P0-009; not a §5 struct |
| §4 witness/recent | YES | = WitnessEntry |
| §4 session/own | NO | = Session |
| §4 society/trust/{id} | YES | = TrustState |
| §4 vault/{name} | NO | = VaultEntry |

Derived schema-less-full-shape set `{Session, R6Action, VaultEntry, society/state}` = the README's four **exactly**. `grep` confirms no schema file anywhere contains `connectedAt`, `allowedConsumers`, or `R6Action` — those shapes live only in spec prose. **The remediation's own new enumeration is complete and every claim in it is true. C128 introduced no regression** — contrast C121 (C83 F2 reword) and C123 (C85 §4 fail-closed) where a frozen file's non-cleanness was entirely the prior remediation's over-reach. This is the second clean presence remediation (with C89).

### A.2 — C89 four findings (C88) + six-mirror `vault_denied`

File byte-identical to its C89 state; all four C89-remediated C88 findings HELD. The G1 six-mirror sweep re-verified (Finder B): `vault_denied` / interactive-approval is uniformly "reserved for v2+" — **no site regressed to v1-available** — at §3.5 approvalToken note (L337-339), §3.5 vault_denied error (L344-345), §3.6 (L351-352), §6.1 registry row (L626 `daemon (v2+)`), §6.1 footer (L634-642), §8 row (L692). The §6.1 footer's `(v1+)` enumeration names **exactly** `policy_denied` + `invalid_role` (the only two `(v1+)` registry rows). G3's v1-supersede property (v0 reply validates against v1 `query_policy` schema; v1 reply rejected by strict v0 schema) re-confirmed by validation. G2/G4 HELD.

### A.3 — C5 / C38 / C88-5

File byte-identical to its C89 state; no edit site regresses a C5 or C38 finding. **13/13 C5 + 5/5 C38 HELD.** The C88-5 R6Action §5.2 INFO (documentary struct; `toolName` absent from §3.2 begin output, no wire-carrier claim) is **unchanged, still INFO** — and now additionally covered by C128's ledger (R6Action explicitly named as "no wire carrier").

### A.4 — C127-1 cross-track facet (standing carry, re-confirmed)

C128 applied only C127-1's **autonomous** facet (the README ledger). Its **cross-track** facet — *author `Session`/`VaultEntry` JSON Schemas under `v0/common/` + 2 `resources/read` conformance vectors for `session/own` and `vault/{name}`* — was correctly routed, not self-applied (same class as C88-2's `validate-presence.py`). It **STANDS** as an open cross-track carry: a judgment call on whether wire-authority coverage for those two resource bodies is wanted at all, not an autonomous prose fix. Do NOT self-apply.

---

## §B — Fresh Findings

**None.** Two refute-by-default finders (A: cross-artifact contradiction across error-codes / field-shapes / enums / versioning / counts+cross-refs / vectors; B: ledger completeness + C89 six-mirror) raised ~17 candidates and refuted all. Selected refutations:

| Candidate | Why refuted |
|-----------|-------------|
| `enforced=true` on default-allow path (P1-002) vs §5.4 L535 "default pass-through" (implies `enforced=false`) | [strongest] Contradiction holds only if "default-allow under the v1 safety preset" = "default pass-through". Spec never equates them; "pass-through" most naturally = the v0 no-engine stub, while the v1 preset actively evaluates. Under-specification of when `enforced=false`, not mutual exclusion. |
| `constraints` `minItems` unenforced by v1 schema vs §3.4/P1-001/002 "≥3" | Schema is permissive (doesn't forbid <3); no shape simultaneously required-and-forbidden. Under-enforcement, not contradiction. |
| `synthetic` tagged v1 (§2 L90) but only a v0 connect schema exists (§8 L695) | connect input `additionalProperties:true` accepts it; §8 tracks it as an acknowledged discipline gap. |
| `record_outcome` "error MUST on failure" (§3.3 L228) vs schema `error:["string","null"]` non-required | Permissive superset; conditional MUST adds constraint without forbidding what the schema allows. |
| `query_history` `outcome` enum: §3.7 3 values vs schema `[...,null]` | `null` = additive no-filter sentinel for an optional field, not a 4th semantic value. |
| Registry-only codes (`not_connected`, `session_expired`, `unknown_tool`) absent from per-tool §3.x lists | Origin column marks them SDK/dispatch-level; registry is a documented superset. All 10 codes identical spelling across spec + CHANGELOG (grep-verified). |
| R6Action `toolName` vs `begin_action` output omitting it | README L50 declares §5.2 documentary with no wire carrier; nothing claims begin_action returns an R6Action. |
| P0-007 (v0 scenario) validates against v1 `query_policy` schema | Intentional + self-documented; validation confirms v0 reply passes v1 schema and v1 reply is rejected by strict v0 schema. |
| `vault_get.approvalToken` "always null" but not `required` | Permissive schema; always-present-but-optional ≠ conflict. |

Version tags (`policy_denied`/`invalid_role`=v1+, `vault_denied`=v2+), enums (`decision`, `TrustLevel`, `eventType`, `outcome`), counts (8 tools / 6 resources / 10 error codes), and all 14 vector `shapeMatchesSchema` `$ref`s (resolve to existing `$id`s; all 12 schemas parse) are internally consistent across every stated site.

---

## Documentation-hygiene note (not routed — no artifact defect)

The C127 audit doc states "13 JSON Schemas" (its lines 8 and 108). Live ground truth at HEAD is **12**: `v0/common/{error_envelope, trust_state, witness_entry}` (3) + `v0/tools/{begin_action, connect, query_history, query_policy, record_outcome, request_witness, vault_get, vault_set}` (8) + `v1/tools/query_policy` (1). No schema file changed between C127's audited state (`0beb1b93`) and HEAD, so this is a **C127 miscount**, not a deletion or an artifact defect — and C128's own commit message already uses the correct "12 presence schemas". Per [[feedback_prior_finding_path_provenance]], the count was re-run at live HEAD rather than carried forward. Nothing to route; recorded so the next delta (C193, presence 5th) inherits the correct baseline.

---

## Remediation Grouping (for C161)

| Cluster | Findings | Shape |
|---------|----------|-------|
| (none — autonomous) | — | **Zero net-new autonomous findings.** C161 (presence remediation turn) is a genuine **no-op** unless the operator greenlights the cross-track carry below. |
| **(cross-track, STANDING) resource-body wire coverage** | C127-1 facet | Author `Session`/`VaultEntry` schemas under `v0/common/` + 2 `resources/read` vectors for `session/own`, `vault/{name}`. Operator/cross-track judgment call — route, do NOT self-apply. |

No operator DESIGN-Q surfaced this delta.

---

## Cross-Cutting Observation

**This delta's value was proving a completeness remediation clean by re-deriving the set it claims to bound — the inverse of the trap it fixed.** C127-1's lesson was "before trusting a remediation's new enumeration as complete, re-derive the full set from ground truth." C160 applied that lesson to C127-1's *own* fix (C128): map every §5 struct and every §4 resource body to its schema binding, then test the derived schema-less set against the README's list. The two structs most likely to be mis-classified — Outcome (§5.3) and PolicyResult (§5.4) — are the ones the ledger *correctly omits*, because they are bound not by an eponymous schema but by a tool's **input** (`record_outcome`) and **output** (`query_policy`) `$defs` respectively. A shallower check that looked only for `Session.schema.json`-style files would have wrongly flagged them as gaps; the binding-not-filename distinction is what makes the ledger correct. Frozen ≠ clean in general, but here — for the second presence remediation running — frozen ≈ clean, with the completeness property verified by construction rather than assumed.

The single documentation-hygiene correction (12 not 13 schemas) is exactly the [[feedback_prior_finding_path_provenance]] discipline applied to a *count* rather than a path: re-run the enumeration at live HEAD, trust ground truth over the prior doc's carried number.
