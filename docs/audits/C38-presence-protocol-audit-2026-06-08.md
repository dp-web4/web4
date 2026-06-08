# C38 — presence-protocol.md Delta Re-Audit

**Date**: 2026-06-08
**Auditor**: autonomous web4 session (legion, C-series **C38**)
**Subject**: `web4-standard/core-spec/presence-protocol.md` (692 lines, 9 sections), v1 Draft
**Baseline**: `docs/audits/presence-protocol-internal-consistency-2026-05-17.md` ("C5", 13 findings P1–P13), remediated in PRs **#206** (G1 casing-authority) + **#207** (G2 discipline-honesty), 2026-05-17/18. File untouched since 2026-05-18 (~3 weeks).
**Companion artifacts cross-checked**: `presence-protocol-CHANGELOG.md`; `web4-standard/schemas/presence-protocol/{v0,v1}/`; `web4-standard/testing/conformance/presence-protocol-conformance.json`.
**Scope**: Internal-consistency delta re-audit. **§A** — verify the 13 C5 findings HELD after #206/#207 and check whether the remediation introduced NEW defects (the [[remediation-introduced regression]] pattern, born C36). **§B** — fresh internal-consistency findings (spec ↔ schemas ↔ conformance vectors ↔ CHANGELOG), refute-by-default. Does NOT compare to SDK/daemon source (other repos). Does NOT patch the spec/schemas/vectors/CHANGELOG — remediation is the next alternation turn.
**Instrument**: 20-agent refute-by-default workflow — 4 §A delta-verification clusters ∥ 8 §B finders → adversarial verify. Per [[feedback_audit_workflow_adversarial_verify]].

---

## Headline

The C5 remediation was **complete and durable: all 13 findings (P1–P13) HELD**, including the two conformance-vector items (P12/P13) that G4 flagged as mechanical/optional — both were in fact applied (P1-003 rewritten to genuinely test connect; new P1-004 covers the wait-protocol defaults).

But the remediation **seeded a regression cluster** — exactly the failure mode [[feedback_remediation_introduced_regression]] predicts. The C5 P6 fix flipped the resource-casing rule from "all wire shapes camelCase" to **"§4 resource bodies are `snake_case`"** to reconcile the one genuinely-snake_case resource (`hestia://society/state`). It **over-generalized to a blanket** covering all six §4 resources — but **four of the six** (`witness/recent`, `session/own`, `society/trust/{plugin_id}`, `vault/{name}`) return **camelCase §5 type-catalog structs**, and the **§7-bound conformance vector P0-010 reads `witness/recent` as camelCase** (`entries[0].chainPosition`). The §8 drift table even labels the blanket rule "None — not drift … consistent with the §7-bound conformance vectors" — a claim **falsified by P0-010**. Three independent §B finder lenses converged on this single defect.

Two further residuals trace to the same remediation: the C5 P9 reservation-tag fix was applied to one cohort sibling (`invalid_role`, §3.1) but not the others (`policy_denied`, §3.4); and the P6 casing resolution was never propagated into the CHANGELOG, which still forecasts the opposite-direction rename. A separate pre-existing cohort error (`vault_denied` swept into "resolved in v1" when its trigger feature is deferred to v2+) rounds out the set.

**§A: 13/13 HELD · 1 regression introduced.**
**§B: 8 raw → 5 confirmed (1 HIGH · 2 MEDIUM · 2 LOW) + 1 INFO deflated · 0 refuted** (after consolidating the 3 same-root casing findings + the §A regression into C38-1).

---

## §A — Delta Verification of C5 Findings (P1–P13)

Every prior finding was re-checked against the live spec and the artifact it cited.

