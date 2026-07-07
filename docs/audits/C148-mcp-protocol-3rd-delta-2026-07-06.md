# C148 — `mcp-protocol.md` Third Delta Re-Audit

**Date**: 2026-07-06
**Auditor**: autonomous web4 session (legion, LEAD `180036`, C-series)
**Subject**: `web4-standard/core-spec/mcp-protocol.md` (964 lines, 16 sections) + `web4-standard/MCP_ENTITY_SPECIFICATION.md` (408 lines, second B1 site)
**Instrument**: proportioned single-file re-read + live-HEAD anchor re-verification (not cached byte-identity) + corpus-delta disjointness test + cross-section blindspot sweep → 1 adversarial verifier (refute-by-default, C144 bar) on all three disposition rulings. Not the C76 9-agent fan-out — target byte-frozen, corpus-delta fully disjoint (see Proportionality).
**Scope**: §A delta re-verification of **C116** (`docs/audits/C116-mcp-protocol-2nd-delta-2026-06-29.md`) and its remediation **C117** (`afab0c43`, PR #422, applied C116-N1). §B new findings since 2026-06-30.
**This audit recommends; it does not patch.** No spec text modified. One new file.

**Lineage**: C35 (first audit, 2026-06-06, #279) → **C76** (first delta, #365, 2026-06-19) → **C77** (#366, `f3d2613d`, remediated 8 findings) → **C116** (second delta, #406) → **C117** (#422, `afab0c43`, applied the sole autonomous finding N1) → **C148** (this audit).

---

## Headline

1. **C117 was a clean remediation, and the target is byte-FROZEN since it.** `mcp-protocol.md` blob is `08856c37` at both `afab0c43` (C117) and live HEAD — `git log afab0c43..HEAD -- …/mcp-protocol.md` = **0 commits**. `MCP_ENTITY_SPECIFICATION.md` likewise unchanged. §A is therefore persistence-by-byte-identity for content, but per the C146 [[feedback_prior_finding_path_provenance]] lesson every finding's line-anchor and cross-section citation was **re-run at live HEAD**, not asserted from the cached C116 table. All anchors resolve; the C117 N1 fix is present and correct at L902.

2. **CLEAN 3rd-delta — zero net-new findings.** The corpus-delta since C117 is **fully disjoint** from mcp: of the 5 sibling remediations that landed (C122 t3-v3, C124 reputation-computation, C126 acp, C128 presence, C130 mrh-via-FRACTAL_ROLE_IDENTITY), **three are uncited by mcp** (acp, reputation-computation, presence — grep-empty) and **two are cited but were not disturbed on the cited surface** (t3-v3 §10 parameter-governance mechanism is intact; C122 touched only a §10.2 ATP-conservation *row citation*; mrh-tensors.md is itself frozen — C130 edited a *different* doc that cites mrh). The cross-section blindspot sweep (the discipline that produced C116's lone net-new N1) found **no** §12↔body over/under-statement remaining after C117: item 6 is fixed, items 1–5 faithfully track their bodies.

3. **All three disposition rulings survived refute-by-default adversarial verification** (C144 bar). A verifier prompted to REFUTE the "clean" verdict CONCEDED all three (t3-v3 disjointness, mrh disjointness, §12 item-1–5 consistency) after reading the actual files and diffs, and independently confirmed the two additional movers (C124/C126) are disjoint-by-non-citation.

This is the **fourth+ confirmation** in the current cycle (after C138, C140, C142 clean 3rd-deltas) that on a byte-frozen, disjoint-delta target the correct outcome is a documented CLEAN pass — yield is on the sibling surface and the internal blindspot sweep, not the frozen bytes.

---

## Severity legend

| Sev | Meaning |
|-----|---------|
| **HIGH** | A conformant implementation cannot satisfy the document as written, OR a normative value/structure is rejected by the canonical taxonomy/SSOT. |
| **MEDIUM** | Normative guidance self-contradicts/ambiguous enough that two good-faith implementations diverge. |
| **LOW** | Maintainability / summary-precision / terminology hazard; recoverable by a careful reader; not a blocking contradiction. |
| **INFO** | Observation; recorded for completeness or to confirm a seam was inspected and found bounded. |

---

## §A — Delta re-verification of C116 (+ C117 remediation)

### A.1 — Prior findings, re-verified at LIVE HEAD (greps re-run, not cached)

Target byte-frozen since C117 → content guaranteed present; the discipline here is confirming each **line-anchor and cross-section citation still resolves** (per C146 [[feedback_prior_finding_path_provenance]] — the tell for a stale anchor is when line#/phrase/section don't all resolve to the named site).

| ID | Origin | Sev | Verdict | Current site (live HEAD) | Evidence re-run |
|----|--------|-----|---------|--------------------------|-----------------|
| **N1** | C116→C117 fix | LOW | **HELD (fix present & correct)** | §12 MUST #6, L902 | L902 now reads *"R7 actions MUST be witnessed: **for high-consequence actions,** an R7 transaction MUST NOT proceed without witnessing (§7.5), and the `reputation.witnesses` array MUST contain at least one Witness-role entry (§7.3)"* — the shared qualifier now governs both clauses, matching §7.5 item 4 (L499) + §7.3 (L417). The over-strict rejection of low-consequence cross-society R7 is closed. |
| **B1+B11** | C76→C77 | HIGH | **HELD** | §3.1 L76 / §3.2 L100 / note L118-119 / §8.2 L737 | `entity_type`=`service`/`ai`; note *"`mcp_server`/`mcp_client` … MUST NOT be used"*; SPARQL `?server a web4:Service`. |
| **B3** | C76→C77 | MED | **HELD** | §7.3 L404 / L417 | `witnesses` array; each entry `{lct, signature, timestamp}` cross-ref `r7-framework.md` §1.7. |
| **B7** | C76→C77 | LOW | **HELD** | §7.3 L395 / L414 / L419 | four `outcome_class` values defined inline; `partial` + `violation` semantics present. |
| **B8** | C76→C77 | LOW | **HELD** | §9.1 L139 / L756 / L765 | `t3_in_role`; `.average()` scoped to present dimensions. |
| **B9** | C76→C77 | LOW | **HELD** | §7.4 L434 / L461 | `responding_role_expected` OPTIONAL/advisory + mismatch handling. |
| **B10** | C76→C77 | LOW | **HELD** | §7.1 L137 / L251 / L314 / L340-346 | `sender_role`/`role_required`/`roleType` harmonization note (+ `roleLCT`). |
| **N14** | C76→C77 | LOW | **HELD** | §7.4 L470 | interim conformance note cross-refs §7.7.1 stable design-invariant. |

**A.1 tally**: 8 HELD (7 C77-applied + N1 C117-applied) · 0 REVERTED · 0 regression. Every anchor re-resolved at live HEAD.

### A.2 — Cross-track / design-Q carries (all cited siblings FROZEN → dispositions unchanged)

All six heavily-cited mcp siblings are **frozen since C117** (0 commits each): `society-roles.md`, `r7-framework.md`, `r6-framework.md`, `entity-types.md`, `inter-society-protocol.md`, `atp-adp-cycle.md`. Every C116 cross-track carry therefore **STANDS unchanged**:

| Cluster | Verdict | Note |
|---------|---------|------|
| **B2 + B6** (r7-reputation shape: V3-delta `{change,from,to}`, `action_id`) | **STILL OPEN** | `r7-framework.md` frozen; cross-track (r7+mcp+SDK must agree on ONE shape). |
| **B5 + B12** (registry-home for §7.6 `web4_cross_society_*` + §7.7.7 `web4_rate_*`) | **STILL OPEN** | `registries/initial-registries.md` + `error-codes.md` frozen. |
| **N5 / N9 / N13** (§7.7 v0.1.0-final promotion wire-shape) | **STILL OPEN (WIP-fenced)** | §7.7 byte-identical; resolve as ONE unit at promotion. atp-adp C79-B7 inbound citation (verified C116) unchanged. |
| **N12** (§10 JSON-RPC vs RFC-9457 error model) | **STILL OPEN** | `errors.md` frozen; operator-scoped. |
| **N15** (`lct:web4:` entity-vs-instance id) | **STILL OPEN** | `data-formats.md` frozen. |
| **F5 / C62-B1** (`established`/`federated` interaction_type home) | **STILL OPEN** | `inter-society-protocol.md` frozen. |
| **F9-inverted** (corpus-wide `PolicyEntity`/`Policy-Entity` form) | **STILL OPEN** | mcp uses `Policy-Entity`, consistent with `society-roles.md`; corpus-wide decision, do NOT single-file rename. |
| **B1-family sub-item** (`MCP_ENTITY_SPECIFICATION.md` `entity_subtype`/`subtype` canonicity) | **STILL OPEN** | 2nd B1 site frozen; taxonomy-refinement question. |

---

## §B — New findings since 2026-06-30

**Corpus-delta surface.** Sibling remediations landing in `web4-standard/` since C117 (`afab0c43`):

| Sibling | Commit | What moved | Cited by mcp? | Disposition |
|---------|--------|------------|---------------|-------------|
| `t3-v3-tensors.md` | C122 `b2a98f7c` | §10.2 ATP-conservation **row citation** re-anchored (atp-adp §6.3 → §3.1/§3.2, §2.4, §6.3) | **Yes** — L32 (substrate list) + L415 ("`t3-v3-tensors.md` parameter governance" for `trust_dimension_updates` Law-Oracle bounds) | **DISJOINT** — see B.1 |
| `mrh-tensors.md` | (unchanged) | — (frozen; C130 `4e3feb26` edited `docs/FRACTAL_ROLE_IDENTITY.md`, a doc that *cites* mrh) | **Yes** — L32 substrate list; internal `mrh`/`mrh_depth`/`mrh_update`/`mrh_graph` fields | **DISJOINT** — see B.2 |
| `reputation-computation.md` | C124 `4d1594ea` | fail-open `matches()` clause + `age_days` clock-skew clamp | **No** (grep-empty; mcp routes reputation via `r7-framework.md`) | **DISJOINT by non-citation** |
| `acp-framework.md` | C126 `aabe4457` | `resourceCaps` snake_case→camelCase | **No** (grep-empty) | **DISJOINT by non-citation** |
| `presence` (schemas) | C128 `cf0d6cc5` | presence schema-README gap ledger | **No** (grep-empty for the doc; mcp's "presence substrate" mentions are internal) | **DISJOINT by non-citation** |

### B.1 — t3-v3 C122 vs mcp L415 — DISJOINT (INFO)

C122 changed exactly one line: the *Related-context column* of the **ATP-conservation row** in t3-v3 §10.2 (the invariant text unchanged). mcp L415 cites t3-v3 **"parameter governance"** for a different rule — `reputation.trust_dimension_updates` deltas MUST be within bounds set by the responding society's Law Oracle. That mechanism lives in §10.1 (governance tiers) / §10.3 (society-configurable role-requirement thresholds), and §10 is still titled "Parameter Governance" (L598) → mcp's citation resolves. The C122-touched ATP-conservation row concerns ATP *supply*, not trust-dimension bounds. **Different normative surface** (C138 disjointness test: which section moved vs which the target CITES). No defect.

- *INFO (inspected & bounded, not a finding):* the adversarial verifier flagged a soft **pre-existing** tension — t3-v3 §10.2 classes the T3-update *formula* protocol-invariant while mcp says the society sets *bounds*. "Bounds/clamps" ≠ "formula", so it is defensible; it is **not** introduced or touched by C122, so it is out of scope for this delta. Recorded for completeness; not routed.

### B.2 — mrh C130 — DISJOINT (frozen file / different-doc mover) (INFO)

`git log afab0c43..HEAD -- …/mrh-tensors.md` = 0 commits (frozen). C130 (`4e3feb26`, `--stat`) changed **only** `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md` — a one-line mrh line-anchor fix (`:143`→`:174`) in a doc that *cites* mrh. It made zero edits to `mrh-tensors.md`, which mcp cites, and mcp does not cite `FRACTAL_ROLE_IDENTITY.md` at all. mcp's L32 mrh reference (and its internal `mrh_*` fields) depend on nothing C130 changed. No defect.

### B.3 — Cross-section blindspot sweep (§12 MUST list vs body) — CLEAN

The one discipline section-anchored finders structurally can't reproduce, and the source of C116's lone net-new. Each §12 MUST item re-checked against its governing body section at live HEAD:

| §12 MUST | Body support | Verdict |
|----------|--------------|---------|
| 1. servers MUST have valid LCTs | §3.1 "Every MCP server has an LCT" (+ §5.1 L161 validation) | consistent |
| 2. interactions MUST include Web4 context headers | §4.1 L125 "Every MCP message includes Web4 context" | consistent |
| 3. Trust evaluation MUST precede resource access | §4.2 "evaluate trust before granting access" (+ §5.1 pseudocode) | consistent (stated universally, not narrowed) |
| 4. ATP metering MUST be enforced | §9.1 "All MCP interactions are metered in ATP" (MAY-1 optional *stakes* ≠ metering) | consistent |
| 5. Agency proofs MUST be validated **when present** | §4.2 pseudocode step 4 (`if present`) + §7.4 L484-488 (`agency_chain` MUST be non-empty **when present**) | consistent — the "when present" qualifier correctly matches the body's `if`-guard (the *opposite* of the old item-6 over-statement) |
| 6. R7 witnessing | §7.3/§7.5 — **C117-fixed** (N1) | consistent (see §A.1) |

**No §12↔body over/under-statement remains.** The §12 preamble (L893-895, "not exhaustive … §7.3/§7.5 govern in full") is unchanged and still subordinates the summary; items partly grounded in §5.1 pseudocode are a long-standing style (present since C35), not a net-new gap. The SHOULD/MAY lists trace cleanly to §4.3/§7.5/§9.1/§3.1/§4.2/§7.7/§2.2 (adversarially confirmed). **Zero net-new findings.**

---

## §C — Routing for the remediation turn

### Autonomous-actionable (single-file, no design decision)
- **None.** C148 is a clean 3rd-delta; the C147 (mcp REMED) slot is therefore a no-op → advance per rotation.

### Cross-track / design-Q / WIP (do NOT self-resolve — all carried unchanged, cited siblings frozen)
- B2+B6 (r7-reputation shape) · B5+B12 (registry-home) · N5/N9/N13 (§7.7 promotion) · N12 (§10 error model) · N15 (`lct:web4:` id) · F5/C62-B1 (interaction_type home) · F9-inverted (corpus-wide PolicyEntity form) · B1-family (`entity_subtype` canonicity). See `carries.md`.

### Confirmed-bounded (no action)
- t3-v3 C122, mrh C130 corpus-delta — disjoint, reinforcing/inert. §10.2 formula-vs-bounds soft tension — pre-existing, defensible, not routed.

---

## Out of scope (handed off, not closed here)

- SDK-vs-spec conformance of §7 behavior (separate SDK-alignment track).
- §7.7 promotion to v0.1.0-final (operator/fleet-review gated); N5/N9/N13 + the atp-adp inbound citation are inputs.
- Corpus-wide PolicyEntity-form decision (F9-inverted) and the C62-B1 relationship-state-home decision.
- `t3-v3-tensors.md`, `mrh-tensors.md`, `reputation-computation.md`, `acp-framework.md`, presence, and the six frozen cited siblings — inspected only for corpus-delta disjointness to mcp, not re-audited on their own terms.

---

*Third delta re-audit. No spec text modified. No SDK or test code touched. One new file. Target byte-frozen since C117 (`afab0c43`, blob `08856c37`) + corpus-delta fully disjoint → proportioned to a re-read + live-HEAD anchor re-verification + disjointness test + blindspot sweep + 1 adversarial verifier (all three rulings CONCEDED under refute-by-default), not the C76 9-agent fan-out. Fourth+ clean 3rd-delta in-cycle (C138/C140/C142): frozen ≠ presumed clean, but here the sibling surface is disjoint and the internal blindspot sweep is clear, so CLEAN is the verified outcome. See [[feedback_prior_finding_path_provenance]], [[feedback_audit_workflow_adversarial_verify]], [[feedback_cross_doc_carry_inbound]].*
