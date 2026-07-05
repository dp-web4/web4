# C138 — `errors.md` Third Delta Re-Audit (4th pass)

**Audit ID**: C138
**Target**: `web4-standard/core-spec/errors.md` (154 lines) — the Web4 core RFC-9457 error taxonomy
**Date**: 2026-07-05
**Auditor**: autonomous web4 session (legion, slot `000036`), v2 protocol
**Type**: **Third delta re-audit** (4th pass overall). Lineage: **C30** (first-pass, 2026-06-04, PR #268 → remediation #269 `aaa2bd86`) → **C66** (first delta, 2026-06-17, PR #345) → **C67** (remediation, 2026-06-17, PR #347 `6189432d`, applied 3 autonomous: B-3/B-6/B-7) → **C106** (second delta, 2026-06-27, PR-logged, **0 net-new**) → **C138**.
**Method note**: This is a frozen-target 3rd-delta wrap. `errors.md` is **byte-identical since C67** (`git log` last touch = `6189432d`, 2026-06-17 10:03; banner `Last-Updated: 2026-06-17` accurate; `grep -c '&#'` = 0). Per the established frozen-wrap proportionality precedent (policy-reviewed and APPROVED this fire), the audit is a single-analyst fresh-internal pass + moved-sibling corpus-delta, **not** a multi-agent finder fleet. §A done by hand against live files + git; §B is the corpus-delta surface (siblings that moved since the **C106 snapshot**, 2026-06-27); §C a focused refute-by-default internal pass. All three moved-sibling calls were verified at **cited-hunk granularity** via `git show`, not from memory.

---

## Scope & Methodology

Because `errors.md` is unchanged since its C67 remediation, §A applies the **C56 completeness method** (audit the remediation's *claims* token-by-token, not merely "is the edit present") and the **bidirectional carry re-check** (C62/C64: a downstream sibling's own remediation may RESOLVE a carry routed here, leaving a stale note — or HARDEN it). §B follows the frozen-wrap lesson (C90/C102/C104/C106): the yield lives entirely on the **corpus-delta surface** — diff the cross-refs of the siblings that moved since the last audit snapshot, and apply the **snapshot-presence guard** (C98: do not report a divergence as net-new if it was already present at the prior audit snapshot).

Severity: **HIGH** correctness/normative contradiction; **MEDIUM** consumer-affecting inconsistency / wrong citation; **LOW** hygiene; **INFO** forward-awareness.
Routing: **AUTONOMOUS** (fixable in `errors.md`, no design decision), **DESIGN-Q** (operator), **CROSS-TRACK** (lands in another file).

---

## §A — Prior-Finding Verification (C67 remediation + C106 findings → current)

### A.1 — The 3 AUTONOMOUS C67 fixes: **all HELD by byte-freeze**

`errors.md` has not changed a byte since C67 (`6189432d`). The C106 2nd-delta already verified all three token-by-token and found them HELD; the byte-freeze mechanically preserves that verdict. Re-confirmed against the live file:

| C66 ID | C67 fix | Verdict | Evidence (current `errors.md`) |
|---|---|---|---|
| **B-3** (MED, priority) | §1 rescope: scope `W4_ERR_*` to SAL §9 / ACP §10 / metering §6; name mcp §7.6 separately as lowercase `web4_*` | **HELD + RE-REINFORCED** | §1 L9 unchanged. Re-verified against the **moved** mcp source (C117) — see §B-1: mcp §7.6 remains all-lowercase `web4_*`, `grep -c W4_ERR mcp-protocol.md` = 0. |
| **B-6** (LOW) | §5 retitle "HTTP Status Code Mapping" → "Status Code Semantics" + transport-agnostic lead | **HELD** | §5 L141 "## 5. Status Code Semantics"; L143 lead presents HTTP reason phrases as "canonical *illustrative labels* … same semantic class applies over non-HTTP transports". |
| **B-7** (LOW) | §5 401/403 prose sharpened to mirror §2's deliberate split | **HELD** | §5 L146/L147 still mirror §2.4's DENIED@401 / SCOPE@403 split without reassigning any status. |

No `&#` / encoding artifacts; §3 examples still consistent with §2 (§3.1 AUTHZ_DENIED/401/"Authorization Denied" = §2.4 L72; §3.2 WITNESS_QUORUM/409/"Quorum Not Met" = §2.3 L66; §3.3 AUTHZ_RATE/429/"Rate Limit Exceeded" = §2.4 L75). PR #347 touched only `errors.md` (single-file diff), so the cross-file regression surface is nil.

### A.2 — Bidirectional carry re-verification (against the current, further-moved corpus)

The C106 ledger left 4 DESIGN-Q (B-1, B-H1/B-D1, B-M1, B-M3), a set of CROSS-TRACK carries (B-2, B-4, B-5, B-8, B-9, B-M2, C16-H1-remainder, C16-M8/B6), and 2 INFO (I2, I3). Re-checked against the current corpus, with attention to the siblings that moved **since C106** (mcp C117, acp C126, handshake C113 — see §B):

| Carry | Status now | Note |
|---|---|---|
| **B-1** `AUTHZ_DENIED`@401 vs RFC 403 + sibling `AUTHZ_SCOPE`@403 (DESIGN-Q + coordinated CROSS-TRACK) | **STANDS; handshake mirror re-confirmed @401 post-C113** | The handshake §10 mirror is one of the 5 coordination sites. **C113 (#404, 2026-06-29) did NOT touch §10's error example** — verified at hunk granularity (§B-3): C113's changed lines are the banner date, the W4-IOT-1 suite-row `CBOR→COSE`, and a Sig-structure prose clarification. `web4-handshake.md` L250–251 is still `"status": 401 / "code": "W4_ERR_AUTHZ_DENIED"`. Coordinated change across errors.md §2.4 + test-vector + SDK + initial-registries + handshake §10 still required; recommend 403 on RFC 9110 §15.5.4 grounds. Operator-gated. |
| **B-H1 / B-D1** numeric `registries/error-codes.md` orphan + SSOT inversion (DESIGN-Q) | **STANDS; sub-facet stayed resolved** | `error-codes.md` last moved at C71 (`3f1d6fad`, 2026-06-18) — **not moved since C106**. The C71-B-A2 placeholder→pointer resolution (recorded at C106) holds; the underlying canonicity design-Q (numeric registry orphaned, errors.md §2 never references it, B-D1 SSOT inversion explicitly operator-gated) STANDS unchanged. |
| **B-2 / X2** `initial-registries.md` divergent core-taxonomy mirror (CROSS-TRACK) | **STANDS** | `registries/initial-registries.md` last moved C71 (`3f1d6fad`, 2026-06-18) — **not moved since C106**. §2-absent codes still present; errors.md §2 still does not define them. |
| **B-4** SDK docstring "canonical per errors.md / 30 codes 7 cats" over-claim (CROSS-TRACK) | **STANDS** | SDK-side fix; errors.md §2 still 24/6. |
| **B-5** SDK cross-society statuses (404/400/403) diverge from mcp §7.6 (403/409/412) (CROSS-TRACK) | **STANDS; mcp source re-confirmed stable post-C117** | mcp §7.6 statuses re-verified after the C117 move (§B-1): still `403 unrecognized_lct` (L520), `409 exchange_invalid` (L521), `409 law_conflict` (L522), `412 witness_required` (L523). Divergence is entirely SDK-side; mcp owns canonicity. |
| **B-8 / X3** ACP §10 / SAL §9 parallel-naming + ledger-write collision (CROSS-TRACK) | **STANDS; acp §10 re-confirmed post-C126** | acp C126 (§B-2) renamed only `resourceCaps` guard fields — the §10 error-code surface is untouched; `W4_ERR_ACP_LEDGER_WRITE` still at L537 vs SAL bare `W4_ERR_LEDGER_WRITE`. CROSS-TRACK, unchanged. |
| **B-9** no cross-society test vectors (INFO/CROSS-TRACK) | **STANDS** | Add after B-5 settles. |
| **B-M1** centralized-vs-distributed error ownership (DESIGN-Q) | **STANDS, load-bearing across 4 sites** | metering, ACP (B-8), numeric registry (B-H1), textual registry (B-2). Unchanged. |
| **B-M2** `web4://` SSOT in `data-formats.md` (CROSS-TRACK) | **STANDS** | unchanged. |
| **B-M3** W4IDp `w4idp-ABCD` form (DESIGN-Q, inherited C29) | **STANDS** | all 3 `instance` URIs still hyphen form; corpus-wide identifier decision. |
| **C16-H1-remainder / C16-M8/B6** SAL §9 3 codes + `chapter-law.ttl` (CROSS-TRACK, SAL/ontology) | **STANDS** | SAL last moved C59 (`0d756773`, 2026-06-15) — **not moved since C106**; SAL C134 3rd-delta AUDIT (2026-07-04) applied no mutation. Route to operator/SAL. |
| **I2** `QUICK_REFERENCE.md` custom `type` URI (INFO/CROSS-TRACK) | **STANDS** | unchanged. |
| **I3** content-type over negotiated transports (INFO) | **STANDS** | §4 unchanged (correct — INFO). |

**No carry resolved into a defect; no carry regressed. B-1 REINFORCED again** by the C113-unchanged handshake §10 mirror. **B-5/B-8 re-confirmed stable** against their now-moved owning siblings (mcp C117, acp C126).

---

## §B — Corpus-Delta Pass (siblings that moved since the C106 snapshot, 2026-06-27)

Of the 5 siblings cited by `errors.md` (or holding its mirrored data), exactly **three moved since C106**: mcp (C117), acp (C126), handshake (C113). core-protocol.md (last 2026-06-05), web4-metering.md (last 2026-04-29), SAL (last 2026-06-15), error-codes.md / initial-registries.md (last C71 2026-06-18) are all **pre-C106** and unchanged. Each fresh mover is a C-series remediation; diffed at cited-hunk granularity for errors-relevant impact:

### B-1 — `mcp-protocol.md` C117 (#422, 2026-06-30): **REINFORCES errors.md §1; 0 net-new**

C117 applied C116-N1: a **one-line** §12 MUST#6 relocation — moving "for high-consequence actions," to govern the whole witnessing clause (closing a C77 remediation-introduced over-tightening regression). The single changed line is `-6. R7 actions MUST be witnessed: an R7 transaction MUST NOT proceed without witnessing (§7.5)…` → `+6. R7 actions MUST be witnessed: for high-consequence actions, an R7 transaction MUST NOT proceed…`. This is a **witnessing-MUST scoping** edit — categorically disjoint from the §7.6 error taxonomy. Re-verified: `grep -c W4_ERR mcp-protocol.md` = **0**; §7.6 failure table (L520–523) still all lowercase `web4_cross_society_*`, and the §7.7.7 refinement note (L527) still lowercase `web4_rate_*`. errors.md §1 L9's characterization ("mcp §7.6 currently uses lowercase `web4_*`") is **two-sided-verified and re-reinforced**. **0 findings routed to errors.md.**

### B-2 — `acp-framework.md` C126 (#437, 2026-07-02): **B-8 surface confirmed standing; 0 net-new**

C126 applied C125-M3: `resourceCaps` guard fields renamed snake_case→camelCase (`max_atp`→`maxAtp`, `max_executions`→`maxExecutions`, `rate_limit`→`rateLimit`) in the guards example and the plan-validation code snippet. Verified at hunk granularity: the changed lines are **exclusively** guard-field renames — **zero** error-taxonomy lines touched. ACP §10 still defines `W4_ERR_ACP_*` including the `W4_ERR_ACP_LEDGER_WRITE` (L537) ↔ SAL `W4_ERR_LEDGER_WRITE` collision (B-8) and the SCOPE/WITNESS overlaps. CROSS-TRACK, unchanged. **0 findings routed to errors.md.**

### B-3 — `web4-handshake.md` C113 (#404, 2026-06-29): **B-1 mirror re-confirmed still @401; 0 net-new**

C113 applied 2 autonomous C112 findings. Verified at hunk granularity: the changed lines are (a) the `Last-Updated` banner (2026-06-18→2026-06-29), (b) the W4-IOT-1 crypto-suite row `AES-CCM … CBOR`→`COSE`, and (c) a Sig-structure prose clarification (splitting `COSE_Sign1` envelope-signing from `HandshakeAuth`'s `Hash(TH || channel_binding)` input per §6.0.5). **None touch §10 (Error Handling).** The §10 `W4_ERR_AUTHZ_DENIED` example (L250–251) is still `status: 401`. The B-1 design-Q's coordination-site count and cost are unchanged. Note: the C113 Sig-structure prose *mentions* "LCT binding, Metering" as non-handshake signed-payload examples, but introduces **no error codes** — disjoint from the errors taxonomy. **0 findings routed to errors.md.**

---

## §C — Fresh Internal-Consistency Pass (refute-by-default)

Focused recheck of the 154-line file (refute-by-default applied to the auditor's own candidates — each read at its call site). **0 net-new internal contradictions:**

- **§2 ↔ §3 examples**: all three §3 examples (codes/statuses/titles) match their §2 rows (§A.1).
- **§2 statuses ⊆ §5 list**: §2 uses exactly {400, 401, 403, 408, 409, 410, 429, 503}; §5 (L145–152) lists exactly those 8 — no orphan, no omission.
- **§1 example ↔ §2.1**: "Binding Already Exists"/409/`W4_ERR_BINDING_EXISTS` = §2.1 L45.
- **§1 Fields ↔ examples**: every example carries the Web4-mandated `status`+`title`+`code`; `type` defaults to `about:blank`; `detail`/`instance` optional and present. Consistent with §1 L28–35. The §1 note that `instance` path segments are "illustrative" (L35) is consistent with the hyphen-form `w4idp-ABCD` URIs (the form itself is the B-M3 corpus-wide design-Q, not an internal contradiction).
- **§1 extender convention ↔ corpus**: the `W4_ERR_*` (SAL/ACP/metering) vs lowercase `web4_*` (mcp §7.6) split is accurate against the live, moved siblings (§B-1/§B-2).

### Considered-and-dismissed (snapshot-presence guard; anti-padding transparency)

- **AGY error codes** — `AGY_INTEGRATION_SUMMARY.md` defines `W4_ERR_AGY_*` codes not named in errors.md §1's extender list. **Dismissed, not net-new** (same adjudication as C106 §C): the AGY summary predates the C30/C66/C67/C106 snapshots; per the snapshot-presence guard a pre-existing condition is not a delta finding. On the merits, errors.md §1 lists *normative framework homes* (`acp-framework.md` §10, not `*_INTEGRATION_SUMMARY.md`); no normative `agy-framework.md` exists, so AGY's summary-only codes are correctly omitted, as are the parallel `ACP_INTEGRATION_SUMMARY.md` codes. At most a latent INFO; no route.
- **handshake C113's new "LCT binding, Metering" prose (§B-3)** — considered as a potential net-new cross-society/error touchpoint; dismissed on read: it introduces no error code and only clarifies which signed-payload signing rule applies. Not an errors.md surface.

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| — | — | **0 net-new distinct findings** | — |

**Totals**: 0 HIGH, 0 MEDIUM, 0 LOW, 0 INFO net-new = **0 distinct new findings**.

**§A**: 3/3 C67 autonomous fixes HELD by byte-freeze, 0 regressed. All standing carries STAND; **B-1 REINFORCED** by the C113-unchanged handshake §10 mirror; **B-5/B-8 re-confirmed stable** against their now-moved owning siblings (mcp C117, acp C126). No carry resolved into a defect.

**§B**: 3 moved siblings (mcp C117, acp C126, handshake C113) → **0 findings routed to errors.md**; net effect is 3 reinforcements/confirmations + carries stand.

**§C**: 0 net-new internal contradictions; AGY omission + C113 prose dismissed via snapshot-presence guard / on-read.

**This is `errors.md`'s 2nd CONSECUTIVE fully-clean delta (C106 + C138), 0 net-new.**

---

## Key Adjudication

1. **Frozen target, sibling-side yield — pattern holds a 4th pass.** errors.md is byte-identical since C67 (18 days). As with every recent 3rd-delta (LCT/ISP/SAL/metabolic/dictionary/entity-types), the yield is on the SIBLINGS, not the bytes — and this fire all three fresh movers were disjoint from the error taxonomy.

2. **All three movers were "adjacent-but-disjoint" via a single mechanism: they touched a DIFFERENT normative surface of a cited sibling than the one errors.md cross-refs.** mcp C117 = §12 witnessing-MUST (errors.md cites mcp §7.6 error codes); acp C126 = `resourceCaps` guard fields (errors.md cross-refs acp §10 error codes); handshake C113 = crypto-suite row + Sig-structure prose (errors.md's B-1 mirror lives in handshake §10). The disjointness test is **"which section did the mover touch vs which section does the target cite"** — verified at cited-hunk granularity, not from the commit subject.

3. **A moved sibling can REINFORCE a downstream cross-ref (repeat of the C104/C117 pattern).** mcp C117's witnessing edit left §7.6 all-lowercase, re-reinforcing errors.md §1's "mcp uses lowercase `web4_*`" characterization — the corpus-delta surface two-side-verified a prior remediation rather than staling it.

4. **The B-1 design-Q's coordination cost is unchanged.** All 5 mirrors (errors.md §2.4, test-vector, SDK, initial-registries, handshake §10) still carry `AUTHZ_DENIED`@401; handshake C113 did not touch its §10 example. Recommend 403, but it remains a coordinated operator decision, not autonomous.

---

## Next-Turn Carry

- **C139 errors.md remediation slot = NO-OP** (0 autonomous findings — consistent with the frozen-wrap no-op precedents). Nothing to apply inside errors.md → rotation advances.
- **Rotation advances to next-oldest.** After errors (now C138, 3rd delta), the next file in the fixed-order round-robin is **`security-framework.md`** → its 3rd-delta (lineage C31→C68→C69→C108→**C140**). [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, SAL, LCT, ISP, entity-types, errors, **security**, registries, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.]
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: B-1 AUTHZ_DENIED 401→403 (5-mirror coordinated) + B-M1 distributed error ownership (4 sites) + B-H1 numeric-registry canonicity / B-D1 SSOT inversion + B-M3 W4IDp form. **Cross-track (other owners)**: B-2 initial-registries mirror, B-4 SDK docstring, B-5 SDK↔mcp statuses (3 codes), B-8 ACP/SAL ledger-write, B-9 cross-society vectors, B-M2 `web4://` SSOT, C16-H1-remainder (3 SAL §9 codes), C16-M8/B6 chapter-law.ttl, I2 QUICK_REFERENCE, I3 content-type. **Do not self-apply any.**
- **D0 (protocols/ cluster) still operator-gated** — unrelated to errors; do not touch.
