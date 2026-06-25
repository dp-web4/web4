# C96 — SOCIETY_METABOLIC_STATES.md 2nd-Delta Re-Audit (C21→C54→C55→C96)

**Audit ID**: C96
**Date**: 2026-06-25
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (445 lines, v1.0.0, "Proposed Standard")
**Lineage**: C21 first-pass (2026-05-29, 16 findings) → C54 first-delta (2026-06-14, 16 distinct findings) → C55 remediation (PR #326, `a504ea41`, applied 5 autonomous) → **C96 (this, 2nd delta)**
**Cadence**: C-series round-robin delta re-audit. Rotation reached SOCIETY_METABOLIC_STATES (oldest last-audited file at C54/C55, 2026-06-14) after the C95 dictionary remediation slot was a no-op (C94 found 0 autonomous defects).
**Auditor session**: legion-web4-20260625-000010 (LEAD)
**Out of scope**: spec source edits, SDK edits, sister-doc edits (this is the AUDIT turn; remediation is the next alternation = C97). Sister-doc/SDK finding-generation is cross-reference reads only.

---

## 1. Methodology

Standard C-series 2nd-delta re-audit. **Target is FROZEN** — the file's only change since C54 is the C55 remediation (`a504ea41`, 11 days ago); the corpus delta is essentially dry (no spec/SDK/test-vector/sister-doc edit touched metabolic concepts since 2026-06-14). This is the **third consecutive frozen target** (after C92 SOCIETY_SPEC and C94 dictionary), so the method leans, per [[feedback_cross_doc_carry_inbound]] and the C92/C94 frozen-target guidance, on the **corpus-delta surface** (what MOVED) and **inbound sibling carries** rather than re-deriving findings on mature twice-audited text.

- **§A — Prior-finding verification**: re-verify all 5 C55 remediations (B2/B10/B12/B13/B16) HELD + introduced no regression, re-reading the C55 commit claims token-by-token vs canonical (C56 remediation-completeness lesson). Re-verify the still-open carries: 8 C21 design-Q + 6 C54 DESIGN-Q + 4 SDK cross-track (B1/B3/B4/B11) + 2 sister-doc cross-track (B14/B15). #-regression sweep on `a504ea41`.
- **§B — Fresh findings**: 3-lens finder workflow proportionate to a frozen target — (1) corpus-delta compliance (mcp-C77 taxonomy, atp-adp-C79 slashing/demurrage carve-out, #384 Act.kind/requires_council), (2) fresh-eyes spec-internal, (3) cross-doc example-DATA divergence + inbound-carry sweep. Each refute-by-default; full C21+C54 exclusion list supplied so finders surface only net-new. Clean-frozen-result-stands.
- **§C — Carries**: reconcile against the standing ledger.
- **§D — Method notes**.

Severity: HIGH / MEDIUM / LOW / INFO. Disposition: AUTONOMOUS-ACTIONABLE / DESIGN-Q / CROSS-TRACK.

### Anchor authorities consulted
| Anchor | Path |
|---|---|
| Spec target | `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` |
| SDK canonical | `web4-standard/implementation/sdk/web4/metabolic.py` |
| Test vector | `web4-standard/test-vectors/metabolic/society-metabolic-states.json` (12 vectors) |
| Corpus delta | `atp-adp-cycle.md` (C79 §3.3 + §7.1 MUST#5), `mcp-protocol.md` (C77 entity_type taxonomy), `referenced-acts.md` + `web4-core/src/act.rs` (#384), `entity-types.md` §2.1 |
| Sister specs | `SOCIETY_SPECIFICATION.md` §1.4, `web4-society-authority-law.md` §3.6 |
| Sibling interval audits | `docs/audits/C58-society-authority-law-audit-2026-06-15.md`, `C92-society-specification-2nd-delta-2026-06-24.md`, `C94-dictionary-entities-2nd-delta-2026-06-24.md` |

---

## 2. §A — Prior-Finding Verification

### A.1 C55 remediations (5 autonomous, PR #326) — held/regressed?

| C54 ID | Finding | C55 remediation | C96 disposition |
|---|---|---|---|
| **B2** (LOW) | §2.4 Hibernation wake bullet stale after M8 updated §3.1/§4.1 only | §2.4 `L91` → "Wake requires external witness, new-citizen trigger, or 90-day timeout (see §3.1)" | **HELD** — present verbatim; now agrees with §3.1 `L184` + §4.1 `L229`. (Minor cosmetic: §2.4 hyphenates "new-citizen", §3.1/§4.1 use `new_citizen` config key — prose-vs-key, not a defect.) |
| **B10** (LOW) | §7.2 #1 "Sleep Deprivation Attack" too narrow; omits hibernation `new_citizen` DoS | §7.2 #1 `L382` → "Wake-Trigger Flooding (incl. Sleep Deprivation)"; mitigation generalized to rate-limit/ATP-bond all cheap wake triggers incl. hibernation `new_citizen` | **HELD** — present; cites §3.1 + §4.1 `triggers.hibernation.wake_on`. *(See §C: SAL-side C58-B10 now frames the same `new_citizen` event as a defer-vs-wake DESIGN-Q.)* |
| **B12** (INFO) | §7.1 orphan term "Dead-man switch" | §7.1 `L373` → "Sentinel heartbeat + timeout wake (§2.4, §4.3)" | **HELD** — present; matches body mechanism (§2.4 `L86`, §4.3). |
| **B13** (INFO) | §10 conformance wording imprecisions (reliability soft, numeric/boolean conflation, molting-not-exercised loose) | §10 `L441` rewritten: §5.2 reliability under MUST-equal clause, numeric (energy/wake/reliability) vs boolean (transition-matrix membership) split, `molt_success_rate`-as-§5.2-input clarified | **HELD + re-verified accurate** — fresh-eyes lens recomputed all 12 vectors against §6.1/§6.2/§5.2; every §10 claim (12 vectors, 3+3+4+2 categories, named states, 6-of-8 driven) matches ground truth. |
| **B16** (INFO) | §3.1 transition cross-ref citation asymmetry | §3.1 added 2 missing-but-backed refs (Sleep→Hibernation `triggers.hibernation.condition` `L182`; Torpor→Active `triggers.torpor.recovery` `L186`); schedule/event transitions stay uncited per §4.1 exclusion | **HELD** — both refs present; uniformity rule ("cite iff a §4.1 key backs it") consistently applied. |

**5/5 C55 remediations HELD. 0 REGRESSED.** C55 was a +6/−6 single-file intra-doc precision edit; like C51 (which introduced 0 defects), it introduced **0** — consistent with the small-surgical-remediation profile. No remediation-introduced regression.

### A.2 #-Regression sweep
- **`a504ea41` (#326, C55 remediation)** — clean. `git show` confirms edits confined to the 5 autonomous findings, one file, no collateral. The C55 PR body's "Out of scope" list correctly enumerated the deferred SDK (B1/B3/B4/B11) and sister-doc (B14/B15) cross-track items — none were silently touched.
- No post-C55 commit touched the target (frozen).

### A.3 Still-open carries — re-verified

**SDK cross-track (4) — ALL STILL STALE** (never routed to an SDK-track pass; `metabolic.py` unchanged since 2026-04-17):
| ID | Site | State |
|---|---|---|
| **B1** | `metabolic.py:147` `Transition(HIBERNATION, ACTIVE, "external witness or timeout")` | **STILL STALE** — omits `new_citizen` + 90-day; spec §3.1 `L184` now richer. |
| **B3** | `metabolic.py:207` docstring "Daily ATP Cost = …" | **STILL STALE** — spec §6.1 `L341` now "Hourly". |
| **B4** | `metabolic.py:110` `description="Frozen + alert bonus"` | **STILL STALE** — spec §5.1 `L299` now "Frozen"; SDK is lone carrier of the phantom string. |
| **B11** | `metabolic.py:412` comment "Rest: queued" but `return state == ACTIVE` (False for Rest) | **STILL STALE** — internal comment/code mismatch atop C21-L5. |

**Sister-doc cross-track (2) — ALL STILL OPEN:**
| ID | Site | State |
|---|---|---|
| **B14** | `SOCIETY_SPECIFICATION.md:89` "MUST also conform" vs metabolic Status "Proposed Standard" + §10 SHOULD | **STILL OPEN** — confirmed C92 (SOCIETY_SPEC 2nd-delta, #383) did **not** touch §1.4; normative-strength escalation persists. |
| **B15** | `web4-society-authority-law.md:140` dormant list (Sleep/Hibernation/Torpor/Estivation) omits Rest, which SDK `DORMANT_STATES` includes | **STILL OPEN** — and now **dual-anchored** by SAL audit C58-B9 (same divergence, SAL-side). |

**C21 design-Q (8) — ALL STILL OPEN**: H1 (Sleep update_rate axis), H3 (§5.1 single-column trust-effect redesign), M3 (emergency-state entry only from Active), M5 (define "dormant"), **M7** (`web4:MetabolicState` absent from ontology — re-confirmed below), L4 (Estivation 10% < Sleep 15% ordering), L5 (Rest "queued" vs SDK refuse), L7 (§6.2 wake-penalty state coverage). None self-resolved.

**C54 design-Q (6) — ALL STILL OPEN**: B5 (§4.3 sentinel monitored-set / Estivation-unfireable), B6 (§6.1 `Society_Size` undefined + baseline units), B7 (§6.2 penalty constants), B8 (§7 Estivation security + `threat_score` integrity), B9 (Dreaming premature-exit transition), B14-normative-strength. None self-resolved.

**M7 ontology absence — re-confirmed via loose-pattern sweep (C54 §D lesson).** `grep -i metabolic web4-standard/ontology/*.ttl` now returns 2 hits in `web4-core-ontology.ttl` (`L85`, `L179`) — but both are the **adjective "metabolic"** in `rdfs:comment` strings describing the *ATP/ADP cycle* ("ATP/ADP metabolic exchange", "Part of the ATP/ADP metabolic cycle"), pre-existing since `a37f3011`. There is **no `web4:MetabolicState` class, no 8 state instances, no transition/dormancy/energy predicates**. M7 absence HOLDS — the 2 hits are a `\b`-blindspot that the sweep correctly disambiguated as unrelated (avoids a false "M7 resolved" overcall). Subordinate-ontology cluster (7 audits) unchanged; **no autonomous TTL drafting** (operator-engagement-flagged).

---

## 3. §B — Fresh Findings

**Workflow**: 3 finder lenses, each refute-by-default, full C21+C54 exclusion list supplied. **Result: 0 NET-NEW AUTONOMOUS DEFECTS on the frozen target** — the expected, honest frozen-target outcome (third consecutive, after C92/C94). Two off-target enrichments surfaced (both route to sibling tracks, not the frozen target). All claims independently re-verified by the auditor against live files.

### Lens 1 — corpus-delta compliance: CLEAN (0 conflicts) + 1 INFO enrichment
- **mcp-C77 entity_type taxonomy** — N/A. The target declares no `entity_type`; its only LCT reference is the opaque `society_lct: "lct-society-example-001"` (§4.1 `L216`). "metabolic" is a *state name*, never an entity type; **Society** is the recognized entity type (entity-types.md §2.1). No surface to conflict. (Contrast C94, where the dictionary target's `"dictionary"` entity_type *was* a compliance surface.)
- **#384 Act.kind / requires_council** — REFUTED. #384 added `referenced-acts.md` + modified `act.rs`; touched neither metabolic nor SOCIETY_SPEC. `referenced-acts.md` §7 is dispositive: an Act "composes with — and does not replace — the society-lifecycle event enumeration of SOCIETY_SPECIFICATION.md §4.2.1." A metabolic transition (§3.2: ledger-record + witness-notify + checkpoint + LCT-metadata) **is** a society-lifecycle event, not an Act; `requires_council()` is per-society charter policy, not type law imposed on metabolic. No Act-wrapping required.
- **atp-adp-C79 demurrage/slashing carve-out** — **INFO enrichment C96-E1** (route atp-adp-side, NOT a target finding). atp-adp-cycle.md §7.1 MUST #5 (`L620`) = "Discharging MUST occur through R6 transactions". The C79-added §3.3 R6-scoping note (`L323-331`) carves out *time-triggered maintenance* discharge (demurrage, slashing) from MUST #5: "MUST #5 scopes *value-spending* discharge, while demurrage is a *maintenance* discharge." Metabolic §6.1's hourly presence cost (`L341`, "maintaining presence") is a **time-triggered maintenance discharge** — it falls squarely on the **carve-out side**, so the C79 delta *resolves* a latent metabolic↔atp-adp tension (compliant-by-carve-out) rather than creating one. Metabolic §6.1 is effectively an **unnamed third member of the demurrage/slashing maintenance-discharge family**. Naming it belongs in atp-adp-cycle.md §3.3 (or a §6.1 forward-pointer), not in the frozen target. *(Directly parallels C94, where atp-adp-C79's carve-out hardened a standing dictionary finding — same delta now touches metabolic.)*

### Lens 2 — fresh-eyes spec-internal: CLEAN
All 8 state multipliers agree across §2.x Energy-Cost lines / §4.1 `state_multipliers` / §10. All 12 test vectors recompute correctly (§6.1: 1000/2400/40; §6.2: 5.0/90.0/50.0; §5.2: 1.0/0.0). §10 conformance claims exact against ground truth (category breakdown, named states, 6-of-8 driven, `molt_success_rate` nuance). §3.1 transition graph: all 8 states reachable, all have ≥1 exit, no orphan/sink. Sketch-code clean beyond the already-known undefined-identifier INFO cluster. All internal §-cross-refs resolve. 3 candidates refuted as overcalls or re-derivations of C54-B6/known INFO.

### Lens 3 — cross-doc example-DATA divergence + inbound carries: CLEAN + 1 carry double-anchor
- **Shared-data diff**: 8 state names+ordering IDENTICAL across SOCIETY_SPEC §1.4 / SAL §3.6 / SDK enum. Energy multipliers EXACT (byte-for-byte) across §4.1 / SDK / test vectors. `baseline_cost "100 ATP/hour"` consistent. No sibling moved a shared value after the 2026-06-14 cutoff. The only live divergences (B14, B15) are pre-recorded and fixable sibling-side.
- **Inbound carries**: C92 (SOCIETY_SPEC 2nd-delta) atp-cycle+metabolic finder lens returned **EMPTY**; its B14 is unrelated (citizenship revocability). C94 mentions metabolic only for rotation order. **C58 (SAL audit, 2026-06-15) — NEW double-anchor**: C58-B9 (LOW) = the SAL-side echo of C54-B15 (DORMANT_STATES⊇REST vs SAL §3.6 4-state list); **C58-B10 (MED design-q)** elevates the metabolic-side B2/B10 remediation into a genuine cross-doc semantic conflict — a `new_citizen` request to a Hibernating society **DEFERS** per SAL §3.6 `L141` ("dormant states SHOULD defer citizenship") but **WAKES** per metabolic §3.1 `L184`/§4.1 `L229` (`wake_on: ["new_citizen", …]`). Which semantic wins is unresolved. See §C.

---

## 4. §C — Carries Reconciliation

### Standing carries — all STAND (frozen target → verbatim)
- **C21 design-Q (8)**: H1, H3, M3, M5, M7, L4, L5, L7 — all re-verified OPEN.
- **C54 design-Q (6)**: B5, B6, B7, B8, B9, B14-normative-strength — all re-verified OPEN.
- **C54 SDK cross-track (4)**: B1, B3, B4, B11 — all STILL STALE in `metabolic.py` (no SDK-track pass applied them; bundle for a future SDK audit).
- **C54 sister-doc cross-track (2)**: B14 (SOCIETY_SPEC §1.4 MUST-vs-SHOULD), B15 (SAL §3.6 dormant omits Rest) — both OPEN.
- **Subordinate-ontology cluster (7 audits)**: M7 member re-confirmed absent. No autonomous TTL drafting (operator-flagged).

### New / elevated at C96
- **C96-E1 (INFO, cross-track → atp-adp-cycle.md)**: metabolic §6.1 hourly maintenance cost = unnamed third member of the atp-adp §3.3 demurrage/slashing maintenance-discharge carve-out; compliant-by-carve-out. Fix (if any) is a one-line atp-adp §3.3 enumeration or §6.1 forward-pointer — atp-adp-side, not the frozen target.
- **C96-C58-link (DESIGN-Q double-anchor)**: C54-B10 (metabolic side: `new_citizen` is a hibernation wake trigger) and **C58-B10** (SAL side: dormant states SHOULD *defer* citizenship) are two views of one open question — **does a new-citizen request to a hibernating society defer or wake?** Now anchored from both docs; route as a single operator DESIGN-Q (couples to M5 "define dormant" + B15). C58-B9 = SAL-side dual-anchor of C54-B15 (DORMANT_STATES membership).

**None of these gate a normal AUDIT turn.** All route to the standing operator DESIGN-Q bundle / SDK-track / atp-adp-track. Surface as part of the one-decision memo when the operator is available.

---

## 5. §D — Method Notes

1. **Third consecutive frozen target → pattern fully confirmed.** C92 (SOCIETY_SPEC), C94 (dictionary), C96 (metabolic) all hit files unchanged since their prior remediation, all found 0 autonomous defects. The round-robin is in steady state: **files churn slower than the audit cadence, so wraps increasingly land on frozen targets.** For these, §A is a verification exercise (all remediations HELD, all carries STAND) and §B's yield is entirely on the corpus-delta/inbound-carry surface — exactly where the 3-lens method was pointed. A maximal finder sweep on the frozen text would only manufacture findings; the proportionate 3-lens pass is the right instrument.

2. **The corpus-delta surface paid off twice — both off-target.** (a) atp-adp-C79's carve-out *resolved* a latent metabolic §6.1 R6-discharge tension (C96-E1) — the same C79 delta that hardened a dictionary finding at C94, demonstrating that one well-placed normative addition (the §3.3 maintenance-discharge carve-out) propagates clarifications across multiple frozen siblings. (b) The SAL audit C58 had already, from its own side, recorded the metabolic↔SAL `new_citizen` defer-vs-wake conflict (C58-B10) as a design-q. **Lesson: reading the *sibling's* interval audit docs ([[feedback_cross_doc_carry_inbound]]) surfaces cross-doc design tensions that the frozen target's own re-audit cannot see — the conflict is only visible from the doc that moved.** C54-B10 (one-sided, metabolic view) is now correctly a two-sided design-q via C58-B10.

3. **M7 `\b`-blindspot disambiguated, not assumed.** The ontology grep went 0→2 hits since C54; the loose-pattern sweep (C54 §D / C17-INFO1 lesson) correctly identified both as ATP/ADP-cycle adjective usage, NOT a `web4:MetabolicState` class — avoiding a false "M7 resolved" overcall. Absence claims stay swept.

4. **Severity discipline held.** 0 HIGH is the honest result for a mature twice-remediated spec; finders refute-by-default surfaced 0 net-new autonomous; the 2 enrichments are correctly INFO/DESIGN-Q and route off-target. No finding manufactured to fill the turn (per policy-review non-blocking guidance + C94 precedent).

---

## 6. Conclusion

C96 is the **2nd delta re-audit** of `SOCIETY_METABOLIC_STATES.md` (lineage C21→C54→C55→C96). The target is **frozen** since the C55 remediation (11 days).
- **§A**: **5/5 C55 remediations HELD, 0 regressed**; #326 #-sweep clean (0 defects introduced — like C51). All standing carries STAND: 8 C21 design-Q + 6 C54 design-Q + 4 SDK cross-track (B1/B3/B4/B11, still stale) + 2 sister-doc cross-track (B14/B15) all OPEN; M7 ontology absence re-confirmed via disambiguated loose-pattern sweep.
- **§B**: 3-lens refute-by-default → **0 net-new autonomous defects** (positive frozen-target result, third consecutive after C92/C94). Off-target enrichments: **C96-E1** (metabolic §6.1 = unnamed member of atp-adp §3.3 maintenance-discharge carve-out, compliant-by-carve-out, route atp-adp-side) and the **C58-B10 double-anchor** (new-citizen defer-vs-wake elevated to a two-sided DESIGN-Q).
- **§C**: all carries reconciled; 1 new INFO + 1 elevated design-q, none gate a normal turn.
- Next: **C97 remediation slot for metabolic = NO-OP** (0 autonomous to apply, like C95 dictionary). Rotation advances to next-oldest = **SAL** (`web4-society-authority-law.md`, last audited C58/C59, 2026-06-15) for its 2nd-delta (≈C98).

---

*Audit produced under Autonomous Session Protocol v2 by legion-web4-20260625-000010 (LEAD). Read-only: zero edits to web4-standard/ or SDK source; this audit document is the only write. §B finder workflow: 3 lenses, refute-by-default, full C21+C54 exclusion list.*
