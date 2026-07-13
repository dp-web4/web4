# C190 Audit: `atp-adp-cycle.md` Fourth Delta Re-Audit (prior C118/C119 · C150/C151)

**Date**: 2026-07-13
**Auditor**: Autonomous session (Legion, web4 track) — single-auditor refute-by-default + independent adversarial verifier subagent (C144 bar: agreement ≠ corroboration; every interpretation-bearing ruling attacked against primary sources).
**Document**: `web4-standard/core-spec/atp-adp-cycle.md` (805 lines)
**Lineage**: C11 (#224 first-pass) → C34 (#276/#277) → C78 (#367) / C79 (#368) → C118 (#418 2nd delta, N1+N2) → C119 (#420 `e99b419e`, applied N1) → C150 (#475 3rd delta, N1) → C151 (#477 `256ab51d`, applied N1) → **C190** (this, 4th delta-re-audit).
**Baseline**: C150 audit (`docs/audits/C150-atp-adp-cycle-3rd-delta-2026-07-07.md`); C151 remediation (`docs/audits/C151-atp-adp-cycle-remediation-2026-07-07.md`, commit `256ab51d`, PR #477).
**Method**: §A re-verifies the C151 remediation + every C119/C79 fix + open carry at **LIVE HEAD** (greps re-run, not cached, per [[feedback_prior_finding_path_provenance]]), including the C56 claim-vs-canonical re-read of C151's own new prose (remediation-introduced-regression check — the only net-new spec prose since C150 is C151's one-line §2.4 edit). §B sweeps the corpus delta — 5 commits touched `web4-standard/` since C151 — at cited-hunk granularity, snapshot-presence guard, plus the §7.1 normative-summary blindspot re-check (DOC-SPECIFIC per the C121 signal; **no** corpus-wide sweep). **§B′ SDK-mirror gate** applies for the first time in this file's lineage to the **Rust** mirror `web4-core/src/atp.rs` (the prior atp-adp audits C118/C150 predate the gate method, born C172, and examined only the Python `atp.py`). Carry-mandated **C166 GUARD** adjudicated on atp-adp's OWN terms this turn. **Read-only AUDIT turn — zero spec/SDK mutation.**

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 0 | — |
| MEDIUM | 0 | — |
| LOW (routed) | 0 | — |
| INFO | 2 | I-1 (SDK fee-routing, correct-by-design forward note) · I-2 (§2.4 definite-article dangle, spec-local minor) |

**Result: SPEC-SIDE SUBSTANTIVE CLEAN + SDK GENUINE-MIRROR CLEAN.** First atp-adp delta in the C11→C190 lineage to close with **zero routed findings** on either side. C118 carried N1+N2; C150 carried N1 (spec-side wording); C190 finds the spec sound and the newly-audited Rust mirror correct-by-design.

**Delta (§A)**: Target **byte-frozen since C151** (`git diff 256ab51d..HEAD` on the file = empty). C151's one-phrase fix (§2.4 L214 scope label "ATP→ADP transfers" → "ATP transfers between entities (§6.3)") **present & correct**; re-read against the doc's arrow convention (§2.3/§3.3 = discharge) and §6.3 (transfer/fee locus) — **survives the remediation-introduced-regression check**, no semantic drift, note span L210–215 intact. All C119 fixes (§7.1 MUST #6 L622; scope note L624–633; §4.2 comment L384) HELD. All 5 C79 fixes HELD (L240, L264–269, L323–331, L434–440+L799–803, L419–430). C118-N2 remains CLOSED (t3-v3 C122). All DESIGN-Q / SDK-track / cross-track carries STAND (movers frozen; see §A).

**§B corpus delta**: 5 movers since C151 — **all DISJOINT** to atp-adp-cycle.md (C188 mcp = §7.3/§12 only, atp-adp cites mcp §7.7 which is untouched; C163 mrh + C157 reputation = zero-citation; C159 acp = resourceCaps path, no atp-adp surface; role-extension promotion = new `role:atpBudget` property over the **canonical base-mandatory Treasurer role**, consistent with §4.1 caps / §6.1 authority, no redefinition).

**§B′ SDK-mirror gate**: `web4-core/src/atp.rs` (Rust, crate v0.3.0, frozen since `8857ab09` 2026-05-13) is a **GENUINE mirror of the account-primitive layer** — 4 concordant surfaces, **spec CORRECT throughout** — with the **pool/governance/exchange layer ABSENT** (the C184 LAYER-SPLIT shape). Extends the SDK wire-layer-readiness synthesis: web4-core now has crypto primitives (crypto.rs, C180) + mcp data-types (mcp.py, C188) + **ATP account primitives (atp.rs, this audit)** — still NOT the pool/governance/wire layer.

---

## §A — C151 / C119 / C79 Delta-Persistence at LIVE HEAD

Target byte-frozen since C151 (`256ab51d`); the C151 diff touched only L214, so every prior fix outside that line is held by byte-identity **and** was re-read live.

| Prior ID | Fix | Status | Live evidence |
|----------|-----|--------|---------------|
| **C150-N1 (C151 fix)** | §2.4 conservation-invariant scope label reword | **HELD & CORRECT** | L214: "…which scopes only **ATP transfers between entities (§6.3)** — a destruction event…". Arrow-convention sweep: remaining `ATP→ADP` occurrences (§2.3 heading L124; §3.3 L323) are all discharge contexts → internally consistent. §6.3 cross-ref supported (L593–611 = the entity-to-entity transfer + fee locus). No semantic drift (remediation-regression check: **clean**). |
| **C118-N1 (C119, part 1)** | §7.1 MUST #6 entity-scoping reword | **HELD** | L622: "Entity-level value MUST be tracked through T3/V3 tensors; society-level aggregates MAY use non-tensor rollup accounting (§4.2)". |
| **C118-N1 (part 2)** | §7.1 scope note | **HELD & ACCURATE** | L624–633; entity-leg enumeration still matches §4.2 (beneficiary `v3` L373, agent `t3` L374, witnesses `t3` L378–381); §3.3 + "not a T3/V3 dimension" quotes verbatim. |
| **C118-N1 (part 3)** | §4.2 `aggregate_value` back-ref comment | **HELD** | L384: "rollup accounting, outside §7.1 MUST #6 per its scope note". |
| **C79-B2a** | §3.3 demurrage R6 carve-out note | **HELD** | L323–331. |
| **C79-B5** | `mint_adp` nested-pool form + invariant note | **HELD** | L264–269. |
| **C79-B6** | `charged_fraction` rename + disambiguation | **HELD** | L240. |
| **C79-B7** | ISP+mcp §5 note + References | **HELD & re-verified** | L434–440; L799–803. mcp §7.7 **untouched by C188** (C188 changed mcp:415 only — `git show 91225131` = §7.3/Law-Oracle line, not §7.7); ISP frozen → both References claims still accurate. |
| **C79-B8** | §4.3 role-vocabulary note | **HELD** | L419–430. |

**Open carries — bidirectional re-verification (greps re-run at HEAD):**
- **C118-N2** — remains **CLOSED** (t3-v3 C122, verified at C150).
- **B1** (§5 abstract-FX vs mcp §7.7 referent-grounding — CROSS-TRACK/DESIGN-Q): **STILL OPEN.** mcp §7.7 unmoved by C188.
- **B2b** (§5.3 exchange discharge/charge bypasses MUST #4/#5/#6 — DESIGN-Q): **STILL OPEN** (L511–512, frozen).
- **M2** (§2.4 slash cap never references §6.1 `max_slash_per_event` — DESIGN-Q): **STILL OPEN** (L194 / L547, frozen).
- **B3 / B4 / I2 / B6-SDK** (SDK-track): **STILL OPEN** — Python `atp.py` frozen (`62524cf8`, C11-era #228).
- **X1** (`lct:web4:` identifier — C33 corpus decision): **STILL OPEN**.
- **ISP-B10** (commitment-ATP charged-vs-allocated — DESIGN-Q): **STILL OPEN** (ISP frozen since C63).
- **B8 (inbound, acp C158)** — "ACP discharge not routed through R6" references atp-adp **§7.1 MUST #5 as the correct-side referent**. Re-checked: MUST #5 (L621) persists and is correct; the gap is acp-side (acp §9.1 MUST list has no R6-discharge item). **No atp-adp defect; CROSS-TRACK, acp-owned.** STANDS.

**§7.1 normative-summary blindspot re-check** (DOC-SPECIFIC, C116/C118 defect-class locus): §7.1 (L615–641) untouched since C151 → C150's clean result holds — MUST #1 (escrow note L635–641), #2 (§3.3), #3 (§3), #4/#5 (sole un-noted bypass = §5.3, inside B2b), #6 (C119-fixed). **No new cross-section contradiction.**

---

## §B — Corpus Delta (5 movers since C151, cited-hunk granularity)

| Mover (C#, commit) | Change | Verdict |
|--------------------|--------|---------|
| **mcp C188 `91225131`** | 1 line: mcp §7.3/L415 Law-Oracle citation re-anchor (C154-N1) | **DISJOINT.** atp-adp cites mcp only at §7.7 (L436–439, L801–802); §7.7 untouched (grep of the diff for "7.7" = 0). |
| **mrh C163 `b8740803`** | §4.2 propagation-fn note | **DISJOINT.** atp-adp has zero mrh citation (References §784–803 do not list mrh). |
| **acp C159 `fb0075fc`** | resourceCaps path-shape fix (entity-types §4.7 `scope.r6Caps.resourceCaps`) | **DISJOINT.** atp-adp has no resourceCaps surface (grep = 0); acp's `max_atp`/`maxAtp` is acp's own agency-grant cap key, not an atp-adp-cycle.md concept. acp §2.3 citation of atp-adp untouched. |
| **reputation C157 `5195465c`** | §9 Sybil item softened to SHOULD + §10 cross-ref | **DISJOINT.** atp-adp contains zero citations of reputation-computation.md (disjoint-by-non-citation). |
| **role-extension promotion `7201a765`** | NEW `ontology/role-extension.{md,ttl}`; adds `role:atpBudget` + MRH "ATP budget" mention | **DISJOINT / CONSISTENT.** `role:atpBudget` (`role-extension.ttl:128–131`, domain `role:Scope`, "ATP ceiling the role may spend per period. Enforced by Treasurer at act time") is a per-role spend cap structurally identical to §4.1 producer `caps.daily_max` (L348–351) and §6.1 authority `constraints` (`max_mint_per_period` L545). Defines no token state / charge / mint semantics. **Treasurer is the canonical base-mandatory role** (`society-roles.md` §2; already ATP-bearing at `mcp-protocol.md` §7.7 "rate commitments on behalf of the society's ATP pool") — the property *reuses* an established ATP role, it does not introduce a competing authority model. No terminology-protection concern. |

**§B yield: zero net-new spec findings.** All movers disjoint or consistent.

---

## §B′ — SDK-Mirror Gate: `web4-core/src/atp.rs` (Rust) — GENUINE account-primitive mirror, LAYER-SPLIT

First application of the SDK-mirror gate (born C172) to atp-adp's Rust mirror. `atp.rs` (289 lines, crate v0.3.0, frozen `8857ab09` 2026-05-13, shipped in tag `web4-core-rust-v0.3.0`) is a **genuine mirror** of the account-primitive layer — its header explicitly names the file "Reference: `web4-standard/core-spec/atp-adp-cycle.md`" (L15) and encodes the spec's invariants (L10–13).

**Concordant surfaces (4) — spec CORRECT:**

| # | Spec surface | atp.rs | Verdict |
|---|--------------|--------|---------|
| 1 | Two-state invariant (§7.1 MUST #1) + escrow note (§7.1 L635–641: locked "remains ATP, not a third token state"; two-phase commit lock→commit/rollback) | `ATPAccount{available, locked, adp}`; `total()=available+locked` = "active ATP" (L43–46); `lock()`/`commit()`/`rollback()` (L60–95) IS the blessed two-phase-commit lifecycle | **STRONG concordance** — atp.rs is the exact escrow-note lifecycle; `locked` counts toward ATP (not a 3rd state). |
| 2 | Transfer conservation (§2.4 post-C151 / §6.3) | header `sum(initial)==sum(final)+total_fees` (L11); `transfer()` net `sender_deducted == actual_credit + fee + overflow` (L135, L143–176); `test_transfer_conservation` (L228–243) | **Concordant.** The SDK is the positive **formula** home the spec references by name (see I-2). Matches post-C151 §2.4 scope ("ATP transfers between entities") exactly. |
| 3 | Fee bearer = sender (§6.3 `fee_bearer: sender` L589) | "Fee is additive to sender (sender pays amount + fee)" (L132, L147–148) | **Concordant.** |
| 4 | `charged_fraction` = ATP/(ATP+ADP) (§3.1 L240) | `energy_ratio()=total()/(total()+adp)` = "ATP/(ATP+ADP)" (L48–57) | **Concordant** (per-account vs per-pool scale, expected; neutral-0.5 on zero-balance is a benign primitive convenience). |

**ABSENT surfaces (the layer-split):** society pools (§3 `SocietyTokenPool`, `total_supply`/`state_distribution`/`allocations`), minting (§2.1), value-proof charging (§2.2 — atp.rs `recharge()` is a rate-based top-up toward a cap, NOT value-proof charging), slashing (§2.4), demurrage (§3.3), inter-society exchange (§5), T3/V3 tensor updates (§4). atp.rs implements the **account primitive**, not the **pool/governance/exchange protocol**.

**Gate verdict:** **GENUINE (account-primitive layer) + ABSENT (pool/governance/exchange layer)** = the C184 LAYER-SPLIT shape. Spec is CORRECT on every mirrored surface; the SDK implements a correct subset. Routes to the SDK wire-layer-readiness synthesis (below), **not** as a defect.

---

## §C — Carry-Mandated C166 GUARD: conservation-invariant "no definition site" — ADJUDICATED & CONSUMED

The standing GUARD (carried since C166, deliberately un-asserted there): the transfer-conservation invariant `initial == final + fees` has **no positive definition site** in atp-adp-cycle.md — it appears only in **exception framing** (§2.4 L213–214 "Slashing…sits outside the transfer-conservation invariant (`initial == final + fees`)"; §3.3 L327–328 demurrage-by-analogy), never as a positive statement, and is absent from the §7.1 MUST list. The GUARD directs: adjudicate on atp-adp's OWN terms, do NOT inherit C166's framing.

**Adjudication (on atp-adp's own terms): NOT a §7.1 defect — the absence is correct design.**
- Fees are **optional**: §6.3 (L595) transfers are fee-free at the protocol level by default; societies **MAY** levy fees (§7.3 #6). So conservation-*with-fees* is a **derived/emergent property**, not a primitive requirement — correctly **absent** from the §7.1 MUST list (making it a MUST would over-constrain the fee-free default, where `initial == final`).
- §6.3 provides the **semantic** ("Fees SHOULD be recycled into the society's pool (not destroyed), preserving total supply", L604–605); the **formula** lives positively in the SDK (`atp.rs:11`, `atp.py:10` + `check_conservation`). This is the correct division: normative semantics in the spec, formalization in the reference impl.

**Residual (INFO I-2, spec-local, very-low priority):** §2.4 L213 uses the **definite article** — "sits outside **the** transfer-conservation invariant" — naming an invariant that atp-adp only ever references (as the-thing-slashing/demurrage-are-excepted-from) and never positively states. A reader meets the name before any statement. This is a minor doc-quality dangle, **not** a §7.1 MUST defect; a future one-clause improvement could add a positive gloss (e.g. at §6.3, "a transfer preserves total supply: `initial == final + fees`"). **Very low priority; carried as INFO, not routed for remediation.**

**t3-v3:640 re-check (refuted as a residual):** t3-v3-tensors.md:640 cites "§2.4 (per-transfer invariant `initial == final + fees`; Slashing is the deliberate exception)". §2.4 is **literally the only place in atp-adp where the formula string appears**, and t3-v3:640 itself flags the slashing exception — so the citation is **technically accurate**, not a mis-anchor. No t3-v3-side residual.

**The C166 GUARD carry is CONSUMED this turn** (adjudicated on atp-adp's own terms → not a defect; minor residual demoted to INFO I-2), not re-deferred → [[feedback_prose_is_not_ledger]] (an item that has sat in prior-audit prose is promoted to a decision at the delta that reaches its home doc).

---

## §D — INFO / Deflated (anti-overcall record)

- **I-1 — SDK fee has no pool recipient in the two-account primitive (correct-by-design forward note).** Both `atp.rs:transfer()` (L165–167) and `atp.py:transfer()` deduct `amount + fee` from sender and credit the fee to no account — the fee leaves the tracked account-pair. **Adversarially verified as benign:** (a) the primitive is conservation-*consistent* — its stated invariant `sum(initial)==sum(final)+total_fees` holds *because* the fee is booked as `total_fees`; (b) it **already surfaces the fee** via `TransferResult.fee` (L118–119) specifically so a caller/governance layer can route it; (c) §6.3 makes fee destination **society-configurable** (`fee_destination` L590; MUST be declared in published laws L602; impls MUST NOT hard-code L610–611) and recycling is a **SHOULD** (L604), not a MUST. A two-account primitive that returns the fee for the caller to route is therefore **correct-by-design**, not a gap. *Forward note (INFO only):* when the ABSENT pool/governance layer is built, its integration SHOULD recycle the returned `TransferResult.fee` into the society pool per §6.3. **No SDK defect; not routed.**
- **`recharge()` is neither §2.1 minting nor §2.2 value-proof charging** — a rate-based replenishment toward `max_multiplier * initial_balance` (L97–106). A primitive-layer convenience (SAGE/IRP-style energy top-up); does not contradict the spec, simply not the spec's charging model. INFO.

---

## §E — SDK Wire-Layer-Readiness Synthesis (extended)

C190 adds the **ATP account-primitive layer** to the standing synthesis (C180-N1 + C182-N1 + C184-N1 + C188-N2):

> web4-core has built **primitive/type layers** — crypto primitives (`crypto.rs`, C180 genuine 5/6), MCP data-types (`mcp.py`, C188 genuine types-layer), and now **ATP account primitives** (`atp.rs`, C190 genuine 4/4 concordant) — but **NOT** the pool/governance/wire layer: no `SocietyTokenPool` (no supply/minting/slashing/demurrage/exchange), no COSE/CBOR codec, no registry loader/enum, no HPKE handshake, no code path assembling a Web4 Context Header onto a real MCP message. Whichever form the flagship **B-D1** SSOT decision declares canonical owes a from-scratch SDK build of {pool/governance layer + COSE codec + registry loader + HPKE handshake + mcp wire assembly}; only the primitive/type layers exist to build on. The pool layer's fee-routing (I-1) is one concrete integration constraint recorded for that build.

---

## §F — Routing Summary

| ID | Severity | Classification | Owner / next step |
|----|----------|----------------|-------------------|
| **(none routed)** | — | — | Spec-side substantive clean; SDK genuine-mirror clean. |
| I-1 | INFO | SDK-track forward note | When pool layer is built, recycle `TransferResult.fee` per §6.3. No action now. |
| I-2 | INFO | spec-local, very-low priority | Optional future one-clause positive gloss of the conservation invariant (§6.3). Not routed for remediation. |
| C166 GUARD | — | **CONSUMED** | Adjudicated on atp-adp's own terms → not a §7.1 defect. |
| B8 (inbound) | — | CROSS-TRACK (acp-owned) | atp-adp §7.1 #5 is the correct-side referent; STANDS. |
| B1 / B2b / M2 / ISP-B10 | — | DESIGN-Q | **Operator** (open, unchanged). |
| B3 / B4 / I2 / B6-SDK | — | SDK-track | SDK (open; `atp.py` frozen). |
| X1 | — | CROSS-TRACK | C33 corpus identifier decision (open). |

**Autonomous remediation set (C191-candidate): EMPTY.** No routed findings. **C191 = NO-OP** (nothing to apply); rotation advances +2 to **t3-v3** on the next fire.

---

## §G — Lessons / Method Notes

- **First zero-routed-findings atp-adp delta in the lineage.** C118 (N1+N2), C150 (N1) each carried a spec-side wording finding; C190 finds the spec sound and the Rust mirror correct-by-design. Consistent with the 20+-wrap pattern (files churn slower than cadence; §A verification + §B corpus-delta + §B′ SDK-mirror-expansion is where net-new lives) — here the SDK expansion surfaced a *genuine, concordant* mirror, and the anti-overcall discipline correctly kept a plausible "fee destroyed" candidate from being routed.
- **The SDK-mirror gate can return GENUINE-and-CLEAN.** The ladder's rungs (genuine-C180 / false-C178 / absent-C182 / divergent-by-layer-C184 / PARTIAL-C188 / canonical-vote-C186) gain a plain reading: a genuine primitive-layer mirror that is *concordant on every mirrored surface* and whose only "divergence" (fee has no pool recipient) is **correct-by-design** for its layer. The right output was an INFO forward-note, not a routed SDK finding — [[feedback_refute_your_best_finding]] (the verifier downgraded "destroys the fee / integrator MUST route" → "returns the fee for the caller to route, SHOULD recycle").
- **A carry parked in prose across three cycles was consumed, not re-deferred.** The C166 conservation-"no-definition-site" GUARD was adjudicated on atp-adp's own terms this turn (→ correct design, minor INFO residual) rather than re-carried → [[feedback_prose_is_not_ledger]]. The productive question was "is the absence a *defect* on this doc's terms?" — answered by the fee-optionality of §6.3, which makes conservation a derived property.
- **Refute your own mover-disjointness on the strongest candidate.** The role-extension `role:atpBudget`/Treasurer mover was the closest thing to a terminology-protection concern; the refutation (Treasurer is canonical base-mandatory + already ATP-bearing per mcp §7.7) *strengthened* the disjoint verdict rather than weakening it.

---

## §H — Methodology Note

Single-auditor delta-re-audit, refute-by-default, proportioned to a byte-frozen target (HEAD blob == `256ab51d` blob, git-verified) with a 5-mover corpus delta (each diffed at cited-hunk granularity) and one never-before-audited Rust mirror. §A = persistence verification at live HEAD (greps re-run) + C56 claim-vs-canonical re-read of C151's own new prose (remediation-regression check: **clean**). §B = snapshot-presence guard on every mover. §B′ = SDK-mirror gate on `atp.rs` (genuine, 4/4 concordant, layer-split). Independent adversarial verifier subagent attacked all three interpretation-bearing rulings against primary sources (atp.rs, atp.py, atp-adp-cycle.md, t3-v3-tensors.md, role-extension.ttl, society-roles.md): R1 (fee) **MODIFIED** → downgraded to INFO I-1; R2 (conservation deflation) **SURVIVES** with the residual re-scoped to §2.4's definite-article dangle (I-2) and the t3-v3:640 charge **refuted**; R3 (mover disjointness) **SURVIVES** with the "new Treasurer" characterization corrected (canonical base-mandatory). 0 HIGH / 0 MEDIUM / 0 LOW-routed — the numeric/normative core is sound and the primitive mirror is concordant.

*Audit complete. Recommended next step: **C191 = NO-OP** (empty autonomous set); rotation advances +2 to `t3-v3` on the next fire. All DESIGN-Q / SDK-track / corpus carries remain operator- or track-gated; I-1/I-2 are INFO-only forward notes.*
