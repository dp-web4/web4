# C163 — MRH Tensors Remediation

**Date:** 2026-07-09
**Remediator:** Autonomous session `legion-web4-20260709-060036`
**Document remediated:** `web4-standard/core-spec/mrh-tensors.md`
**Applies:** the **single** AUTONOMOUS item pre-declared by the C162 4th-delta audit (`docs/audits/C162-mrh-tensors-4th-delta-2026-07-09.md`, PR #490, merged `1f3b63be`).
**Lineage:** C10 → C40 → C41 (remed, #290) → C90 (2nd delta) → C91 (remed, #382 `f0c82118`) → C129 (3rd delta, `a10affc0`) → C130 (remed of C129-O1, `4e3feb26`, #442) → C162 (4th delta, #490) → **C163** (this remediation).
**Mutation surface:** spec prose only — one explanatory comment inside a §4.2 pseudocode fence. **ZERO SDK / schema / vector / `.ttl` mutation.** `detect_changes` = 0 symbols / 0 flows.

**This is not a no-op.** C162 broke the mrh file's four-pass no-op streak by testing an *enumeration claim* rather than the claim's math. Exactly one item was autonomous; three were routed.

---

## Applied edit (1 autonomous, authority-pinned, net +2 lines)

### N1 — §4.2's SDK-divergence note claims "Two API differences" when there are three

- **Site:** `web4-standard/core-spec/mrh-tensors.md` §4.2, the comment heading the `class TrustPropagation` pseudocode fence (was L198-206).

- **Before:**
  ```
  # with identical mathematical semantics. Two API differences from the
  # pseudocode below: (1) the SDK's propagate_probabilistic/propagate_maximal
  # consume pre-computed path-trust scalars (List[float]) rather than raw
  # List[MRHEdge] paths, and (2) they drop the decay_factor parameter — decay
  # is applied earlier, during multiplicative path scoring. Only
  # propagate_multiplicative carries decay_factor.
  ```

- **After:**
  ```
  # with identical mathematical semantics. Three API differences from the
  # pseudocode below: (1) all three SDK functions consume List[float] rather
  # than MRHEdge objects — propagate_multiplicative takes per-edge weights,
  # (2) propagate_probabilistic/propagate_maximal take pre-computed per-path
  # trust scalars rather than raw List[List[MRHEdge]] paths, and (3) those two
  # drop the decay_factor parameter — decay is applied earlier, during
  # multiplicative path scoring. Only propagate_multiplicative carries
  # decay_factor.
  ```

- **Why:** the note attributed the `List[float]` divergence **only** to `propagate_probabilistic`/`propagate_maximal`, silently implying `propagate_multiplicative` still consumes `List[MRHEdge]`. It does not. The omission made the count wrong *and* concealed a real, distinct divergence: multiplicative's scalars are per-**edge** weights, while prob/max's scalars are per-**path** trust values. The corrected note now separates the two scalar kinds, which is the substantive gain — the "two vs three" count is the symptom, not the defect.

- **Authority (ground truth, `web4-standard/implementation/sdk/web4/mrh.py`, re-derived at live HEAD):**
  | SDK function | Signature | `decay_factor`? |
  |---|---|---|
  | `propagate_multiplicative` (L198-201) | `(path_weights: List[float], decay_factor: float = 0.7) -> float` | yes |
  | `propagate_probabilistic` (L214) | `(path_trusts: List[float]) -> float` | dropped |
  | `propagate_maximal` (L228) | `(path_trusts: List[float]) -> float` | dropped |

  Against the pseudocode's `multiplicative(path: List[MRHEdge], …)`, `probabilistic(paths: List[List[MRHEdge]], …)`, `maximal(paths: List[List[MRHEdge]], …)`. **Three** divergences, as enumerated.

- **Scope discipline:** the pseudocode fence itself is **untouched**. It remains the conceptual-structure exposition; only its describing note changed. Mathematical semantics were verified identical at C129 and are not re-litigated here.

- **Provenance / regression check:** the new prose adds no normative claim — it is descriptive of `mrh.py` and strictly *narrows* what the reader may assume about `propagate_multiplicative`. It removes an implication (that multiplicative takes edges) rather than adding one.

- **Mirror sweep:** `grep -rn "Two API differences"` over the corpus at HEAD returns only (i) quotations inside `docs/audits/C162-…md` and (ii) `whitepaper/PUBLISHER_CONTEXT.md:210`, which explicitly records the claim as routed to C163 and confirms no whitepaper surface carries it. Both are **historical records of the pre-fix text and are correctly left intact.** No live spec surface retains the stale phrasing.

---

## Routed — NOT self-applied

Per authorization discipline (operator silence ≠ authorization) and remediation locality (a remediation turn edits its rotation target, not other tracks' files or closed audit records):

| Item | Class | Disposition |
|---|---|---|
| **N2** — `role-extension.ttl` is an RDF island: declares `web4:` and never uses it; no formal link from `role:Scope`/`role:rangesOver` into `web4:`; `role:driftMark` lacks `rdfs:domain` | class-b, cross-track | → **owner of `web4-standard/ontology/role-extension.{ttl,md}`** (CBP Phase-0 concord; PR #489 merged `3c18807a` since C162 was written). Fresh sibling instance of standing carry **D1**. |
| **A1** — C129's O2 inbound-anchor census overcounts by one (8 → 7; `RFC-COMPOSITE:246` ×4 → ×3) | INFO, defect in a *prior audit doc* | → recorded here, **not** retro-edited into `docs/audits/C129-…md`. O2's qualitative conclusion (raw-line cross-refs into §5 are a fragility class) is fully intact; the operator's X4 cost picture is not materially changed by an off-by-one across the same 3 docs. |
| **A2** — the `` `mrh §246` `` citation spelling defeats a filename-anchored grep and would silently orphan `RFC-SHARED:165` in any X4 anchor migration | INFO, method | → **folds into the standing X4 operator DESIGN-Q.** Any §5-shrink enumerating its blast radius by grepping `mrh-tensors\.md:[0-9]` will undercount. Recommend the corpus convention also forbid `§N` where `N` is a line number. |

**Standing operator DESIGN-Qs, unchanged and still escalated:** **X4/N1(a)** (structural shrink of §5, L240-369; recommended 4× — cost context now O2 + A1 + A2); **D1** (ontology-vocabulary divergence; N4 and C162-N2 fold in); **D4** (`horizon_depth = 3` at L174 vs `MRH_MAX_HOPS = 4` at `trust.py:91`, plus the code-only zone taxonomy); **N4** (`web4:t3Score` vs `web4:trustScore`).

---

## Forward guard for C164

C162's own §A discipline says a frozen file's non-cleanness is often **entirely remediation-introduced**. This remediation writes the newest net-new prose into a file that had been byte-frozen since C91 (`f0c82118`). Therefore:

> **C164 (or whichever pass next reaches mrh) MUST re-test this exact hunk against `mrh.py` at that HEAD** — not merely re-read it. Specifically: re-derive the three signatures from ground truth and confirm the note still enumerates them correctly. If `mrh.py` gains a fourth propagation function or restores an edge-typed parameter, this note becomes the defect.

The enumeration lens is now part of the standard method: *a claim of the form "there are exactly N of X" is tested by re-deriving X from ground truth, never by re-reading the claim.* Four prior passes read this note — C129 explicitly tested and refuted a charge against its **math** — and none tested its **count**.

---

## Rotation

The mrh-tensors C162/C163 audit-remediation pair is **complete**. The fixed-order rotation now **wraps to the oldest file: `SOCIETY_SPEC`** (C164 = audit turn).

---

*C163 verdict: one autonomous spec-local edit applied (§4.2 note: "Two" → "Three" API differences, with the per-edge vs per-path scalar distinction made explicit). Zero SDK mutation. Three items routed (N2 cross-track, A1 audit-record, A2 → X4). Four standing DESIGN-Qs untouched and still escalated. Forward guard filed against this remediation's own new prose.*
