# C42 Audit: `t3-v3-tensors.md` Delta Re-Audit

**Date**: 2026-06-09
**Auditor**: Autonomous session (Legion, web4 track) — exit #170, AUDIT turn
**Document**: `web4-standard/core-spec/t3-v3-tensors.md` (583 lines, dated 2026-05-24)
**Prior pass**: C13 — `docs/audits/t3-v3-tensors-internal-consistency-2026-05-24.md` (11 findings: H1–H3, M1–M4, L1–L4)
**Methodology**: Delta re-audit via multi-agent **refute-by-default WORKFLOW** (1 carry-verifier + 6 dimension finders → adversarial verification, default-to-refute). 36 agents.
**Reference materials**: SDK `implementation/sdk/web4/trust.py` (1072L), ontology `ontology/t3v3-ontology.ttl` (167L) + `ontology/t3v3.jsonld` (38L) + `ontology/web4-core-ontology.ttl`, test vectors `test-vectors/t3v3/tensor-operations.json` (305L; t3v3-001…015), sibling spec `mrh-tensors.md` §5 (the X4 carry), `atp-adp-cycle.md`, `multi-device-lct-binding.md` §4.4.

---

## Summary

| | Count |
|---|---|
| **§A** C13 carries verified | 11 (8 HELD-REMEDIATED, 3 PARTIAL, 0 STILL-OPEN, **0 REGRESSED**) |
| **§B** raw candidate findings | 29 |
| §B surviving (CONFIRMED or DEFLATED) | 27 |
| §B REFUTED | 2 |
| §B clean-bill no-defect verifications | 7 |
| §B actionable defects | 20 |

**§B actionable-defect severity**: 2 MEDIUM / 9 LOW / 9 INFO = **20 actionable**. Of these, **~12 are autonomous-actionable** inside `t3-v3-tensors.md` alone; the rest are operator DESIGN-Qs or cross-doc (mrh-side) fixes.