| C5 # | Sev | One-line | Status | Evidence (live) |
|------|-----|----------|--------|-----------------|
| P1 | HIGH | Normative input-casing rule false (claimed camelCase; actually snake) | **HELD** | §3 L106–115 now states the 3-way split (input snake / output+§5 camel / §4 resource snake); §5 L446–451 narrows the old "all wire shapes" mandate. Matches every input example + `v0` input schemas. |
| P2 | HIGH | `synthetic` violates the spec's own completion-discipline rule | **HELD** | §3.1 L150–151 "**Not yet conformed**"; §8 drift row L665; §9 pending item L688–692. `grep synthetic` across schemas/vectors/CHANGELOG = ∅ (gap honestly disclosed, audit path b). |
| P3 | MED | No normative tiebreaker for the casing contradiction | **HELD** | §7 L639–644 new **Precedence** clause binds the Schemas dir normatively + makes schemas/vectors win over prose. §3 L107–108 cross-binds. |
| P4 | MED | §3.1 output pinned to stale `protocolVersion: 0` | **HELD** | §3.1 output L159 now `1`; conformance header `protocolVersion:1`; v0-baseline `0` only in P0-001 input (legitimate). |
| P5 | MED | §5.4 type catalog lags `status`/`nextPollMs`/`enforced` | **HELD** | §5.4 L505–515 carries `status`+`nextPollMs` + `enforced` gloss + §3.4.1 cross-ref. |
| P6 | MED | §4.1 resource fields snake vs §5 camelCase mandate | **HELD** (but → regression R1) | §5 L449–451 exempts §4 bodies; §8 L664 reconciles `society/state` snake. The *specific* P6 contradiction is closed — but the fix over-generalized. See **R1 / C38-1**. |
| P7 | LOW | §2 connect link wrong name + dead anchor | **HELD** | §2 L92–93 `[hestia_connect](#31-hestia_connect)`; no `tool/connect` hits. |
| P8 | LOW | Additive-field bump exception applied but unstated | **HELD** | §2 L85–90 explicit exception clause, lists `synthetic`/`status`/`nextPollMs`. |
| P9 | LOW | §3.1 error list omits §6.1 `(v1+)` reservation caveat | **HELD** (but → asymmetry C38-4) | §3.1 L164 `invalid_role (v1+) … see §6.1`. Fix applied to `invalid_role` only, not the cohort siblings. See **C38-4**. |
| P10 | MED | §9 lists completed work as pending | **HELD** | §9 "Completed in v1" subsection L671–678 (policy engine + vault v2 struck through). |
| P11 | MED | §8 drift row 3 indeterminate after v1 landing | **HELD** (but → C38-2) | §8 L662 struck through, "**Resolved in v1.**" — but sweeps in `vault_denied` incorrectly. See **C38-2**. |
| P12 | LOW | P1-003 vector tests wrong thing | **HELD** | Conformance P1-003 L339–364 now calls `hestia_connect` with `protocol_version:1` and asserts `protocolVersion==1`. Applied via option (a). |
| P13 | LOW | Wait protocol has zero vector coverage | **HELD** | New scenario **P1-004** L365–398 asserts `status:"decided"` / `nextPollMs:null` against the v1 schema. |

**Result: 13/13 HELD.** The C5 remediation resolved every finding and durably held for 3 weeks. G4 (conformance vectors), flagged mechanical/optional, was applied in full.

### Regression introduced by the remediation

| ID | Sev | Where | What the remediation broke |
|----|-----|-------|----------------------------|
| **R1** | MED→**HIGH** (consolidated) | §3 L114–115 + §5 L449–451 + §8 L664 vs §4.1/§4.2 + §5.1/§5.5/§5.6/§5.7 + vector P0-010 | The P6 fix broadened "the `society/state` stats object is snake_case" into a **blanket** "§4 resource bodies are snake_case," sweeping in the four §4 resources that return camelCase §5 structs. **Consolidated with the 3 §B confirmations as C38-1 below** (which raises it to HIGH on the strength of the bound-vector + bound-schema conflict and the false §8 justification).

---

## §B — Fresh Findings (confirmed)

Raw §B = 8 findings; 3 were the same root defect (resource-casing) surfaced by three lenses (`resources-types`, `type-catalog-completeness`, `conformance-vectors`) and are consolidated with §A's R1 into **C38-1**. Net: **5 distinct confirmed + 1 INFO deflated**.

### C38-1 — Blanket "§4 resource bodies are snake_case" contradicts the four camelCase §5-typed resources, bound vector P0-010, and the witness_entry/trust_state schemas (HIGH)

**Locations**: §3 L114–115; §5 L449–451; §8 L664 (the blanket rule, 3 places) ↔ §4.1 L430–431, §4.2 L437–438 (the four §5-typed resources); §5.1/§5.5/§5.6/§5.7 (camelCase structs); conformance **P0-010** L247–262; `v0/common/witness_entry.schema.json`, `v0/common/trust_state.schema.json` (`additionalProperties:false`, camelCase required keys).

