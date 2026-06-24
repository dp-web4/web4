# C91 Remediation: `mrh-tensors.md` (paired with C90 2nd-delta audit)

**Date**: 2026-06-24
**Author**: Autonomous session (Legion, web4 track) — REMEDIATION turn (alternation following C90 audit #381)
**Document**: `web4-standard/core-spec/mrh-tensors.md`
**Pairs with**: `docs/audits/C90-mrh-tensors-2nd-delta-2026-06-24.md` (PR #381, merged `4ab09b7a`)
**Lineage**: C10 → C40 → C41 (#290) → **C90 (audit #381)** → **C91 (this remediation)**

---

## Scope

Applies the **three autonomous findings** the C90 audit routed to C91 in its
"Disposition for C91 (paired remediation)" section. Single file, no design
decisions. The operator DESIGN-Q items are explicitly **NOT** applied (see
"Deferred" below).

Policy review: **APPROVED** (subagent, v2 protocol) — confirmed phase match,
respects the audit's autonomous-vs-DESIGN-Q split, no drift signatures, ≤5 files.

## Findings Applied

### N1(b) — MED — §5.2 `web4:training 0.90 → 0.92` (cross-doc contradiction)
The Alice-as-Surgeon T3 example carried `web4:training 0.90` in mrh §5.2 vs
the established-canonical `0.92` in `t3-v3-tensors.md` §5.2 (the analogous RDF
Role-Tensor Binding, `t3-v3-tensors.md:407`). Talent (0.95) and temperament
(0.88) already agreed; only training diverged. C82-D2 hardened this into a
confirmed cross-doc numeric contradiction and routed the fix to the mrh side.

**Verification at remediation time** (per policy-reviewer reminder — confirm
against *current* HEAD of t3-v3, not just the C82 note): `t3-v3-tensors.md:407`
(Alice Surgeon `web4:T3Tensor`) and `:375` (`candidate_evaluation` role_tensor)
both = `0.92` at current HEAD. The `0.9` at `t3-v3:367` is `minimum_t3` (a role
*requirement* threshold — a different quantity, not the parallel of mrh's
binding) and is a t3-v3-internal matter, out of scope here. mrh's binding now
matches t3-v3's binding.

Applied: `mrh-tensors.md:259` `web4:training 0.90 → 0.92`.

> **Note on the larger X4 / N1(a):** this fix reconciles the *number* only. The
> structural half — shrinking mrh §5 to a pure pointer into `t3-v3-tensors.md`
> (recommended 3×: C40-X4, C42-F17, C82-D2) — remains an **operator DESIGN-Q**
> and was NOT applied. If/when that shrink is ratified and §5.2's Turtle is
> deleted wholesale, this number fix folds into it harmlessly.

### N2 — LOW — §6 query-1 projected unbound `?path` / `?trust`
The "Find trust paths" pattern did `SELECT ?path ?trust WHERE { … (web4:hasRelationship+) … }`
— a SPARQL property path (`+`) is a boolean reachability test that binds no
intermediate nodes, so both projected variables were always NULL and the
`# Calculate trust along path` comment was an unfulfilled placeholder.

Applied: converted to an honest `ASK { <lct:alice> (web4:hasRelationship+) <lct:bob> . }`
reachability check, with a comment stating that path enumeration and trust
aggregation are materialized SDK-side (`mrh.py`:
`TrustPropagation.multiplicative / .probabilistic / .maximal`). The query is now
a correct, runnable pattern rather than an all-NULL non-functional one.

### N3 — LOW — §4.2 `maximal()` lacked the SDK's empty-input guard
`max(self.multiplicative(path, …) for path in paths)` raises `ValueError` on
empty `paths`; the SDK `propagate_maximal` guards `if not path_trusts: return 0.0`,
and the sibling `probabilistic()` already returns `0.0` on empty. `maximal` was
the lone un-guarded outlier.

Applied: `return max((… for path in paths), default=0.0)` + docstring note
"(0.0 if no paths, matching SDK propagate_maximal)". Verified: empty → `0.0`,
non-empty unchanged.

## Deferred — NOT applied (operator DESIGN-Q)

- **N1(a)** — X4 structural shrink of mrh §5 to a pointer (keep only the
  mrh-unique residual: §5.4 `web4:RolePairing` Turtle + §5.3 `RoleContextualT3V3`
  code class). Recommended 3×; needs operator ratification — structural change.
- **D1** — consolidated ontology-vocabulary divergence (undefined illustrative
  predicates; N4 `web4:trustScore` vs `web4:t3Score` folds in here — pick
  `t3Score` or define `trustScore` distinctly).
- **D4** — `horizon_depth = 3` (spec) vs SDK `MRH_MAX_HOPS = 4` + zone taxonomy.

These remain in the standing operator DESIGN-Q bundle (see `private-context`
carries ledger). No ontology `.ttl` edits (protected). No sibling-doc edits.

## Result

`mrh-tensors.md`: 3 edits (1 Turtle value, 1 SPARQL pattern, 1 Python guard).
No date/version banner on this file → nothing to stamp. The C90-confirmed
cross-doc numeric contradiction is closed; two LOW correctness/honesty fixes
applied; the three structural/vocabulary decisions remain correctly escalated
to the operator.
