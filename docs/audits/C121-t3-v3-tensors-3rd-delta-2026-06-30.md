# C121 Audit: `t3-v3-tensors.md` Third Delta Re-Audit

**Date**: 2026-06-30
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn, slot `000036`
**Document**: `web4-standard/core-spec/t3-v3-tensors.md` (687 lines)
**Prior passes**: C13 (`t3-v3-tensors-internal-consistency-2026-05-24.md`, 11 findings) → C42 (first delta, 20 actionable) → **C43** remediation (PR #299, 13 edits) → C82 (second delta, `C82-t3-v3-tensors-audit-2026-06-21.md`, 6 new) → **C83** remediation (PR #374, `25d36bb0`, 5 edits F2–F6) → **C121** (this, third delta).
**Methodology**: Third delta re-audit, single-auditor refute-by-default, proportioned to a **byte-frozen** target (HEAD blob `f5dcba0a` == C83 blob, verified) with a bounded corpus delta. §A = C83 fix persistence (byte-identity) + **C56 claim-vs-canonical re-read against the LIVE SDK/vectors** (not the C83-era snapshot) + **bidirectional re-verification** of every open carry (D1/D2/D3/F1/L3). §B = corpus-delta **snapshot-presence guard** on the five siblings that changed since C83 AND cite t3-v3 (atp-adp/mcp/mrh/reputation/referenced-acts) + a **cross-section internal blindspot sweep** for the C118-N1/C116-N1 MUST-vs-reference-impl pattern + confirm/route the **inbound C118-N2** finding.
**Reference materials** (all cross-checks hand-verified against live blobs): SDK `web4-standard/implementation/sdk/web4/trust.py`, vectors `web4-standard/test-vectors/t3v3/tensor-operations.json` (t3v3-008), ontology `web4-standard/ontology/t3v3-ontology.ttl`, siblings `atp-adp-cycle.md` §2.4/§3.1/§3.2/§6.3, `mrh-tensors.md` §5, `mcp-protocol.md`, `reputation-computation.md`, `referenced-acts.md`.

---

## Summary

| | Count |
|---|---|
| **§A** C83 fixes (F2–F6) verified | 5/5 HELD (byte-frozen) — **0 regressed** |
| **§A** C56 claim re-read vs LIVE SDK/vectors | 4/4 accurate (bridge weights, t3v3-008, V3/T3 weights, T3 default) |
| **§A** open carries bidirectionally re-verified | D2/X4 **number sub-facet RESOLVED downstream** (mrh C91); D1/D3/F1/L3 + X4-structural + D2 attach-strategy STILL OPEN |
| **§B** NET-NEW findings surviving verification | **0** |
| **§B** inbound C118-N2 | **CONFIRMED live** (LOW, t3-v3-owned, autonomous-in-file) → next t3-v3 remediation |
| Corpus-delta siblings classified | 5 (4 REINFORCING/neutral, 1 = mrh C91 which RESOLVED the D2 number) |

**Health verdict**: `t3-v3-tensors.md` remains in **excellent health** — the C13→C42→C43→C82→C83 cycle holds with **zero regression**, all 5 C83 edits present, and every C83 claim still numerically accurate against the *current* SDK/vectors (SDK unchanged since Sprint 38, so no drift). The single live actionable item is the **inbound C118-N2** citation-precision defect (introduced by C83's own F2 reword — a mild [[feedback_remediation_introduced_regression]] instance surfaced by the atp-adp sibling audit, not by this file's own delta), routed to the next t3-v3 remediation turn. **0 net-new** from this file's own §B pass. The notable positive result: the C82-D2/X4 Surgeon-number contradiction is now **resolved downstream** by mrh C91 — the C82 routing ("fix lands on the mrh side") worked exactly as designed.

---

## §A — C83 Fix Persistence + C56 Claim Re-Read + Carry Re-Verification

### A.1 — C83 remediations (5/5 HELD, byte-frozen)

Target byte-FROZEN since C83 (`25d36bb0`, 2026-06-21); HEAD blob `f5dcba0a` identical → §A is pure persistence + claim-vs-live re-verification.

| C82 ID (C83 fix) | Location (current) | Status |
|------------------|--------------------|--------|
| **F2** ATP-conservation re-anchored off §2.4 "Slashing" → §6.3 "preserving total supply" | §10.2 L640 | PRESENT — **but see §B/N2**: the reword introduced an anchor/quote mismatch |
| **F3** "mirrors the T3 composite weights" → "parallels the T3 composite *structure* … own weights" | §3.3 L335–337 | HELD |
| **F4** V3-range row: clamping SDK-enforced, no dedicated boundary vector | §10.2 L635 | HELD |
| **F5** SPARQL PREFIX decls (§9.2 `web4:`; §9.3 `rdfs:`, `lct:`) | L544, L570–571, L585–586 | HELD |
| **F6-partial** new §2.5 6D→3D bridge prose + §2.4 names the two multi-device dims as candidate sub-dimensions + §10.2 6D-bridge row → §2.5 | §2.5 L204–246, §2.4 L193–202, §10.2 L637 | HELD |

### A.2 — C56 claim-vs-canonical re-read (against the LIVE SDK/vectors)

Every C83 edit that *added a claim* re-verified against the current blob (the discipline: a byte-accurate edit can still make a claim that has since gone stale):

- **§2.5 bridge formula** (F6): `trust.py:526 trust_bridge()` uses `BRIDGE_PRIMARY_WEIGHT = 0.6` (L87) and `sw = (1.0 − 0.6)/3 = 0.4/3 ≈ 0.1333` (L88 `BRIDGE_SECONDARY_WEIGHT_EACH = 1/3` of remaining 0.4). Primary mapping competence→talent / reliability→training / consistency→temperament; secondaries shared. **Matches §2.5 exactly.** Vector **t3v3-008** worked: inputs (0.7/0.6/0.5/0.8/0.4/0.3) → talent `0.6×0.7 + 0.1333×1.5 = 0.62`, training `0.6×0.6+0.2 = 0.56`, temperament `0.6×0.5+0.2 = 0.50`. **Vector `expected` = {0.62, 0.56, 0.5}. Exact.**
- **§3.3 V3 weights** (F3): SDK `V3_WEIGHTS = {0.3, 0.35, 0.35}` (L78) ≠ `T3_WEIGHTS = {0.4, 0.3, 0.3}` (L77) — the F3 "parallels structure but uses its own weights (V3 0.3/0.35/0.35 distinct from T3 0.4/0.3/0.3)" claim is **still exactly right**.
- **§10.2 rows** (F2/F4): V3-range clamp is `V3.__post_init__` — still present; T3/V3 composite/update/diminishing rows still match SDK constants + vectors.
- **SDK freshness**: `trust.py` last touched Sprint 38 (`759eaefa`), well before C83 → **zero SDK drift since C83**; all C82/C83 numeric claims persist by construction.

### A.3 — Open carries, bidirectional re-verification

| Carry | C82 state | C121 state | Evidence |
|-------|-----------|-----------|----------|
| **D2 / X4 — Surgeon `training` number** (t3-v3 `0.92` vs mrh §5 `0.90`, "confirmed cross-doc contradiction") | HARDENED | **RESOLVED downstream** | mrh C91 (`f0c82118`, #382) changed mrh §5.2 `web4:training 0.90 → 0.92` — now == t3-v3 canonical `0.92` (`mrh-tensors.md:262`). C82 routed the fix "to the mrh side / next mrh re-audit" = C90/C91; **it landed.** The stale C82 "confirmed contradiction" note is now closed. |
| **D2 / X4 — structural duplication** (mrh §5 duplicates Surgeon Turtle + composite SPARQL despite its own canonical-pointer) | OPEN | **STILL OPEN** | mrh §5 still carries the Surgeon Turtle (L254–271) + composite SPARQL BIND (L349). Shrink-to-pointer is an operator DESIGN-Q (routed to mrh per C90). |
| **D2 / N1-N2 attach-strategy** (multi-device flat-8 → 6D→3D bridge; formalize-bridge / declare-sub-dims / both) | OPEN | **STILL OPEN** | operator DESIGN-Q; C120 re-confirmed t3v3-ontology still 3-roots-only. §2.5 (C83) documents the owner-side bridge path but the ontology declaration + multi-device rewrite remain operator-gated. |
| **D1 — ontology-vocab** (`web4:matchesTask` undefined; role IRIs undeclared) | OPEN | **STILL OPEN** | `t3v3-ontology.ttl` untouched since `bedd3bf8` (pre-C83); `matchesTask` has 0 defining triples corpus-wide; §9.2 L549 still uses it. |
| **D3 / M4 — Valuation range** (spec/ontology unbounded vs SDK clamp) | OPEN | **STILL OPEN** | §3.1 L260–267 open-question note intact; SDK `V3.__post_init__` still clamps; ontology still "may exceed for value." 3-way divergence unchanged. |
| **F1 — "minimal" vs SDK neutral-0.5** (§6.3 "New roles MUST start with minimal trust") | OPEN (cross-track) | **STILL OPEN** | SDK `get_t3` still "Returns default (0.5,0.5,0.5)" (L438); `T3` dataclass defaults 0.5 (L151). Non-inheritance half still satisfied; magnitude word "minimal" (=0.0) vs "neutral" (=0.5) still diverges. Cross-track (SDK coordination). |
| **L3 — t3v3-010 "coherence" vector label** | OPEN (cross-doc) | **STILL OPEN** | §10.2 L639 spec-side note intact; vector rename is an SDK/vector-reader item, not spec. |

**Verdict**: 5/5 C83 fixes held; 0 regression; all numeric claims persist vs the live SDK/vectors. One carry sub-facet (D2/X4 number) **resolved downstream** — an instance of the C106 lesson (a sibling's own remediation resolves a sub-facet of a shared carry while its design-Q stays operator-gated). Analytic weight shifts to §B (no remediation landed on *this* file since C83).

---

## §B — Corpus Delta & Cross-Section Blindspot Sweep

### B.1 — Inbound sibling cross-refs (snapshot-presence guard vs the C82/C83 snapshot)

Five siblings changed since C83 (`git log --since` on core-spec/) AND cite t3-v3. Each t3-v3 citation git-diffed pre/post C83:

| Sibling (C#) | Change touching t3-v3 | Snapshot guard | Verdict |
|--------------|-----------------------|----------------|---------|
| **atp-adp (C119, `e99b419e`)** | §7.1 MUST #6 "Value MUST be tracked through T3/V3" → "**Entity-level** value MUST … society-level aggregates MAY use non-tensor rollup (§4.2)"; §4.2 `aggregate_value` back-ref | net-new (C118-N1 remediation) | **REINFORCING** — the entity-vs-society scoping is *consistent* with t3-v3 §1.1 role-contextual / §6.3 "MUST NOT compute global trust": society-level aggregates are explicitly non-tensor, so they don't collide with the role-bound tensor model. No t3-v3 action. |
| **mcp (C117, `afab0c43`)** | none — t3-v3 citations (§12 param-governance bounds L415; society-society T3/V3 L512) unchanged | no diff | **Neutral/REINFORCING** — L512 "mirrors the entity-role T3/V3 (three root dimensions … `web4:subDimensionOf`)" still accurate to t3-v3 §2.4. |
| **mrh (C90/C91, `f0c82118`)** | §5.2 `web4:training 0.90 → 0.92` | net-new remediation | **RESOLVES D2/X4 number** (see §A.3). Duplication structure unchanged (X4 structural still open). |
| **reputation (C85 era)** | t3-v3 citations unchanged (Valuation open-question L217, diminishing-returns t3v3-007 L762, Validity formula L188) | no diff | **REINFORCING** — all three defer to t3-v3 as canonical and are accurate (open-question correctly flagged as unresolved; t3v3-007 `max(0.8^(n−1),0.1)` matches §7.1). |
| **referenced-acts (recent)** | net-new §6 "Act outcome → EntityTrust (the T3/V3 pair bound to the entity) … See `t3-v3-tensors.md` for tensor definitions" | all `+` lines (new) | **REINFORCING (mild imprecision, referenced-acts-owned)** — "bound to the entity" elides the entity-*role* qualifier of §1.1, but the passage defers to t3-v3 for definitions and describes the SDK `EntityTrust` aggregate container (which holds per-role tensors). Below the bar; if tightened, the edit is referenced-acts-owned, not a t3-v3 defect. Deflated. |

### B.2 — Internal cross-section blindspot sweep (C118-N1 / C116-N1 pattern)

Charge: does t3-v3 have an **unconditional summary MUST** whose own reference implementation/example carves out an unstated exception? (The C120 signal: this defect class recurs only in docs with a **normative-summary section** — t3-v3 §6 "Implementation Requirements" and §10 "Parameter Governance" qualify.)

- **§10.2 "ATP conservation" row** (the normative-summary section) — the one MUST-adjacent cross-ref with an issue = **N2** (citation anchor/quote mismatch, below). Already caught by the sibling audit.
- **§6.3 "New roles MUST start with minimal trust"** vs SDK neutral-0.5 = **F1** (known cross-track carry; SDK-owned magnitude, non-inheritance half holds). Not net-new.
- **§6.1 "All tensor values MUST use ≥3 decimal places"** vs 2-decimal illustrative examples (§2.2/§3.2/§5.1) — **prior disposition** (C82 cleared; §2.2 note L85–89 marks those blocks illustrative). An implementation-precision MUST is not violated by illustrative example values. Refuted / not net-new.
- **§10.2 "Talent no-decay" MUST NOT** = matches §2.3 + t3v3-012; no impl carve-out. Clean.

**Result: exactly ONE MUST-vs-reference-impl issue in t3-v3's normative-summary sections (N2, the ATP-conservation citation) — already flagged.** This is the **4th consecutive file** (after multi-device C120, plus mcp/atp-adp where it *did* recur only in a normative-summary section) confirming C120's signal: the class is **doc-specific, not corpus-wide**; do not batch a speculative corpus-wide MUST sweep.

### B.3 — Inbound C118-N2 (CONFIRMED live, LOW, t3-v3-owned)

**Finding**: `t3-v3-tensors.md` §10.2 **L640** ATP-conservation row (post-C83):

> `| ATP conservation | total supply = ATP + ADP (transfers preserve total supply; the per-transfer form is` `initial == final + fees`) `| atp-adp-cycle.md §6.3 (§2.4 Slashing is the deliberate exception) | — |`

**Issue** — anchor/quote mismatch, verified against the **live** `atp-adp-cycle.md` (frozen in the relevant sections; C119 touched only §4.2/§7.1, confirmed by `git show e99b419e`):
- The quoted per-transfer form `initial == final + fees` lives in atp-adp **§2.4** (L214, the slashing supply-accounting note) — **not** §6.3.
- The equation `total supply = ATP + ADP` lives in atp-adp **§3.1/§3.2** (`total_supply` + `state_distribution`, L227–228; the `mint_adp` invariant `total_supply == sum(...)`, L266).
- atp-adp **§6.3** ("Transfer Fees", L593) supports only the *looser* "**preserving total supply**" via fee-recycling (L604–605) — it does **not** state the equation or the per-transfer form.

So the C83 F2 reword **primary-anchors on §6.3** while **quoting a §2.4 string and an §3.1/§3.2 equation**.

**Snapshot-presence guard (net-new at C83, not pre-existing)**: pre-C83, t3-v3 co-cited "§2.4 + §6.3" (co-primary, no quote). C83 F2 **demoted §2.4** to a parenthetical exception **and added** the `initial == final + fees` quote — so C83 itself introduced the mismatch. (Cf. [[feedback_snapshot_presence_guard]] + the §D lesson from C82 that C83's *explanatory* prose made new claims needing token-by-token verification.)

**Severity**: LOW (citation precision; the invariant itself is correct — total supply is conserved, transfers preserve it, slashing is the deliberate exception). **Owner**: t3-v3 (atp-adp is read-only here; **not** the defect site — this is why C118 correctly routed it flag-only to the t3-v3 track). **Autonomous-in-file** (one §10.2 cell edit).

**Fix (for the next t3-v3 REMEDIATION turn)**: re-anchor the "Related context" cell to
`atp-adp-cycle.md §3.1/§3.2 (supply equation total supply = ATP + ADP) + §2.4 (per-transfer invariant `initial == final + fees`); §6.3 fee-recycling preserves total supply; §2.4 Slashing is the deliberate exception.`

---

## §C — Disposition

**AUDIT turn — no spec mutation this session.** Routing:

- **N2 (inbound, CONFIRMED live)** → **next t3-v3 REMEDIATION turn** (autonomous-in-file, 1-cell §10.2 L640 re-anchor). This is the single autonomous-actionable item for this file.
- **D2/X4 number** → **CLOSED** (resolved downstream at mrh C91). Remove the "confirmed contradiction" note from the standing carry ledger.
- **D2/X4 structural + D2/N1-N2 attach-strategy** → operator DESIGN-Q (mrh shrink-to-pointer; ontology sub-dimension declaration + multi-device flat-block rewrite). Unchanged.
- **D1** (ontology-vocab), **D3** (M4 Valuation range), **F1** (minimal-vs-neutral, cross-track), **L3** (t3v3-010 vector) → all STILL OPEN, unchanged; operator/SDK-gated.

**0 net-new findings** from this file's own §B pass. The corpus-delta yield was one confirmed inbound (N2) + one resolved-downstream carry (D2/X4 number).

## §D — Lessons

1. **A carry can be resolved by a *sibling's* remediation, not this file's.** C82-D2 hardened the Surgeon-number divergence into a "confirmed cross-doc contradiction" and routed the fix to the mrh side; mrh C91 applied it (0.90→0.92). The bidirectional carry re-verification (re-read the *sibling's* current byte, per [[feedback_cross_doc_carry_inbound]] / [[feedback_snapshot_presence_guard]]) caught that the carry is now closed — a stale "STILL OPEN" here would have mis-stated the ledger. (Cf. the C106 failure mode: a sub-facet resolves downstream while the design-Q stays gated.)
2. **The inbound finding was the live yield, not the internal sweep.** On a byte-frozen target with an exemplary remediation history, this file's *own* §B produced 0 net-new; the one live actionable defect (N2) was surfaced by the **atp-adp** sibling audit reading t3-v3's outbound citation. Cross-doc audits find defects a same-file audit structurally cannot — keep routing inbound flags across the rotation. (6th "frozen ≠ clean" confirmation: C108/C112/C114/C116/C118/**C121**; here the non-cleanness is entirely inbound.)
3. **C120's "not corpus-wide" signal holds at the 4th file.** t3-v3 has two normative-summary sections (§6, §10) — the exact locus C120 predicted for the MUST-vs-reference-impl class — and yields exactly one instance (N2, a citation, not a missing carve-out). No speculative corpus-wide MUST sweep is warranted.

---

*Audit complete. Recommended next step: a t3-v3 REMEDIATION turn applying **N2** (1 spec-only §10.2 cell re-anchor); D2/X4-number is CLOSED (mrh C91); D1/D3/F1/L3 + X4-structural + N1/N2 attach-strategy remain operator/SDK-gated. Rotation advances t3-v3 → reputation-computation for the next AUDIT turn.*