**Tension**:
- **Blanket rule (normative prose, unqualified)** — §3 L114–115: "**§4 resource bodies are `snake_case`** (`sovereign_lct`, `chain_length`, …), matching the bound conformance vectors." §5 L449–451 reinforces it; §8 L664 affirmatively labels it "**None — not drift** … consistent with the §7-bound conformance vectors."
- **But §4 binds four of six resources to camelCase §5 structs** — `hestia://witness/recent`→§5.6 WitnessEntry (`prevHash`,`eventType`,`signerLct`,`chainPosition`); `hestia://session/own`→§5.1 Session (`sessionId`,`pluginId`,`connectedAt`); `hestia://society/trust/{plugin_id}`→§5.5 TrustState (`entityId`,`actionCount`,`successRate`,`daysSinceLast`); `hestia://vault/{name}`→§5.7 VaultEntry (`allowedConsumers`,`createdAt`). §5 L446–447 makes camelCase **normative** for these.
- **A §7-bound vector falsifies the rule's own justification** — P0-010 reads the `hestia://witness/recent` **resource body** and asserts `entries[0].chainPosition` (camelCase), with description "returns the same WitnessEntry shape as the query_history tool." `witness_entry.schema.json` requires camelCase keys with `additionalProperties:false` — so `chain_position` is schema-**forbidden**.

**Why internal / genuine**: An implementer who follows §3's blanket rule serves `witness/recent` as `entries[0].chain_position` and **fails bound vector P0-010 and the witness_entry schema**; one who follows §4.1/§5.6 serves camelCase and violates §3's normative prose. The §3 self-justification "matching the bound conformance vectors" is **factually half-false**: the bound vectors are *split* — P0-009 (`society/state`) is snake_case scalars, P0-010 (`witness/recent`) is camelCase WitnessEntry objects. Only `society/state` (an ad-hoc stats object **not** in the §5 catalog) is genuinely snake_case; `context/shared` is opaque user JSON. This is **not** disclosed in §8 — §8 L664 asserts the wrong rule as "not drift." It is **distinct from C5 P6** (which concerned `society/state` scalars vs the old camelCase mandate); it is the **NEW residual** the P6 over-generalization created.

**Severity adjudication**: Two lenses rated HIGH ("a conformant impl cannot satisfy the doc as written; normative prose contradicts a bound artifact"); one rated MEDIUM, arguing the §7 Precedence clause (L639–644) gives a deterministic tiebreak (schemas/vectors win, prose "is in error"), so a §7-aware implementer does not fork. **Adjudicated HIGH**, because: (a) §8 L664 contains a *verifiably false statement* about the bound vectors ("consistent with the §7-bound conformance vectors" — P0-010 refutes it), which is worse than a silent ambiguity; and (b) a §3-following implementer fails a bound vector + a `additionalProperties:false` schema. The §7-precedence mitigation is real and **lowers practical interop risk to MEDIUM for §7-aware readers** — recorded here as the dissent — but does not erase the documentary contradiction or the false §8 claim. Either label, this is the load-bearing remediation target.

**Recommended resolution (AUTONOMOUS)**: Scope the rule per-resource. §4 resources split into (1) ad-hoc snake_case payloads — `society/state` (P0-009-confirmed) and opaque `context/shared`; and (2) §5-typed resource bodies — `witness/recent` (WitnessEntry), `session/own` (Session), `society/trust/{plugin_id}` (TrustState), `vault/{name}` (VaultEntry) — which carry their §5 **camelCase** keys, as P0-010 + the common schemas already require. Reword §3 L114–115 and §5 L449–451 accordingly; drop/scope the "matching the bound conformance vectors" justification (the vectors are split); update §8 L664 to the per-resource split.

### C38-2 — §8 drift row claims `vault_denied` is "now emittable in v1," but its only trigger (interactive vault approval) is deferred to v2+ (MEDIUM)

**Locations**: §8 L662; §6.1 L604 + L612–613; §3.5 L324–325, L330; §3.6 L336; CHANGELOG L82–83 + L150.

**Tension**: §8 L662 (struck through, then "**Resolved in v1.** The policy engine is wired … these codes are now emittable") sweeps **three** codes — `policy_denied`, `vault_denied`, `invalid_role` — into one "resolved in v1" claim, grounded in the policy-engine landing. But `vault_denied` means "**interactive vault approval refused**" (§6.1 L604) — unrelated to the policy engine. §3.5 L330 / §3.6 L336 ("v0 has no interactive approval … v1+ MAY add approval flow") and CHANGELOG L82–83 + L150 ("**deferred to v2+** … `approvalToken` … still always `null`") confirm the approval flow is **not** in v1.