The file is in **very good health** — among the most-remediated targets in the C-series, second only to C35/mcp. The C13 pass (the 2026-05-17/05-24 editorial passes) closed 8 of 11 findings cleanly, with **zero regressions** — extending the clean streak seen in C40 and standing in contrast to the [[feedback_remediation_introduced_regression]] pattern of C36/C38. The 3 PARTIALs are by-design: M2/L3 were covered structurally rather than by the literal C13 recommendation, and M4 is a genuine operator DESIGN-Q the spec now discloses in-line. New findings cluster into three themes: (1) a **systemic ontology-vocabulary divergence** (predicates/role-IRIs used in examples but undefined in the canonical ontology — the same D1 theme as C40, consolidated below); (2) the **X4 canonical-home question** (role-contextual T3/V3 material duplicated between this spec §5 and `mrh-tensors.md` §5); and (3) a cluster of **§10.2 traceability nits** (citations pointing at sections that motivate but do not state the parameter — already disclaimed by the table's own "Related context" preamble, so mostly LOW/INFO).

---

## §A — C13 Carry Verification

| C13 ID | Title | Status | Evidence (current file) |
|--------|-------|--------|-------------------------|
| **H1** | §9.2 SPARQL — T3 composite weights SWAPPED | **HELD-REMEDIATED** | L462 `BIND((?t * 0.4 + ?tr * 0.3 + ?tm * 0.3) AS ?trust)` — talent=0.4/training=0.3/temperament=0.3, matching §10.2 L531, SDK `T3_WEIGHTS`, and t3v3-001. The swap is fixed. |
| **H2** | §10.2 "Diminishing returns" cites §7.1 — formula not defined there | **HELD-REMEDIATED** | Resolved via approach (2)/(b): column renamed "Related context" (L529) + new preamble (L522–527) declares "This table is the normative source … the authoritative values are those stated in this table." §7.1 still lacks the formula prose, but the cite is now explicitly non-authoritative. (Residual nit tracked as §B-F13.) |
| **H3** | §10.2 formulas with "—" spec reference | **HELD-REMEDIATED** | L538 (6D→3D) and L540 (operational health) still show "—", but preamble L525–527 closes the ambiguity: "Where a parameter has no related context ('—'), the table row and its corresponding test vector constitute the complete normative definition." Approach (b). |
| **M1** | §10.2 cites §2.3 for T3 update formula — §2.3 had different mechanism | **HELD-REMEDIATED** | Two-sided fix. §2.3 now adds "Continuous Quality-Formula Updates" (L94–106) defining `delta = 0.02 × (quality − 0.5)` + factors talent=1.0/training=0.8/temperament=0.6 — the exact values §10.2 L533–534 reference. Citation is now accurate. |
| **M2** | §10.2 cites §3.3 for V3 composite weights — §3.3 defines dimension formulas only | **PARTIAL (by-design)** | §3.3 (L253–261) still gives only per-dimension formulas + "weighted averages based on recency and significance"; the explicit 0.3/0.35/0.35 weights are NOT in §3.3. M2's literal recommendation (add weights to §3.3) not applied — covered instead by the table-is-normative preamble path. Residual tracked as §B-F12/F14. |
| **M3** | Ontology domain gap — V3Tensor binding properties undefined | **HELD-REMEDIATED** | Adopted option (c): §5.2 note (L341–346) states V3 derives entity-role context from the co-located T3Tensor rather than carrying independent `web4:entity`/`web4:role`. Consistent with TTL (`web4:entity`/`web4:role` domain `web4:T3Tensor` only, L65–73). Verified by §B-F6. |
| **M4** | §3.1 Valuation "can exceed 1.0" — SDK clamps to [0,1] | **PARTIAL (operator DESIGN-Q)** | L186 still "Range: Variable (can exceed 1.0)"; added "Open question (C13/M4)" note (L191–198) documents the 3-way divergence (spec+ontology vs SDK-clamp vs vector). SDK `trust.py` L288–291 still clamps. Divergence persists **by design** pending operator decision. Carried as the standing M4 DESIGN-Q. |
| **L1** | §2.2 redundant `role_tensors`/`contextual` blocks | **HELD-REMEDIATED** | §2.2 (L42–77) now has only `role_tensors` + `evolution`; the parallel `contextual` subset block is removed (option a). |
| **L2** | §2.3 conflates two update mechanisms | **HELD-REMEDIATED** | §2.3 L102–106 adds the explanatory paragraph distinguishing the outcome table (categorical) from the quality formula (continuous), "complementary — implementations MAY use either or both." Exactly L2's recommendation. |
| **L3** | Test vector t3v3-010 "coherence" naming tension | **PARTIAL (spec-side done; vector unchanged)** | Spec-side fixed: §10.2 L540 adds the inline note clarifying this is NOT identity coherence C×S×Phi×R. BUT the vector itself (`tensor-operations.json` t3v3-010, L182–198) still uses `operation:"coherence"`/`"coherence":0.71` with no clarifying note. Cross-doc residual (vector + SDK reader), tracked as §B-F10. |
| **L4** | §10.2 ATP conservation §7.1 imprecise | **HELD-REMEDIATED** | L541 now cites "atp-adp-cycle.md §6.3 + §7.1" (was §7.1 alone), L4's option (b). (Minor anchor-precision residual: the named invariant lives in atp-adp §2.4 — tracked as §B-F19, INFO.) |

**Carry verdict: 8 HELD-REMEDIATED, 3 PARTIAL (M2 by-design, M4 operator-DESIGN-Q, L3 cross-doc), 0 STILL-OPEN, 0 REGRESSED.**

---

## §B — New Findings

Severities are post-adversarial-verification. AUTO = remediable inside `t3-v3-tensors.md` alone at C43.

### MEDIUM

#### F3 (MEDIUM, DESIGN-Q) — `web4:matchesTask` used in §9.2 SPARQL but undefined in the entire ontology corpus
**Lines**: 455–459. §9.2: `?tensor web4:entity ?entity ; web4:role ?role ; web4:matchesTask ?taskType .` Corpus-wide grep for `matchesTask` returns exactly one file — `t3-v3-tensors.md` itself. It is in NEITHER `t3v3-ontology.ttl`, `web4-core-ontology.ttl`, NOR `t3v3.jsonld`: no class/property/domain/range anywhere. Every *other* property in the same query is defined (`web4:entity`, `web4:role`, `web4:talent/training/temperament`), making `matchesTask` the lone undefined term — an isolated, actionable gap, not indistinguishable mass.
**Disposition**: Consolidated into **D1 (ontology-vocabulary)** below. Autonomous-in-spec interim available (annotate the example as illustrative / non-canonical prefix); the durable fix is an operator/ontology decision (add `web4:matchesTask` to the protected `web4-core-ontology.ttl`, or rewrite the example).

#### F17 (MEDIUM, DESIGN-Q) — X4 canonical-home: role-contextual T3/V3 material duplicated across this spec and `mrh-tensors.md` §5
**Lines**: this spec §1.1 (L12–14), §2.2 (L40–78), §5.2 (L311–339), §9.2 (L450–466) ↔ `mrh-tensors.md` §5 (L237–366). Three concrete duplications, independently verified:
1. **Principle restated near-verbatim**: this spec L14 "T3/V3 tensors are not absolute properties — they exist only within role contexts. An entity trusted as a surgeon has no inherent trust as a mechanic." vs mrh L243 "T3/V3 tensors are not absolute properties of entities — they only exist within the context of specific roles. A person trusted as a surgeon has no inherent trust as a mechanic."
2. **RDF role-tensor binding Turtle duplicated** (same `lct:alice web4:hasRole web4:Surgeon/Researcher` + `_:tensor a web4:T3Tensor …`).
3. **Surgeon-role T3 composite SPARQL** (`?t*0.4 + ?tr*0.3 + ?tm*0.3`) in both files.

mrh §5 **already declares the intended split** (L239: "For the full T3/V3 specification … see t3-v3-tensors.md. This section describes how T3/V3 tensors integrate with MRH context") but **does not honor it** — §5.2/§5.3 re-specify the tensor shape rather than pointing.
**Disposition**: **Operator DESIGN-Q — NOT self-resolved.** Recommended direction (per mrh §5's own pointer at L239 and the CLAUDE.md terminology table making `t3v3-ontology.ttl` + `t3-v3-tensors.md` the T3/V3 authority): **`t3-v3-tensors.md` is canonical** for the role-contextual principle, the entity-role RDF binding shape, and the composite-weight SPARQL; **mrh §5 shrinks to a pure MRH-integration pointer**, keeping only its MRH-unique residual — §5.4 `web4:RolePairing` Turtle (`subjectRole`/`objectRole`/`trustContext`/`t3Score`/`interactionType`) and the §5.3 `RoleContextualT3V3` code class (F21) — both of which are NOT duplicated. Operator must also pick the authoritative number for the diverging Surgeon example (see F18). This is the C40 X4 carry; the fix lands in `mrh-tensors.md`, not the target, so it is for an mrh re-audit/remediation, not C43.

### LOW

#### F4 (LOW, AUTO) — `web4:hasRole` used in §5.2 but defined in `web4-core-ontology.ttl`, not the two ontology files the spec header names
**Lines**: 3–4 (header names only `t3v3-ontology.ttl` + `t3v3.jsonld`), 313–314 (`lct:alice web4:hasRole web4:Surgeon`). `web4:hasRole` has zero matches in both named files; it is defined only in `web4-core-ontology.ttl:134`. Also absent from the `t3v3.jsonld` `@context`, so a JSON-LD processor using that context alone would not resolve `hasRole`. **Fix**: add a one-line pointer near §5.2 (or the header) noting `web4:hasRole` is defined in `web4-core-ontology.ttl` — load both. No ontology edit.

#### F5 (LOW, AUTO) — Turtle examples use `lct:`/`xsd:`/`rdfs:` prefixes without declaring them; `lct:` IRI lives only in the JSON-LD context
**Lines**: 128–162 (§2.4 declares only `web4:`/`analytics:` yet uses `lct:`/`xsd:`/`rdfs:`), 311–337 (§5.2 Turtle declares NO `@prefix` lines at all). As written these snippets are not standalone-parseable. The canonical `lct:` IRI (`https://web4.io/lct/`) is defined only in `t3v3.jsonld`; `t3v3-ontology.ttl` never declares `lct:`. **Fix**: add `@prefix lct:`/`xsd:`/`rdfs:` declarations to the two Turtle fences (IRIs already canonical in the JSON-LD/ontology). Spec-internal only.

#### F8 (LOW, DESIGN-Q) — role IRIs minted in the core `web4:` namespace (`web4:DataAnalyst`, `web4:Surgeon`, `web4:Mechanic`, …) are undeclared instances/classes
**Lines**: 47–58, 288, 313–328. `web4:role` has `rdfs:range rdfs:Resource` (TTL L70–73), so these are **not** domain violations, but minting application/society-defined roles under the reserved `web4:` core namespace implies they are core-ontology terms when they are not (none declared in any ontology file). Consistent corpus-wide pattern (mrh §5 too). **Disposition**: namespace-governance DESIGN-Q — couples to the X4 canonical-home and the standing role-naming/Policy-Entity-casing carries. Autonomous interim: switch examples to a non-core illustrative prefix (e.g. `ex:DataAnalyst`) with a note that roles are application/society-defined.

#### F12 (LOW, AUTO) — §10.2 "V3 composite weights" row cites §3.3, but §3.3 states no composite weights
**Lines**: 532 (cites §3.3); §3.3 = 253–261. The values (0.3/0.35/0.35) are correct (match SDK `V3_WEIGHTS` and t3v3-002) — this is purely a broken intra-doc cross-reference, against a column the preamble already disclaims as non-authoritative. The parallel T3 row (L531→§9.2) *does* resolve to a literal formula, so the V3 pointer fails the standard the table sets for itself. **Fix**: minimal honest fix — set Related context to "—" (like the 6D-bridge/operational-health rows), OR add the 0.3/0.35/0.35 composite weights to §3.3. (§3.3 IS correctly cited by the separate "V3 calculation" row, L539.)

#### F13 (LOW, AUTO) — §10.2 "Diminishing returns formula" row cites §7.1, but §7.1 has no formula or constants
**Lines**: 537 (cites §7.1); §7.1 = 388–392. §7.1 contains only the bullet "Exponential decay on repeated similar actions" — no `base_factor^(n−1)`, base=0.8, or floor=0.1. The formula IS anchored in the cited test vector t3v3-007, so it is not orphaned (the "no normative home" framing was deflated). **Fix**: set Related context to "—", OR add `factor = max(base_factor^(n−1), floor)` (base=0.8, floor=0.1) to §7.1 — preferred, to give floor=0.1 a body home, mirroring how §2.3 hosts the T3 update formula.

#### F18 (LOW, X4-coupled) — numeric divergence in the duplicated Surgeon T3 example: training 0.92 (this spec §5.2) vs 0.90 (mrh §5.2)
**Lines**: 316–321. Same `lct:alice`/`web4:Surgeon`, identical talent (0.95) and temperament (0.88), but training diverges. **Within `t3-v3-tensors.md` the example is already internally consistent** (0.92 also in §5.1 candidate_evaluation L297–301), so no autonomous edit in the target; the mrh-side 0.90 is the outlier to reconcile when X4 is resolved. **Do not self-change this spec's 0.92.**

#### F22 (LOW, AUTO) — §6.3 Role-Based Segregation uses hard normative constraints with zero RFC-2119 keywords
**Lines**: 380–384. Four bare declaratives ("No global trust scores…", "Each role maintains separate…", "New roles start with minimal trust, not inherited", "Cross-role trust transfer requires explicit bridging") — these are the document's central §1.1 principle and are SDK-enforced, yet unlike sibling §6.1 (three MUSTs) and §6.2 (SHOULD/MUST/SHOULD) they carry no keyword. **Fix**: add RFC-2119 keywords to each bullet (e.g. "Implementations MUST NOT compute global (role-agnostic) trust scores"; "Each role MUST maintain separate T3/V3 tensors"; etc.).

#### F23 (LOW, partial-AUTO) — §10.2 includes a T3 value-range row but omits the V3 value range, despite SDK clamping V3 identically
**Lines**: 536, 186–198. SDK `V3.__post_init__` (L288–291) clamps valuation/veracity/validity to [0,1] exactly as T3; §3.1 states Veracity/Validity as [0,1]. The table is silent on V3, so a reader cannot tell from §10 alone that Veracity/Validity are protocol-invariant. **Fix (partial-autonomous)**: add a V3 value-range entry for **Veracity and Validity** ([0,1], t3v3-002/t3v3-014). **Valuation cannot be added autonomously** — it is the unresolved M4 3-way divergence; note in §10.2 that V3-Valuation range classification is pending per the §3.1 open question.

#### F24 (LOW, AUTO) — §10.1 maps Society-configurable tier to "MAY" alone, but §10.3 contains SHOULD obligations
**Lines**: 510–514, 555, 557. §10.3 carries "Societies SHOULD implement demurrage" (L555) and "rates SHOULD be transparent" (L557) — faithful to atp-adp §7.2, so the source is fine, but the §10.1 keyword column over-simplifies. **Fix**: relax the §10.1 Society-configurable RFC-2119 column to "MAY / SHOULD", or add a one-line note that society-configurable parameters may carry SHOULD recommendations for adoption/transparency.

### INFO

#### F2 (INFO, AUTO) — §8.2 `compute_team_trust` pseudocode diverges from SDK name and no-qualified-member return
**Lines**: 417–428. Spec names `compute_team_trust` returning sentinel `NO_TRUST`; SDK is `compute_team_t3` returning `None`. Illustrative pseudocode (uses undefined helpers), so a doc/naming mismatch, not a numeric divergence; equal-weight mean semantics match t3v3-015. **Fix (optional)**: align names to the SDK and note it returns `None` (not a sentinel) when no member holds the role; or add a pointer to the SDK function.

#### F7 (INFO, AUTO) — §2.2/§3.2/§5.1 JSON shapes (`role_tensors`, `aggregate`, `by_context`, …) have no ontology mapping
**Lines**: 42–77, 214–251, 285–307. The blocks are fenced ` ```json ` (not json-ld), carry no `@context`/`@type`, and are presented as illustrative data structures distinct from the §5.2 Turtle — so this is expected, not a defect (the "claims ontology backing" framing was deflated). **Fix (optional)**: add a one-line clarifier that these JSON blocks are illustrative application-level serializations, NOT JSON-LD bound to `t3v3.jsonld`.

#### F14 (INFO, AUTO) — V3 composite weights have no in-body literal home (asymmetric with T3 weights in §9.2)
**Lines**: 531–532; cf. 462. T3 weights appear literally in §9.2's BIND; V3 weights appear only in §10.2. By the table's own architecture both have a complete normative home (row + test vector), so "no normative home" was refuted — the residue is editorial asymmetry. Couples to F12. **Fix (optional)**: add a V3 analogue (short §3.3 sentence or a V3 BIND) so both §10.2 rows have literal body referents.

#### F15 (INFO, AUTO) — §10.2 intro over-lists "§6" as a synthesis source
**Lines**: 503–506. The intro names §2.3, §3.3, and §6, but no §10.2/§10.3/§10.4 row cites §6 (the closest, the T3 value-range row, cites §2.1). (The headline claim that §3.3 is over-promised was refuted — §3.3 genuinely supplies the V3-calculation normative decision.) **Fix (optional)**: drop or qualify the bare "§6" mention.

#### F16 (INFO, AUTO) — §10.2 "T3 value range … clamped at boundaries" cites §2.1, which states ranges but not clamping
**Lines**: 536; §2.1 = 20–38. §2.1 says "Range: 0.0 to 1.0" but never "clamped"; clamping is defined by t3v3-005/006 and SDK `_clamp`. Partially-accurate citation. **Fix (optional)**: add a one-line note in §2.1 that out-of-range updates are clamped to [0,1].

#### F19 (INFO, AUTO-optional) — §10.2 ATP-conservation anchor "§6.3 + §7.1" is imprecise; the named invariant lives in atp-adp §2.4
**Lines**: 541. §7.1 anchors the two-state premise and §6.3 the "preserving total supply" half, but the named invariant `initial == final + fees` is stated in atp-adp §2.4, which neither anchor cites. Compound-claim citation that is partial, not wrong. **Fix (optional, single-cell)**: change to "§2.4 + §6.3" or add §2.4.

#### F1 (INFO, M4-coupled) — §5.3 `calculate_atp_price` `(1 + v3.valuation)` multiplier assumes unbounded Valuation
**Lines**: 352–366. Real but fully subsumed by the already-disclosed M4 Valuation-range open question (the multiplier is bounded to [1,2] under a clamping SDK). No new defect. **Disposition**: resolves with the M4 operator decision — no autonomous edit.

#### F21 (INFO, X4 scoping) — `mrh §5.3 RoleContextualT3V3` and §5.4 `web4:RolePairing` are mrh-unique, not duplicated
**Lines**: mrh §5 (L272–329), no counterpart here. Confirms the X4 duplication is **partial/asymmetric**: principle + Turtle + Surgeon-SPARQL are duplicated, but this code class and the RolePairing Turtle are the legitimate MRH-integration residual that should survive when mrh §5 shrinks to a pointer. Informs the F17 scoping. No edit.

#### F25 (INFO, M4-coupled) — §3.1 Valuation headline (L186) asserts the range as settled while the adjacent note (L191–198) marks it unresolved
**Lines**: 186, 191–198. The open-question blockquote is directly below the bullets, so skimming-reader risk is minimal. **Fix (optional, operator-gated)**: soften L186 to "Range: Variable — see open question below" so the headline does not present an unresolved value as canonical.

### Clean-bill no-defect verifications (positive PASS records)

- **F6** (§5.2 V3 entity/role note is CONSISTENT with the current TTL — keep; optionally also mention `web4:hasV3Tensor` as the canonical entity→V3 path).
- **F9** (§10.2 protocol-invariant table — **all 11 rows verified** against test vectors AND SDK constants: T3/V3 weights, update formula+factors, no-decay, ranges, diminishing returns, 6D→3D bridge, V3 calc, operational health, ATP conservation; all identical).
- **F10** (the "coherence" label correctly documented in §10.2; the only residual is the unchanged vector label = L3 cross-doc).
- **F11** (t3v3-008 secondary-weight precision: spec carries the exact `0.4/3`; only the vector's display string rounds to 0.1333 — reconciles within tolerance).
- **F20** (§10.3/§10.4 cross-refs to atp-adp §6.3/§7.2/§7.3 and multi-device §4.4 — all eight resolve correctly).
- **F26** (§10.2 MUST-scoped table contains no SHOULD/MAY leakage; all values consistent with SDK/ontology/vectors).
- **F27** (heading hierarchy + preamble structure clean; internal anchor `#24-fractal-sub-dimensions` resolves).

### REFUTED (2)

- SPARQL aggregate/composite shorthand examples "assume shorthand that breaks" — refuted; the shorthand `web4:talent/training/temperament` is canonically defined and the queries are well-formed.
- §10.1 Simulation-only tier keyword "N/A" "understates the MUST NOT obligation" — refuted; §10.4 prose carries the MUST NOT explicitly, and "N/A" correctly marks the tier as non-RFC-2119-governed.

---

## §C — Consolidated operator DESIGN-Q (per [[feedback_cross_cutting_consolidation_audit]])

### D1 — ontology-vocabulary divergence (shared with C40 carry-C40-design-Q)
The spec's illustrative Turtle/SPARQL use terms that are undefined or namespace-questionable in the canonical ontology. Resolve **per-term**: extend the (protected) ontology vs rewrite the example.
- **`web4:matchesTask`** (F3) — used in §9.2, defined nowhere in the corpus. Genuine ontology gap.
- **role IRIs in the core `web4:` namespace** (F8) — `web4:Surgeon`/`web4:DataAnalyst`/… undeclared; namespace-governance question (couples to the standing role-naming / Policy-Entity-casing carries).
- (Already-correct, no action: `web4:hasRole`, `web4:entity/role` domains, shorthand dimensions, `web4:hasDimensionScore` — all defined; F4/F5 are spec-internal pointer/prefix fixes, not ontology changes.)

This is the **same D1 theme** flagged at C40 for `mrh-tensors.md` — fold into the single standing operator DESIGN-Q bundle rather than scattering.

### D2 — X4 canonical home (F17/F18/F21)
Decide the canonical home for role-contextual T3/V3 material duplicated between `t3-v3-tensors.md` §5 and `mrh-tensors.md` §5, and which Surgeon-example numbers are authoritative (0.92 vs 0.90). Recommended direction recorded in F17 (this spec canonical; mrh §5 → pointer keeping §5.4 RolePairing + §5.3 code class). **Fix lands in `mrh-tensors.md`** — surface at the next mrh re-audit/remediation, not C43.

### D3 — M4 Valuation range (carried from C13)
The 3-way divergence (spec+ontology "can exceed 1.0" vs SDK clamp vs vector [0,1]) remains the standing operator decision. Couples F1, F23-Valuation, F25.

---

## Disposition for C43 (next REMEDIATION turn)

**Autonomous-actionable inside `t3-v3-tensors.md`** (apply at C43): F4, F5, F12, F13, F22, F24 (LOW) + F2, F7, F14, F15, F16, F19 (INFO) + F23-partial (Veracity/Validity range row only). ~13 edits, all spec-internal (no `.ttl`, no SDK, no vectors, no date bump beyond the edited-file convention).

**Deferred (operator DESIGN-Q / cross-doc)**: D1 (F3 ontology gap, F8 namespace), D2 (X4 — F17/F18/F21, mrh-side), D3 (M4 — F1/F23-Valuation/F25). L3 vector "coherence" rename + t3v3-010 (cross-doc, SDK reader). The C13→C42 cycle for `t3-v3-tensors.md` is otherwise in excellent health with zero regressions.
