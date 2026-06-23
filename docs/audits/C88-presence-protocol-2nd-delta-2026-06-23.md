# C88 — presence-protocol.md Second Delta Re-Audit

**Date**: 2026-06-23
**Auditor**: autonomous web4 session (legion, C-series **C88**)
**Subject**: `web4-standard/core-spec/presence-protocol.md` (710 lines, 9 sections), v1 Draft
**Baseline**: `docs/audits/C38-presence-protocol-audit-2026-06-08.md` (first delta; itself baselined on `presence-protocol-internal-consistency-2026-05-17.md` = "C5", 13 findings P1–P13). C5 remediated in #206/#207; C38's 5 findings remediated in **#285** (`cfdcff99`, 2026-06-08). **File byte-stable since `cfdcff99`** (~2 weeks) → the [[feedback_remediation_introduced_regression]] + C56 completeness method apply: audit the C38 remediation's own claims token-by-token, not just "did it hold."
**Companion artifacts cross-checked**: `presence-protocol-CHANGELOG.md`; all 13 JSON Schemas under `web4-standard/schemas/presence-protocol/{v0,v1}/` **+ that directory's `README.md`** (first time the schema README itself is in scope); `web4-standard/testing/conformance/presence-protocol-conformance.json` (14 vectors); filesystem ground-truth (`ls` of schema + conformance dirs).
**Scope**: Internal-consistency 2nd-delta re-audit. **§A** — verify the 5 C38 findings HELD after `cfdcff99`, re-verify the 13 C5 findings + the F-r6action-orphan INFO deflate, and check for NEW remediation-introduced defects. **§B** — fresh internal-consistency findings (spec ↔ 13 schemas ↔ schema README ↔ conformance vectors ↔ CHANGELOG), refute-by-default, primitive-clustered. Does NOT compare to SDK/daemon source (other repos). Does NOT patch anything — remediation is the next alternation turn (C89).
**Instrument**: 3 parallel refute-by-default §B finders (schema/README/vector ∥ error-code/versioning ∥ cross-section structural) + adversarial verification against full ground-truth in the lead context. §A done inline against the complete spec + CHANGELOG + schema set. Per [[feedback_audit_workflow_adversarial_verify]].

---

## Headline

The C38 remediation **held on 4 of its 5 findings and on all 13 C5 findings** — the resource-casing per-resource split (C38-1, the HIGH one) is clean, complete, and consistent with the bound vectors P0-009/P0-010 and the `witness_entry`/`trust_state` schemas. But **C38-2 was applied to only one of its two sites, and the omission introduced a fresh contradiction that did not exist before C38.** C38-2 split `vault_denied` out of §8's "resolved in v1" into a v2+ "still pending" row — but its own recommendation's *optional* sub-item ("narrow the §6.1 `until v1 lands` footer") was skipped. Before C38, §8 and the §6.1 footer **agreed** (both implied v1). After C38, §8 says **v2+** while the §6.1 footer + the `(v1+)` registry tag + the §3.5 marker still say **v1** — a new §8↔§6.1 seam the C38 §8 row even points at ("Reserved in §6.1 as `(v1+)` … but no daemon can emit it until that approval flow ships"). This is the cleanest remediation-introduced regression since C54: the fix corrected one mirror and left the other.

Two further fresh defects are unrelated to the C38 remediation and surfaced for the first time because this is the first audit to put the **schema directory's `README.md`** and the **conformance harness's forward-compat claim** under the lens: (a) the schema `README.md` is substantially fictional — its Layout tree names files that do not exist, it points to a `validate-presence.py` that does not exist, and it describes v1 as not-yet-landed; (b) conformance vector **P0-007 binds the strict `additionalProperties:false` v0 `query_policy` output schema**, which a v1 daemon's reply (carrying `ruleId`/`ruleName`/`constraints`/`status`/`nextPollMs`) cannot satisfy — directly falsifying the file's own "v0 scenarios (P0-*) still pass on v1+ daemons by design" claim and making a conformant v1 daemon unable to pass a §7-item-5 MUST.

