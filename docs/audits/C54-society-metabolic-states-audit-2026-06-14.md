# C54 — SOCIETY_METABOLIC_STATES.md Delta Re-Audit (prior C21)

**Audit ID**: C54
**Date**: 2026-06-14
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (445 lines, v1.0.0, "Proposed Standard")
**Prior audit**: C21 (2026-05-29, 16 findings 3H/8M/5L + 6 INFO + 2 DEMOTED) — `docs/audits/C21-society-metabolic-states-audit-2026-05-29.md`
**Prior remediation**: PR #250 (`f142fcdb`) — 8 autonomous-actionable applied, 8 design-Q deferred
**Cadence**: C-series delta re-audit cycle. SOCIETY_METABOLIC_STATES.md is the **oldest never-delta-re-audited core-spec file** (first pass C21, 2026-05-29). This is its first delta pass.
**Auditor session**: legion-web4-20260614-000047 (LEAD, exit #186)
**Out of scope**: spec source edits, SDK edits, sister-doc finding-generation (cross-reference reads only). Remediation of C54 findings is the next alternation turn (C55).

---

## 1. Methodology

Standard C-series delta re-audit:
- **§A — Prior-finding verification**: re-verify every C21 finding. For the 8 remediated (PR #250): confirm the fix HELD and introduced no regression. For the 8 deferred design-Q: confirm still open/valid. Targeted #-regression sweep on commits `f142fcdb` (#250, the C21 remediation) and `252e77bd` (#252, the C22 remediation that ALSO touched this file and is known to have introduced 9 defects into SOCIETY_SPECIFICATION.md at C50).
- **§B — Fresh findings**: multi-agent finder workflow (`wf_1109813b-386`), 8 lenses (table-semantics, transition-graph, energy-economics, sdk-align, conformance-sketchcode, cross-doc-parent, security-future, primitive-clustered cross-section pass), each refute-by-default per finding, then an independent adversarial verifier per candidate (refute-by-default). Known C21 findings supplied as an explicit exclusion list so finders surface only net-new issues.
- **§C — Carries**: reconcile the 8 still-open C21 design-Q + cluster trackers (subordinate-ontology) with the standing ledger.
- **§D — Method notes**.

Severity tags: HIGH / MEDIUM / LOW / INFO / DEMOTED. Disposition tags per finding: AUTONOMOUS-ACTIONABLE / DESIGN-Q / CROSS-TRACK.

### Anchor authorities consulted
| Anchor | Path |
|---|---|
| Spec target | `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` |
| SDK canonical | `web4-standard/implementation/sdk/web4/metabolic.py` |
| Sister SDK | `web4-standard/implementation/sdk/web4/society.py` |
| Test vector | `web4-standard/test-vectors/metabolic/society-metabolic-states.json` (132L, **12** vectors) |
| Ontology | `web4-standard/ontology/web4-core-ontology.ttl`, `t3v3-ontology.ttl` |
| Parent specs | `SOCIETY_SPECIFICATION.md` (§1.4 now references metabolic), `web4-society-authority-law.md` (§3.6 now references metabolic) |

---

## 2. §A — Prior-Finding Verification

### A.1 Remediated findings (PR #250) — held/regressed?

| C21 ID | Finding | Remediation applied | C54 disposition |
|---|---|---|---|
| **H2** | §1.2 biological list only 5/8 states | §1.2 extended to all 8 (`L19-27`) | **HELD** — all 8 states present with analogs; "Each state maps to" claim now backed. |
| **M1** | Parent-doc orphan (SOCIETY_SPEC + SAL had zero metabolic refs) | SOCIETY_SPECIFICATION.md §1.4 (`L85-89`) + web4-society-authority-law.md §3.6 (`L137-144`) added | **HELD** — both sister paragraphs present, name all 8 states, link the spec. (See B-cross-doc lens for a nuance on §1.4's "MUST conform" wording vs this doc's Proposed-Standard/SHOULD status.) |
| **M2** | "Alert bonus" phantom in §5.1 Torpor row | Stripped → "Frozen \| Crisis response" (`L299`) | **HELD in spec.** Reverse-drift exposed: SDK `metabolic.py:110` still `description="Frozen + alert bonus"` — see §B sdk-align. |
| **M4** | §6.1 "Daily ATP Cost" but baseline hourly | Relabelled "Hourly ATP Cost" + hours note (`L341-344`) | **HELD** — label now matches §4.1 `baseline_cost: "100 ATP/hour"`. |
| **M6** | Test-vector orphan (spec unaware of conformance suite) | §10 Conformance added (`L428-441`) | **HELD + accurate.** Verified §10's "12 vectors", category breakdown (3 energy / 3 wake / 4 transition / 2 reliability), and "6 of 8 states (estivation+molting not exercised)" against the live vector file — all correct. *Note:* §10's count (12) is **more accurate than C21 itself**, which miscounted the file as "11 vectors". |
| **M8** | §3.1 matrix vs §4.1 schema reconciliation gaps | §3.1 imported thresholds (threat_score>80/<20, 90d timeout, new_citizen) + §4.1 illustrative-vs-normative note (`L212`) | **HELD** — matrix cross-refs resolve to existing §4.1 keys; "normative source" disclaimer present. |
| **L1** | §2.3 Sleep analog "Deep sleep with REM" overlaps Dreaming | → "Deep non-REM (slow-wave) sleep" (`L78`) | **HELD** — disambiguated from §2.7 Dreaming "REM sleep". |
| **L6** | §5.1 Molting "-20%" magic number absent from §2.8 body | §2.8 adds "-20% trust-tensor penalty ... (see §5.1)" (`L156`) | **HELD** — number now grounded in body; SDK `temporary_penalty=-0.20` consistent. |

**8/8 remediated findings HELD. 0 REGRESSED.** No remediation-introduced regression in this file.

### A.2 #-Regression sweep (binding policy note #2)

- **`f142fcdb` (#250, C21 remediation)** — clean. Edits confined to the 8 autonomous findings + M1's two sister files. No collateral edits, no scope creep. The §10 Conformance text is fully accurate against ground truth (verified above).
- **`252e77bd` (#252, C22 remediation)** — **INNOCENT.** Treated guilty-until-verified per policy note #2. `git show 252e77bd -- SOCIETY_METABOLIC_STATES.md` shows the file's ONLY change was the I1 date bump (`## Date: January 17, 2025` → `2026-05-30`). **Zero content/normative edits.** This is the same #252 that injected a content regression into SOCIETY_SPECIFICATION.md (C50 flagship) — but here its footprint was a pure sister-doc date refresh, so no regression propagated into this file. (Minor process note: #252's own BC#15 cautions against bumping dates on upcoming audit candidates; this file was bumped as a BC#1 sister-doc, defensible since #250 had made substantive same-day edits. Not a finding.)

### A.3 Deferred design-Q (8) — still open?

| C21 ID | Finding | SDK/spec anchor re-checked | C54 disposition |
|---|---|---|---|
| **H1** | §2.3/§5.1 Sleep: spec silent on update_rate (only decay) | SDK `metabolic.py:108` still `update_rate=0.0, decay_rate=0.1`; spec §2.3/§5.1 unchanged | **STILL OPEN** |
| **H3** | §5.1 single column mixes rate/decay/scope/penalty axes | §5.1 unchanged (single "Trust Tensor Effect" col) | **STILL OPEN** |
| **M3** | Torpor/Estivation reachable only from Active (§3.1) | §3.1 still Active-only entry; SDK transition list unchanged | **STILL OPEN** |
| **M5** | "dormant states" undefined; SDK partitions Dreaming as active | SDK `DORMANT_STATES={REST,SLEEP,HIBERNATION,TORPOR,ESTIVATION}`, `ACTIVE_STATES={ACTIVE,DREAMING,MOLTING}` unchanged; §6.2 still applies wake-penalty to Dreaming | **STILL OPEN** |
| **M7** | `web4:MetabolicState` absent from ontology | `grep -i metabolic *.ttl` → no class (loose-pattern sweep confirms true absence) | **STILL OPEN** — subordinate-ontology cluster (now 7 audits per ledger). |
| **L4** | Estivation 10% energy < Sleep 15% anomaly | §2.6/§2.3 + §4.1 multipliers unchanged | **STILL OPEN** |
| **L5** | §2.2 Rest "queued" vs SDK refuse | §2.2 unchanged; SDK `accepts_new_citizens` returns `True` only for ACTIVE — *and* the SDK comment now reads "Rest: queued" while the code returns `False` for Rest (no queue), a fresh internal SDK inconsistency | **STILL OPEN** (slightly evolved; see §B sdk-align) |
| **L7** | §6.2 wake-penalty omits Torpor/Estivation/Molting | §6.2 penalties dict unchanged (sleep/hibernation/dreaming only) | **STILL OPEN** |

**8/8 deferred design-Q remain open.** None silently resolved; none newly invalidated.

### A.4 INFO/DEMOTED re-check
- INFO1 (old date/Proposed-Standard): date now `2026-05-30` (refreshed by #252); Status still "Proposed Standard" — advisory, open.
- INFO2 (no CHANGELOG sibling): still none — advisory.
- INFO3/INFO4 (sketch-code undefined identifiers `CYCLE_LENGTH`/`deterministic_shuffle`/`society_lct`, §4.3 global `society`): unchanged — advisory.
- INFO5 (§7.2 omits Dreaming): unchanged — advisory.
- INFO6 (§4.1 bare-string `society_lct`): unchanged — advisory cross-corpus tracker.
- DEMOTED D1/D2: D1 (Molting accepts_transactions) and D2 (SDK Dreaming accepts_transactions vs ACTIVE_STATES) are SDK-side; out of spec-audit scope, carried for SDK audit.

---

## 3. §B — Fresh Findings

**Workflow**: `wf_1109813b-386` — 8 lenses (table-semantics, transition-graph, energy-economics, sdk-align, conformance-sketchcode, cross-doc-parent, security-future, primitive-cluster), each refute-by-default, then one adversarial verifier per candidate (refute-by-default). **27 raw → 24 verifier-confirmed / 3 refuted.** After auditor de-duplication (multiple lenses re-surfaced the same root defect) the 24 confirmed collapse to **16 distinct findings (0 HIGH / 5 MEDIUM / 8 LOW / 3 INFO)**. Every SDK and sister-doc claim below was re-verified by the auditor against the live files (not taken on the finder's word).

### Flagship: the **#250 (C21) remediation itself introduced a mirror-drift cluster**
Unlike #252 (innocent here — date-only), the C21 remediation `f142fcdb` edited one side of several spec↔SDK and spec↔sister-doc pairs and left the mirror stale. This is the same *class* as the C50 flagship (remediation-introduced regression) but **milder — all LOW/MEDIUM, no HIGH, mostly SDK-mirror lag rather than spec-internal corruption.** §A's clean 8/8-HELD verdict is about the *target file's* edited lines; the regression surface is in the **mirrors the remediation did not touch.** Findings B1–B4, B14, B15 are this cluster.

### MEDIUM

#### B1 — M8 remediation updated spec Hibernation→Active trigger; SDK transition mirror left stale (CROSS-TRACK SDK)
**Lines**: spec `L184` vs SDK `metabolic.py:147`. **Verified**: pre-#250 spec §3.1 read "External witness or timeout"; SDK `Transition(HIBERNATION, ACTIVE, "external witness or timeout")` matched it byte-for-byte. #250/M8 changed the spec to "External witness, **new_citizen** trigger, or **90-day** timeout" (importing §4.1 `wake_on`) but did NOT update the SDK string, which still omits the `new_citizen` wake path and the 90-day quantification. `transition_trigger(HIBERNATION, ACTIVE)` now returns wording that disagrees with the normative spec. **Tag**: CROSS-TRACK (SDK). **Rec**: update the SDK `_TRANSITIONS` Hibernation→Active trigger string to match §3.1; confirm a `new_citizen` wake is actually wired in `society.py` wake logic (if not, the spec/§4.1 promises a path the SDK never honors — escalate).

#### B5 — §4.3 SentinelWitness monitored-state set unreconciled with §2.4/§2.5/§3.1/§7.1 (DESIGN-Q)
**Lines**: §4.3 `L279` (`while society.state in ['hibernation','torpor']`) against §3.1 `L189`, §7.1 `L372`, §2.4 `L86`, §2.5 `L101-107`; SDK `metabolic.py:312` (`ESTIVATION` witness fraction 0.0). The single loop-guard list is inconsistent with three other sections:
- **(a) headline — Estivation transition unfireable**: §3.1 `L189` mandates `Estivation → Active: threat_score < 20`, an *internally-monitored* threshold, but the only described live monitor (§4.3) never runs during Estivation, and the SDK provisions **0 witnesses** for Estivation. No entity exists to evaluate threat-clear and fire the transition.
- **(b)** §7.1 `L372` lists Sleep's mitigation as "Sentinel witnesses", but §4.3 never monitors Sleep (Sleep's real safeguard is the §2.3 2-of-10 quorum).
- **(c)** §4.3 DOES monitor Torpor, yet §2.4 introduces the sentinel only for Hibernation and §2.5 says Torpor is "Reactive only — no proactive operations / Witnesses wake only on triggers" (a 60s heartbeat is proactive).
**Tag**: DESIGN-Q. **Rec**: define the monitored-state set once (which low-energy sentinel evaluates triggers in which states) and reconcile §2.4/§2.5/§3.1/§4.3/§7.1 + SDK `WITNESS_REQUIREMENTS`; or redefine Estivation→Active as an external/operator trigger.

#### B6 — §6.1 cost formula under-defined: `Society_Size` undefined + baseline per-member-vs-per-society ambiguous (DESIGN-Q)
**Lines**: §6.1 `L341` (`Hourly ATP Cost = Baseline * State_Multiplier * Society_Size`), §4.1 `L241` (`baseline_cost: "100 ATP/hour"`), test vector `metabolic-energy-active-baseline` (100 × 10 members × 1h → 1000). `Society_Size` is used in the formula but defined nowhere in the spec (loose-grep confirms). The conformance vector only resolves correctly if `baseline_cost` is **per-member-per-hour**, but §4.1 labels it flatly "100 ATP/hour" with no per-member qualifier — so the spec's own normative baseline is ambiguous about whether it is per-society or per-member. **Tag**: DESIGN-Q. **Rec**: define `Society_Size` (citizen count? witness count?) and disambiguate `baseline_cost` units to match the test vector's per-member reading.

#### B8 — §7 Security omits Estivation entirely + `threat_score` trigger has no defined provenance/integrity (DESIGN-Q)
**Lines**: §7.1 `L370-376`, §7.2 `L382-385`, vs §2.6 `L127` (Estivation use case = "Network attacks, regulatory freezes"), §3.1 `L176/L189`, §4.1 `L236-237`. Estivation — the *dedicated threat-response state* — is absent from BOTH the §7.1 vulnerability table and the §7.2 attack-prevention list. Compounding: Estivation entry/exit is driven entirely by `threat_score` (>80 enter, <20 clear) whose authoritative source, integrity, and anti-manipulation controls are never specified (the scalar appears only at `L176/L189/L236/L237`). An adversary able to influence `threat_score` can force a society into Estivation (availability DoS — external interactions suspended per §2.6) or pin it there by holding the score above the clear threshold. **Tag**: DESIGN-Q. **Rec**: add Estivation rows to §7.1/§7.2 (lock-in / forced-isolation + bounded duration); specify `threat_score`'s authoritative source (witnessed/quorum-attested, T3-weighted) and an anti-manipulation requirement.

#### B14 — M1 remediation overstated normative strength in SOCIETY_SPECIFICATION §1.4 (CROSS-TRACK sister-doc)
**Lines**: SOCIETY_SPECIFICATION.md `§1.4 L89` ("Implementations of this Society Specification **MUST also conform** to the metabolic-states specification ...") vs SOCIETY_METABOLIC_STATES.md Status `L5` ("Proposed Standard") + §10 `L430` ("Implementations **SHOULD** validate ..."). The M1-added paragraph imposes a hard MUST-conform on a spec that is itself Proposed-Standard with SHOULD-level conformance — a normative-strength escalation the metabolic spec does not assert for itself. **Tag**: CROSS-TRACK (sister-doc; introduced by this file's M1 remediation). **Rec**: soften §1.4 to "SHOULD conform" (or gate the MUST on the metabolic spec reaching a normative-standard maturity), aligning with §10's SHOULD.

*(MEDIUM set: B1, B5, B6, B8, B14 = 5 distinct. The 6 confirmed-MEDIUM raw candidates included the SDK Hibernation-trigger pair — both merged into B1 — and the two Estivation-security candidates — both merged into B8. 24→16 dedup detail in §D.3.)*

### LOW

#### B2 — §2.4 Hibernation prose not updated to match M8's §3.1/§4.1 wake triggers (AUTONOMOUS-ACTIONABLE)
**Lines**: §2.4 `L91` ("Wake requires external trigger or timeout") vs §3.1 `L184` + §4.1 `L229` (now include `new_citizen` + 90-day). #250/M8 updated the matrix and schema but left the §2.4 characteristic bullet stale — an intra-doc inconsistency introduced by the fix. **Tag**: AUTONOMOUS-ACTIONABLE. **Rec**: mirror §3.1 wording into §2.4 ("Wake requires external witness, new-citizen trigger, or 90-day timeout").

#### B3 — M4 reverse-drift: SDK `energy_cost` docstring still says "Daily ATP Cost" (CROSS-TRACK SDK)
**Lines**: SDK `metabolic.py:207` (`Formula (§6.1): Daily ATP Cost = ...`) vs spec §6.1 `L341` (now "Hourly"). #250/M4 relabeled the spec but the SDK docstring (a single site) still cites the old "Daily" label and the §6.1 reference. **Tag**: CROSS-TRACK (SDK). **Rec**: update the SDK docstring to "Hourly ATP Cost".

#### B4 — M2 reverse-drift: SDK `TrustEffect` still `description="Frozen + alert bonus"` (CROSS-TRACK SDK)
**Lines**: SDK `metabolic.py:110` vs spec §5.1 `L299` (now "Frozen"). #250/M2 stripped the phantom "Alert bonus" from the spec, making the spec authoritative — but the SDK is now the *lone* carrier of the undefined feature string. (The #250 PR body explicitly chose to leave the SDK string "to avoid churn"; post-remediation it is stale.) **Tag**: CROSS-TRACK (SDK). **Rec**: change SDK Torpor description to "Frozen" (or "Crisis response") to match the now-authoritative spec.

#### B7 — §6.2 wake-penalty magic numbers (10/100/50) ungrounded (DESIGN-Q)
**Lines**: §6.2 `L356-358`. The penalty constants are uncited (parallel to C21-L6's "-20%" before it was grounded). SDK `metabolic.py:228` mirrors them. **Tag**: DESIGN-Q. **Rec**: derive or parameterize the constants in prose, or state they are illustrative defaults.

#### B9 — §6.2 prices a "dreaming" premature-wake penalty with no §3.1 transition to attach to (DESIGN-Q)
**Lines**: §6.2 `L358` + §10 `L437` (dreaming wake vector) vs §3.1 `L192` (only `Dreaming → Active: Consolidation complete`). §3.1 admits no *premature* Dreaming exit, so the penalty (and the `metabolic-wake-dreaming-interrupted` vector, planned 2h/actual 0h) prices a transition the state machine does not permit. **Tag**: DESIGN-Q. **Rec**: add an interruptible `Dreaming → Active: wake trigger` to §3.1, or scope-note §6.2 that the dreaming penalty applies only under an external interrupt not in §3.1.

#### B10 — §7.2 omits hibernation `new_citizen` wake as an economic-DoS vector (AUTONOMOUS-ACTIONABLE)
**Lines**: §3.1 `L184` + §4.1 `L229` (hibernation wakes on `new_citizen`) vs §6.2 `L357` (100×incompleteness penalty borne by the victim) vs §7.2 `L382` (#1 "Sleep Deprivation Attack" scoped to Sleep only). An attacker submitting citizenship applications can force repeated hibernation wakes, each costing the victim society the penalty; §7.2 #1 covers only Sleep wake-triggers. **Tag**: AUTONOMOUS-ACTIONABLE (generalize §7.2 #1) / borderline DESIGN-Q. **Rec**: generalize §7.2 #1 to rate-limit/ATP-bond all cheap external wake triggers including hibernation `new_citizen`.

#### B11 — L5 evolution: SDK `accepts_new_citizens` comment "Rest: queued" contradicts its own return (CROSS-TRACK SDK)
**Lines**: SDK `metabolic.py:412-413` (comment "Active: yes. Rest: queued. All others: no or queued." but `return state == MetabolicState.ACTIVE`, i.e. `False` for Rest with no queue). Atop the still-open C21-L5 spec↔SDK gap (§2.2 "queued" vs SDK refuse), the SDK now has an *internal* comment/code mismatch. **Tag**: CROSS-TRACK (SDK). **Rec**: bundle with L5 resolution — implement queueing or fix the comment to match the refuse behavior.

#### B15 — M1 remediation: SAL §3.6 dormant-state parenthetical omits Rest (CROSS-TRACK sister-doc)
**Lines**: web4-society-authority-law.md §3.6 `L140` ("dormant states (Sleep, Hibernation, Torpor, Estivation)") vs SDK `DORMANT_STATES` (5 states **incl. REST**). The M1-added paragraph's dormant list drops Rest, which the SDK classifies as dormant — a fresh instance of the still-open **M5** "dormant undefined" gap, now baked into a sister doc. (Minor: §3.6 also attributes quorum-scaling to SAL §3.1 — verify that cross-ref.) **Tag**: CROSS-TRACK (sister-doc). **Rec**: resolve M5 first (define "dormant"), then make §3.6's list conform; couples to M5.

### INFO

#### B12 — §7.1 Hibernation mitigation "Dead-man switch" is an orphan term (advisory)
**Lines**: §7.1 `L373` (only occurrence in the spec; loose-grep confirms). The body's actual mechanism is a sentinel heartbeat + timeout (§2.4 `L86`, §4.3, §3.1). The verifier correctly **downgraded** the finder's "inverse mechanism" framing as an overcall (a heartbeat monitor is canonically *implemented* as a watcher-side dead-man switch); the residual defect is only the undefined/orphan term. **Rec**: replace with "Sentinel heartbeat + timeout wake (§2.4, §4.3)" or add a one-line definition.

#### B13 — §10 Conformance wording imprecisions (remediation-added §10) (advisory)
**Lines**: §10 `L430-441`. Three minor precision issues in the M6-added section: (a) the reliability-score vectors are excluded from the "MUST produce numerically equal results" clause (stated as "weights as written"), leaving their conformance strength soft; (b) "transition matrix membership" is grouped under "numerically equal results" though membership is boolean, not numeric; (c) "molting ... not exercised" is slightly loose since `molt_success_rate` feeds the §5.2 reliability vectors (though no vector drives the molting *state* through energy/wake/transition, so the core claim holds). **Rec**: tighten §10 wording; none affect conformance behavior.

#### B16 — §3.1 transition-matrix cross-ref citation asymmetry (advisory)
**Lines**: §3.1 `L171-194`. Post-M8, some transitions carry "(see §4.1 triggers.X)" cross-refs and others do not (e.g. scheduled/event transitions). Cosmetic precision only. **Rec**: optional — add or omit cross-refs uniformly.

### Refuted (3)
- **dreaming-recalibration-vs-frozen** (INFO) — re-derivation of H1+H3 (spec silent on Dreaming rate semantics; SDK gap-filled with 0.0/0.0). Not net-new; "operational opposite" framing was an overcall.
- **sdk-docstring-biological-list-truncated** (INFO) — SDK module docstring names 4 of 8 analogs, but the parenthetical is illustrative-by-construction and the same docstring states "8 states"; correct-by-construction, self-conceded non-contradiction.
- **sal-1.4-instantaneous-vs-hourly** (INFO) — "instantaneous energy cost" in §1.4 is a defensible prose denotation of the currently-applicable hourly *rate*; no conflict with §6.1.

---

## 4. §C — Carries Reconciliation

### Still-open C21 design-Q (8) — routed to operator DESIGN-Q bundle
All re-verified OPEN in §A.3: **H1** (Sleep update_rate axis), **H3** (§5.1 single-column trust-effect redesign), **M3** (emergency-state entry only from Active), **M5** (define "dormant"; reconcile §6.2 vs SDK partition — *now also surfaced in sister doc via B15*), **M7** (ontology absence), **L4** (Estivation 10% < Sleep 15% ordering), **L5** (Rest "queued" vs SDK refuse — *now compounded by SDK internal comment/code mismatch B11*), **L7** (wake-penalty state coverage). None self-resolved.

### Cluster trackers
- **Subordinate-ontology cluster** (M7): ledger records this cluster at **7 audits** (carry-NEW-A bundle, BC-C23-3). C21-M7 (`web4:MetabolicState` + 8 instances + transition/dormancy/energy predicates) remains a member; re-confirmed absent from `web4-core-ontology.ttl` / `t3v3-ontology.ttl` via loose-pattern sweep. **No autonomous TTL drafting** (operator-engagement-flagged).
- **snake/camel cluster** (4 audits): no new metabolic instance found in §B.

### New C54 design-Q / cross-track additions (route to ledger)
- **DESIGN-Q (new)**: B5 (§4.3 monitored-state set / Estivation-unfireable), B6 (§6.1 `Society_Size` + baseline units), B7 (§6.2 penalty constants), B8 (§7 Estivation security + `threat_score` integrity), B9 (Dreaming premature-exit transition), B14 (§1.4 MUST-vs-SHOULD normative strength).
- **CROSS-TRACK SDK (new — the #250 mirror-drift cluster)**: B1 (Hibernation trigger string + new_citizen path), B3 (energy_cost "Daily" docstring), B4 (Torpor "alert bonus" description), B11 (`accepts_new_citizens` comment/code). These four are mechanical SDK edits a future SDK-track pass should apply together; all are remediation-introduced.
- **CROSS-TRACK sister-doc (new)**: B14 (SOCIETY_SPEC §1.4), B15 (SAL §3.6 dormant list) — introduced by this file's M1 remediation; couple to the C55 remediation of THIS audit.
- **AUTONOMOUS-ACTIONABLE for C55 (spec-internal)**: B2 (§2.4 prose), B10 (§7.2 hibernation-wake bullet), B12 (dead-man term), B13 (§10 wording), B16 (§3.1 cross-ref). These are the mechanical spec edits the next alternation turn can apply without operator design input.

---

## 5. §D — Method Notes

1. **#252 guilty-until-verified → INNOCENT (date-only).** Per policy note #2 I treated the #252 footprint as a regression suspect. `git show 252e77bd -- <file>` proved the only change was the I1 date bump. This is the *correct negative result* — the same #252 that produced the C50 flagship was benign here, demonstrating the regression-suspicion method does not manufacture findings.

2. **The real regression surface was the MIRRORS the remediation didn't touch, not the edited lines.** §A's 8/8-HELD verdict on the target's edited lines was accurate, yet #250 still introduced a drift cluster (B1/B3/B4/B14/B15) by updating spec text and leaving SDK strings + sister-doc paragraphs stale. **Lesson (memory-worthy): a delta re-audit's §A "HELD" check must extend to every artifact the remediation mirrored INTO or FROM — SDK transition/description strings, sibling-doc paragraphs, docstrings — not just the audited file's own diff hunks.** This is the SDK/sister-doc analog of the C50 "+58-line remediations warrant a mirror sweep" lesson, generalized: *one-sided remediation of a two-sided invariant is the dominant residual-defect mode.*

3. **Lens de-duplication: 24 verifier-confirmed → 16 distinct.** Multiple lenses independently re-derived the same root: dead-man term (×2 → B12), SDK Hibernation trigger (×2 → B1), SDK "daily" label (×2, actually one SDK site → B3), §4.3 sentinel coverage (×3: sleep/estivation/torpor → B5), §6.1 economics (×2 → B6), Estivation security (×2 → B8), §3.6 sister-doc (×2 → B15), §10 wording (×3 → B13). The C52 §D lesson (pin routed §A candidates to one lens) was honored for §A; the §B over-derivation here was *cross-lens convergence on un-pinned fresh surfaces*, which is acceptable (independent convergence raises confidence) but inflates raw counts — **report distinct-after-dedup as the headline, raw as provenance.**

4. **Loose-pattern absence sweeps run** (C52 §D / C17-INFO1 lesson): `dead-man` (1 hit, L373), `threat_score` (4 hits), `Society_Size`/`society size` (formula-only, undefined), `metabolic` in ontology TTLs (0 → M7 absence confirmed). No `\b`-blindspot absence claim entered the record unswept.

5. **Severity discipline / verifier downgrades held**: the verifier downgraded `deadman-switch-orphan` LOW→INFO (overcalled "inverse mechanism") and refuted 3 candidates as re-derivations/overcalls — refute-by-default working as intended. 0 HIGH is the honest result: this is a mature, well-remediated spec whose residual defects are mirror-lag and under-specification, not correctness breaks.

---

## 6. Conclusion

C54 is the first delta re-audit of `SOCIETY_METABOLIC_STATES.md` (oldest never-delta'd core-spec file; prior C21).
- **§A**: 8/8 remediated C21 findings HELD, 0 regressed *in the target file*; 8/8 deferred design-Q still open. **#252 regression check INNOCENT (date-bump only)** — contrast C50.
- **§B**: 27 raw → 24 confirmed → **16 distinct (0 HIGH / 5 MEDIUM / 8 LOW / 3 INFO)**. **Flagship: the #250 remediation introduced a one-sided mirror-drift cluster** (B1/B3/B4/B14/B15) — spec edited, SDK strings + sister-doc paragraphs left stale — plus genuine under-specification findings around the §4.3 sentinel monitored-set (Estivation transition unfireable, B5), §6.1 cost-formula units (B6), and §7 Estivation/threat_score security (B8).
- **§C**: 8 C21 design-Q carried; subordinate-ontology cluster (7 audits) unchanged; 6 new DESIGN-Q + 4 SDK cross-track + 2 sister-doc cross-track + 5 spec-autonomous routed for C55.
- Next: **C55 remediation** applies the 5 spec-autonomous findings (B2, B10, B12, B13, B16); SDK and sister-doc cross-track items route to their tracks; DESIGN-Q to the operator bundle.

---

*Audit produced under Autonomous Session Protocol v2 by legion-web4-20260614-000047 (LEAD, exit #186). Read-only: zero edits to web4-standard/ or SDK source; this audit document is the only write. §B finder workflow: `wf_1109813b-386` (35 agents, refute-by-default).*
