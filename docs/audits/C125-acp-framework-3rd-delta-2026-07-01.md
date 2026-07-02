# C125 — ACP Framework Third-Delta Re-Audit

**Date:** 2026-07-01
**Auditor:** Autonomous session `legion-web4-20260701-180036`
**Document audited:** `web4-standard/core-spec/acp-framework.md` (709 lines)
**Method:** §A hand-verification against the live spec + SDK + schema + vectors. §B multi-agent refute-by-default workflow (3 primitive-clustered finders — mcp/agency-envelope drift, atp-adp/t3-v3 drift, cross-section internal-consistency blindspot — every cited line re-read against live source before a verdict; refute unless a named authority genuinely contradicts the spec).
**Lineage:** C-series **third-delta** re-audit. First-pass internal-consistency **C18** (`docs/audits/acp-framework-internal-consistency-2026-05-28.md`, 11 findings, remediated PR #244 `1bb9bcaa`). First delta **C37** (`C37-acp-framework-audit-2026-06-07.md`, §A 12 / §B 37, remediated PR #283 `c43822e9`). Second delta **C86** (`C86-acp-framework-2nd-delta-2026-06-22.md`, §A 30/30 held / §B 18 findings). Remediation **C87** (PR #378 `31cea0b0`, applied C86's 8 autonomous findings). **C125** re-verifies the C87 state and surfaces drift introduced since #378 by churned canonical neighbors.

---

## Instrument note — why ACP, why now

Rotation lands the audit pointer on acp-framework (reputation-computation → acp per the fixed-order round-robin). The target is **byte-frozen since C87** (`git diff 31cea0b0 HEAD -- acp-framework.md` = empty). As with every wrap onto a frozen target, the yield surface is (1) **remediation-completeness + remediation-introduced-regression** — did C87's own edits (footnote arithmetic, SPARQL rewrite) hold *and* stay correct — and (2) the **corpus-delta / inbound-carry surface**: ACP's canonical neighbors churned again after #378 — **mcp-protocol.md C117** (#422, `afab0c43`), **atp-adp-cycle.md C119** (#420, `e99b419e`), **t3-v3-tensors.md C122** (#427, `b2a98f7c`) — and ACP *references* all three (§4.2 agency envelope ← mcp; §2.4 atpConsumed ← atp-adp §2.3; §2.4 t3v3Delta ← t3-v3) while none reference ACP back. A third-delta is the instrument that catches one-directional mirror-drift. The **chapter-law → hub-law rename (#412)** is also live corpus-wide; ACP contains **no** `chapter` reference (`grep` clean) so it is unaffected.

---

## Authority Hierarchy

| Claim class | Authority (highest → lowest) | Files |
|-------------|------------------------------|-------|
| Wire shape / field presence | Conformance vectors → JSON-LD schema → SDK serializers → spec example | `test-vectors/acp/plan-operations.json`, `schemas/acp-jsonld.schema.json`, SDK `acp.py`, `acp-framework.md` |
| Error taxonomy | Canonical `errors.md` → SDK error classes → spec §10.1 | `core-spec/errors.md`, SDK `acp.py`, `acp-framework.md` §10 |
| State machine | SDK `VALID_TRANSITIONS` + tests → vector `acp-002` → spec §3 | SDK `acp.py` L173-181, `plan-operations.json`, `acp-framework.md` §3 |
| ATP / energy | Canonical `atp-adp-cycle.md` → SDK → spec | `core-spec/atp-adp-cycle.md`, `acp-framework.md` §2.4/§5.1 |
| Agency proof envelope | Consuming-spec `mcp-protocol.md` `web4_context` → spec | `core-spec/mcp-protocol.md` §4.1/§7.4, `acp-framework.md` §4.2 |
| Trust dims / RDF | T3/V3 spec + ontology TTLs → spec §2.4/§8 | `core-spec/t3-v3-tensors.md`, `ontology/*.ttl`, `acp-framework.md` |

---

## §A — C86/C87 Finding Delta Re-Verification

### §A.1 — C87's 8 applied autonomous fixes (HELD + CORRECTNESS re-check)

The C87 remediation diff (`31cea0b0`, +45/−15, single file) was re-read line-by-line against the live spec. **All 8 are HELD (edit present and still correct):**

| Fix (C86 id) | Live evidence | State |
|---|---|---|
| **B1** strip 4 leading-`+` literals | §2.4 L162-163 `temperament:0.01`/`valuation:0.02`; §6.2 L384-385 `t3:0.05`/`v3:0.03` — no signed literals remain; all 7 json fences parse | HELD |
| **B2** footnote miscount 6+7 → 5+8 | §3.2 footnote L234 now "**five**" `→Failed` edges + "**eight**" explicit rows = **13** | HELD **+ arithmetically CORRECT** (see §A.2) |
| **B3** witness type `audit`→`audit-minimal` | §5.2 L331 `"types": ["time", "audit-minimal"]` (+ "Witness Role Registry roles" gloss) | HELD |
| **B4** declare §8.2's 3 predicates in §8.1 | §8.1 L444 `acp:executedIntent`; L447 `acp:status`; L448 `acp:atpConsumed` + record→result edges | HELD |
| **B5** rewrite invalid SPARQL | §8.2 L455-473 — aggregates only in SELECT, `SUM(IF(...))` conditional count, `?agent` grouped; explanatory note L475-478 | HELD + valid |
| **B6** §11 illustrative/non-normative note | §11 L599-607 (names the disjoint use-case guard keys; asserts the canonical §2.1 guard model) | HELD |
| **B7** `atpConsumed` == atp-adp §2.3 discharge x-ref | §2.4 ATP-accounting note L171-176 | HELD + correct (see §A.3) |
| **B10** add `createdAt` to §2.1 example | §2.1 L90 `"createdAt": "2025-09-15T15:30:00Z"` | HELD |

**0 regressions among applied fixes.**

### §A.2 — Remediation-introduced-regression re-check (C87's own new prose)

The [[feedback_remediation_introduced_regression]] class recurred at C86 (#283's footnote said 6+7), C121 (#283→C83 reword), and C123 (#376 §4 fail-closed). **C87 does NOT recur it — its two computed/generated edits are correct:**

- **B2 footnote (L234).** Verified against SDK `VALID_TRANSITIONS` (acp.py L173-181): exactly **5** states carry a `→FAILED` edge (`PLANNING`, `INTENT_CREATED`, `APPROVAL_GATE`, `EXECUTING`, `RECORDING`); `IDLE`, `COMPLETE`, `FAILED` do not. The §3.2 table has **8** explicit non-wildcard rows. 5 + 8 = **13**, and the full `VALID_TRANSITIONS` map totals 13 edges — matching vector `acp-002 totalValidTransitions=13`. The corrected footnote is sound.
- **B5 SPARQL (§8.2).** Re-inspected: aggregates confined to `SELECT`, conditional count is `SUM(IF(...))` (not `COUNT(IF(...))`), single non-aggregated projection `?agent` is grouped — structurally valid SPARQL 1.1 (the PR reports validation under rdflib 7.6.0). No new defect.

**C87 is a clean remediation.** Worth recording: the remediation-introduced-regression class is *not* universal — a carefully-verified remediation avoids it (contrast C86-B2/C121/C123).

### §A.3 — Still-open carries (current state vs churned authorities)

| Carry | C86 state | C125 state | Evidence |
|---|---|---|---|
| **M3** — `resourceCaps` snake_case in examples vs camelCase authority | STILL-OPEN | **STILL-OPEN + INTRA-DOC-SHARPENED → now AUTONOMOUS-recommend** | §2.1 L77-79 `max_atp`/`max_executions`/`rate_limit` and §5.1 L312 `resourceCaps.max_atp` are snake_case; schema `$defs.ResourceCaps` L56-58 = `maxAtp`/`maxExecutions`/`rateLimit`; SDK `to_jsonld` emits camelCase. **New at C125:** C87-B6's §11 note (L604) *itself* asserts the canonical form `resourceCaps{maxAtp,maxExecutions,rateLimit}`, and every *other* key in the §2.1 `guards` object is camelCase (`lawHash`, `witnessLevel`, `humanApproval`, `autoThreshold`, `expiresAt`, `createdAt`). So M3 is now an **intra-document self-contradiction** (§11 note ⊥ §2.1/§5.1 examples), not merely a spec-vs-schema drift. It is cleanly spec-local AUTONOMOUS (align the 3 example keys + 1 usage to camelCase). See §B routing. |
| **M6 / B-M6** — 11 `acp:` predicates in §8 absent from all TTLs | STILL-OPEN | **STILL-OPEN (unchanged)** | `grep acp: ontology/*.ttl` = 0; no `acp-ontology.ttl` (only a planned-files comment in `web4-core-ontology.ttl`). C87-B4 added the 3 §8.2 predicates to §8.1 prose but not to any TTL — intra-doc closed, ontology-track open. CROSS-TRACK. |
| **M7** — integer `witnessLevel` vs structured `witness_requirement` | STILL-OPEN | **STILL-OPEN (unchanged)** | §2.1 L81 / §5.1 L316 integer `witnessLevel`; §5.2 L328-338 structured `{level,types,quorum{model,threshold},timeout,fallback}`. SDK implements only the integer model. No bridge. |
| **L1 / B-AGENCY** — `web4_context` proofOfAgency casing + field-set + `agency_chain` | HARDENED/WIDENED | **STILL-OPEN (unchanged after mcp C117)** | Re-verified by finder-1 vs the **current** mcp file: §4.1 `proof_of_agency` still `{grant_id, scope}` (snake_case); §7.4 `agency_chain` still present (L452, L484-488). ACP §4.2 `proofOfAgency` still 7-key camelCase. **C117 remediated §12 (witnessing summary) only — it did NOT touch §4.1 or §7.4**, so all four B-AGENCY components (casing, field-set disjunction, agency_chain absence, ledgerProof) are unchanged. MEDIUM CROSS-TRACK. |
| **C37-5 / B-LEDGERPROOF** — §4.2 `ledgerProof {grantBlock,grantHash,inclusionProof}` | collapsed-then-migrated | **STILL-OPEN (unchanged)** | Sole in-doc ledger object (§4.2 L281-285); absent from schema `$defs.ProofOfAgency` (`additionalProperties:false`, admits `{grantId,planId,intentId,nonce,audience,expiresAt}`) and SDK `ProofOfAgency` (acp.py L592-604) → schema-rejected. Diverges from the R6/R7-shared `{txHash,blockHeight,inclusionProof}`. DESIGN-Q. |
| **B8** — ACP discharge not routed through R6 | STILL-OPEN CROSS-TRACK | **STILL-OPEN (unchanged after atp-adp C119)** | Re-verified vs the **current** atp-adp file: §7.1 **#5** "Discharging MUST occur through R6 transactions" persists; **C119 added #6** (entity-level value / society-aggregate carve-out) and did NOT touch #5. ACP §9.1 MUST list (L484-488) still contains no R6-discharge requirement. Unbridged linkage, not a conservation contradiction. CROSS-TRACK. |
| **t3v3Delta consistency** — sparse single-root delta (REFUTED at C86) | REFUTED (non-finding) | **REFUTATION HOLDS (unchanged after t3-v3 C122)** | Re-verified vs the **current** t3-v3 file: 3-root open-RDF-subgraph model intact (Talent/Training/Temperament, Valuation/Veracity/Validity via `web4:subDimensionOf`); §2.3 outcome table permits partial updates. **C122 edited only §10.2 (ATP-conservation citation re-anchoring), not the tensor model or update rules.** The §2.4 sparse `{agent:{t3:{temperament:0.01}}, client:{v3:{valuation:0.02}}}` remains consistent. |

**Snapshot-presence guard applied.** All three neighbors that MOVED since C87 edited **outside** ACP's cross-ref surface: mcp C117 → §12; atp-adp C119 → §7.1 #6; t3-v3 C122 → §10.2. Cited hunk locations prove the inbound surface is clean — the same clean-inbound pattern C123 recorded for reputation.

---

## §B — New / Hardened Findings (this delta)

**Method:** 3 primitive-clustered finders → refute-by-default verify (re-read every cited line; refute unless a named authority genuinely contradicts). Finder yield below.

### Summary by severity

| Severity | Count | IDs |
|----------|-------|-----|
| MEDIUM | 0 net-new | — (B-AGENCY, B-LEDGERPROOF re-confirmed in §A, unchanged) |
| LOW | 0 net-new | — |
| INFO | 0 net-new | — |
| **Net-new confirmed** | **0** | **First clean ACP delta** (C37 first / C86 second / C125 clean) |
| Refuted overcalls | 2 | F2 dead-branches, F3 else-dispatch |
| Carries re-confirmed | 6 | M3(+sharpen), M6, M7, B-AGENCY, B-LEDGERPROOF, B8 |
| Refutations that HELD | 1 | t3v3Delta single-root consistency |

### Refuted overcalls (load-bearing — they corroborate §A's internal-consistency verdict)

- **F2 — "§10.1 error classes handled in §10.2 but never raised = dead branches."** REFUTED. The §10.2 preamble (L552-558) *explicitly* states recovery "dispatches over the §10.1 error **taxonomy** … not over the raise-site inventory." The §4.1/§5.1 code are *illustrative fragments*, not the complete raise inventory; the handled-but-not-shown classes are raised at their real state-machine sites in the SDK — `InvalidTransition` acp.py L1058/L1090, `PlanExpired` L1072, `ResourceCapExceeded` L1081 (and `ApprovalRequired`/`LedgerWriteFailure` at the approval-gate / ledger-write sites the fragments omit). Anticipatory taxonomy-dispatch handlers are correct defensive design, not a contradiction. Framing them as "dead code" is an overcall.
- **F3 — "NoValidGrant/ResourceCapExceeded raised but only caught by the `else` clause violates the dispatch pattern."** REFUTED. The §10.2 `else: log_error; abort_plan` is the correct *default remedy* for fatal conditions that need no special recovery (no valid grant → abort; over caps → abort). The preamble warns against applying the *wrong* remedy (e.g. grant-expansion for a LAW violation); the else-abort applies no wrong remedy. Not every taxonomy class needs an explicit branch. Observation real (not all classes have explicit branches), defect framing overstated.

The 3 finders converged on **zero net-new confirmed findings**: finder-1 (mcp) → B-AGENCY unchanged, 0 net-new; finder-2 (atp-adp/t3-v3) → ATP-note correct + B8 unchanged + t3v3Delta refutation holds, 0 net-new; finder-3 (internal) → 1 carry (M3) + 2 refuted overcalls.

---

## Routing Summary (for the C126 remediation turn)

### AUTONOMOUS — spec-local, canonical authority already correct (recommend apply in C126)

- **M3** (long-standing C18 carry, now intra-doc-sharpened): align the snake_case guard keys to the schema/§11-note camelCase form — §2.1 L77-79 `max_atp`/`max_executions`/`rate_limit` → `maxAtp`/`maxExecutions`/`rateLimit`; §5.1 L312 `.max_atp` → `.maxAtp`. Closes the intra-document self-contradiction between the C87-B6 §11 note (L604) and the §2.1/§5.1 examples. Authority: schema `$defs.ResourceCaps` L56-58 + the doc's own §11 note. **This is the only autonomous item C125 surfaces** — every other observation is a re-confirmed cross-track/design-Q carry or a refuted overcall.

> Note: M3 was carried in C86 §A.2 and *not* folded into C87's autonomous batch (C87 applied only B1/B2/B3/B4/B5/B6/B7/B10). C125 recommends promoting it — it is spec-local, its authority is in-file, and the C87-B6 note now makes it an intra-doc inconsistency.

### DESIGN-Q — operator decision (do NOT self-apply)

- **B-LEDGERPROOF / C37-5:** §4.2 `ledgerProof` admit-vs-strip; if admit, align to R6/R7 `{txHash,blockHeight,inclusionProof}` (couples schema+SDK). Likely strip (agency proof is grant-binding; ExecutionRecord already carries `canonicalHash`).
- **B11 (from C86, corpus-wide):** how subsystem `W4_ERR_*` tables (ACP §10, SAL §9, metering §6) carry title/status onto the errors.md §1 RFC 9457 envelope.
- **B14 (from C86):** define "ACP-critical actions" or reference SAL's enumerated witness set.

### CROSS-TRACK — needs another spec/SDK to move first

- **B-AGENCY (L1):** `web4_context` proofOfAgency casing + field-set + `agency_chain` reconciliation — mcp-owned envelope; couples mcp §4.1/§7.4 + both SDK `ProofOfAgency` classes. **UNCHANGED after mcp C117** (C117 touched §12 only) — remains queued.
- **B8:** ACP execution ↔ R6 discharge linkage (atp-adp §7.1 #5) — **UNCHANGED after atp-adp C119** (C119 added #6, not #5).
- **B12 / B13 (from C86):** ACP §5 witness vocabulary (`byzantine`/`threshold`; `min_witness_level`) ↔ SAL count+policy quorum — couples M7 + SAL.
- **B-M6 / M6:** `acp:` predicates need an `acp-ontology.ttl` (or definitions in an existing TTL) — ontology-track.
- **B15 (from C86):** errors.md L9 metering reference rides the C75 D0 cluster decision.

### Carries re-confirmed / hardened (see §A.3)

M3 STILL-OPEN + intra-doc-sharpened (→ AUTONOMOUS recommend); M6 unchanged; M7 unchanged; L1/B-AGENCY unchanged after mcp C117; C37-5/B-LEDGERPROOF unchanged; B8 unchanged after atp-adp C119. Refutation that HELD: t3v3Delta single-root consistency (unchanged after t3-v3 C122).

---

## Calibration Note

C125 is the **first clean ACP delta** — 0 net-new confirmed findings — because C87 remediated all 8 autonomous items *correctly* (no remediation-introduced regression, unlike #283 which C86 caught) and none of the three neighbors that churned since #378 touched ACP's cross-ref surface. This mirrors the reputation-computation pattern (C123: fifth clean delta on a frozen target). The finder yield is entirely (a) re-confirmed cross-track/design-Q carries whose *neighbors moved but outside the shared surface* (B-AGENCY vs mcp §12, B8 vs atp-adp §7.1 #6, t3v3Delta vs t3-v3 §10.2 — snapshot-presence guard cites each moved hunk) and (b) two refuted internal overcalls (F2/F3) that are load-bearing: both corroborate that ACP's §10 error-handling is internally consistent under its own explicitly-stated taxonomy-dispatch design. The single actionable item — **M3** — is not net-new; it is a C18-era autonomous carry that C87-B6's §11 note *sharpened into an intra-document contradiction*, making it the natural first target for C126.

The remediation-introduced-regression re-check (§A.2) is the load-bearing verification this turn: C87's footnote arithmetic (5+8=13 vs SDK `VALID_TRANSITIONS`) and SPARQL rewrite were re-derived from the authority, not pattern-matched from the prior CONFIRMED C86-B2 — and both are correct. **Frozen ≠ dirty**: here frozen = genuinely clean.

---

*C125 complete. NO spec/SDK/vector/.ttl mutation (AUDIT turn). Next: **C126 remediation turn** — recommend applying **M3** (align resourceCaps snake_case→camelCase in §2.1 L77-79 + §5.1 L312) to `acp-framework.md`; all other items route to operator/existing cross-track queues. Audit-side rotation advances acp → **presence-protocol** (check presence's last audit #: C88 2nd-delta → C89 remediation → next is 3rd-delta). ACP lineage C18 → C37 → C86 → C87 → C125 → (C126).*
