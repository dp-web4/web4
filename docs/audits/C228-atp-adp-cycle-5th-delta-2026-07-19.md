# C228 Audit: `atp-adp-cycle.md` Fifth Delta Re-Audit (prior C118/C119 · C150/C151 · C190)

**Date**: 2026-07-19
**Auditor**: Autonomous session (Legion, web4 track) — single-auditor refute-by-default + independent adversarial policy-review subagent (C144 bar: agreement ≠ corroboration; every interpretation-bearing ruling attacked against primary sources).
**Document**: `web4-standard/core-spec/atp-adp-cycle.md` (804 lines)
**Lineage**: C11 (#224 first-pass) → C34 (#276/#277) → C78 (#367) / C79 (#368) → C118 (#418 2nd delta) → C119 (#420, applied N1) → C150 (#475 3rd delta) → C151 (#477 `256ab51d`, applied N1) → C190 (#514 `fce49107` 4th delta, first zero-routed) → **C228** (this, 5th delta-re-audit).
**Baseline**: C190 audit (`docs/audits/C190-atp-adp-cycle-4th-delta-2026-07-13.md`); target commit `256ab51d` (C151), SDK mirrors `atp.rs` `8857ab09` / `atp.py` `62524cf8`.
**Method**: §A re-verifies the C151 remediation + every C119/C79 fix + open carry at **LIVE HEAD** (greps re-run, not cached, per [[feedback_prior_finding_path_provenance]]), including the §7.1 normative-summary blindspot re-check (DOC-SPECIFIC per the C121 KEY SIGNAL; **no** corpus-wide MUST sweep). §B sweeps the corpus delta — **9 movers touched `web4-standard/` since C190** — at cited-hunk granularity, snapshot-presence guard, with a focused adjudication of the **W4IP governance-immune-enforcement** landing, which is the **first external framework in the corpus to make atp-adp's `slash_atp` (§2.4) load-bearing**. **§B′ SDK-mirror gate** re-derived at live HEAD (Python `atp.py` AND `web4-core/src/*.rs`, per the standing METHOD GUARD — the "SDK mirror" is not a fixed set). **Read-only AUDIT turn — zero spec/SDK mutation.**

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 0 | — |
| MEDIUM | 0 | — |
| LOW (routed) | 0 | — |
| INFO | 2 | I-1 (Effector/slashing-authority forward-harmonization note, W4IP/SAL-owned) · I-2 (`lct.rs:585` slash name-collision false-mirror, growth-edge) |

**Result: SPEC-SIDE SUBSTANTIVE CLEAN + SDK GENUINE-MIRROR CLEAN — 2nd consecutive zero-routed atp-adp delta.** The most significant corpus event since the last audit — the W4IP enforcement framework standing up an entire response-side vocabulary on top of atp-adp's slashing primitive — **strengthens** rather than stresses the spec: every citation of atp-adp is accurate and grounded, and the new Effector-via-R7 enactment path composes cleanly with atp-adp's deliberately-abstract slashing-authority model.

**Delta (§A)**: Target **byte-frozen since C151** (`git diff 256ab51d..HEAD` on the file = empty; HEAD blob `2d060579` == C151 blob). All C151/C119/C79 fixes HELD by byte-identity and re-read live. All C190 carries (B1 / B2b / M2 / ISP-B10 / B3 / B4 / I2 / B6-SDK / X1 / B8-inbound) STAND — movers frozen. C118-N2 remains CLOSED (t3-v3 C122). C166 GUARD remains CONSUMED (C190). §7.1 normative-summary blindspot re-check: clean (no new cross-section contradiction).

**§B corpus delta**: 9 movers since C190 — all **DISJOINT or CONSISTENT** to atp-adp-cycle.md. The W4IP cluster (#521/#522/#523/#525 + `role-extension` #541) cites atp-adp's `slash_atp` and §9.2 anti-patterns; both citations verified accurate. mcp §7.8 mailbox (#550) and reputation C195 (#526) are zero-atp-surface.

**§B′ SDK-mirror gate**: `atp.rs` (`f5b0efe0`) and `atp.py` (`efa5de3c`) **byte-frozen since the C190 baseline** → the C190 GENUINE account-primitive-mirror verdict (4/4 concordant, layer-split) HELD by byte-identity; C190 I-1 (fee-routing forward note) held. **No new pool/governance/slash mirror surfaced.** The one growth-edge hit — `web4-core/src/lct.rs:585 slash()` — is a **name-collision FALSE-mirror** (LCT-lifecycle `LctStatus::Slashed` ≠ atp-adp `slash_atp` ATP-destruction), excluded per the C178/C216/C222 false-mirror method → I-2.

---

## §A — C151 / C119 / C79 Delta-Persistence at LIVE HEAD

Target byte-frozen since C151 (`256ab51d`); every prior fix is held by byte-identity **and** re-read live.

| Prior ID | Fix | Status | Live evidence |
|----------|-----|--------|---------------|
| **C150-N1 (C151 fix)** | §2.4 conservation-invariant scope label reword | **HELD & CORRECT** | L214 "…which scopes only **ATP transfers between entities (§6.3)**…". Arrow-convention sweep clean (remaining `ATP→ADP` at §2.3/§3.3 = discharge contexts). |
| **C118-N1 (C119 ×3)** | §7.1 MUST #6 entity-scoping + scope note + §4.2 back-ref | **HELD** | L622 MUST #6; L624–633 scope note (entity-leg enumeration still matches §4.2); L384 `aggregate_value` comment. |
| **C79-B2a / B5 / B6 / B7 / B8** | §3.3 demurrage carve-out; `mint_adp` nested-pool; `charged_fraction` rename; ISP+mcp §5 note & References; §4.3 role-vocab note | **HELD** | L323–331; L264–269; L240; L434–440 + L799–803; L419–430. mcp §7.7 still untouched (C226 §7.8 mailbox is a net-new section, not a §7.7 edit — see §B). |

**Open carries — bidirectional re-verification (greps re-run at HEAD):** All STAND unchanged from C190; movers gating them are frozen.
- **C118-N2** — CLOSED (t3-v3 C122).
- **B1** (§5 abstract-FX vs mcp §7.7 referent-grounding — CROSS-TRACK/DESIGN-Q): STILL OPEN. mcp §7.7 unmoved (C226 added §7.8, did not touch §7.7).
- **B2b** (§5.3 exchange bypasses MUST #4/#5/#6 — DESIGN-Q): STILL OPEN (L511–512, frozen).
- **M2** (§2.4 slash cap never references §6.1 `max_slash_per_event` — DESIGN-Q): STILL OPEN (L194 / L547, frozen).
- **B3 / B4 / I2 / B6-SDK** (SDK-track): STILL OPEN — `atp.py` frozen (`62524cf8`).
- **X1** (`lct:web4:` identifier — C33 corpus decision): STILL OPEN.
- **ISP-B10** (commitment-ATP charged-vs-allocated — DESIGN-Q): STILL OPEN (ISP frozen).
- **B8 (inbound, acp C158)** — atp-adp §7.1 MUST #5 (L621) is the correct-side referent; the gap is acp-side. **No atp-adp defect; CROSS-TRACK, acp-owned.** STANDS.

**§7.1 normative-summary blindspot re-check** (DOC-SPECIFIC, C116/C118/C121 KEY SIGNAL): §7.1 (L615–641) untouched since C151 → C150/C190's clean result holds. No mover in this delta introduces an entity-level MUST that §7.1 would need to mirror. The W4IP enforcement framework's obligations (RWOA+S+V+F on Effector R7 enactments) live in `hub-law-schema.md` and cite atp-adp as the *slashing primitive*, not as an entity-level MUST that §7.1 restates. **No new cross-section contradiction.**

---

## §B — Corpus Delta (9 movers since C190, cited-hunk granularity)

| Mover (commit) | Change | Verdict |
|----------------|--------|---------|
| **W4IP #521 `767eb564`** | reputation-computation §4 — Coercive/Extractive rule category + decision-vocab sync | **CONSISTENT (cited authority = atp-adp).** New §4 clause "Resource extraction without consent — draining ATP… **Distinct from the ATP anti-patterns' economic rent-seeking**". The "ATP anti-patterns" referent is **grounded**: atp-adp §9.2 "Anti-Patterns Prevented" (L690) enumerates "Rent extraction (value requires work)" (L696) and §9.1 "not rent-seeking" (L684). Citation accurate; no atp-adp surface changed. |
| **W4IP #522 `87377c38`** | SOCIETY_SPEC §7.3 + hub-law-schema response vocabulary (spec half) | **CONSISTENT.** Kinetic verb `slash` documented as "ATP stake slashing, `atp-adp-cycle.md` (`slash_atp`, already…)". Citation verified ACCURATE — §2.4 L175 literally defines `def slash_atp(caller, violator, amount, evidence, witnesses)`. `correct` verb's "return of extracted ATP" is restorative framing, no atp-adp primitive claim. |
| **W4IP #523 `1354e4c2`** | Effector Role — entity-types §4.8 + society-roles + SAL | **CONSISTENT (see I-1).** Effector "Acts **only via R7**; each enactment binds recognition evidence… gate is RWOA+S+V+F". Effector is a new *enactor* of kinetic verbs incl. `slash`; atp-adp §2.4 gates slashing on abstract `has_slashing_authority(caller)` (L184) + §6.1 `slash_violations` power (L541). Effector-via-R7 is **additive** — an Effector enacting `slash` must still hold slashing authority. Parse-don't-enact preserves the atp-adp gate. |
| **W4IP #525 `cb788768`** | policy engine response-vocabulary code half (parse-don't-enact) | **CONSISTENT.** Comment "kinetic verbs name existing scattered primitives (`slash_atp`…)"; namespace note declares response rules select over `reputation.delta.category`, disjoint from norm rules over `r6.resource.atp`. Reinforces the disjoint-surface finding; no atp-adp edit. |
| **role-extension #541 `4f76f110`** | oracle consult/write sets on `role:Scope` | **DISJOINT.** Touches `role-extension.ttl` oracle-set properties; `atp_budget`/`AtpBudget` appears only as an *existing* Scope field in a doctest example (consistent with C190's role:atpBudget adjudication — reuses Treasurer's canonical ATP ceiling, defines no token semantics). |
| **mcp §7.8 #550 `3e765345`** | net-new §7.8 Asynchronous Mailbox (deferred R6/R7 actions) | **DISJOINT (zero atp surface).** `git show` grep for atp/adp = 0. atp-adp cites mcp only at §7.7 (untouched). *Cross-track awareness:* C226-N1 flags §7.8 double-completion of deferred R6/R7 actions could double a discharge/slash — but that is an **mcp-owned** obligation (idempotency-on-redelivery keyed `action_id`), not an atp-adp defect; atp-adp's primitives are correct if invoked once. Noted, not routed here. |
| **reputation C195 #526 `062fd24b`** | §5 no-match returns None; drop spec-only `value` key | **DISJOINT.** Zero atp-adp citation. |
| **hub law #6 `6b66c949`** | starter-law folds RWOA+S+V; "ATP magnitude" in a V-veto comment | **DISJOINT.** Governance-config, not a spec surface; "ATP magnitude above" references the veto threshold narrative, no atp-adp construct. |
| **inspectable-evidence #531 `d89595e8`** | canonize "Inspectable Evidence, Not Prescribed Trust"; renumbered a heading list incl. "10. Value as Energy (ATP/ADP)" | **DISJOINT.** Principle doc; the ATP/ADP list item is a pointer, not an atp-adp edit. |

**§B yield: zero net-new spec findings.** All movers disjoint or consistent. **The strongest candidate — the W4IP framework making `slash_atp` load-bearing — refutes to CONSISTENT on every axis** (citation accurate, referent grounded, authority-gate preserved). See [[feedback_refute_your_best_finding]].

---

## §B′ — SDK-Mirror Gate Re-Derived at LIVE HEAD

Per the standing METHOD GUARD ("the SDK mirror is not a fixed set — re-derive implementers at live HEAD"), re-scanned `web4-standard/implementation/sdk/`, `web4-core/src/*.rs`, and the `hub/` growth edge for any ATP pool/slash/mint/demurrage implementer.

- **`web4-core/src/atp.rs`** (`f5b0efe0`) — **byte-frozen since the C190 baseline** (`8857ab09`, last touch). The C190 verdict **GENUINE account-primitive mirror, 4/4 concordant, LAYER-SPLIT** (society pool / minting / slashing / demurrage / exchange all ABSENT) HELD by byte-identity. **C190 I-1** (fee has no pool recipient in the two-account primitive — correct-by-design; `TransferResult.fee` surfaced for a caller/governance layer to route per §6.3) **HELD** by byte-identity → carried forward, not re-routed.
- **`web4-standard/implementation/sdk/web4/atp.py`** (`efa5de3c`) — byte-frozen (`62524cf8`). SDK-track carries B3/B4/I2/B6-SDK STAND.
- **No new pool/governance/slash mirror** anywhere in `web4-core` or `hub/` (the C226 growth-edge files `hub-lib/store.rs`/`rest.rs` mirror the §7.8 mailbox, not any ATP primitive).
- **Growth-edge false-mirror (I-2):** `web4-core/src/lct.rs:585 pub fn slash(&mut self)` sets `self.status = LctStatus::Slashed` — this is **LCT-lifecycle slashing** ("Slash this LCT (compromised or malicious)"), the web4-lct/LCT-spec entity-status lens, **NOT** atp-adp §2.4 `slash_atp` (which destroys ATP from `society_pool.slash(...)` and reduces `total_supply`). Name-collision **false mirror**, excluded per C178/C216/C222 — it does not exercise atp-adp's slashing surface. (Same discipline that caught `ratchet.rs` at C222-N1 and `attestation.rs`-for-registries at C220-N1.) INFO only.

**Gate verdict:** GENUINE (account-primitive layer, frozen/held) + ABSENT (pool/governance/exchange layer) + FALSE-mirror-excluded (`lct.rs` slash). Spec CORRECT on every mirrored surface. Routes to the standing SDK wire-layer-readiness synthesis (§E), not as a defect.

---

## §C — INFO / Forward Notes (anti-overcall record)

- **I-1 — Effector/slashing-authority forward-harmonization note (W4IP/SAL-owned, NOT an atp-adp defect).** atp-adp §2.4 (`has_slashing_authority(caller)`, L184) and §6.1 (`slash_violations` power in the authority `powers` list, L541; `max_slash_per_event` constraint, L547) predate the Effector role (#523). The W4IP framework now names the Effector as the canonical *enactor* of the `slash` kinetic verb (always-R7, gate RWOA+S+V+F). These compose cleanly today — Effector-via-R7 is one holder of `slash_violations`/`has_slashing_authority`, and parse-don't-enact preserves atp-adp's authority check. A **future** cross-doc harmonization *could* add a one-clause note (e.g. at §6.1 or §2.4) that "an Effector's R7 slash enactment must hold `slash_violations` authority" to make the linkage explicit — but this is a **W4IP/SAL-track editorial choice on the citing docs**, not an atp-adp obligation, and atp-adp's abstract gate is deliberately role-agnostic (correct design). **Not routed; forward note for the W4IP/SAL track.** (This also revives the C190 M2 DESIGN-Q neighborhood: §2.4 slashing and §6.1 `max_slash_per_event` remain unlinked — now with a second consumer, the Effector, potentially interested in that cap. Still operator/cross-track, still open.)
- **I-2 — `lct.rs:585 slash()` name-collision false-mirror** (growth-edge). Documented in §B′. INFO; standing SDK-condition, not a defect. Carry-guard: at atp-adp's next delta, do NOT re-count `lct.rs slash()` as an ATP-slash mirror.

---

## §D — SDK Wire-Layer-Readiness Synthesis (held)

C228 adds no new SDK layer; the C190/C188/C184/C182/C180 synthesis holds verbatim:

> web4-core has built **primitive/type layers** — crypto primitives (`crypto.rs`), MCP data-types (`mcp.py`), ATP account primitives (`atp.rs`, frozen/held here) — but **NOT** the pool/governance/wire layer: no `SocietyTokenPool` (no supply/minting/slashing/demurrage/exchange), no COSE/CBOR codec, no registry loader/enum, no HPKE handshake, no MCP wire assembly. Whichever form flagship **B-D1** SSOT declares canonical owes a from-scratch build of {pool/governance layer + COSE codec + registry loader + HPKE handshake + mcp wire assembly}. The pool layer's fee-routing (C190 I-1) is one recorded integration constraint; **the Effector-via-R7 slash-authority linkage (I-1) is a second** — when the pool/slash layer is built, its `slash` entry point must enforce `has_slashing_authority`/`slash_violations` for the enacting Effector.

---

## §E — Routing Summary

| ID | Severity | Classification | Owner / next step |
|----|----------|----------------|-------------------|
| **(none routed)** | — | — | Spec-side substantive clean; SDK genuine-mirror frozen/held/clean. |
| I-1 | INFO | cross-doc forward note | W4IP/SAL track: optional one-clause note linking Effector R7 `slash` enactment to atp-adp `slash_violations` authority. No atp-adp action. |
| I-2 | INFO | SDK growth-edge | Standing condition; `lct.rs slash()` = LCT-lifecycle, not ATP. No action. |
| C166 GUARD | — | **CONSUMED (C190)** | Not re-opened. |
| B8 (inbound) | — | CROSS-TRACK (acp-owned) | atp-adp §7.1 #5 is the correct-side referent; STANDS. |
| B1 / B2b / M2 / ISP-B10 | — | DESIGN-Q | **Operator** (open, unchanged; M2 gains a second interested consumer via I-1). |
| B3 / B4 / I2 / B6-SDK | — | SDK-track | SDK (open; `atp.py` frozen). |
| X1 | — | CROSS-TRACK | C33 corpus identifier decision (open). |

**Autonomous remediation set (C229-candidate): EMPTY.** No routed findings. **C229 = NO-OP** (nothing to apply). Rotation advances +2 to **t3-v3** on the next fire (per the C190→C192 precedent — atp-adp is immediately followed by t3-v3 in the active round-robin; **GUARD carried from memory: do NOT re-open the t3-v3 spec side — C192-N1 is SDK-side, spec byte-frozen & CORRECT**).

---

## §F — Lessons / Method Notes

- **2nd consecutive zero-routed atp-adp delta — and the reason is instructive.** The biggest corpus event since C190 (an entire enforcement framework standing up on atp-adp's slashing primitive) was the natural place to expect a net-new defect. Refuting the strongest candidate on every axis — citation accuracy (`slash_atp` literally at §2.4 L175), referent grounding (§9.2 anti-patterns), and authority-gate preservation (abstract `has_slashing_authority` composes with Effector-via-R7) — turned the "load-bearing" event into a **consistency confirmation**. A mature primitive being newly depended-upon without breaking is a positive signal, correctly recorded as INFO not routed. [[feedback_refute_your_best_finding]]
- **The false-mirror discipline is now a reflex on the growth edge.** `lct.rs:585 slash()` is the fourth name-collision false-mirror in the rotation (after `ratchet.rs` C222, `attestation.rs`-for-registries C220, and the `error.rs` C178 class) — caught by re-deriving the mirror set at live HEAD and asking "does this construct exercise *this doc's* surface?" rather than grepping a keyword. [[feedback_enumeration_and_grep_hypotheses]]
- **A "new consumer" can revive a dormant DESIGN-Q without creating a defect.** The M2 carry (§2.4 slash / §6.1 `max_slash_per_event` unlinked) gains a second interested party (the Effector) via I-1 — recorded as increased salience for the operator, not escalated to a finding, because atp-adp's own text is unchanged and correct.

---

## §G — Methodology Note

Single-auditor delta-re-audit, refute-by-default, proportioned to a byte-frozen target (HEAD blob == `256ab51d` blob, git-verified) with a 9-mover corpus delta (each diffed at cited-hunk granularity, snapshot-presence guarded) and both SDK mirrors byte-frozen since the C190 baseline. §A = persistence verification at live HEAD (greps re-run) + §7.1 normative-summary blindspot re-check (DOC-SPECIFIC, no corpus sweep). §B = W4IP-cluster citation-accuracy adjudication against primary sources (atp-adp §2.4 L175, §9.2 L690–696; reputation §4; SOCIETY_SPEC §7.3; entity-types §4.8 Effector). §B′ = SDK-mirror gate re-derived at live HEAD, false-mirror-excluding `lct.rs slash()`. Independent adversarial policy-review subagent verified freeze status, rotation lineage, and both citation anchors before scope approval. 0 HIGH / 0 MEDIUM / 0 LOW-routed — the numeric/normative core is sound, the primitive mirror is concordant-and-frozen, and the newly-dependent enforcement framework cites the spec accurately.

*Audit complete. Recommended next step: **C229 = NO-OP** (empty autonomous set); rotation advances +2 to `t3-v3` on the next fire. All DESIGN-Q / SDK-track / corpus carries remain operator- or track-gated; I-1/I-2 are INFO-only forward notes.*
