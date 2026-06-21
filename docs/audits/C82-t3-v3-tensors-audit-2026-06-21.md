# C82 Audit: `t3-v3-tensors.md` Second Delta Re-Audit

**Date**: 2026-06-21
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn, slot `120009`
**Document**: `web4-standard/core-spec/t3-v3-tensors.md` (626 lines)
**Prior passes**: C13 (`docs/audits/t3-v3-tensors-internal-consistency-2026-05-24.md`, 11 findings) → C42 (`docs/audits/C42-t3-v3-tensors-audit-2026-06-09.md`, first delta, 20 actionable) → **C43 remediation** (PR #299, 13 autonomous edits applied).
**Methodology**: Second delta re-audit. §A = C42/C13 carry verification + **C43 remediation-completeness** (token-by-token against canonical sources, per the [[feedback_remediation_introduced_regression]] / C56–C64 lessons) + **bidirectional re-verification** of the 3 deferred operator DESIGN-Qs against the current corpus. §B = fresh finder pass (refute-by-default), 2 parallel finder agents + auditor adversarial hand-verification of every load-bearing new claim. Special charge: deliver an explicit **verdict on the C80 multi-device HELD items N1/N2** (flat-8 `t3_tensor` vs canonical-3-root + no entity-role binding), which were flagged as needing "t3-v3 + ontology coordination."
**Reference materials** (all cross-checks hand-verified): SDK `implementation/sdk/web4/trust.py`, ontology `ontology/t3v3-ontology.ttl` + `ontology/t3v3.jsonld` + `ontology/web4-core-ontology.ttl`, test vectors `test-vectors/t3v3/tensor-operations.json` (t3v3-001…015), sibling specs `mrh-tensors.md` §5, `atp-adp-cycle.md` §2.4/§6.3/§7, `multi-device-lct-binding.md` §2.3/§4.1/§4.4.

---

## Summary

| | Count |
|---|---|
| **§A** C42/C13 carries verified | 11 (all HELD; 8 remediated, 3 by-design partials) — **0 regressed** |
| **§A** C43 remediation edits checked | 13/13 PRESENT and SDK/vector-accurate |
| **§B** new findings surviving verification | 6 (0 HIGH / 1 MEDIUM / 3 LOW / 2 INFO) |
| **§B** refuted at verification | several (listed) |
| Deferred DESIGN-Q re-verification | D1 STILL-OPEN · D2 STILL-OPEN (numeric divergence HARDENED) · D3 STILL-OPEN |

**Health verdict**: `t3-v3-tensors.md` remains in **very good health** — among the most-remediated, most-internally-coherent core-spec documents. All 11 prior carries hold with **zero regression**, and all 13 C43 edits are present and numerically correct against the SDK/vectors. The new findings are minor. The single notable structural result is the **N1/N2 verdict** (§C-D2 below): the multi-device flat-8 divergence is a **consumer-side defect** (in `multi-device-lct-binding.md`), **but** it exposes a genuine **owner-side documentation gap** in this file — the 6D→3D trust bridge (the actual reconciliation mechanism) is documented only as an opaque one-row table entry with no body prose, and the fractal §2.4 never names the real in-corpus extension dimensions. A second, milder theme: **three of the six new findings (F2/F3/F4) trace to prose C43 itself added** — a mild instance of the remediation-introduced-imprecision pattern (§D).

---

## §A — Carry Verification + C43 Remediation Completeness

### A.1 — C42/C13 carries (all 11 re-verified in current file)

All 11 C13 findings were verified HELD-REMEDIATED or by-design-PARTIAL at C42, and **none has regressed** in the current file:
- **H1** (T3 composite weights) — L498 `?t*0.4 + ?tr*0.3 + ?tm*0.3` matches SDK `T3_WEIGHTS` + t3v3-001. HELD.
- **H2/H3** (§10.2 "Related context" non-authoritative preamble) — L558–563 intact. HELD.
- **M1** (§2.3 continuous quality formula `0.02×(quality−0.5)` + factors 1.0/0.8/0.6) — L110–111 matches SDK `T3_UPDATE_RATE`/`T3_UPDATE_FACTORS`. HELD.
- **M2** (by-design: table-is-normative path) — intact; see F3 below for a residual.
- **M3** (V3 entity-role note §5.2 L372–377) — consistent with TTL (`web4:entity`/`web4:role` domain `T3Tensor` only). HELD.
- **M4** (Valuation range) — PARTIAL, standing DESIGN-Q D3 (still open, §C-D3).
- **L1/L2** (§2.2 redundancy removed; §2.3 two-mechanism paragraph) — HELD.
- **L3** (t3v3-010 "coherence" label) — spec-side fixed (L577 note); **vector unchanged** (cross-doc residual, still open).
- **L4** (ATP conservation anchor) — see F2: C43 applied F19's "§2.4 + §6.3" but the §2.4 anchor is imprecise (slashing section). HELD-with-residual.

### A.2 — C43 remediation completeness (13/13 verified present + accurate)

| C43 edit | Location | Verified |
|----------|----------|----------|
| F4 `web4:hasRole` provenance note | §5.2 L331–336 | ✓ accurate (`hasRole` ∈ `web4-core-ontology.ttl:134`, not the two header files) |
| F5 `@prefix` decls on Turtle | §2.4 L140–144, §5.2 L339–341 | ✓ present (note: F5-new finds SPARQL blocks still lack PREFIX — see F5 below) |
| F12+F14 V3 weights body home | §3.3 L277–281 | ✓ values 0.3/0.35/0.35 match SDK `V3_WEIGHTS` + t3v3-002 (but see F3 prose) |
| F13 diminishing-returns formula | §7.1 L420–424 | ✓ `max(0.8^(n−1), 0.1)` matches SDK `DIMINISHING_BASE/FLOOR` + t3v3-007 |
| F22 RFC-2119 on §6.3 | L412–415 | ✓ four MUST/MUST NOT keywords present |
| F24 §10.1 Society-configurable MAY→MAY/SHOULD | L549 | ✓ present |
| F23-partial V3 range row (Veracity/Validity only) | §10.2 L573 + note L580–583 | ✓ Valuation correctly withheld pending M4 (but see F4 vector cite) |
| F2 §8.2 `compute_team_t3`/`None` SDK-align | L452–463 | ✓ matches SDK signature + `return None` |
| F7 illustrative-JSON clarifier | L85–89 | ✓ present |
| F15 drop bare §6 from §10.2 intro | L538–542 | ✓ now names §2.3/§3.3/atp-adp/multi-device, no bare §6 |
| F16 §2.1 clamp note | L22–25 | ✓ present |
| F19 ATP-conservation anchor §2.4 + §6.3 | L578 | ✓ present (but anchor imprecise — see F2) |

**Carry verdict: 11/11 HELD (0 regressed); 13/13 C43 edits present and numerically accurate.** The three residuals (F2/F3/F4) are NOT regressions of prior findings — they are *new imprecisions in the prose C43 added*, surfaced for the first time at this delta.

---

## §B — New Findings (post-adversarial-verification)

### MEDIUM

#### F1 (LOW→MEDIUM boundary, CROSS-TRACK) — §6.3 "New roles MUST start with minimal trust" vs SDK neutral-0.5 default
**Lines**: 414. §6.3 states "New roles MUST start with minimal trust, not inherited from other roles." The SDK returns the **neutral midpoint** `T3(0.5, 0.5, 0.5)` for an absent role: `get_t3` → "Returns default (0.5, 0.5, 0.5) if role not found" (`trust.py:438–440`); `T3` dataclass defaults all three dims to 0.5 (`trust.py:151–153`); `resolve_trust` reaffirms the same default (`trust.py:~1003`).
**Adversarial verification**: the **non-inheritance** half of the MUST IS satisfied — the SDK default does not copy another role's tensor. Only the **magnitude** word "minimal" diverges: 0.5 is neutral, not minimal (0.0), and "minimal trust" is undefined numerically anywhere in the file (sole occurrence, L414). So this is a *word-choice/semantics* divergence, not a structural violation — hence LOW-leaning-MEDIUM, not the MEDIUM the finder first proposed.
**Disposition**: CROSS-TRACK (needs SDK coordination). Either define "minimal trust" as a concrete bootstrap value in §6.3 and align the SDK default, OR soften L414 from "minimal" to "neutral, uninherited" (preserving the load-bearing non-inheritance clause). Not autonomous-in-file (touches SDK semantics).

### LOW

#### F2 (LOW, AUTO — remediation-residue) — §10.2 ATP-conservation anchor "§2.4" points at the *slashing* section, which frames the invariant as something slashing *escapes*
**Lines**: 578. The row reads `ATP conservation | total supply = ATP + ADP (invariant) | atp-adp-cycle.md §2.4 + §6.3 | —`. Hand-verified: atp-adp §2.4 heading is **"Slashing (ATP Destruction)"** (`atp-adp-cycle.md:170`); its only mention of the invariant is `atp-adp-cycle.md:214` — "(`initial == final + fees`), which scopes only ATP→ADP transfers — a destruction [sits outside it]." So §2.4 names the invariant *only to carve slashing out of it*, and the canonical invariant form there is `initial == final + fees` (transfer-conservation), **not** the row's "total supply = ATP + ADP." This is the C42-F19 edit C43 applied; F19's premise ("the named invariant lives in atp-adp §2.4") was itself imprecise.
**Fix (autonomous-in-file)**: re-anchor to atp-adp's actual conservation statement (§6.3 "preserving total supply", `atp-adp-cycle.md:603–604`) and either drop the §2.4 pointer or annotate it as "(slashing exception)"; optionally adopt the canonical `initial == final + fees` wording. Spec-internal cell edit.

#### F3 (LOW, AUTO — remediation-residue) — §3.3 "This mirrors the T3 composite weights" asserts a false numeric equivalence
**Lines**: 280–281 (added by C43 for F12/F14). "The composite V3 score combines the three dimensions with the protocol-invariant weights `valuation=0.3, veracity=0.35, validity=0.35` … This mirrors the T3 composite weights applied in the §9.2 SPARQL." The §9.2 SPARQL applies T3 weights **0.4/0.3/0.3** (L498) — *different* from V3's 0.3/0.35/0.35. "mirrors the … weights" literally claims they are equal. The intended meaning is "parallels the composite *structure*," not the weight values.
**Fix (autonomous-in-file)**: change "mirrors the T3 composite weights applied in" → "parallels the T3 composite *structure* (with its own weights) applied in".

#### F4 (LOW, AUTO/partial-cross-track — remediation-residue) — §10.2 V3 range row cites vectors that do not exercise clamping
**Lines**: 573 (added by C43 for F23-partial). `V3 Veracity / Validity range | [0.0, 1.0] — clamped at boundaries | §3.1 | t3v3-002, t3v3-014`. Hand-verified: t3v3-002 is a v3_composite calc (interior inputs 0.3/0.85/0.8) and t3v3-014 is a v3_calculate (interior results); **neither tests boundary clamping**. Contrast the parallel T3 range row (L572), which correctly cites the *dedicated clamp* vectors t3v3-005/t3v3-006. There is no V3-side clamp boundary vector, so "clamped at boundaries" is SDK-enforced (`V3.__post_init__`) but not vector-enforced as the row implies.
**Fix**: autonomous-in-file — soften the row to note V3 clamping is SDK-enforced without a dedicated boundary vector; OR (cross-track) add a V3 clamp test vector mirroring t3v3-005/006.

### INFO

#### F5 (INFO, AUTO) — §9.2/§9.3 SPARQL blocks use undeclared prefixes (the SPARQL analogue of C42's Turtle-prefix F5)
**Lines**: 486–502 (§9.2, no `PREFIX` at all), 510–533 (§9.3 first query declares only `PREFIX web4:` yet uses `rdfs:` at L521; second query uses `lct:alice`/`lct:bob` at L529–531 with neither `lct:` nor `rdfs:` declared). As written these are not runnable. C43 added `@prefix` to the Turtle fences (C42-F5) but left the SPARQL fences.
**Fix (autonomous-in-file)**: add the missing `PREFIX` lines, or a one-line note that SPARQL snippets assume the standard `web4:`/`lct:`/`rdfs:` prefixes.

#### F6 (INFO — N1/N2 owner-side gap, see §C-D2) — §2.4 fractal section never names the one real in-corpus protocol extension; the 6D→3D bridge has zero body prose
**Lines**: §2.4 (133–191), §10.2 6D-bridge row (575, "Related context = —", no body text). See the full N1/N2 verdict in §C-D2.

### Checked and REFUTED / clean-bill
- **Markdown anchors** `#102-…`, `#24-…`, `#92-…` all resolve to real headings. No defect.
- **§5.1 vs §5.2 Surgeon numbers** (talent 0.95 / training **0.92** / temperament 0.88; composite 0.92 = 0.95×0.4+0.92×0.3+0.88×0.3) — internally consistent, matches t3v3-013. (The 0.92-vs-0.90 divergence is *cross-doc* with mrh §5 — D2, not an in-file defect.)
- **All in-file test-vector citations** (t3v3-001/002/003/005/006/007/008/010/012/013/014) map to the correct operations/values — accurate (F4 is the lone nuance).
- **§2.3 outcome table / update formula / factors / decay-recovery rates** — all match SDK `OUTCOME_DELTAS` etc. and vectors.
- **§6.1 "MUST use ≥3 decimal places"** — no contradiction with table/SDK precision.
- **§5.2 ontology notes** (V3 entity-role; `web4:hasRole` provenance) — both accurate against the TTL.
- **§2.4/§5.2 Turtle shapes** — all properties exist with matching domains/ranges; prefixes declared. No ontology violation.

---

## §C — Consolidated operator DESIGN-Q (bidirectional re-verification)

### D1 — ontology-vocabulary divergence — **STILL-OPEN (unchanged since C42)**
- `web4:matchesTask` (§9.2 L491) — appears **exactly once corpus-wide**; no defining triple in any `.ttl`/`.jsonld`. STILL undefined.
- Role IRIs `web4:Surgeon`/`web4:DataAnalyst`/`web4:Mechanic`/`web4:ProjectManager`/`web4:Researcher` — **undeclared** as classes or individuals in any ontology file (`web4:hasRole` itself IS declared at `web4-core-ontology.ttl:134`; the role *values* are not). No change.
- Resolve **per-term**: extend the protected core ontology vs rewrite the example to a non-core illustrative prefix. Shared with the C40 mrh-side D1 theme — fold into the single standing bundle.

### D2 — X4 canonical home **+ the N1/N2 multi-device verdict** — **STILL-OPEN; numeric divergence HARDENED; new owner-side gap identified**

**X4 (mrh §5 duplication)** — STILL-OPEN. mrh-tensors.md §5 still duplicates this file's role-contextual principle (mrh `:243` ≈ t3-v3 `:14`), Surgeon Turtle (mrh `:255–269` ≈ t3-v3 `:347–359`), and composite SPARQL (mrh `:337–350` ≈ t3-v3 `:488–502`), despite mrh's own §5-opening pointer (`mrh:239`) declaring t3-v3 canonical. **The Surgeon `training` number divergence is now a confirmed cross-doc contradiction**: t3-v3 `web4:training 0.92` (`:351`, also `:319`) vs mrh `web4:training 0.90` (`mrh:259`) — same Alice-as-Surgeon. The fix lands in `mrh-tensors.md` (shrink §5 to a pointer; reconcile the number), for an mrh re-audit/remediation, not a t3-v3 C83 item.

**N1/N2 VERDICT (the C80 multi-device HELD items, charged to this audit):**

1. **Where is the defect?** In the **consumer** (`multi-device-lct-binding.md`), not the owner. t3-v3-tensors.md is the canonical T3/V3 owner (CLAUDE.md terminology table; this file's §10.2 L542 states it "synthesizes normative decisions … and `multi-device-lct-binding.md` §4.4" — i.e. t3-v3 governs). The multi-device §2.3/§4.1 `t3_tensor` is a non-conformant serialization: a flat `"dimensions"` object of 8 keys + `composite_score` with **no entity-role binding** (`multi-device:218–230`, `:850–859`), violating this file's §1.1 role-contextual principle and §6.3 "MUST NOT compute global (role-agnostic) trust scores" (L412). N1 (flat-8 vs 3-root) and N2 (no entity-role binding) are **real defects, located in the consumer.**

2. **KEY FINDING — the reconciliation mechanism already exists in the corpus.** The 6 *base* multi-device flat keys are **exactly the inputs of the canonical 6D→3D trust bridge** (hand-verified against SDK `trust_bridge(competence, reliability, consistency, alignment, witnesses, lineage)` `trust.py:526–549` and vector t3v3-008):

   | multi-device flat key | 6D bridge input | maps to |
   |---|---|---|
   | `technical_competence` | competence | talent (primary ×0.6) |
   | `social_reliability` | reliability | training (primary ×0.6) |
   | `temporal_consistency` | consistency | temperament (primary ×0.6) |
   | `context_alignment` | alignment | secondary ×(0.4/3) |
   | `witness_count` | witnesses | secondary ×(0.4/3) |
   | `lineage_depth` | lineage | secondary ×(0.4/3) |

   So those 6 keys are **pre-bridge 6D source inputs** the canonical model collapses INTO the 3 roots — not roots, not sub-dimensions. The 2 multi-device-specific keys (`hardware_binding_strength`, `constellation_coherence`) **could legitimately be declared `web4:subDimensionOf` a root** under §2.4's open-ended mechanism (`constellation_coherence` is already canonically owned by multi-device §4.4 and correctly cited by t3-v3 §10.4 L609). **None of the 8 keys is currently declared anywhere as a root or sub-dimension** — the multi-device flat block floats free of the ontology.

3. **GENUINE OWNER-SIDE GAP (F6).** t3-v3 references multi-device only for the *governance* angle (constellation_coherence as a simulation parameter, §10.4 L609), **never for the structural attach-point**. The 6D→3D bridge — the actual mechanism that reconciles a flat trust schema to the 3 roots — appears in this file **only as one opaque §10.2 table row (L575) with "Related context = —" and zero body prose**: the spec never says what the 6 source dimensions are, where they come from, or that multi-device's flat-8 is an instance of them. And §2.4 (the fractal-extension section) never names `hardware_binding_strength`/`constellation_coherence` as example sub-dimensions despite §10.4 treating the latter as canonical. The owner spec thus offers no documented path for protocol-level extensions to attach — which lets the divergence persist.

4. **Routing (split):**
   - **Operator DESIGN-Q (N1/N2 core):** decide the canonical attach-strategy for protocol-level flat trust schemas — (A) formalize the 6D→3D bridge as the documented attach path, (B) declare the 2 extension dims as `web4:subDimensionOf` sub-dimensions, or (C) both. Needs t3-v3 + ontology + multi-device coordination. Couples C19-M5 (sub-dimension ontology) and the C80 N1/N2 carries.
   - **Bounded t3-v3 C83 item (owner-side, F6, do regardless of A/B/C):** add body prose to §2.4 / §10.2 documenting the 6D→3D bridge as the canonical attach-path (currently zero prose), and add the two multi-device dimensions as named §2.4 sub-dimension examples. Independently fixable.
   - **multi-device cross-doc item (contingent on the DESIGN-Q):** rewrite §2.3/§4.1 `t3_tensor` to nest under entity-role binding (or relabel the flat object as "6D bridge inputs"). Belongs on the multi-device track, gated by the operator decision. This is the durable resolution of C80 N1/N2.

### D3 — M4 Valuation range — **STILL-OPEN (3-way divergence intact)**
- Spec §3.1 "Range: Variable (can exceed 1.0)" (L200) + open-question note (L205–212) + §10.2 deliberate omission (L580–583).
- Ontology agrees: `t3v3-ontology.ttl:90` "may exceed for value."
- SDK is the odd one out: `V3.__post_init__` `_clamp(...)` to [0,1] (`trust.py:289`, also `from_action` `:328`).
- No movement since C42. Operator semantic decision (clamp the spec/ontology, or unbound the SDK). Couples F1/F25 from C42.

---

## §D — Lessons (for [[feedback_remediation_introduced_regression]] / [[feedback_audit_workflow_adversarial_verify]])

1. **Remediation-introduced-imprecision is mild but real even on a "very good health" target.** Three of the six new findings (F2 §2.4 slashing anchor, F3 "mirrors weights" false equivalence, F4 V3-range vector citation) are imprecisions in **prose C43 itself added** — none caught at C43 write-time. The pattern: when a remediation adds *explanatory* prose (not just a value flip), the new prose makes *new claims* (a cross-ref, an equivalence, a vector citation) that need the same token-by-token verification the value edits get. Add to the standard method: **at remediation time, every newly-written explanatory sentence is itself an auditable claim — verify its cross-refs/equivalences/citations before commit.** C42-F19's own premise ("invariant lives in §2.4") propagated into C43 as a citation to the *slashing* section — a finding-premise that was imprecise at birth and rode through remediation unchecked (cf. C46-M1, C50-R1).

2. **A "byte-accurate" remediation can still be substantively imprecise.** All 13 C43 edits are PRESENT and the *values* are SDK/vector-correct (A.2) — yet 3 carry prose imprecisions. "Did the edit land + are the numbers right" is necessary but not sufficient; the surrounding sentence's *claims* are the second axis.

3. **Cross-track HELD items pointed at a canonical owner can resolve to "consumer defect + owner doc-gap," not "owner defect."** C80 framed N1/N2 as needing "t3-v3 coordination," implying an owner fix. The delta found the owner model *correct* but *under-documented* (no bridge prose, no extension examples) — so the right resolution is a small owner-side doc item PLUS a consumer rewrite, gated by an operator attach-strategy decision. When a downstream audit routes a finding "to the owner," the owner audit should test both "is the owner wrong?" and "does the owner document the path the consumer needed?" — they have different fixes.

---

## Disposition for C83 (next REMEDIATION turn for this file)

**Autonomous-actionable inside `t3-v3-tensors.md`** (apply at C83): **F2** (re-anchor ATP-conservation off the §2.4 slashing section), **F3** ("mirrors weights"→"parallels structure"), **F4** (soften V3-range vector citation), **F5** (SPARQL PREFIX decls), **F6-partial** (add 6D→3D bridge body prose to §2.4/§10.2 + name the 2 multi-device dims as §2.4 sub-dimension examples — the owner-gap half that is fixable regardless of the DESIGN-Q). ~5 spec-internal edits, no `.ttl`/SDK/vector changes.

**Deferred (operator DESIGN-Q / cross-doc)**:
- **D2 / N1/N2 core** — operator attach-strategy decision (A formalize-bridge / B declare-sub-dims / C both); then multi-device-side `t3_tensor` rewrite. Resolves C80 N1/N2.
- **D2 / X4** — mrh §5 shrink-to-pointer + reconcile Surgeon training 0.92-vs-0.90 (mrh-side, next mrh re-audit/remediation).
- **D1** — ontology-vocab (`web4:matchesTask` gap, role-IRI namespace), shared with the C40 bundle.
- **D3 / M4** — Valuation range 3-way divergence.
- **F1** — "minimal vs neutral" §6.3-vs-SDK (cross-track, SDK coordination; non-inheritance half already holds).
- **L3** — t3v3-010 vector "coherence" rename (cross-doc, SDK reader) — still open.

The C13→C42→C43→C82 cycle for `t3-v3-tensors.md` is in excellent health: zero regressions, all remediation edits accurate, only minor prose/citation residue plus the now-clarified N1/N2 structural route.
