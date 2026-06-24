# C90 Audit: `mrh-tensors.md` Second Delta Re-Audit

**Date**: 2026-06-24
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn (alternation following C89 presence-protocol remediation #380)
**Document**: `web4-standard/core-spec/mrh-tensors.md` (414 lines; byte-stable since C41 remediation `ab1aec64`, 2026-06-09)
**Lineage**: C10 (`mrh-tensors-internal-consistency-2026-05-23.md`, 9 findings) → C40 (`C40-mrh-tensors-audit-2026-06-09.md`, 12 F-findings + D1–D4 + X1–X4) → C41 remediation (#290 `ab1aec64`, applied all 12 F-findings) → **C90** (this 2nd delta)
**Method**: §A holds-check (C10 + C40 carries + standing D1/D4/X4) + §B fresh multi-agent refute-by-default audit (5 dimension finders → adversarial verification, default-to-refute), with explicit attention to (a) C41-remediation-introduced regressions per [[feedback_remediation_introduced_regression]] and (b) cross-reference drift against siblings remediated since C41: `t3-v3-tensors.md` (C42/C82/C83) and `LCT-linked-context-token.md` (C60/C61).
**Reference materials**: SDK `implementation/sdk/web4/mrh.py`, ontology `ontology/t3v3-ontology.ttl` + `web4-core-ontology.ttl`, sibling spec `t3-v3-tensors.md` + its audit docs `C42-…` / `C82-…`, test vectors `test-vectors/t3v3/tensor-operations.json` (t3v3-001/013).

---

## Summary

| | Count |
|---|---|
| **§A** C10 carries | 9 (8 HELD-REMEDIATED, 1 STILL-OPEN-INFO by design, **0 REGRESSED**) |
| **§A** C40 F-findings | 12 (12/12 HELD-REMEDIATED, **0 REGRESSED**) |
| **§A** standing carries | D1 STILL-OPEN, D4 STILL-OPEN, **X4 STILL-OPEN + HARDENED → §B-N1 flagship** |
| **§B** raw candidate findings | 14 (across 5 finders) |
| §B CONFIRMED new defects | 4 (1 MED, 3 LOW) + 2 INFO |
| §B REFUTED / engine-artifact / deflated | 8 |

The file remains in **good health** — the C41 remediation held cleanly with **zero regressions** (a third consecutive clean-streak target alongside C40/C42, contrast [[feedback_remediation_introduced_regression]]), and the high-risk cross-reference chain (`t3-v3 §9.2/§10.2` + parameter `t3v3-001` + composite weights 0.4/0.3/0.3) survived the t3-v3 C82/C83 remediation intact (triangulated across 5 sources).

**Flagship (N1):** the long-deferred **X4** carry (role-contextual T3/V3 material duplicated between mrh §5 and `t3-v3-tensors.md` §5) is no longer "resolve at C42" — **both** t3-v3 audits (C42-F17/F18/F21, C82-D2) determined the fix **lands on the mrh side** and explicitly routed it to *"the next mrh re-audit/remediation"* = **C90/C91 (now)**. C82 further **hardened** it into a confirmed cross-doc **numeric contradiction**: mrh §5.2 `web4:training 0.90` (L259) vs canonical t3-v3 `web4:training 0.92` for the same Alice-as-Surgeon example. This is the substantive output of C90.

---

## §A — Carry Verification

### C10 carries (9)

| C10 | Title | Status | Evidence (current file) |
|-----|-------|--------|--------------------------|
| H1 | §3 subsection numbering collision | **HELD-REMEDIATED** | §3.1 (L114)/§3.2 (L133)/§3.3 (L141); no collision. |
| M1 | `MRHEdge.probability`/`distance` vs SDK | **HELD-REMEDIATED** | L65 `weight`; `distance` removed, L68–71 BFS note. |
| M2 | `TrustPropagation` OOP vs SDK functions | **HELD (caveat now resolved)** | L198–206 divergence note; the "identical semantics" claim is now **true** post-F1 (probabilistic fixed). |
| M3 | §5 duplicates T3/V3 without cross-ref | **HELD-REMEDIATED** (banner) | L239 cross-ref banner present. Body trim still outstanding = X4 (see N1). |
| M4 | Inconsistent ontology cross-ref styles | **HELD-REMEDIATED** | L110 markdown link, L262 relative path. |
| L1 | Blank lines at file start | **HELD-REMEDIATED** | Title on L1. |
| L2 | Unnumbered preamble before §1 | **STILL-OPEN (INFO, by design)** | L5/L14/L18 precede §1 (L27); C41 explicitly declined the demotion (net-neutral churn, no normative dep). No change recommended. |
| L3 | SPARQL hardcodes T3 weights | **HELD-REMEDIATED + drift-verified** | L345–346 cites `t3-v3-tensors.md §9.2/§10.2 (t3v3-001)`; citation **still resolves** post-C82/C83 (see §B refuted). |
| L4 | §7 refs point to scripts not SDK | **HELD-REMEDIATED** | L406 leads with canonical SDK module. |

### C40 F-findings (12) — all HELD-REMEDIATED, 0 REGRESSED

F1 (§4.2 `combined = 0.0`, L220) ✓ algorithm now correct, matches SDK · F2 (§5.3 retitled "Trust Tensor (T3) in Code", L272) ✓ heading/intro/body agree, V3 marked undemonstrated L285 · F3+F9 (L16 prose requalified) ✓ · F4 (§2.1 `@prefix rdfs:`, L83) ✓ · F5 (§3.3 FILTER removed + structural note, L155–160) ✓ · F6 (§5.5/§6 multi-SELECT fences split, each with PREFIX) ✓ · F7 (§3.3 RDFS entailment note + property-path alternative, L147–151) ✓ valid alternation · F8 (`MRHEdge` `relation: RelationType` / `timestamp: str (ISO 8601)` / weight-clamp note, L64–71) ✓ · F10 (§4.2 note extended, L198–206) ✓ frames List[float]/decay drop as acknowledged divergence · F11 (§5.5 GROUP BY comment, L354) ✓ · F12 (§5.3 f-string in-string PREFIX, L290) ✓.

Per-fix-site adversarial regression scan (dedicated finder): **all 12 sites CLEAN — no remediation-introduced regression, partial correction, broken adjacent claim, or new internal contradiction.**

### Standing carries

- **D1 (operator DESIGN-Q, STILL-OPEN)** — consolidated ontology-vocabulary divergence (illustrative Turtle/SPARQL reference predicates undefined in the canonical ontology: `web4:hasRelationship`, `RolePairing`, `subjectRole`, `t3Score`, `interactionType`, `memberOf`, `trustScore`, reification predicates). Unchanged; not self-resolvable. N4 below folds in.
- **D4 (operator DESIGN-Q, STILL-OPEN)** — `horizon_depth = 3` (spec) vs SDK `MRH_MAX_HOPS = 4` + SELF/DIRECT/INDIRECT/PERIPHERAL/BEYOND zone taxonomy living only in code. Unchanged.
- **X4 (was "resolve at C42") — STILL-OPEN + HARDENED → promoted to §B-N1.** See flagship below. Per the policy-review note for this session, X4's "C42" tag is **stale** (C42/C82 have passed); both t3-v3 audits routed the fix back to the mrh side. It is hereby routed explicitly to **C91** (autonomous number reconciliation) + **operator DESIGN-Q** (structural shrink-to-pointer), not re-deferred.

---

## §B — New Findings

### N1 (MEDIUM, flagship) — X4 cross-doc duplication, now a confirmed numeric contradiction
**Lines**: mrh §5 (L237–366), esp. §5.2 L258–260 ↔ `t3-v3-tensors.md` §1.1/§5.2/§9.2 (`:14`, `:406–408`, `:488–502`).

The role-contextual T3/V3 material is duplicated across mrh §5 and the canonical `t3-v3-tensors.md` §5, despite mrh's own §5-opening pointer (L239: "For the full T3/V3 specification … see `t3-v3-tensors.md`. This section describes how T3/V3 tensors **integrate with** MRH context") declaring t3-v3 canonical. Three concrete duplications (verified at C42-F17, re-verified here): the role-contextual **principle** (mrh L243 ≈ t3-v3 :14), the Surgeon-role **T3 binding Turtle** (mrh L255–269 ≈ t3-v3 :400–408), and the composite-weight **SPARQL** (mrh L337–350 ≈ t3-v3 :488–502).

**The duplication is now a confirmed cross-doc contradiction** (hardened at C82-D2): the same Alice-as-Surgeon example carries **`web4:training 0.90`** in mrh §5.2 (L259) vs **`web4:training 0.92`** canonically in t3-v3 (`:407`, also `:319`, test vector `t3v3-013`). Talent (0.95) and temperament (0.88) agree; only training diverges. The mrh number even yields a different composite (0.914 vs the canonical 0.92). The mrh-side `0.90` is the outlier.

Both t3-v3 audits explicitly state the fix lands here, not in t3-v3: C42-F17 — *"the fix lands in `mrh-tensors.md`, not the target, so it is for an mrh re-audit/remediation, not C43"*; C82-D2 — *"shrink §5 to a pointer; reconcile the number … for an mrh re-audit/remediation, not a t3-v3 C83 item."* **C90 is that re-audit.**

**Routing (two parts):**
- **(a) Operator DESIGN-Q (ratify direction).** Shrink mrh §5 to a pure MRH-integration pointer: keep only the mrh-unique residual — §5.4 `web4:RolePairing` Turtle (`subjectRole`/`objectRole`/`trustContext`/`t3Score`/`interactionType`) and the §5.3 `RoleContextualT3V3` code class (both confirmed NOT duplicated, C42-F21) — and replace the duplicated principle/Turtle/SPARQL with pointers into t3-v3. This direction has now been recommended **three times** (C40-X4, C42-F17, C82-D2) and is consistent with the CLAUDE.md terminology table making `t3-v3-tensors.md` + `t3v3-ontology.ttl` the T3/V3 authority. Structural change → operator ratification, do NOT self-apply.
- **(b) Autonomous for C91 (reconcile the number).** Regardless of (a)'s timing, the `web4:training 0.90 → 0.92` reconciliation in mrh §5.2 L259 aligns mrh to the established-canonical source — a clean autonomous cross-doc-contradiction fix. (If (a) is approved and §5.2's Turtle is deleted wholesale, this folds into (a).)

### N2 (LOW) — §6 query-1 projects unbound `?path` / `?trust` (non-functional placeholder)
**Lines**: L372–380.
```sparql
SELECT ?path ?trust WHERE {
    <lct:alice> (web4:hasRelationship+) <lct:bob> .
    # Calculate trust along path
}
```
Both projected variables are **never bound** in the WHERE clause — the `+` property-path triple is a boolean existence pattern binding no intermediate nodes, so the query can only return all-NULL rows. Presented as a "Common SPARQL pattern" but computes neither a path nor a trust value (the `# Calculate trust along path` comment is an unfulfilled placeholder). Independently confirmed by two finders. Contrast every other query in the file, which binds what it projects.
**Fix** (autonomous): mark it explicitly as a skeleton (e.g. comment "existence check only — SPARQL property paths cannot bind intermediate nodes; path materialization is SDK-side, see `mrh.py`"), convert to `ASK`, or bind explicit hop variables as §3.3 does.

### N3 (LOW) — §4.2 `maximal()` lacks the SDK's empty-input guard
**Lines**: L226–228 (vs SDK `propagate_maximal`).
```python
def maximal(self, paths, decay_factor=0.7):
    return max(self.multiplicative(path, decay_factor) for path in paths)
```
On empty `paths`, `max()` raises `ValueError`; the SDK `propagate_maximal` guards `if not path_trusts: return 0.0`. The sibling `probabilistic()` already returns `0.0` on empty (matches SDK), so `maximal` is the lone un-guarded outlier — an **un-acknowledged** divergence (the L198–206 note covers the List[float]/decay-drop differences but not empty-input behavior).
**Fix** (autonomous): `return max((self.multiplicative(p, decay_factor) for p in paths), default=0.0)`, or note empty-input is undefined.

### N4 (LOW, D1-coupled, CROSS-TRACK) — §6 uses `web4:trustScore` where §5 uses `web4:t3Score`
**Lines**: L388 (`?member web4:trustScore ?trust`) vs L320/L328/L362 (`web4:t3Score`).
The persisted trust-value predicate is named two ways for the same concept; `web4:trustScore` appears only at L388 and is defined nowhere (already flagged undefined at C40-X3). The **new** angle is the in-file naming inconsistency (t3Score vs trustScore). Note: `?trustScore` at L337/346 is an unrelated local BIND variable — fine. Severity LOW (the §6 queries are standalone illustrative patterns over a hypothetical fully-populated graph, not over §5's specific triples, so the "zero rows" framing is weak).
**Routing**: folds into the **D1** consolidated ontology-vocabulary decision — when D1 picks the canonical predicate set, pick `t3Score` (or define `trustScore` distinctly) for both sections. Not cleanly autonomous in isolation.

### INFO (recorded, not carried)
- **§3.2 "Network Context (Depth 3+)" (L139) vs §3.3 `horizon_depth = 3`** — the "+" overstates reach relative to the default horizon, but the same line's "limited by horizon_depth" clause mitigates it; "Depth 3+" reads as the conceptual *tier* (network-level vs direct/inherited), not a literal depth >3. Distinct from operator-tracked D4. No action recommended.
- **§2 lone subsection §2.1, no §2.2 (L76)** — re-raise of an item **already DEFLATED at C40** ("§2.1 is a stable cite anchor, consistent with doc style; leave as-is"). Status unchanged; no action.

---

## §B — Refuted / engine-artifact / deflated (default-to-refute upheld)

| Candidate | Disposition |
|-----------|-------------|
| Cross-ref `t3-v3 §9.2/§10.2` + `t3v3-001` + composite weights 0.4/0.3/0.3 stale post-C82/C83 | **RESOLVES-CLEAN** — triangulated across prose/§10.2 table/§9.2 SPARQL/SDK/test-vector; section numbers, parameter id, and weights all intact. |
| Any of the 12 C41 fixes regressed | **REFUTED** — all 12 sites clean (dedicated regression finder). |
| §6-b `HAVING (?avg_trust > 0.8)` returns nothing | **ENGINE ARTIFACT** — rdflib HAVING decimal-vs-double quirk; query is SPARQL-1.1 standards-correct. Not a doc defect. |
| §5.5-a `BIND` + `FILTER(?trustScore > 0.8)` is a no-op | **REFUTED** — correctly scoped, filters alice in / bob out. |
| §5.3 f-string SPARQL / `RoleContextualT3V3` stubs (`role_matches_interaction`, `self.t3=None`) | **REFUTED as fidelity defect** — §5.3 has no SDK counterpart (grep: no `RoleContextualT3V3`/`TrustPropagation`/`RDFGraph` in SDK); purely illustrative pattern code. f-string brace escaping correct. |
| `MRHEdge.timestamp: str` vs SDK `Optional[str]=None` | **REFUTED** — pseudocode shows no defaults at all (consistent style); not an un-acknowledged divergence. |
| LCT (C60/C61) cross-reference drift | **REFUTED (vacuous)** — `mrh-tensors.md` does not cite `LCT-linked-context-token.md`; no citation to drift. |
| §6 multi-query fences / missing PREFIX | **REFUTED** — every fence is a single query with its own PREFIX (C41-F6 held). |

---

## Disposition for C91 (paired remediation)

- **Apply autonomous**: **N1(b)** reconcile mrh §5.2 `web4:training 0.90 → 0.92` (align to established-canonical t3-v3, closing the C82-hardened contradiction); **N2** annotate/fix §6 query-1 placeholder; **N3** add `maximal()` empty-input guard. All single-file, no design decision. (If N1(a) is approved before C91, N1(b) folds into the §5 shrink.)
- **Defer — operator DESIGN-Q**: **N1(a)** ratify the X4 shrink-to-pointer direction (3× recommended; t3-v3 canonical per CLAUDE.md terminology table) — this is the structural half of X4 and the one item C90 most needs an operator decision on; **D1** consolidated ontology-vocabulary (N4 folds in: pick `t3Score` vs define `trustScore`); **D4** horizon_depth=3 vs MRH_MAX_HOPS=4 + zone-taxonomy documentation. Fold D1/D4 into the standing operator DESIGN-Q bundle.
- **Defer — cross-track**: ontology-side of D1 (editing `web4-core-ontology.ttl` is protected). X4's t3-v3 side is already settled (t3-v3 canonical, no t3-v3 edit needed) — the remaining work is entirely mrh-side.
- **No date bump**: `mrh-tensors.md` carries no date/version banner; nothing to stamp (audit-only turn).

---

## §D — Method Notes

1. **Cross-reference drift must include shared example-DATA, not just citations.** The dedicated cross-ref-drift finder, scoped to section-number / parameter-id / file-path citations, returned "NONE" — yet a real cross-doc contradiction existed (Surgeon `training` 0.90 vs 0.92). It was an **example-value** divergence, not a citation, so a citation-shaped scan structurally cannot see it. A 2nd-delta cross-reference pass must additionally diff **example data values** that appear in both docs.
2. **Read the SIBLING's own audit docs.** The contradiction (and the X4 routing-back-to-mrh) was surfaced not by re-reading mrh but by reading `C42-…`/`C82-…` (the t3-v3 audits run *between* mrh's audits). When sibling X is audited in the interval between this file's audits, X's audit doc may contain findings **assigned to this file** — a 2nd-delta must check the interval's sibling audits for items routed inbound. Extends [[feedback_frozen_parallel_spec]] and [[feedback_cross_cutting_consolidation_audit]]: cross-doc carries can be parked on the *other* doc's ledger.
3. **Stale deferral tags rot.** X4 sat tagged "resolve at C42" through C42, C82, and C83 without landing, because each pass correctly observed "the fix is on the *other* file." A cross-doc carry needs an explicit **owning file + owning turn**, not a "resolve at <sibling's next audit>" tag that no sibling audit will action.

---

*C90 verdict: file in good health; C41 held with zero regressions; cross-reference citation chain intact post-t3-v3-remediation. One flagship cross-doc item (X4/N1) is overdue and now lands here — operator ratification of shrink-to-pointer + autonomous training-number reconciliation for C91. 3 LOW autonomous + 1 LOW cross-track + standing D1/D4.*
