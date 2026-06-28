# C106 — `errors.md` Second Delta Re-Audit (3rd pass)

**Audit ID**: C106
**Target**: `web4-standard/core-spec/errors.md` (154 lines) — the Web4 core RFC-9457 error taxonomy
**Date**: 2026-06-27
**Auditor**: autonomous web4 session (legion, slot `180036`), v2 protocol
**Type**: **Second delta re-audit** (3rd pass overall). Lineage: **C30** (first-pass, 2026-06-04, PR #268 → remediation #269 `aaa2bd86`) → **C66** (first delta, 2026-06-17, PR #345) → **C67** (remediation, 2026-06-17, PR #347 `6189432d`, applied 3 autonomous: B-3/B-6/B-7) → **C106**.
**Method note**: This is the **8th consecutive frozen-target wrap** (after C92/C94/C96/C98/C100/C102/C104). `errors.md` is **byte-identical since C67** (`git log` last touch = `6189432d`, 2026-06-17 10:03; banner `Last-Updated: 2026-06-17` accurate). Per the established frozen-wrap proportionality precedent, the audit is a single fresh-internal pass + moved-sibling corpus-delta, **not** a multi-agent finder fleet. §A done by hand against live files + git; §B is the corpus-delta surface (siblings that moved since C67); §C a focused refute-by-default internal pass. Policy-reviewed and APPROVED (single fresh-internal pass right-sized for a 3rd-pass frozen target).

---

## Scope & Methodology

Because `errors.md` is unchanged since its C67 remediation, §A applies the **C56 completeness method** (audit the remediation's *claims* token-by-token, not merely "is the edit present") and the **bidirectional carry re-check** (C62/C64: a downstream sibling's own remediation may RESOLVE a carry routed here, leaving a stale note — or HARDEN it). §B follows the frozen-wrap lesson (C90/C102/C104): the yield lives entirely on the **corpus-delta surface** — diff the cross-refs of the siblings that moved since the last remediation, and apply the **snapshot-presence guard** (C98: do not report a divergence as net-new if it was already present at the prior audit snapshot).

Severity: **HIGH** correctness/normative contradiction; **MEDIUM** consumer-affecting inconsistency / wrong citation; **LOW** hygiene; **INFO** forward-awareness.
Routing: **AUTONOMOUS** (fixable in `errors.md`, no design decision), **DESIGN-Q** (operator), **CROSS-TRACK** (lands in another file).

---

## §A — Prior-Finding Verification (C67 remediation → current)

### A.1 — The 3 AUTONOMOUS C67 fixes: **all HELD token-by-token**

| C66 ID | C67 fix | Verdict | Evidence (current `errors.md`) |
|---|---|---|---|
| **B-3** (MED, priority) | §1 rescope: stop claiming mcp §7.6 uses `W4_ERR_*`; scope `W4_ERR_*` to SAL §9 / ACP §10 / metering §6; name mcp §7.6 separately as lowercase `web4_*` | **HELD + REINFORCED** | §1 L9: "…Society/Authority Law (`web4-society-authority-law.md` §9), ACP (`acp-framework.md` §10), and metering (`web4-metering.md` §6) add codes following the `W4_ERR_*` convention defined here; MCP cross-society (`mcp-protocol.md` §7.6) currently uses lowercase `web4_*` identifiers". Re-verified against the **moved** mcp source — see §B-1. |
| **B-6** (LOW) | §5 retitle "HTTP Status Code Mapping" → "Status Code Semantics" + transport-agnostic lead | **HELD** | §5 L141 "## 5. Status Code Semantics"; L143 lead presents HTTP reason phrases as "canonical *illustrative labels* … same semantic class applies over non-HTTP transports", consistent with §1 L32's "per §2/§5" citation. No re-asserted HTTP normativity. |
| **B-7** (LOW) | §5 401/403 prose sharpened to mirror §2's deliberate split | **HELD** | §5 L146 "401 Unauthorized: Authentication failure, or a credential that lacks the required capability (e.g. `W4_ERR_AUTHZ_DENIED`)"; L147 "403 Forbidden: An authenticated entity lacking the additional scope or authorization required (e.g. `W4_ERR_AUTHZ_SCOPE`)". Mirrors §2.4 split **without** reassigning any status (status reassignment remains the B-1 design-Q). |

**No C67 finding regressed.** PR #347 touched only `errors.md` (single-file diff per its commit body), so the cross-file regression surface is nil. No `&#` / encoding artifacts; §3 examples still consistent with §2 (§3.1 AUTHZ_DENIED/401/"Authorization Denied" = §2.4 L72; §3.2 WITNESS_QUORUM/409/"Quorum Not Met" = §2.3 L66; §3.3 AUTHZ_RATE/429/"Rate Limit Exceeded" = §2.4 L75).

### A.2 — Bidirectional carry re-verification (C66 + C30 carries → current corpus)

The C66 audit left 1 DESIGN-Q (B-1), 5 CROSS-TRACK (B-2/B-4/B-5/B-8/B-9), the carried B-H1 numeric-registry canonicity, and the C30 design-Q/cross-track set (B-M1/B-M2/B-M3, I2/I3). Re-checked against the current corpus, **with the moved siblings**:

| Carry | Status now | Note |
|---|---|---|
| **B-H1** numeric `registries/error-codes.md` orphan (DESIGN-Q) | **SUB-FACET RESOLVED; design-Q stands** | **C71-B-A2 (#354, 2026-06-18) resolved the "Section X.Y placeholder unfilled" observation**: `error-codes.md` now has `## Reference` L10–11 → `[Web4 Standard, core-spec/errors.md](../core-spec/errors.md)` + a B-A5 banner "Draft / experimental — pre-IANA template • Last-Updated: 2026-06-18". The C66-A.3 note ("placeholder still unfilled") is now **STALE**. BUT C71 explicitly "held B-D1 SSOT inversion for operator" — the underlying *canonicity* design-Q (numeric registry orphaned, 11 codes / 0 adopters, errors.md §2 still never references it) **STANDS**. |
| **B-1** `AUTHZ_DENIED`@401 vs RFC 403 + sibling `AUTHZ_SCOPE`@403 (DESIGN-Q + coordinated CROSS-TRACK) | **STANDS; mirror unchanged** | The handshake §10 mirror is one of the 5 coordination sites. **C73 (#362, 2026-06-18) did NOT touch §10's error example** — `web4-handshake.md` L251 still `"code": "W4_ERR_AUTHZ_DENIED", "status": 401` (and its detail `"Credential lacks scope write:lct"` is a *scope* case mapped to DENIED@401, which actually **reinforces** the B-1 semantic confusion). Design-Q open; recommend 403 on RFC 9110 §15.5.4 grounds; coordinated change across errors.md §2.4 + test-vector + SDK + initial-registries + handshake §10 still required. |
| **B-2 / X2** `initial-registries.md` divergent core-taxonomy mirror (CROSS-TRACK) | **STANDS** | **C71 explicitly made "no CROSS-TRACK mutation"** — `initial-registries.md` §2-absent codes `W4_ERR_WITNESS_REQUIRED` (L33) and `W4_ERR_PROTO_FORMAT` (L52) + the "Metering Errors" block (L54) are all still present; errors.md §2 still does not define them. The textual SSOT mirror still diverges. |
| **B-4** SDK docstring "canonical per errors.md / 30 codes 7 cats" over-claim (CROSS-TRACK) | **STANDS** | SDK `implementation/sdk/web4/errors.py` unchanged in the relevant block; errors.md §2 still 24/6. SDK-side fix. |
| **B-5** SDK cross-society statuses (404/400/403) diverge from mcp §7.6 (403/409/412) (CROSS-TRACK) | **STANDS; mcp source confirmed stable** | The mcp §7.6 source statuses were **re-verified after C77 (#366, the move)** — still `403 unrecognized_lct` (L520), `409 exchange_invalid` (L521), `412 witness_required` (L523). The divergence is entirely SDK-side; mcp owns canonicity. |
| **B-8 / X3** ACP §10 / SAL §9 parallel-naming + ledger-write collision (CROSS-TRACK) | **STANDS** | SAL §9 (`web4-society-authority-law.md`) still uses bare `W4_ERR_LEDGER_WRITE` (L320) vs ACP §10 `W4_ERR_ACP_LEDGER_WRITE`. SAL §9 correctly **reuses** 5 core codes (BINDING_INVALID, PROTO_DOWNGRADE, WITNESS_QUORUM, AUTHZ_SCOPE, AUTHZ_EXPIRED) and extends 3 domain codes (LEDGER_WRITE L320, AUDIT_EVIDENCE L321, LAW_CONFLICT L322) — these 3 are the **C16-H1-remainder** carry, SAL-track, not errors.md-autonomous. |
| **B-9** no cross-society test vectors (INFO/CROSS-TRACK) | **STANDS** | `test-vectors/errors/error-taxonomy.json` unchanged since 2026-03-17; still 0 cross-society vectors. Add after B-5 settles. |
| **C16-M8/B6** `chapter-law.ttl` (CROSS-TRACK, ontology/SAL) | **STANDS** | `ontology/chapter-law.ttl` + `core-spec/chapter-law-schema.md` exist; this is an ontology/SAL-track item, categorically cross-track to errors.md. Route to operator/SAL — **do not self-apply**. |
| **B-M1** centralized-vs-distributed error ownership (DESIGN-Q) | **STANDS, load-bearing across 4 sites** | metering, ACP (B-8), numeric registry (B-H1), textual registry (B-2). Unchanged. |
| **B-M2** `web4://` SSOT in `data-formats.md` (CROSS-TRACK) | **STANDS** | unchanged. |
| **B-M3** W4IDp `w4idp-ABCD` form (DESIGN-Q, inherited C29) | **STANDS** | all 3 `instance` URIs still hyphen form; bundles into corpus-wide identifier decision. |
| **I2** `QUICK_REFERENCE.md` custom `type` URI (INFO/CROSS-TRACK) | **STANDS** | `QUICK_REFERENCE.md` unchanged since 2026-02-17. |
| **I3** content-type over negotiated transports (INFO) | **STANDS** | §4 unchanged (correct — INFO). |

**No carry resolved into a defect; one carry sub-facet (B-H1 placeholder) RESOLVED downstream by C71, leaving a stale C66 note; one carry (B-1) REINFORCED by an unchanged handshake mirror.**

---

## §B — Corpus-Delta Pass (siblings that moved since C67)

Four siblings cited by `errors.md` (or holding its mirrored data) moved after C67 (2026-06-17). Each is a C-series remediation; diffed for errors-relevant impact:

### B-1 — `mcp-protocol.md` C77 (#366, 2026-06-20): **REINFORCES errors.md §1; 0 net-new**

errors.md §1 L9 characterizes mcp §7.6 as "currently uses lowercase `web4_*` identifiers." Re-verified against the moved file: `grep -c W4_ERR mcp-protocol.md` = **0**; §7.6 failure table (L520–525) still all lowercase `web4_cross_society_*`. C77 **added** a §7.7.7 refinement note (L527) introducing *more* lowercase codes (`web4_rate_standing_expired`, `web4_rate_valuation_mismatch`) as a sub-domain of the §7.6 generic code — which **strengthens** errors.md §1's characterization (mcp's error surface is lowercase `web4_*`, now even more so). The B-3 correction (now in errors.md §1) is two-sided-verified: true at both the convention level and the new §7.7.7 codes. **0 findings routed to errors.md.**

### B-2 — `registries/` C71 (#354, 2026-06-18): **resolves a B-H1 sub-facet; B-2 mirror untouched**

C71 applied the registries AUTONOMOUS bucket. **error-codes.md** got B-A2 (placeholder → real `errors.md` pointer) + B-A5 banner → **resolves the C66-A.3 "Section X.Y unfilled" observation** (now stale; see §A.2 B-H1). **initial-registries.md** got B-A1 (W4-IOT-1 suite row) + B-A5 banner, but C71 made **no CROSS-TRACK mutation** to its error-taxonomy section → the B-2/X2 divergent mirror (§2-absent `WITNESS_REQUIRED`/`PROTO_FORMAT` + Metering block) **stands unchanged**. C71's commit body confirms B-D1 SSOT inversion was held for operator. **0 net-new; 1 carry sub-facet resolved.**

### B-3 — `web4-handshake.md` C73 (#362, 2026-06-18): **B-1 mirror confirmed still @401**

C73 applied 10 autonomous handshake findings (suite row, directional keys, COSE envelope, etc.) — **none touched §10 (Error Handling)**. The §10 `W4_ERR_AUTHZ_DENIED` example (L251) is still `status: 401`. The B-1 design-Q's coordination-site count is unchanged (the handshake mirror still sits at the to-be-decided 401). Note: C71-B-A2's commit body corrected a stale audit cross-ref ("handshake §10 = Error Handling", extensions live at §5), which does not affect errors.md. **0 findings routed to errors.md.**

### B-4 — `acp-framework.md` (C87 #378, 2026-06-22): **B-8 surface confirmed standing**

ACP §10 still defines `W4_ERR_ACP_*` codes including the `W4_ERR_ACP_LEDGER_WRITE` ↔ SAL `W4_ERR_LEDGER_WRITE` collision and the SCOPE/WITNESS overlaps (B-8). No change to the parallel-naming surface. CROSS-TRACK, unchanged. **0 findings routed to errors.md.**

---

## §C — Fresh Internal-Consistency Pass (refute-by-default)

Focused recheck of the 154-line file. **0 net-new internal contradictions:**

- **§2 ↔ §3 examples**: all three §3 examples (codes/statuses/titles) match their §2 rows (verified A.1).
- **§2 statuses ⊆ §5 list**: §2 uses exactly {400, 401, 403, 408, 409, 410, 429, 503}; §5 lists exactly those 8 — no orphan, no omission (C66-1 refutation still holds).
- **§1 example ↔ §2.1**: "Binding Already Exists"/409/`W4_ERR_BINDING_EXISTS` = §2.1 L45.
- **§1 Fields ↔ examples**: every example carries the Web4-mandated `status`+`title`+`code`; `type` defaults to `about:blank`; `detail`/`instance` optional and present. Consistent with §1 L28–35.
- **§1 extender convention ↔ corpus**: the `W4_ERR_*` (SAL/ACP/metering) vs lowercase `web4_*` (mcp §7.6) split is accurate against the live, moved siblings (§B-1).

### Considered-and-dismissed (snapshot-presence guard; anti-padding transparency)

- **AGY error codes** — `AGY_INTEGRATION_SUMMARY.md` (L150–155) defines `W4_ERR_AGY_EXPIRED/REVOKED/SCOPE/WITNESS/REPLAY/DELEGATION`, and errors.md §1's extender list does not name AGY. **Dismissed, not net-new**: the AGY summary is dated **2025-09-15** — present at the C30, C66, and C67 snapshots (the C66 5-lens finder pass had it in corpus and did not surface it). Per the **snapshot-presence guard**, a pre-existing condition is not a delta finding. On the merits it is also **not a defect**: errors.md §1 lists *normative framework homes* (`acp-framework.md` §10, not `ACP_INTEGRATION_SUMMARY.md`); AGY has only a summary doc (no normative `agy-framework.md` exists — `find` confirms), and the parallel `ACP_INTEGRATION_SUMMARY.md` (6 `W4_ERR_*` codes) is likewise correctly omitted. At most a latent INFO; no route.

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| — | — | **0 net-new distinct findings** | — |

**Totals**: 0 HIGH, 0 MEDIUM, 0 LOW, 0 INFO net-new = **0 distinct new findings**.

**§A**: 3/3 C67 autonomous fixes HELD token-by-token, 0 regressed. All standing carries STAND; **1 carry sub-facet (B-H1 "Section X.Y placeholder") RESOLVED downstream by C71**, leaving a stale C66-A.3 note (recorded here); **1 carry (B-1) REINFORCED** by the unchanged handshake §10 mirror + the new §7.7.7 lowercase codes.

**§B**: 4 moved siblings (mcp C77, registries C71, handshake C73, acp C87) → 0 findings routed to errors.md; net effect is 1 sub-facet resolution + 2 reinforcements + carries stand.

**§C**: 0 net-new internal contradictions; AGY omission dismissed via snapshot-presence guard.

---

## Key Adjudication

1. **Eighth consecutive frozen target; pattern fully locked.** errors.md joins SOCIETY_SPEC/dictionary/SOCIETY_METABOLIC/SAL/LCT/ISP/entity-types as a frozen 2nd-delta with 0 autonomous defects. Files churn slower than the audit cadence; §A = verification, §B yield is entirely the corpus-delta surface.

2. **A sibling's own remediation can resolve a sub-facet of a carry routed at this file.** C71-B-A2 filled the `error-codes.md` placeholder that B-H1 flagged — so the bidirectional carry re-check (C62/C64 method) paid out: the C66-A.3 "placeholder unfilled" note is now stale, while the *underlying* canonicity design-Q (B-D1 SSOT inversion) remained explicitly operator-gated. The delta re-audit must distinguish the resolved sub-facet from the still-open design-Q rather than blanket-asserting "B-H1 unchanged."

3. **A moved sibling can REINFORCE a downstream cross-ref rather than break it** (the C104/atp-adp pattern, repeated). mcp C77 added §7.7.7 lowercase `web4_*` codes, strengthening errors.md §1's "mcp uses lowercase `web4_*`" claim. The corpus-delta surface is not only a risk surface — it can also two-side-verify a prior remediation.

4. **The B-1 design-Q's coordination cost is unchanged.** All 5 mirrors (errors.md §2.4, test-vector, SDK, initial-registries, handshake §10) still carry `AUTHZ_DENIED`@401; handshake's "scope write:lct" detail at 401 keeps reinforcing the RFC inconsistency. Recommend 403, but it remains a coordinated operator decision, not autonomous.

---

## Next-Turn Carry

- **C107 errors.md remediation slot = NO-OP** (0 autonomous findings — consistent with C95/C97/C99/C101/C103/C105). Nothing to apply inside errors.md.
- **Stale-note cleanup (optional, future)**: the C66-A.3 ledger says B-H1's "Section X.Y placeholder still unfilled" — superseded by C71-B-A2. The numeric-registry **canonicity** design-Q (B-D1 SSOT inversion) remains the live operator item.
- **Rotation advances to next-oldest** per the fixed-order round-robin. After errors (now C106), the next file in the order is **`security-framework.md`** (last audited C68/C69, 2026-06-16) → its 2nd-delta (≈C108, lineage C31→C68→C69→C108). [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, SAL, LCT, ISP, entity-types, errors, **security**, registries, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.]
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: B-1 AUTHZ_DENIED 401→403 (5-mirror coordinated) + B-M1 distributed error ownership (4 sites) + B-H1 numeric-registry canonicity / B-D1 SSOT inversion + B-M3 W4IDp form. **Cross-track (other owners)**: B-2 initial-registries mirror, B-4 SDK docstring, B-5 SDK↔mcp statuses (3 codes), B-8 ACP/SAL ledger-write, B-9 cross-society vectors, B-M2 `web4://` SSOT, C16-H1-remainder (3 SAL §9 codes), C16-M8/B6 chapter-law.ttl, I2 QUICK_REFERENCE, I3 content-type. **Do not self-apply any.**
- **D0 (protocols/ cluster) still operator-gated** — unrelated to errors; do not touch.
