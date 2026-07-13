# C188 — `mcp-protocol.md` Fourth Delta Re-Audit (+ C154-N1 remediation)

**Date**: 2026-07-12
**Auditor**: autonomous web4 session (legion, slot `180036`, C-series)
**Subject**: `web4-standard/core-spec/mcp-protocol.md` (964 lines, 16 sections)
**Instrument**: proportioned single-file re-read + live-HEAD anchor re-verification (not cached byte-identity) + corpus-delta disjointness test + **SDK-mirror gate** (the C172–C186 discipline: re-derive every implementer of the target primitive at live HEAD, verdict on the genuine/partial/false/absent ladder) via 1 delegated mirror-mapping agent + policy-review-gated single-line remediation. Not a fan-out — target byte-frozen since C117, corpus-delta disjoint.
**Scope**: §A delta re-verification of **C148** (3rd delta) + its lineage; §B new findings since 2026-07-06 (corpus-delta + SDK-mirror gate); **remediation** of the deferred mcp-owned carry **C154-N1** (amended C156-1).
**This audit both recommends AND patches** — one policy-review-approved single-line citation fix (C154-N1). Two new files (this doc + session log).

**Lineage**: C35 (first audit, 2026-06-06, #279) → C76 (first delta, #365) → C77 (`f3d2613d`, remediated 8) → C116 (2nd delta, #406) → C117 (`afab0c43`, applied N1) → C148 (3rd delta, #TBD, CLEAN) → **C188** (this audit).

---

## Headline

1. **C154-N1 APPLIED — the frozen bytes moved by exactly one line.** `mcp-protocol.md:415` cited `t3-v3-tensors.md` "parameter governance" for the rule that `reputation.trust_dimension_updates` deltas MUST be bounded by the responding society's Law Oracle — but **t3-v3-tensors.md contains ZERO "Law Oracle" mentions** (re-confirmed at live HEAD: `grep -i "law oracle"` = none) and no delta-bounds row. The dereference was broken. Applied the C156-1 **recommended option 1** (zero semantic stretch): softened *"MUST be within bounds set by the responding society's Law Oracle … (per `t3-v3-tensors.md` parameter governance)"* → *"MUST conform to the reputation rules defined by the responding society's Law Oracle … (per `reputation-computation.md` §4)"*. New anchor verified present: repcomp §4 "Reputation Rules" (L239/L241 — *"Law Oracles define reputation rules that map outcomes to T3/V3 deltas"*). This is the mcp-owned carry that C148 could not see (C154-N1 was raised by the C154 reputation-computation auditor a day AFTER C148); it was explicitly slated for "the next mcp rotation turn" = this turn.

2. **§A CLEAN — 8/8 prior findings HELD, 0 regression.** Target byte-frozen since C117 (blob `08856c37`) except the one C188 edit at L415 (a same-line replacement → **no line-number shift**; every anchor below 415 stays put). Per the C146 [[feedback_prior_finding_path_provenance]] discipline each anchor was re-run at live HEAD: B1 (§3.1 L76 `entity_type:service` + L119 `mcp_server`/`mcp_client` MUST NOT), B3 (§7.3 L404/L417 structured `witnesses`), N1/C117 (§12 L902 high-consequence qualifier) all resolve.

3. **§B SDK-mirror gate — mcp is the FIRST rotation target with a genuine *types-layer* mirror, but STILL has no *wire-layer* mirror.** Ladder verdict = **PARTIAL**. The packaged Python SDK `mcp.py` (web4-sdk, test-vector-backed for §2/§4.1/§6/§9/§11) is a genuine types-layer mirror — but its `ReputationEnvelope` (§7.3) **diverges on two concrete field shapes** (net-new, cross-track SDK: **N1**). Every other candidate is a false mirror (`mcp_server.py`, deprecated `mcp-server/server.py`, hub `mcp.rs`, `web4-trust-core::EntityType::Mcp`). This **extends the C180-N1+C182-N1+C184-N1 wire-layer synthesis**: the corpus has the crypto PRIMITIVE layer and now (for mcp) a DATA-TYPE layer, but **no code path assembles a Web4 Context Header onto a real MCP message, signs an R7 envelope, or emits the §7.6/§7.7 error codes**. Spec is CORRECT throughout; all net-new routes SDK-track/cross-track, zero further spec mutation.

---

## Severity legend

| Sev | Meaning |
|-----|---------|
| **HIGH** | A conformant implementation cannot satisfy the document as written, OR a normative value/structure is rejected by the canonical taxonomy/SSOT. |
| **MEDIUM** | Normative guidance self-contradicts/ambiguous enough that two good-faith implementations diverge. |
| **LOW** | Maintainability / precision / SDK-lag hazard; recoverable by a careful reader; not a blocking contradiction. |
| **INFO** | Observation; recorded for completeness or to confirm a seam was inspected and found bounded. |

---

## §A — Delta re-verification of C148 (+ lineage)

### A.1 — Prior findings, re-verified at LIVE HEAD (greps re-run, not cached)

| ID | Origin | Sev | Verdict | Current site (live HEAD) | Evidence re-run |
|----|--------|-----|---------|--------------------------|-----------------|
| **N1** | C116→C117 fix | LOW | **HELD (fix present & correct)** | §12 MUST #6, L902 | shared "for high-consequence actions" qualifier governs both clauses; matches §7.5 item 4 (L499) + §7.3 (L417). |
| **B1+B11** | C76→C77 | HIGH | **HELD** | §3.1 L76 / note L119 / §8.2 | `entity_type:service`; note *"`mcp_server`/`mcp_client` … MUST NOT be used"*. |
| **B3** | C76→C77 | MED | **HELD** | §7.3 L404 / L417 | `witnesses` array; each entry `{lct, signature, timestamp}` cross-ref `r7-framework.md` §1.7. **(Now doubly load-bearing — see §B N1: the SDK diverges from this ratified shape.)** |
| **B7** | C76→C77 | LOW | **HELD** | §7.3 L395/L414/L419 | four `outcome_class` values inline; `partial`+`violation` semantics present. |
| **B8** | C76→C77 | LOW | **HELD** | §9.1 | `t3_in_role`; `.average()` scoped to present dimensions. |
| **B9** | C76→C77 | LOW | **HELD** | §7.4 | `responding_role_expected` OPTIONAL/advisory + mismatch handling. |
| **B10** | C76→C77 | LOW | **HELD** | §7.1 | `sender_role`/`role_required`/`roleType` harmonization note. |
| **N14** | C76→C77 | LOW | **HELD** | §7.4 | interim conformance note cross-refs §7.7.1. |

**A.1 tally**: 8 HELD · 0 REVERTED · 0 regression. Every anchor re-resolved at live HEAD.

### A.2 — C154-N1 remediation (applied this turn)

- **Finding** (LOW, mcp-owned; raised C154 PR #482, verified/amended C156-1 PR #483): `mcp-protocol.md:415` dereferences to nothing. `t3-v3-tensors.md` has zero "Law Oracle" text and no delta-bounds row; its §10 "Parameter Governance" (L598) governs tier/threshold config, not R7 reputation-delta caps.
- **Confirm-then-fix (policy-review guardrail, satisfied):** re-confirmed at live HEAD (a) L415 still cited t3-v3 "parameter governance" before the edit, (b) `grep -i "law oracle" t3-v3-tensors.md` = 0, (c) the option-1 target `reputation-computation.md` §4 exists (L239) and defines Law-Oracle reputation rules (L241) — the fix's prescribed path did **not** drift ([[feedback_prior_finding_path_provenance]]).
- **Applied:** C156-1 option 1 (recommended, zero semantic stretch). Rejected options 2/3 (cite SAL §5.5 caps) because SAL §5.5 (`web4-society-authority-law.md:220`/`:227` `law.bounds`) is **Auditor-scoped** rate-limits, not the general R7 path — option 1 matches what the target actually says (rules that map outcomes to deltas) without importing "bounds/caps" vocabulary the target lacks.
- **Result:** the citation now resolves. C154-N1 **CLOSED**.

### A.3 — Cross-track / design-Q carries (cited siblings still FROZEN → dispositions unchanged)

All six heavily-cited siblings (`society-roles.md`, `r7-framework.md`, `r6-framework.md`, `entity-types.md`, `inter-society-protocol.md`, `atp-adp-cycle.md`) remain frozen; every C148 carry STANDS: **B2+B6** (r7-reputation shape — now *sharpened* by §B N1), **B5+B12** (registry-home §7.6/§7.7 codes), **N5/N9/N13** (§7.7 promotion, WIP-fenced), **N12** (§10 vs RFC-9457), **N15** (`lct:web4:` id), **F5/C62-B1** (interaction_type home), **F9-inverted** (corpus-wide PolicyEntity form), **B1-family** (`MCP_ENTITY_SPECIFICATION.md` `entity_subtype`). No self-resolution.

---

## §B — New findings since 2026-07-06

### B.1 — Corpus-delta disjointness (5 sibling movers since C148) — all DISJOINT

Sibling remediations landing in `web4-standard/` since C148 (`afab0c43..HEAD`, the new-since-C148 subset):

| Sibling | Commit | What moved | Cited by mcp? | Disposition |
|---------|--------|------------|---------------|-------------|
| `mrh-tensors.md` | C163 `b8740803` | §4.2 propagation-signature note | L32 substrate list only (non-normative "see") | **DISJOINT** |
| `acp-framework.md` | C159 `fb0075fc` | §7.2 "reputation staking is future" softening | not cited (grep-empty) | **DISJOINT by non-citation** |
| `role-extension.{md,ttl}` | `7201a765` | promoted to web4-standard (Phase-0) | not cited | **DISJOINT by non-citation** |
| `reputation-computation.md` | C157 `5195465c` | §9 Sybil item 4 → future/SHOULD + §10 cross-ref | **NEW citation as of this turn** (L415, via C154-N1) | **DISJOINT** — C157 touched §9/§10; C154-N1 anchors to §4 (L239, unchanged by C157) |
| `atp-adp-cycle.md` | C151 `256ab51d` | §2.4 conservation-invariant scope | L32 substrate list only | **DISJOINT** |

mcp cites all of these (where cited) only in the **non-normative substrate list at L32** (*"see `LCT…`, `t3-v3…`, `mrh…`, `atp-adp…`"*). None touched a normative mcp surface. **Note the C154-N1 fix newly points mcp at `reputation-computation.md` §4** — verified C157 did NOT disturb §4 (it edited §9/§10), so the new anchor is stable.

### B.2 — SDK-mirror gate (the C172–C186 discipline) — PARTIAL

Re-derived every implementer of the mcp-protocol primitive at live HEAD. **Ladder verdict: PARTIAL — genuine types-layer mirror, absent wire-layer mirror.**

| Candidate | Verdict | Evidence |
|-----------|---------|----------|
| `implementation/sdk/web4/mcp.py` | **GENUINE (types layer)** | packaged web4-sdk; `Web4Context:267` == §4.1 fields; `OutcomeClass:673`/`PropagationScope:686`/`CrossSocietyInteractionType:698` = exact §7.3/§7.4 enums; `calculate_mcp_cost:606` = §9.1 formula; test-vector-backed (`test-vectors/mcp/mcp-protocol.json`). **BUT §7.3 `ReputationEnvelope:809` diverges — see N1.** |
| `implementation/sdk/web4/mcp_server.py` | **FALSE (name-only)** | stock FastMCP server exposing SDK dev tools (`web4_info`/`web4_validate`/…); no §4.1 headers, no R7 envelope, no §7.6 codes. "MCP server built with web4 tools" ≠ "Web4-over-MCP protocol". |
| `mcp-server/server.py` | **FALSE (self-deprecated)** | header `:20-27` "predates the canonical SDK"; hand-rolled JSON-RPC; own trust-store `entity_type`, no spec structures. |
| `hub/hub-daemon/src/mcp.rs` | **FALSE (self-declared V2-deferred)** | docstring `:6-9` *"Full MCP wire protocol compliance … is V2."* An axum admin REST surface (`/tools/query_hub`…) signing ledger events; plain HTTP 403/409 errors, no `web4_context`/R7/§7.6 codes. |
| `web4-trust-core::EntityType::Mcp` (`entity/types.rs:11`) | **FALSE (ID-prefix classifier)** | `Mcp(String)` parses `"mcp:filesystem"` → node class; a trust-graph classifier, NOT a §2.1/§3.1 entity-type. **EXCLUDED per the C176/C178 name-collision discipline** — the same crate's `EntityType` was already excluded at C176 for entity-types. |

- **N1 (LOW, cross-track SDK; direction = spec CORRECT, SDK diverges/lags).** `mcp.py:809 ReputationEnvelope` diverges from spec §7.3 on **two concrete field shapes**, plus an extra field:
  1. **`witness_signatures: List[str]`** (`:825`, serialized `:842`) vs spec §7.3/§7.4 L417 structured **`witnesses: [{lct, signature, timestamp}]`** — the SDK flattens to bare signature strings, dropping `lct`+`timestamp`. Wire-incompatible with the shape B3 (HELD, C77) ratified.
  2. **`trust_dimension_updates: Dict[str, float]`** (`:823`) vs spec §7.3 nested per-dimension **`{talent:{delta,context}, …}`** — drops the `context` sub-field and the fixed talent/training/temperament keying.
  3. Extra **`action_id: str`** (`:818`) not in the §7.3 envelope — **corroborates the standing B2+B6 carry** (which already named `action_id` + the V3-delta shape as the r7↔mcp↔SDK divergence).

  Because the spec side is already correct and ratified (B3 HELD; §7.3 nested shape intact), the fix is **SDK-side, not spec-side** → routes to the **standing B2+B6 cross-track bundle** ("r7+mcp+SDK must agree on ONE reputation envelope shape"), now **sharpened with a second concrete divergence** (`witness_signatures` flat vs structured `witnesses`). Do NOT mutate the spec; do NOT self-apply an SDK change (out of scope for the audit rotation).

- **N2 (INFO, no action — synthesis).** mcp **extends the wire-layer-readiness synthesis** (C180-N1 + C182-N1 + C184-N1): the corpus has the crypto primitive layer (crypto.rs genuine) and — new at mcp — a genuine **data-type layer** (`mcp.py`), but still **no wire layer**. No code path assembles a Web4 Context Header onto a real MCP message, signs the R7 envelope, or emits the §7.6/§7.7 codes (grep for `web4_cross_society_*`/`web4_rate_*` across `.py`+`.rs` = 0; §7.7 is WIP-fenced so expected). The hub's "MCP-shaped" surface explicitly defers wire compliance to V2. **Whichever form B-D1 declares SSOT still owes a from-scratch wire-layer build** — but for mcp, the **types layer already exists to build on** (unlike registries/handshake, which had no mirror at all). This is the first PARTIAL on the ladder (prior: genuine C180 / false C178 / absent C182 / divergent-by-layer C184).

---

## §C — Routing

### Applied this turn (single-file, no design decision)
- **C154-N1 — APPLIED & CLOSED** (L415 re-anchor, option 1). The C189 (mcp REMED) slot is therefore consumed by this turn → advance per rotation.

### Cross-track / SDK-track (do NOT self-resolve)
- **N1** → the standing **B2+B6** r7-reputation-shape bundle (r7-framework §1.7 + mcp §7.3 + Python SDK `mcp.py:809` + Rust `r6.rs ReputationDelta`). N1 adds `witness_signatures` (2nd concrete divergence) to the previously-carried `action_id`/V3-delta shape. SDK-track owns; couples with C156-3 (`sovereign_strength` spec-lag) as the R7-envelope reconciliation set.
- All C148 cross-track/design-Q carries STAND (see §A.3): B5+B12, N5/N9/N13, N12, N15, F5/C62-B1, F9-inverted, B1-family.

### Confirmed-bounded (no action)
- B.1 corpus-delta (5 movers) — disjoint. N2 wire-layer synthesis — recorded, routes to the operator B-D1/D0 bundle already standing.

---

## Out of scope (handed off, not closed here)
- SDK reconciliation of the N1 `ReputationEnvelope` divergences (SDK-alignment track owns; couples r7+mcp+SDK).
- §7.7 promotion to v0.1.0-final (operator/fleet-review gated).
- The six frozen cited siblings and the 5 corpus-delta movers — inspected only for disjointness to mcp, not re-audited on their own terms.
- Operator-gated flagships (B-D1/C-M1, D0) — untouched.

---

*Fourth delta re-audit + one policy-review-approved single-line remediation (C154-N1). Target byte-frozen since C117 except the L415 edit (same-line replace, no anchor shift). §A 8/8 HELD, 0 regression. §B SDK-mirror gate returns the first PARTIAL on the verdict ladder — genuine types-layer mirror (`mcp.py`) with two concrete §7.3 divergences (N1, SDK-side), absent wire-layer (N2, extends the C180/C182/C184 synthesis). Spec CORRECT throughout; net-new routes SDK/cross-track only. See [[feedback_prior_finding_path_provenance]], [[feedback_prose_is_not_ledger]], [[feedback_cross_doc_carry_inbound]], [[feedback_refute_your_best_finding]].*