**§A: C38 4/5 fully HELD · 1 (C38-2) incomplete → regression C88-1 · 13/13 C5 HELD · F-r6action-orphan still INFO.**
**§B: 8 raw finder findings → 4 confirmed (3 MED · 1 LOW) + 1 INFO (re-surfaced, held) + 10 refuted.**

---

## §A — Delta Verification of the 5 C38 Findings

Each C38 finding re-checked against the live spec/CHANGELOG token-by-token (C56/C64 method — verify the remediation's *claims*, not just "is an edit present").

| C38 # | Sev | One-line | Status | Evidence (live) |
|-------|-----|----------|--------|-----------------|
| **C38-1** | HIGH | Blanket "§4 bodies snake_case" over-generalized P6 | **HELD (complete)** | §3 L114–126 carries the per-resource split (`society/state` ad-hoc snake, bound by P0-009 · `context/shared` opaque · the four §5-typed bodies camel, `witness/recent`→WitnessEntry bound by P0-010). §5 L463–468 mirrors it. §8 L682 reconciles it. Consistent with `witness_entry`/`trust_state` schemas (`additionalProperties:false`, camel keys) and vectors P0-009 (snake) / P0-010 (`entries[0].chainPosition`). No new contradiction in the rewrite. |
| **C38-2** | MED | `vault_denied` swept into "resolved in v1" but trigger is v2+ | **PARTIALLY HELD → C88-1** | §8 L680 correctly split into a "Still pending / v2+" row. **But** the recommendation's optional sub-item — narrow the §6.1 footer — was skipped. §6.1 footer L629–630 still says "v0 daemons MAY emit `internal_error` … **until v1 lands**" (firm v1 go-live) and the §6.1 registry row L621 still tags `vault_denied` `daemon (v1+)`. §8 now contradicts §6.1. See **C88-1**. |
| **C38-3** | MED | CHANGELOG still forecast the `trustStatesKnown` rename §8 had killed | **HELD** | CHANGELOG L161–166 removed the rename from "Upcoming" and added the explicit "intentionally **not** listed … no casing rename is pending" note tied to P0-009 + the §3 split. |
| **C38-4** | LOW | §3.4 `policy_denied` missing the `(v1+)` reservation marker | **HELD** | §3.4 L308–310 now: "`policy_denied` (v1+; … v0 daemons MAY emit `hestia.internal_error` instead, see §6.1)". Mirrors the C5-P9 `invalid_role` fix. (The cohort sibling `vault_denied` §3.5 marker remains asymmetric — folds into **C88-1**.) |
| **C38-5** | LOW | CHANGELOG v0 "approval arrives in v1" stale | **HELD** | CHANGELOG L139–140 now: interactive approval "**did not land in v1** and is now targeted for v2+ … `vault_denied` remains reserved-but-unemittable until it ships." |

**Result: 4/5 fully HELD, C38-2 incomplete (one mirror left stale → C88-1).**

### C5 findings (P1–P13) + INFO

The file is byte-identical to its C38 remediation; `cfdcff99` touched only the §3 casing block, the §3.4 `policy_denied` errors line, the §5 casing block, two §8 drift rows, and the CHANGELOG. C38 verified all 13 C5 findings HELD; none of those five edit sites regresses a C5 finding (the casing rewrites P1/P6 are now *more* correct — per-resource rather than blanket). **13/13 C5 HELD.** The C38 **F-r6action-orphan** INFO (R6Action §5.2 has no wire carrier) is **re-surfaced** by a fresh finder and **re-confirmed as INFO**, not promoted — see C88-5.

---

## §B — Fresh Findings (confirmed)

### C88-1 — `vault_denied` is documented as v1-available in §6.1 (footer + registry tag) and §3.5, contradicting the §8/CHANGELOG v2+ deferral — a regression introduced by the C38-2 remediation (MED)

**Locations**: §6.1 footer L629–630 ("…v0 daemons MAY emit `hestia.internal_error` instead **until v1 lands**") + §6.1 registry row L621 (`hestia.vault_denied | daemon (v1+)`) + §3.5 L342 ("`hestia.vault_denied` — interactive approval refused (**reserved for v1+**)") ↔ §8 drift row L680 ("**Still pending** … deferred to **v2+** … no daemon can emit it until that approval flow ships") + CHANGELOG L139–140 / L157 (interactive approval "did not land in v1 … targeted for **v2+**").

**Tension**: The §6.1 footer promises every `(v1+)` code becomes daemon-emittable when v1 lands; v1 landed 2026-05-16, yet `vault_denied` is still unemittable (its only trigger, interactive vault approval, is v2+). §8 and CHANGELOG correctly say v2+; §6.1's footer and the `(v1+)` tag say v1. The C38-added §8 row itself names the seam: "Reserved in §6.1 as `(v1+)` … but no daemon can emit it until that approval flow ships" — §8 declares v2+ while pointing at the un-narrowed §6.1 `(v1+)` tag.

**Why internal / a regression (not pre-existing)**: `cfdcff99` did **not** touch §6.1 (verified: the only §6.1 strings in the diff are the new §3.4 cross-ref and the §8 row's own "Reserved in §6.1" phrase). Before C38, §8's row read "resolved in v1 … now emittable" — which **agreed** with the §6.1 footer's "until v1 lands." C38 changed the §8 side to v2+ and left the §6.1 side at v1, *creating* a contradiction that did not exist at C38-audit time. C38-2's recommendation explicitly anticipated this — "Optionally narrow the §6.1 L612–613 'until v1 lands' note to the two policy/role codes" — and the "optional" sub-item was the one dropped. Classic [[feedback_remediation_introduced_regression]]: the fix updated one mirror and left the other, and the "HELD" verification must extend to every mirror the remediation's *logic* touches, not just the lines in the diff hunk (the §54/C54 lesson).

**Severity adjudication**: MED. Three finder lenses (§6.1 footer, §6.1 registry tag, §3.5 marker) converged on this single root. The registry `(v1+)` tag is loosely defensible ("reserved from v1 *or later*"), so the *sharpest* defect is the footer's firm "until v1 lands" + the §3.5 marker's missing v0/v1-fallback caveat (the only one of the three reserved codes whose feature is genuinely deferred carries the *least* explicit marker). Not HIGH: nothing bound breaks (no daemon emits `vault_denied`, so no vector/SDK conflict today); it is a documentary contradiction between two authoritative forward statements about a single code's go-live version.

**Recommended resolution (AUTONOMOUS — direction already fixed by §8/CHANGELOG = v2+)**: (1) Split the §6.1 footer: `policy_denied`/`invalid_role` are live as of v1; `vault_denied` stays reserved until interactive vault approval ships (v2+, see §8). (2) Retag the §6.1 row `vault_denied` as `daemon (v2+)` or `(reserved, v2+)` to distinguish it from the v1-live pair. (3) Bring §3.5 into cohort symmetry with the v0-fallback caveat the other two carry, and correct "v1+" → "v2+" there: "(reserved for v2+; interactive approval not yet shipped — daemons emit `hestia.internal_error`, see §6.1)".

### C88-2 — The schema directory's `README.md` is substantially stale/fictional: nonexistent Layout tree, nonexistent `validate-presence.py`, "v1 not yet landed" (MED)

**Locations**: `web4-standard/schemas/presence-protocol/README.md` — Layout block L14–33; validator claim L36–39; "once v1 lands" L9–12 ↔ filesystem (`ls`) + spec `presence-protocol.md` L3–4 (Version 1) / §9 L689–696 (v1 shipped) / the existing `v1/tools/hestia_query_policy.schema.json`.

**Tension (three falsified claims, one root = README never updated since the v0 scaffold)**:
- **Layout tree is fictional** — README lists split `hestia_connect.input.schema.json` + `hestia_connect.output.schema.json`, a `v0/resources/` directory (`society_state.schema.json`, …), and `common/r6_action.schema.json`. **Actual**: tools are single combined files (`hestia_connect.schema.json` with `$defs/input` + `$defs/output`); there is **no `resources/` dir**; structs live in `v0/common/`; **no `r6_action.schema.json` and no `society_state.schema.json` exist anywhere**.
- **`validate-presence.py` does not exist** — README L36–39 "A reference validator script lives at `web4-standard/testing/conformance/validate-presence.py` (Step 1b)." The conformance dir contains no `.py` file; the string is referenced nowhere in the repo.
- **Stale tense** — README L9–12 "v1 schemas will live alongside v0 … **once v1 lands**" (future), but v1 has landed and `v1/tools/` is populated.

**Why internal / genuine**: §7 binds the schemas directory *normatively* (Precedence clause), so its self-description is part of the bound artifact set. An implementer following the README's `$ref` paths (`.input.schema.json`) hits 404; one looking for the promised `society_state`/`r6_action` schemas (the two §5 structs/resources that genuinely have *no* schema) finds the README implies they exist. This is the first audit to scope the README, so it is genuinely new, not a missed-earlier carry.

**Severity adjudication**: MED (one finder rated the first two HIGH). Downgraded from HIGH because the README is *advisory* documentation — the normative chain (spec → schema `$id` URL → actual combined file) is internally consistent and is what the conformance vectors and spec actually reference; nothing in the wire-format authority breaks. But it is a concrete, multi-claim falsehood in a bound directory.

**Recommended resolution (AUTONOMOUS for the prose)**: Rewrite the README Layout block to the real tree (combined `hestia_*.schema.json` under `v0/tools/`, structs under `v0/common/`, `v1/tools/hestia_query_policy.schema.json`); change "once v1 lands" to present tense. For the validator: the autonomous path is to **soften/remove** the `validate-presence.py` pointer (e.g. "a reference validator is planned"). *Cross-track note*: actually authoring `validate-presence.py` is a separate tooling task, not a spec edit — route it as cross-track if a validator is wanted.

### C88-3 — Conformance P0-007 binds the strict `additionalProperties:false` v0 `query_policy` output schema, which a v1 daemon cannot satisfy — falsifying the file's "v0 scenarios pass on v1+ by design" claim (MED, leaning HIGH)

**Locations**: `presence-protocol-conformance.json` top-level description L4 ("v0 scenarios (P0-*) **still pass on v1+ daemons by design**") + P0-007 `shapeMatchesSchema` L197 (→ `v0/tools/hestia_query_policy.schema.json#/$defs/output`) ↔ `v0/tools/hestia_query_policy.schema.json` output (`additionalProperties: false`, properties = {`decision`,`reason`,`policyId`,`enforced`} only) ↔ spec §3.4 v1 output L258–283 / §5.4 L507–532 (v1 reply adds `ruleId`,`ruleName`,`constraints`,`status`,`nextPollMs`).

**Tension**: A v1 daemon's `query_policy` reply carries five fields the strict v0 output schema forbids (`additionalProperties:false`). P0-007 validates the *whole* response (`shapeMatchesSchema`) against that v0 schema, so a conformant v1 daemon **fails P0-007**. §7 conformance item 5 makes passing the vectors a MUST — so a conformant v1 daemon cannot satisfy §7. This directly contradicts the file's own "P0-* pass on v1+ by design" design statement.

**Why internal / genuine**: `query_policy` is the *one* tool whose output shape grew in v1, and its v0 output schema is the *one* output schema whose `additionalProperties:false` therefore bites forward-compat. (All other v0 output schemas are also `additionalProperties:false`, but their v1 responses add no fields, so they are unaffected — verified.) The conflict is between the vectors' stated forward-compat design and the schema P0-007 actually binds. Demonstrable, narrow, single-vector.

**Severity adjudication**: MED, leaning HIGH. Leans HIGH because §7-item-5 conformance is a MUST and the contradiction is mechanically demonstrable (a conformant v1 daemon fails a bound vector). Held at MED because it bites only the conformance harness (no production wire breakage) and the file's "by design" line is a description, not a normative MUST.

**Recommended resolution (AUTONOMOUS — both options inside remediation scope, which may touch schemas/vectors)**: Preferred — repoint P0-007's `shapeMatchesSchema` to the **v1** `query_policy` output schema (the only one that tolerates the extra fields) when run against v1+, mirroring how P1-001/002/004 already bind the v1 schema. Alternative (more principled, aligns with §2 L86–90 "older readers can safely ignore new keys" forward-compat philosophy) — relax the **v0** `query_policy` output schema to `additionalProperties:true`. Recommend the repoint as the most targeted fix; flag the `additionalProperties` philosophy question for the remediation turn since it touches a normative schema.

### C88-4 — §2 frames `synthetic` as a landed v1 back-compat addition co-equal with `status`/`nextPollMs`, contradicting §3.1/§8/§9 "not yet conformed / no CHANGELOG entry" (LOW)

**Locations**: §2 L87–90 ("`status`/`nextPollMs` (output, v1 back-compat addition) **and** `synthetic` (input, v1 back-compat addition) were **both** added under this exception") ↔ §3.1 L161–162 ("**Not yet conformed** — no JSON Schema, no conformance vector, **no CHANGELOG entry**") + §8 L683 ("spec-documented but not artifact-conformed") + §9 L706–710 ("`synthetic` discipline completion" still pending) + CHANGELOG v1 (L15–87 mentions `status`/`nextPollMs` but never `synthetic`).

**Tension**: §2 presents the two as co-equal landed v1 additions when one (`status`/`nextPollMs`) is fully conformed (schema + vector P1-004 + CHANGELOG) and the other (`synthetic`) is explicitly un-conformed per three other sections + the CHANGELOG's own omission.

**Why internal (partial-refute noted)**: Both sides cited exactly; the CHANGELOG omission is verifiable and is itself the §8/§9 drift item. **Partial refutation**: §2 is stating the *versioning rule*, and `synthetic` genuinely *is* an optional additive input field that does not trigger a bump — so the versioning-treatment claim is itself correct. The defect is only the *parallel framing* with a fully-conformed field, which a reader can mistake for "synthetic is conformed." LOW.

**Recommended resolution (AUTONOMOUS)**: Qualify the §2 mention: "`synthetic` (input, v1 back-compat addition — **spec-documented but not yet artifact-conformed; see §8**)".

---

## §B — Re-surfaced & Held as INFO

| ID | Claimed | Verdict | Why |
|----|---------|---------|-----|
| **C88-5** (= C38 F-r6action-orphan) | LOW/structural | **INFO — held, not promoted** | §5.2 R6Action `{actionId,toolName,startedAt,chainPosition}` is the only §5 struct with no wire carrier — the §3.2 begin_action output `{actionId,startedAt,chainPosition}` omits `toolName`. A finder re-raised it reading §5's "all tool **output** shapes use camelCase" as implying §5 structs are wire-returned. **C38 already adjudicated this is not a contradiction** (§5 is a documentary type catalog; the spec never claims the begin output *is* an R6Action record — same benign pattern as connect output (4 fields) vs §5.1 Session (8)). Re-confirmed INFO. Optional maintainability note only: annotate §5.2 as an internal/stored record (paralleling §5.3 Outcome's "orchestrator → presence" label), or add `toolName` to §3.2 output. Safe to skip. |

---

## §B — Refuted (checked, NOT findings)

10 candidate tensions were raised across the finders and refuted at synthesis:

| Candidate | Why refuted |
|-----------|-------------|
| P1-003 binds v0 connect schema but expects `protocolVersion:1` | v0 connect schema sets `protocolVersion {integer, minimum:0}`, no `const`/enum — `1` validates. |
| v0 connect schema omits `synthetic` | Spec §3.1 itself flags it "not yet conformed"; input schemas are `additionalProperties:true` so it validates anyway. Both sides agree. |
| input/output casing mismatch | Every tool verified: inputs snake (`plugin_id`,`action_id`,`allowed_consumers`), outputs/structs camel (`sessionId`,`chainPosition`,`witnessEntryHash`). Consistent. |
| `society/state` snake vs §5 camel rule | §3 split + §8 L682 + P0-009 all carve it out as ad-hoc snake. Consistent (this is the C38-1 fix working). |
| v1 query_policy schema fields vs §3.4/§5.4 | Field-by-field identical 9-field set incl. enums. |
| P1-001/002 fieldChecks vs v1 schema required | Schema requires only decision/reason/enforced; vectors assert *values* of permitted optional fields. Consistent. |
| record_outcome `error` "MUST on failure" vs schema non-required | Prose conditional the flat schema can't express; not a two-statement wire contradiction. |
| error-code counts/names | §6.1 (10) ≡ CHANGELOG v0 "(10)" ≡ union of per-tool lists (+ the 3 legitimately registry-only SDK/dispatch codes). |
| status/nextPollMs no-bump | §2 additive-field exception + CHANGELOG account agree; the v1 bump (ruleId/ruleName/constraints) was the shape extension, additive fields rode the exception. |
| error_envelope pattern `^hestia\.[a-z_]+$` | Admits every registry code. |
| numeric counts (8 tools / 6 resources / 4+2 / 7 capabilities / 4 presets / §1.2→§3-4 map / §8↔§9 resolved-vs-pending / §9↔CHANGELOG) | All internally consistent. |

---

## Remediation Grouping (for C89)

All confirmed findings are **autonomous-actionable** (no operator DESIGN-Q; the C88-3 `additionalProperties` philosophy is the only judgment call and has a targeted fix that sidesteps it). Suggested clustering:

| Cluster | Findings | Shape |
|---------|----------|-------|
| **G1 — `vault_denied` v1→v2+ honesty** (load-bearing, the regression) | C88-1 (MED) | Split the §6.1 footer; retag the §6.1 `vault_denied` row to v2+; bring §3.5 into cohort symmetry with the v0-fallback caveat + "v1+"→"v2+". One coherent edit; finishes the C38-2 fix's skipped second mirror. |
| **G2 — schema README de-fiction** | C88-2 (MED) | Rewrite the README Layout to the real tree; present-tense the v1 note; soften the `validate-presence.py` pointer. (Cross-track: author the validator if wanted.) |
| **G3 — conformance forward-compat** | C88-3 (MED) | Repoint P0-007 to the v1 `query_policy` schema (preferred) — or relax the v0 output schema to `additionalProperties:true` (flag the philosophy choice). |
| **G4 — `synthetic` framing** | C88-4 (LOW) | One-clause qualifier in §2. |
| **(optional) catalog note** | C88-5 (INFO) | Annotate §5.2 R6Action as internal/stored. Safe to skip. |

G1 is the highest-leverage: it is the [[feedback_remediation_introduced_regression]] fix and closes the C38-2 mirror that was left stale. None requires operator input — §8/CHANGELOG already fixed the canonical direction (v2+) for G1, and §7 Precedence + the conformance design intent fix the direction for G2/G3.

---

## Cross-Cutting Observation

**The 2nd-delta earned its keep on C38-2.** The first-delta (C38) was itself a textbook remediation-audit and scored 13/13 on its baseline — yet its own remediation reproduced the exact failure mode it had just documented: it fixed one of C38-2's two named sites and left the other, and the dropped site was the one C38 had flagged as "optional." A delta-audit that only verified "did the §8 edit land?" would have missed C88-1 entirely, because the §8 edit *did* land — it is the §6.1 side, which the remediation never touched, that now disagrees. The [[feedback_remediation_introduced_regression]] prescription holds: **"HELD" must extend to every mirror the remediation's logic implicates, not just the lines in the diff.** Here §8 and §6.1 are mirrors of the same fact (when does `vault_denied` go live); the remediation moved one and the C56 completeness re-read of the remediation's *own recommendation* (which explicitly listed the §6.1 footer) is what surfaced the gap.

Separately, two of the four fresh defects (C88-2 README, C88-3 P0-007) were invisible to C5 and C38 not because those audits were weak but because **neither had scoped the schema directory's README or stress-tested the conformance harness's forward-compat claim against the one output schema that grew in v1.** Widening the artifact set at delta time — per the standard method's "feed finders the mirrors too" — is what found them.