**Why internal**: A code reachable only via an unshipped feature cannot be "emittable" in v1. §8's blanket claim is false for `vault_denied` specifically (`policy_denied` + `invalid_role` are legitimately v1-emittable). An SDK author reading §8 expects v1 `vault_denied` reachability; §3.5/§3.6 + CHANGELOG say it cannot occur. Not a disclosed drift (§8 asserts *resolved*, the opposite).

**Recommended resolution (AUTONOMOUS)**: Scope §8 L662's resolution to `policy_denied` + `invalid_role`; move `vault_denied` to a separate still-pending row (reserved-but-unemittable until interactive approval ships, v2+). Optionally narrow the §6.1 L612–613 "until v1 lands" note to the two policy/role codes.

### C38-3 — CHANGELOG "Upcoming" still forecasts the `trust_states_known → trustStatesKnown` rename that §8 resolved in the opposite direction ("no rename", snake_case) (MEDIUM)

**Locations**: CHANGELOG L155–157 (live "Upcoming (deferred from v1)") ↔ spec §8 L664 + §3 L114–115 + §4.1 L429 + vector P0-009.

**Tension**: CHANGELOG L155–157 forecasts a still-pending rename **to camelCase** (`trustStatesKnown`). Spec §8 L664 (dated 2026-05-18, after the 2026-05-16 CHANGELOG entries) resolves the same field the **opposite** way: "**No rename** … the earlier camelCase aspiration contradicted the bound vectors" — snake_case is permanent. The §7-bound vector P0-009 binds `society/state` to snake_case.

**Why internal**: The CHANGELOG's own Process makes the deferred-items section authoritative; a reader following it implements a `trustStatesKnown` rename that breaks the §3/§7-bound snake_case convention. The P6 remediation chose snake_case intra-spec but never propagated it to the bound CHANGELOG — a **NEW spec↔CHANGELOG residual** (distinct from the intra-spec C5 P6). MEDIUM not HIGH: the field `trust_states_known` is not in any currently-bound schema/vector body or §4.1's field list, so nothing bound breaks *today*; the conflict is between two authoritative forward statements. **Couples to C38-1** (the casing model). Note: the CHANGELOG forecast is wrong under *either* resolution of C38-1, since `society/state` is the genuinely-snake_case resource.

**Recommended resolution (AUTONOMOUS)**: Remove the rename item from CHANGELOG "Upcoming"; record the casing as resolved snake_case (no rename) per §8 / P0-009. Optionally back-annotate the v0 "Known drift" origin.

### C38-4 — §3.4 lists `policy_denied` with no `(v1+)` reservation marker — the C5 P9 fix was applied to one cohort sibling only (LOW)

**Locations**: §3.4 L297–298 ↔ §6.1 L603 + L612–613; cohort siblings §3.1 L164 (`invalid_role`, the remediated P9 text) + §3.5 L330 (`vault_denied`).

**Tension**: §3.4 L297–298 lists "`hestia.policy_denied` (when deny is enforced)" with only a semantics qualifier, **no version marker**. §6.1 L603 marks it "daemon (v1+)" and L612–613 says `(v1+)` codes are reserved (v0 MAY emit `internal_error`). The siblings carry the reservation in their per-tool lists: `invalid_role` §3.1 L164 "(v1+) … v0 daemons MAY emit `hestia.internal_error` instead (see §6.1)"; `vault_denied` §3.5 L330 "(reserved for v1+)". Only `policy_denied` lacks it.

**Why internal**: A §3.4-alone reader concludes v0 `hestia_query_policy` emits `policy_denied`, which §6.1 contradicts. This is the **same defect** C5 P9 fixed for `invalid_role` — an **asymmetric remnant** of that remediation across the reservation cohort. LOW (a registry-aware reader resolves it), matching the LOW C5 assigned P9.

**Recommended resolution (AUTONOMOUS)**: Annotate `policy_denied` in §3.4 with "(v1+; v0 daemons MAY emit `hestia.internal_error` — see §6.1)", mirroring the §3.1 P9 fix; normalize `vault_denied` §3.5 wording for cohort symmetry. Or add one blanket sentence at the top of §3: per-tool error lists are subject to §6.1 reservation tags.

### C38-5 — CHANGELOG self-contradicts on which version delivers interactive vault approval (LOW)

**Locations**: CHANGELOG L134 (v0 section) ↔ L82–83 (v1) + L150 (Upcoming).

