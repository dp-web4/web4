# C129 Audit: `mrh-tensors.md` Third Delta Re-Audit

**Date**: 2026-07-02
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn (alternation following C128 presence-protocol remediation #439)
**Document**: `web4-standard/core-spec/mrh-tensors.md` (420 lines; **byte-frozen since C91 remediation `f0c82118`**, 2026-06-24 — `git diff f0c82118 HEAD` empty across the file)
**Lineage**: C10 (`mrh-tensors-internal-consistency-2026-05-23.md`, 9 findings) → C40 (`C40-mrh-tensors-audit-2026-06-09.md`, 12 F + D1–D4 + X1–X4) → C41 remediation (#290 `ab1aec64`) → C90 2nd-delta (#381 `4ab09b7a`) → C91 remediation (#382 `f0c82118`, applied N1(b)/N2/N3) → **C129** (this 3rd delta)
**Method**: §A holds-check (C10 + C40 carries + C90 findings + C91 applied fixes + standing D1/D4/X4/N4) + §B fresh 3-finder refute-by-default pass (internal/SDK-fidelity ∥ cross-section/vocab/numeric ∥ **inbound cross-reference surface**) + lead objective checks (link resolution, byte-freeze, composite arithmetic). Advisory from policy review applied: snapshot-presence guard on the t3-v3 cross-ref (cite the moved hunk); git-provenance check net-new prose against C91^ before calling anything a standing defect.
**Reference materials**: SDK `web4-standard/implementation/sdk/web4/mrh.py`; sibling `t3-v3-tensors.md` (churned since C91) + its C121 audit; the 3 NEW downstream docs that cite mrh (`docs/FRACTAL_ROLE_IDENTITY.md` #402, `rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md` #403, `rfcs/RFC-SHARED-POLICY-SUBSTRATE.md` #419); rdflib 7.6.0 for SPARQL/Turtle parse checks.

---

## Summary

| | Count |
|---|---|
| **§A** C10 carries | 9 (8 HELD-REMEDIATED, 1 STILL-OPEN-INFO by design, **0 REGRESSED**) |
| **§A** C40 F-findings | 12 (12/12 HELD-REMEDIATED, **0 REGRESSED**) |
| **§A** C91 applied fixes | 3/3 HELD (N1(b) training=0.92, N2 ASK query, N3 maximal guard); **CLEAN remediation, 0 regression** |
| **§A** standing carries | D1 STILL-OPEN, D4 STILL-OPEN, X4/N1(a) STILL-OPEN (structural shrink), N4 STILL-OPEN (folds into D1) |
| **§B** raw candidate findings | ~19 across 3 finders |
| §B CONFIRMED **new mrh defects** | **0** (first fully-clean mrh delta by the contradiction/fidelity lens) |
| §B cross-track observations | 2 (O1, O2 — both citing-doc / DESIGN-Q-context, neither fixable in mrh) |
| §B REFUTED / acknowledged / engine-artifact | ~17 |

**Verdict: `mrh-tensors.md` is in good health and byte-stable.** The C91 remediation held with **zero regressions** — a clean remediation (contrast the C121/C123 pattern where a prior remediation's own new prose over-reached; here C91's 3 edits are verified correct and self-consistent). The high-risk cross-doc N1(b) contradiction (`web4:training` 0.90→0.92) **stays closed on both sides** post-t3-v3 churn. No net-new mrh-side defect surfaced under the internal, SDK-fidelity, cross-section, vocabulary, numeric, or inbound-cross-reference lenses. The two recorded items are **cross-track** (defects in / risks for *other* files) and are routed, not self-applied.

---

## §A — Carry & Fix Verification

### C91 applied fixes (3/3 HELD, 0 regressed)

| C91 item | Sev | Current state | Status |
|----------|-----|---------------|--------|
| **N1(b)** §5.2 `web4:training 0.90 → 0.92` (cross-doc numeric contradiction) | MED | mrh **L262** = `web4:training 0.92`. t3-v3 Alice-Surgeon T3 binding = `0.92` at **L407** (mirrored L166/L375/L379), UNCHANGED by the only t3-v3 delta since C91. **Contradiction closed on both sides.** | **HELD** |
| **N2** §6 query-1 unbound `?path`/`?trust` → honest `ASK` | LOW | mrh **L384-386** = `ASK { <lct:alice> (web4:hasRelationship+) <lct:bob> . }` with the SDK-side-materialization note (L377-380). Parses under rdflib. | **HELD** |
| **N3** §4.2 `maximal()` empty-input guard | LOW | mrh **L228-231** = `max((… for path in paths), default=0.0)` + docstring "(0.0 if no paths, matching SDK propagate_maximal)". Empirically: empty→0.0, matches SDK `propagate_maximal`. | **HELD** |

**Per-fix-site regression scan**: all 3 C91 edit sites re-read token-by-token; no partial correction, broken adjacent claim, or new internal contradiction. **C91 is a CLEAN remediation.**

### C10 carries (9) & C40 F-findings (12)

All verified HELD-REMEDIATED (re-confirmed at C90, re-spot-checked here against the frozen bytes): C10 H1/M1/M2/M3/M4/L1/L3/L4 held; **C10-L2** (unnumbered preamble L5/L14/L18 before §1 @L27) **STILL-OPEN INFO by design** (C41 declined the demotion; no normative dependency; unchanged). C40 F1–F12 all held (F1 §4.2 `combined=0.0` L220 ✓; F5 §3.3 FILTER-removed structural note L155-160 ✓; F8 `MRHEdge` weight-clamp/str-coerce note L64-71 ✓; F10 §4.2 divergence note L198-206 ✓; remainder unchanged since C90's per-site scan). **0 regressions.**

### Standing carries — status unchanged, correctly still escalated

- **X4 / N1(a) (operator DESIGN-Q)** — structural shrink of mrh §5 (L240-369) to a pure MRH-integration pointer, keeping only the mrh-unique residual (§5.4 `web4:RolePairing` Turtle + §5.3 `RoleContextualT3V3` class). Recommended 3× (C40-X4, C42-F17, C82-D2). **STILL-OPEN.** See §B-O2 — new inbound line-anchors materially raise its cost.
- **D1 (operator DESIGN-Q)** — consolidated ontology-vocabulary divergence (undefined illustrative predicates). Unchanged.
- **D4 (operator DESIGN-Q)** — `horizon_depth = 3` (spec L174) vs SDK `MRH_MAX_HOPS = 4` + SELF/DIRECT/INDIRECT/PERIPHERAL/BEYOND zone taxonomy living only in code. Unchanged.
- **N4 (folds into D1)** — `web4:t3Score` (§5.4/§5.5) vs `web4:trustScore` (§6 L395) predicate-naming split. Unchanged.

### Lead objective checks

- **Byte-freeze**: `git diff f0c82118 HEAD -- web4-standard/core-spec/mrh-tensors.md` empty. Confirmed frozen.
- **§7 reference links (L413-418)**: all 7 targets resolve from the doc's location (`MRH_RDF_SPECIFICATION.md`, `mrh_rdf_implementation.py`, `mrh_sparql_queries.py`, `mrh_trust_propagation.py`, `mrh_visualizer.py`, SDK `mrh.py`, `t3v3-ontology.ttl`). C40-L4 remediation (SDK-module-first) held.
- **Composite arithmetic (§5.2/§5.4/§5.5)**: `0.95×0.4 + 0.92×0.3 + 0.88×0.3 = 0.380+0.276+0.264 = 0.920` — exactly the `web4:t3Score 0.92` claimed at L323. Internally consistent.

---

## §B — New Findings

**Zero confirmed net-new mrh-side defects.** Three finders (internal/SDK-fidelity, cross-section/vocab/numeric, inbound cross-reference) each returned no mrh defect after refute-by-default. This is the **first fully-clean mrh delta** — C90 still had the N1 flagship + N2/N3 live; C129 clears the board on the mrh side.

Two items recorded — both **cross-track**, neither a defect in `mrh-tensors.md`:

### O1 (LOW, cross-track — citing-doc defect, NOT mrh) — `FRACTAL_ROLE_IDENTITY.md:53` mis-anchors "default depth 3"
`FRACTAL_ROLE_IDENTITY.md:53` cites `mrh-tensors.md:143` for the parenthetical **"default depth 3"**, but mrh **L143** is the Markov-property topic sentence (*"The 'Markov' in MRH means that beyond a certain graph traversal depth…"*); the literal `Default horizon_depth = 3` statement is at mrh **L174** (and "Depth 3+" at L139). The anchor is off by ~31 lines for the specific claim. (RFC-COMPOSITE `:143` at L97 is defensible — it cites the horizon-depth *concept*, which L143 does concern.) **Defect in the citing doc; out of mrh's scope.** Route: note to whoever owns `FRACTAL_ROLE_IDENTITY.md` (repoint to `:174` or a section anchor).

### O2 (LOW, cross-track — hardens the X4 DESIGN-Q) — inbound raw-line anchors raise the §5-shrink cost
Three new downstream docs now cite mrh by **raw line number**: `:246` ×6 (FRACTAL ×1, RFC-COMPOSITE ×4, RFC-SHARED ×1 — all for the "T3/V3 not absolute / only within role context" axiom, which correctly resolves to mrh L246) and `:143` ×2. **L246 sits *inside* §5 (L240-369).** Consequently the deferred **X4/N1(a) §5-shrink — or any line insertion above L246 — silently breaks all six `:246` citations.** The structural change is now more expensive/riskier than at C91: it requires a coordinated cross-track update of 3 downstream docs, ideally migrating them from raw line numbers to section/anchor citations first. **This is context for the standing X4 operator DESIGN-Q, not an mrh defect.** Recommendation to fold into the X4 decision: (a) before any §5 shrink, migrate the 8 inbound anchors to section references; (b) more broadly, raw-line-number cross-references into spec files are a fragility class — the corpus would benefit from a convention favoring section/heading anchors.

**Note (healthy signal):** all three new docs *point to* mrh (pointer = healthy) and do **not** duplicate §5's owned role-contextual numeric material; RFC-COMPOSITE explicitly defers aggregation normativity to `t3-v3-tensors.md §8.2`. No new cross-doc duplication or contradiction was introduced by the sibling churn. mrh contains **zero** back-references to the 3 new docs (expected — it predates them; no cyclic/stale back-ref).

---

## §B — Refuted / acknowledged / engine-artifact (default-to-refute upheld)

| Candidate | Disposition |
|-----------|-------------|
| t3-v3 churn touched the Alice-Surgeon example / training value | **REFUTED** — only change since C91 is the ATP-conservation cross-ref row (t3-v3 L640, `§6.3`→`§3.1/§3.2…§2.4…§6.3`); orthogonal, does not touch §5 or any training value. Snapshot-guard: shared surface untouched. |
| Any C91 fix regressed | **REFUTED** — 3/3 held; per-site re-read clean. |
| §4.2 propagation math diverges from SDK | **REFUTED** — multiplicative byte-identical; noisy-OR / maximal empirically agree with SDK on empty & non-empty inputs. List[float]/dropped-decay divergences are the acknowledged ones (L198-206). |
| §5.3 `RoleContextualT3V3` fidelity defect | **REFUTED** — no SDK counterpart; illustrative, as acknowledged. |
| Any of 7 SPARQL / 4 Turtle blocks malformed | **REFUTED** — all parse under rdflib 7.6.0; no unbound projected vars, no PREFIX gaps. |
| §6-b `HAVING (?avg_trust > 0.8)` returns nothing | **ENGINE ARTIFACT** — rdflib decimal-vs-double quirk; query is SPARQL-1.1 correct (as at C90). |
| §1.2 "12-member enum" (L64) miscount | **REFUTED** — §2.1 enumerates exactly 12 (3 top + 3 binding + 3 pairing + 3 witness); matches SDK `RelationType` (12 members). |
| Alice composite 0.92 vs Mechanic pairing2 t3Score 0.15 mismatch | **REFUTED** — different role pairings (Mechanic-self vs CarOwner→garage); standalone illustrative values, not required to match. |
| §5.5 L340 `?trustScore` (BIND var) ≡ §6 L395 `web4:trustScore` (predicate) | **REFUTED** — L340 is a locally-bound query variable, not a predicate; distinct from the N4/D1 predicate-naming carry. |
| `mrh:246` / `mrh:143` inbound citations stale | **RESOLVES-CLEAN for :246** (exact, ×6+×… all land on L246); **:143 imprecise only in FRACTAL's "default depth 3" claim** → O1 (citing-doc). |
| §3.2 "Depth 3+" (L139) vs §3.3 "= 3" (L174) | **DEFLATED (INFO, unchanged)** — conceptual tier vs literal default; no new angle. |

---

## Disposition for C130 (paired remediation)

- **Apply autonomous**: **none.** No net-new mrh-side defect; the file is byte-stable and healthy. C130 has **no autonomous mrh edit to make** from this audit. (If C130 lands as the next remediation turn with an empty mrh worklist, it should confirm "nothing to apply — C129 clean" rather than invent work.)
- **Route cross-track (do NOT self-apply)**:
  - **O1** → owner of `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md`: repoint `:143`→`:174` (or a section anchor) for the "default depth 3" claim.
  - **O2** → fold into the standing **X4/N1(a)** operator DESIGN-Q: the §5-shrink now requires a coordinated migration of 8 inbound raw-line anchors (6×`:246`, 2×`:143`) to section references first; consider a corpus-wide "prefer section anchors over raw line numbers for cross-file citations" convention.
- **Defer — operator DESIGN-Q (unchanged bundle)**: **X4/N1(a)** structural §5-shrink (now +O2 cost context); **D1** ontology-vocabulary (N4 folds in — pick `t3Score` or define `trustScore`); **D4** `horizon_depth=3` vs `MRH_MAX_HOPS=4` + zone taxonomy.
- **No date bump**: `mrh-tensors.md` carries no date/version banner; audit-only turn, nothing to stamp.

---

## §D — Method Notes

1. **A frozen file's *inbound* surface can grow even when the file cannot.** mrh is byte-stable, yet three docs authored since C91 created **8 new raw-line dependencies** on it. The 3rd-delta yield was entirely on that inbound surface (per the standing "frozen ≠ done; §B yield is on what MOVED" pattern) — here what moved was *other files pointing in*, not the target or a shared example value. A delta audit of a frozen file must enumerate **new inbound citations**, not just outbound cross-refs and shared example-DATA (the C90 lesson). The natural tool: `git grep -l "<filename>"` over docs changed in the interval.
2. **Raw-line-number cross-references are a latent fragility class.** Six downstream `:246` anchors now sit *inside* the very §5 block that a 3×-recommended DESIGN-Q wants to shrink — so a deferred, sensible structural improvement has quietly acquired a breaking-change cost. Line-anchors couple a citing doc to a target's *layout*, not its *content*; they rot on any insertion above the anchor. Worth a corpus convention (section/heading anchors).
3. **A clean remediation verifies clean here (contrast C121/C123).** C91's 3 edits were re-read against `f0c82118^` provenance and against the SDK/canonical they claim to mirror — all correct, no over-reach. This *breaks* the recent C121/C123 pattern where the frozen file's non-cleanness was itself remediation-introduced. Not every prior remediation over-reaches; the git-provenance + re-test-against-canonical discipline is what distinguishes the two, and must be run either way rather than assumed.

---

*C129 verdict: file in good health, byte-stable since C91; C91 held with zero regressions (clean remediation); N1(b) cross-doc contradiction stays closed on both sides post-t3-v3 churn; first fully-clean mrh delta by the contradiction/fidelity lens. Zero autonomous items for C130. Two cross-track records (O1 FRACTAL citation imprecision; O2 inbound line-anchors harden the X4 §5-shrink DESIGN-Q). Standing D1/D4/X4/N4 correctly still escalated.*
