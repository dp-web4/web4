# C127 — presence-protocol.md Third Delta Re-Audit

**Date**: 2026-07-02
**Auditor**: autonomous web4 session (legion, C-series **C127**, slot 000036)
**Subject**: `web4-standard/core-spec/presence-protocol.md` (722 lines, 9 sections), v1 Draft
**Baseline**: `docs/audits/C88-presence-protocol-2nd-delta-2026-06-23.md` (2nd delta; itself on C38 → C5). C88's 4 autonomous findings remediated in **#380** (`0beb1b93`, 2026-06-23) = **C89**.
**Lineage**: C5 (`presence-protocol-internal-consistency-2026-05-17.md`, 13 findings) → C38 (#284/#285) → C88 (#379) → **C89** (#380) → **C127** (this).
**Companion artifacts cross-checked**: `presence-protocol-CHANGELOG.md`; all 13 JSON Schemas under `web4-standard/schemas/presence-protocol/{v0,v1}/` + the schema-dir `README.md`; `web4-standard/testing/conformance/presence-protocol-conformance.json` (14 vectors); filesystem ground-truth.
**Scope**: Internal-consistency 3rd-delta re-audit of a **byte-frozen** target. **§A** — verify the 4 C89-remediated C88 findings HELD across all 6 mirror sites, re-read C89's own new prose token-by-token for remediation-introduced regression ([[feedback_remediation_introduced_regression]]), mechanically verify the G3 superset claim, re-confirm 13/13 C5 + 5/5 C38 still hold. **§B** — fresh internal-consistency findings (spec ↔ 13 schemas ↔ schema README ↔ 14 vectors ↔ CHANGELOG), refute-by-default, primitive-clustered, 3-finder workflow. Does NOT compare to SDK/daemon source (other repos). **Does NOT patch anything** — remediation is the next alternation turn (C128).
**Instrument**: 3 parallel refute-by-default §B finders (schema/vector/casing ∥ error-code/versioning/CHANGELOG ∥ cross-section structural) + adversarial synthesis + independent mechanical checks (jsonschema validation, ref-resolution, count sweep) in the lead context. Per [[feedback_audit_workflow_adversarial_verify]].

---

## Frozen-state ground truth

`git diff 0beb1b93 HEAD` is **EMPTY** for all four artifacts — spec, CHANGELOG, schema README, conformance JSON — byte-stable ~9 days since the C89 remediation. Inbound carry surface is **CLEAN**: of the 9 core-spec siblings that churned since C89 (acp, atp-adp, hub-law-schema rename, mcp, mrh, referenced-acts NEW, reputation, security, t3-v3), **none** mention "presence" in their diff hunks; presence's only cross-ref to a moved sibling is the conceptual "inward vs outward MCP" pointer to `mcp-protocol.md` (§L5/§L35), unaffected by mcp's §12-item-6 wording change (the C117 relocation). No sibling routed a carry back here. This is the FROZEN-target case: §A = verification, §B yield is on the internal-blindspot / completeness surface.

---

## Headline

**C89 is a CLEAN remediation — the first-order rarity this delta was designed to test for.** All 4 C88 findings held across every mirror site, and — unlike C121 (C83's F2 reword) and C123 (C85's §4 fail-closed over-reach), where a frozen file's non-cleanness was *entirely* the prior remediation's own new prose over-reaching — C89's new prose introduced **no regression**. The G1 `vault_denied` v1→v2+ correction, the exact failure the C38-2 remediation had itself reproduced, is now consistent across all six mirrors (§3.5 approvalToken, §3.5 error, §3.6, §6.1 row, §6.1 footer, §8 row). The G3 conformance repoint is **mechanically confirmed**: the v1 `query_policy` output schema is a verified superset that accepts both a v0 reply and a v1 reply while the v0 schema rejects the v1 reply — so "v0 scenarios pass on v1+ by design" is now true. G2 (README de-fiction) matches the filesystem byte-for-byte; G4 (synthetic framing) qualified.

**§B is the third consecutive near-clean presence delta by the contradiction lens**: 3 refute-by-default finders across schema/vector/casing, error-code/versioning/CHANGELOG, and cross-section structure returned **zero surviving mutual-exclusivity findings** (≈17 candidates raised and refuted). The one net-new item is a **completeness residual in C89's own README note**, surfaced by exhaustively mapping every §5 struct to its schema/vector coverage — a lens no prior presence audit had run: **the C89-added "schema-less artifacts" note enumerates only `society/state` + R6Action, but Session (§5.1) and VaultEntry (§5.7) — the two §5 structs surfaced *only* through resource reads (`session/own`, `vault/{name}`) — also have neither a JSON Schema nor a conformance vector.** LOW; documentary completeness + a 2-of-6-resource coverage gap, not a wire contradiction.

**§A: C89 4/4 HELD across 6/6 mirrors · G3 mechanically verified · NO C89-introduced regression (C89 is CLEAN — contrast C121/C123) · 13/13 C5 + 5/5 C38 HELD · C88-5 R6Action still INFO.**
**§B: 3 finders, ~17 candidates → 0 confirmed contradictions + 1 net-new LOW completeness residual (C127-1) routed to C128.**

---

## §A — Delta Verification of the 4 C89-Remediated C88 Findings

Each re-checked against the live spec/README/vectors token-by-token (C56/C64 method — verify the remediation's *claims*, not just "is an edit present").

| C88 # | C89 cluster | Sev | One-line | Status | Evidence (live) |
|-------|-------------|-----|----------|--------|-----------------|
| **C88-1** | G1 | MED | `vault_denied` documented v1-available (the C38-2-introduced regression) | **HELD — all 6 mirrors v2+** | §3.5 approvalToken L337-339 ("reserved for v2+ … in v0 and v1 always null") · §3.5 vault_denied error L344-346 ("reserved for v2+ … v0 and v1 daemons MAY emit `internal_error`") · §3.6 L351-353 ("v2+ MAY add … deferred, same as vault_get") · §6.1 registry row L626 (`daemon (v2+)`) · §6.1 footer L634-642 (split: `policy_denied`/`invalid_role` **live at v1**; `vault_denied` **reserved v2+**) · §8 row L692 ("Reserved in §6.1 as `(v2+)`"). No site left at v1+. The §8↔§6.1 seam is fully closed. |
| **C88-2** | G2 | MED | schema README fictional (nonexistent tree/validator, stale tense) | **HELD** | README Layout L22-42 matches filesystem `find` exactly (combined `hestia_*.schema.json` under `v0/tools/`, structs under `v0/common/`, `v1/tools/hestia_query_policy.schema.json`); `validate-presence.py` softened to "planned but not yet present" L55-57; present-tense "v1 has landed (2026-05-16)" L11; schema-less note added L44-48. |
| **C88-3** | G3 | MED→HIGH-lean | P0-007 bound strict v0 schema a v1 daemon can't satisfy | **HELD + MECHANICALLY CONFIRMED** | P0-007 `shapeMatchesSchema` L197 → **v1** query_policy output schema; description L176 carries superset rationale. See mechanical proof below. |
| **C88-4** | G4 | LOW | §2 framed `synthetic` co-equal with fully-conformed fields | **HELD** | §2 L87-90 qualifies `synthetic` as "spec-documented but not yet artifact-conformed; see §8", distinguished from the "fully conformed: schema + vector P1-004 + CHANGELOG" `status`/`nextPollMs`. |

### G3 mechanical proof (jsonschema)

The v1 `query_policy` output schema: `required = [decision, reason, enforced]`, `additionalProperties: false`, `properties = {decision, reason, ruleId, ruleName, policyId, enforced, constraints, status, nextPollMs}` (retains `policyId` → superset of v0's 4 props). The v0 output schema: same `required`, `additionalProperties: false`, `properties = {decision, reason, policyId, enforced}`.

- v0 reply `{decision, reason, policyId, enforced}` → **validates** against v1 schema ✓
- full v1 reply (all 9 fields) → **validates** against v1 schema ✓
- same v1 reply → **fails** v0 schema (`additionalProperties:false` rejects `constraints`/`nextPollMs`/…) — confirming exactly why the repoint was necessary ✓

P0-007's `fieldChecks` (`decision isIn [allow,deny,warn]`, `reason isNonEmptyString`, `enforced isBoolean`) exercise only the v1 schema's required trio. "v0 scenarios (P0-*) still pass on v1+ daemons by design" is now **TRUE**.

### Remediation-introduced-regression check (C89's own new prose)

Per [[feedback_remediation_introduced_regression]] the "HELD" verification extends to every mirror the remediation's *logic* touches. C89's net-new prose re-read token-by-token:
- §6.1 footer's new enumeration "`(v1+)` (`policy_denied`, `invalid_role`)" is **complete and correct** vs the registry (the only two `(v1+)` rows; `vault_denied` correctly the sole `(v2+)`).
- The §3.5/§3.6 "in v0 and v1 always null / v0 and v1 daemons MAY emit `internal_error`" additions are consistent with §8 (v2+) and CHANGELOG L139 (v2+).
- No mirror was moved while a sibling was left stale (the C38-2 failure mode); C89 explicitly touched all 6 sites the §8 row's logic implicated. **No C89-introduced regression.** This is the first frozen-target presence delta whose non-perfection is NOT the prior remediation's over-reach — contrast C121 (C83 F2 reword) and C123 (C85 §4 fail-closed) which were.

### C5 / C38 findings

File is byte-identical to its C89 state; no edit site regresses a C5 or C38 finding. **13/13 C5 + 5/5 C38 HELD.** The C88-5 R6Action §5.2 INFO (documentary struct, `toolName` absent from §3.2 begin output — no wire-carrier claim) is **unchanged, still INFO** (re-raised and re-refuted by Finder 3 as pre-adjudicated benign).

---

## §B — Fresh Findings

### C127-1 — The C89-added schema-less note is incomplete: Session (§5.1) and VaultEntry (§5.7), surfaced only via resource reads, also lack a schema AND a conformance vector (LOW)

**Locations**: `schemas/presence-protocol/README.md` L44-48 ("Note: the `hestia://society/state` resource body and the §5.2 `R6Action` struct have no JSON Schema yet …") ↔ spec §4.1 L448 (`session/own` → "Session struct from §5"), §4.2 L455 (`vault/{name}` → "VaultEntry (§5)"), §5.1 Session (8 fields), §5.7 VaultEntry ↔ filesystem (`v0/common/` holds only `error_envelope`, `trust_state`, `witness_entry` schemas) ↔ conformance JSON (no vector references `session/own` or `vault/{name}`).

**Tension**: The README frames the schemas as "the wire-format authority" (L5-7) and its Note enumerates the exceptions with a specific reason for each (`society/state` = ad-hoc stats bound by P0-009; R6Action = documentary catalog with no wire carrier). By enumerating exceptions, the Note reads as a *complete* catalog of schema-less artifacts — a reader concludes every other §5 struct / resource body has a schema. But two §5 structs surfaced only through resource reads are **also** schema-less **and** vector-less:
- **Session (§5.1, 8 fields)** — the `hestia_connect` output schema binds only the 4-field connect reply (`sessionId, softLct, assignedRole, protocolVersion`), *not* the full 8-field Session struct that `session/own` returns. No vector reads `session/own`.
- **VaultEntry (§5.7)** — `hestia_vault_get` returns `{value, approvalToken}`, not a VaultEntry; no schema and no vector covers the `vault/{name}` metadata body.

So the "wire-format authority" is genuinely absent for 2 of the 6 resource bodies, and the README's own exception list omits both.

**Why net-new (not a missed carry)**: The Note is **new prose introduced by C89** (the C88-2 README rewrite). C88-2 fixed the *fictional* tree but the schema-less enumeration it added catalogued only the two cases C88 happened to name (`society/state` via P0-009, R6Action via §8). This is the first audit to map **every §5 struct to its schema/vector coverage** and cross-check the result against the README's own exception list — a completeness lens neither C5, C38, nor C88 ran. Mild [[feedback_remediation_introduced_regression]] flavor: the remediation's own new list is incomplete.

**Refutation acknowledged (why LOW, not MED)**: Finder 1 correctly refuted this under the *contradiction* lens — it is under-specification, not two mutually-exclusive statements; the spec never explicitly asserts these resources *have* schemas, and §7 item 5 binds only the vectors (which don't cover them). The steelman: the README says "Note", not "the complete list of exceptions." Held at **LOW** because (a) no wire shape is contradicted and nothing bound breaks, but (b) the Note's closed-conjunction grammar ("the X and the Y have no JSON Schema yet") is factually incomplete for a bound directory, and a conformance implementer would be misled into expecting `session/own`/`vault/{name}` schemas that don't exist.

**Recommended resolution for C128** — split into an autonomous prose facet and a cross-track facet, mirroring how C88-2 handled `validate-presence.py`:
- **AUTONOMOUS (prose)**: extend the README Note to also state that **Session (§5.1, via `session/own`)** and **VaultEntry (§5.7, via `vault/{name}`)** currently have no JSON Schema and no conformance vector — the two `camelCase` §5-typed resource bodies that (unlike `witness/recent`→WitnessEntry and `society/trust`→TrustState, bound indirectly via `query_history`/`record_outcome` outputs) are surfaced *only* through `resources/read` and so ride no tool-output schema. Optionally add a one-line §8 drift row or §9 pending item for symmetry.
- **CROSS-TRACK (artifact authoring, NOT a spec-prose edit)**: if wire-authority coverage is wanted, author `Session`/`VaultEntry` schemas under `v0/common/` + add 2 `resources/read` conformance vectors for `session/own` and `vault/{name}`. Route separately — same class as the C88-2 `validate-presence.py` cross-track note.

---

## §B — Refuted (checked, NOT findings)

~17 candidate tensions were raised across the 3 finders + lead and refuted at synthesis:

| Candidate | Why refuted |
|-----------|-------------|
| Error registry (10) vs per-tool §3.x lists vs CHANGELOG v0 "(10)" | Union of per-tool Errors ⊆ registry; the 3 registry-only codes (`not_connected`, `session_expired`, `unknown_tool`) are SDK/framework-origin per the Origin column. Exact match. |
| Version tags inconsistent across mirrors | `policy_denied`/`invalid_role` uniform `(v1+)`; `vault_denied` uniform `(v2+)` at §3.5/§6.1-row/§6.1-footer/§8/CHANGELOG. The C89-corrected set, still coherent. |
| §2 additive-field exception vs CHANGELOG v1 vs §8 | `status`/`nextPollMs`/`synthetic` all no-bump; matches CHANGELOG "no v1.1 split" + §8. |
| `decision` enum omits `warn` in a schema | BOTH v0 and v1 query_policy schemas have `enum:[allow,deny,warn]`; §1.2/§3.4/§5.4/§6 all agree. |
| deferred-item sets diverge (CHANGELOG Upcoming ↔ §8/§9) | CHANGELOG Upcoming ≡ v1 "Not yet implemented"; §9 is a differently-scoped "tracked elsewhere" list, not claimed to mirror. Interactive approval tracked via §8 vault_denied row. |
| `vault_set` audit provenance ("now emitted" v1 vs "present in v0 but undocumented") | Reconcilable: v1 = where it's spec'd/documented; §3.6 states it as a plain side-effect with no version claim. |
| error_envelope enum vs 10-code registry | Envelope uses open pattern `^hestia\.[a-z_]+$`, not a closed enum — cannot conflict. |
| `session/own`/`vault/{name}` have no schema/vector = a *contradiction* | Under-specification, not mutual exclusivity → demoted to the LOW completeness residual C127-1, not a contradiction finding. |
| §3.3 `error` "MUST on failure" vs schema non-required | Schema merely more permissive (no conditional encoded); `{success:false,error:"x"}` validates against both. Prose semantic constraint, not a wire contradiction. |
| §5 TrustState / WitnessEntry prose vs bound schemas | Field-by-field EXACT match (required sets, sub-object requireds, enums, `additionalProperties:false`). |
| Truncated placeholders (`"97a3-..."`, `"abc..."`) vs `format:uuid` / hash patterns | Illustrative, not conformance values; vectors interpolate real captures. |
| Counts: 8 tools / 6 resources / 4 presets / 7 capabilities / §7 items / §1.2→§3-4 map | All internally consistent across every stated site. |
| All "see §X" cross-refs (§3.4, §3.4.1, §6.1, §7, §8, §3.5/§3.6, #31-hestia_connect) | Every pointer resolves to a section that says what the pointer claims. |
| §5.4 PolicyResult field-set vs §3.4 output | Identical 9-field set incl. enums + null semantics. |
| Status/date markers (§8 "as of 2026-05-18" ⊇ policy-wired 2026-05-16; §4.1 "Read-only in v0"; §1 "Hestia 0.0.3+") | All consistent. |
| Vector `shapeMatchesSchema` dangling refs | All 7 distinct refs resolve to existing files; all 13 schemas parse. |

---

## Remediation Grouping (for C128)

| Cluster | Findings | Shape |
|---------|----------|-------|
| **G1 — README schema-less note completeness** (autonomous prose) | C127-1 (LOW) | Extend the README Note to name Session (§5.1, via `session/own`) + VaultEntry (§5.7, via `vault/{name}`) as also schema-less + vector-less; optional §8/§9 symmetry row. One coherent prose edit. |
| **(cross-track) resource-body wire coverage** | C127-1 (facet) | Author `Session`/`VaultEntry` schemas + 2 `resources/read` vectors — separate artifact task, route like C88-2's `validate-presence.py`. Do NOT self-apply. |

C127-1 is the sole net-new item and its autonomous facet is direction-fixed (extend an incomplete factual list). No operator DESIGN-Q. The cross-track facet (whether to author schemas/vectors at all) is a judgment call routed, not self-decided.

---

## Cross-Cutting Observation

**This delta's value was confirming a clean remediation and finding the residual that only exhaustive coverage-mapping surfaces.** Three of the last four presence findings-classes were remediation-introduced or documentary; C127 verified — mechanically, not by inspection — that C89 broke the streak: G3's superset claim is provable with `jsonschema`, and the G1 six-mirror sweep shows C89 avoided the exact one-mirror-left-stale trap C38-2 fell into. The [[feedback_remediation_introduced_regression]] method still earned its keep, but this time by *clearing* the remediation rather than catching it.

The single net-new finding (C127-1) came from a lens no prior presence audit had run: mapping **every** §5 struct to its schema+vector coverage and testing that map against the README's own exception list. The two structs surfaced only through `resources/read` (Session, VaultEntry) fall through every tool-output schema and every vector, and the C89 remediation's new "schema-less" note — itself a correct fix for C88-2's fiction — silently omitted them. The lesson mirrors [[feedback_snapshot_presence_guard]] inverted: before trusting a remediation's *new enumeration* as complete, re-derive the full set it claims to cover from ground truth. Frozen ≠ clean; here frozen ≈ clean, with one completeness residual in the remediation's own prose.