**Tension**: CHANGELOG v0 section L134: "Interactive vault approval **arrives in v1**." v1 section L82–83 + Upcoming L150: it **did not** land in v1, **deferred to v2+**, `approvalToken` still `null`. Same file, two incompatible version assignments for the same feature; both entries dated 2026-05-16 and coexist in the current revision. This is the historical root that C38-2 propagated into §8.

**Why internal**: A single file contradicts itself. LOW — the v1/Upcoming sections are the current authoritative statements and agree with §3.5/§3.6; only the stale v0 forecast is wrong. **Couples to C38-2** (same feature deferral).

**Recommended resolution (AUTONOMOUS)**: Correct CHANGELOG L134 from "arrives in v1" to "deferred (still pending as of v1; see the v1 'Not yet implemented' and 'Upcoming' sections)."

---

## §B — Deflated

| ID | Claimed | Verdict | Why deflated |
|----|---------|---------|--------------|
| F-r6action-orphan | INFO | **DEFLATED → INFO** | §5.2 R6Action `{actionId,toolName,startedAt,chainPosition}` is emitted by no §3 output or §4 resource (the §3.2 begin-action output is a distinct 3-field, schema-bound handle that omits `toolName`). True observation, but **not a contradiction** — §5 is a documentary "Type catalog"; the spec never claims the begin output *is* an R6Action record. Same benign pattern as §3.1 connect output (4 fields) vs §5.1 Session (8). Optional maintainability note only: label §5.2 as an internal/stored record not directly wire-returned (paralleling §5.3 Outcome's "orchestrator → presence" label). No conformant-impl impact. |

**0 refuted** — every §B finder claim survived adversarial verification at or near its claimed severity (the only adjustment was the C38-1 HIGH/MEDIUM adjudication, recorded above).

---

## Remediation Grouping (for the next alternation turn)

All five confirmed findings are **autonomous-actionable** spec/CHANGELOG-internal edits (no SDK/daemon changes, no DESIGN-Q). Suggested clustering:

| Cluster | Findings | Shape |
|---------|----------|-------|
| **G1 — resource-casing scoping** (load-bearing) | C38-1 (HIGH) + C38-3 (MEDIUM, coupled) | Rewrite §3 L114–115 + §5 L449–451 + §8 L664 to the per-resource split (ad-hoc snake vs §5-typed camel); propagate the snake_case `society/state` resolution into the CHANGELOG (drop the `trustStatesKnown` forecast). One coherent edit. |
| **G2 — vault_denied / approval-flow deferral honesty** | C38-2 (MEDIUM) + C38-5 (LOW, coupled) | Scope §8 L662 to `policy_denied`+`invalid_role`; move `vault_denied` to still-pending; fix the stale CHANGELOG v0 "arrives in v1" forecast. Same feature (interactive approval). |
| **G3 — reservation-tag cohort symmetry** | C38-4 (LOW) | Annotate `policy_denied` §3.4 (+ normalize `vault_denied` §3.5) per §6.1, or one blanket §3 sentence. Mechanical. |
| **(optional) catalog note** | F-r6action-orphan (INFO) | Label §5.2 R6Action as internal/stored. Safe to skip. |

G1 is the highest-leverage: it is the [[feedback_remediation_introduced_regression]] fix and touches the spec's central casing-discipline. None requires operator DESIGN-Q input — the §7 Precedence clause already establishes the canonical direction (schemas/vectors normative), so the per-resource split is the unambiguous resolution.

---

## Cross-Cutting Observation

**This is the cleanest [[remediation-introduced regression]] case in the C-series since the pattern was born at C36.** The C5 remediation scored 13/13 — every finding genuinely resolved and held 3 weeks. Yet **three of the five fresh defects are residuals of that very remediation**: P6's casing fix over-generalized (C38-1), P6's resolution was never propagated to the CHANGELOG (C38-3), and P9's reservation-tag fix was applied to one cohort sibling but not the others (C38-4). The lesson reinforces the pattern's prescription: a delta re-audit must check not just "did the fix hold?" but "did the fix's *broadened wording* or *incomplete propagation* seed adjacent defects?" Here, "all resource bodies camelCase" → "all resource bodies snake_case" was a clean inversion that fixed one resource and broke four — the over-correction is the regression.

The §7 Precedence clause (itself a C5 P3 remediation) is doing real protective work: it gives C38-1 a deterministic tiebreak that caps its practical interop risk. That is the system working — a normative precedence rule absorbing a prose/artifact contradiction — but it does not excuse the false §8 "not drift / consistent with the vectors" claim, which a remediation should correct.
