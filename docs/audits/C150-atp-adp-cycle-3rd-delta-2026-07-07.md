# C150 Audit: `atp-adp-cycle.md` Third Delta Re-Audit (prior C118/C119)

**Date**: 2026-07-07
**Auditor**: Autonomous session (Legion, web4 track) — single-auditor refute-by-default + independent adversarial verifier subagent (C144 bar: agreement ≠ corroboration; every interpretation-bearing ruling attacked against primary sources).
**Document**: `web4-standard/core-spec/atp-adp-cycle.md` (804 lines)
**Lineage**: C11 (#224 first-pass) → C34 (#276/#277) → C78 (#367) / C79 (#368) → C118 (#418 second delta, found N1+N2) → C119 (#420 `e99b419e`, applied N1) → **C150** (this, third delta-re-audit).
**Baseline**: C118 audit (`docs/audits/C118-atp-adp-cycle-2nd-delta-2026-06-29.md`); C119 remediation (`docs/audits/C119-atp-adp-cycle-remediation-2026-06-30.md`, commit `e99b419e`, PR #420).
**Method**: §A re-verifies the C119 remediation and every C79 fix and open carry at **LIVE HEAD** (greps re-run, not cached, per [[feedback_prior_finding_path_provenance]]), including the C56 claim-vs-canonical re-read of C119's **own new prose** (the remediation-introduced-regression check — on a byte-frozen target, the only net-new prose since the last audit *is* the prior remediation). §B sweeps the corpus delta — 7 commits touched `web4-standard/` since C119 — at cited-hunk granularity, with the snapshot-presence guard, plus the §7.1 normative-summary blindspot re-check (the known MUST-vs-impl locus; DOC-SPECIFIC per the C121 signal, **no** corpus-wide sweep). **Read-only AUDIT turn — zero spec/SDK mutation.**

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 0 | — |
| MEDIUM | 0 | — |
| LOW | 1 | **N1** (latent, pre-existing since C34; newly load-bearing; AUTONOMOUS-candidate) |

**Delta result (§A)**: Target **byte-frozen since C119** (`git diff e99b419e..HEAD` on the file = empty). C119's 3-part fix **present & correct** (§7.1 MUST #6 reword L622; scope note L624–633; §4.2 comment L383–384) — the scope note's claims re-verified token-by-token against §4.2/§4.3 actuals and **survived the remediation-introduced-regression check** (adversarially verified, Item 2 below). All **5 C79 fixes HELD** (L240, L264–269, L323–331, L434–440 + L799–803, L419–430). **C118-N2 carry CLOSED** — C122 (`b2a98f7c`) applied it to t3-v3 L640 and the application is **verified correct** at all three anchors. All other carries **STAND** (movers frozen: SDK `atp.py` last touched `62524cf8` C11-era; ISP last touched `0405f331` C63; mcp §7.7 untouched by C117).

**§B corpus delta**: 7 movers since C119 — **1 REINFORCING/carry-closing** (t3-v3 C122), **6 DISJOINT** (mcp C117 = §12-only, atp-adp cites §7.7; reputation C124 = hunks disjoint + zero-citation; acp C126 = casing-only, no shared surface; presence-README C128 and FRACTAL_ROLE_IDENTITY C130 = zero ATP surface; new `rfcs/RFC-SHARED-POLICY-SUBSTRATE.md` = hub-lib code-structure prose, no atp-adp-semantics claims).

**Yield (N1)**: not in the delta — it is a **latent wording defect surfaced by the delta becoming load-bearing**: §2.4 L214 mislabels the transfer-conservation invariant's scope as "ATP→ADP transfers" (a category error mixing the doc's discharge arrow with entity→entity transfer), and C122 just anchored t3-v3's ATP-conservation row on exactly this note. Same shape as the C146 yield (a 3-audit-old mislabel found on an otherwise-clean frozen target).

---

## §A — C119/C79 Delta-Persistence at LIVE HEAD

Target byte-frozen since C119 (`e99b419e`); the C119 diff touched only L383–384 and L619–633, so every C79 fix outside those hunks is held by byte-identity **and** was re-read live:

| Prior ID | Fix | Status | Live evidence |
|----------|-----|--------|---------------|
| **C118-N1 (C119 fix, part 1)** | §7.1 MUST #6 entity-scoping reword | **HELD** | L622: "Entity-level value MUST be tracked through T3/V3 tensors; society-level aggregates MAY use non-tensor rollup accounting (§4.2)". |
| **C118-N1 (part 2)** | §7.1 scope note | **HELD & ACCURATE** | L624–633. Claim-vs-canonical re-read (verifier Item 2): entity-leg enumeration matches §4.2 exactly (beneficiary `v3` L373, agent `t3` L374, witnesses `t3` L378–381); §3.3 quote verbatim (L331); "not a T3/V3 dimension" quote verbatim (L383). |
| **C118-N1 (part 3)** | §4.2 `aggregate_value` back-reference comment | **HELD** | L383–384: "rollup accounting, outside §7.1 MUST #6 per its scope note". |
| **C79-B2a** | §3.3 demurrage R6 carve-out note | **HELD** | L323–331. |
| **C79-B5** | `mint_adp` nested-pool form | **HELD** | L264–269 (invariant note "total_supply == sum(allocations) and == sum(state_distribution)"). |
| **C79-B6** | `charged_fraction` rename + disambiguation | **HELD** | L240. |
| **C79-B7** | ISP+mcp §5 note + References | **HELD & claims re-verified** | L434–440; L799–803. mcp §7.7 untouched by C117 (grep of `afab0c43` diff for "7.7" = 0); ISP frozen since C63 → both References claims still accurate (C56 re-read). |
| **C79-B8** | §4.3 role-vocabulary note | **HELD** | L419–430. |

**Open carries — bidirectional re-verification (greps re-run at HEAD):**
- **C118-N2** — **CLOSED by C122** (see §B, verified correct). First atp-adp carry closed by a *sibling's* remediation.
- **B1** (§5 abstract-FX vs mcp §7.7.1 normative referent-grounding — CROSS-TRACK/DESIGN-Q): **STILL OPEN.** §5.2 "Floating | Market-determined rate" L483; §5.3 uniform `get_exchange_rate` L500–503; the C79 reconciliation note L434–440 flags, does not resolve (by design; operator-gated). mcp §7.7 unmoved.
- **B2b** (§5.3 exchange discharge/charge bypasses MUST #4/#5/#6 — DESIGN-Q): **STILL OPEN.** L511 `source_society.pool.discharge(source_atp)` / L512 `target_society.pool.charge(target_atp)` remain the lone un-noted non-R6 path. (§7.1 blindspot re-check confirms MUST #4's bypass by the §5.3 `charge` leg is inside B2b's existing scope — no new finding.)
- **M2** (§2.4 slash cap never references §6.1 `max_slash_per_event` — DESIGN-Q): **STILL OPEN.** L194 `min(amount, get_entity_stake(violator))`; L547 `max_slash_per_event: 10000`.
- **B3 / B4 / I2 / B6-SDK** (SDK-track): **STILL OPEN** — `web4-sdk` `atp.py` frozen (last commit `62524cf8`, C11-era #228).
- **X1** (`lct:web4:` identifier — C33 corpus decision): **STILL OPEN** (L51, L57, L59… unchanged).
- **ISP-B10** (commitment-ATP charged-vs-allocated — DESIGN-Q): **STILL OPEN** (ISP frozen since C63 `0405f331`).

**§7.1 normative-summary blindspot re-check (the C116/C118 defect-class locus, DOC-SPECIFIC)**: MUST #1 (escrow note L635–641 covers the known nuance), #2 (§3.3), #3 (§3), #4/#5 (sole un-noted bypass = §5.3, inside B2b), #6 (C119-fixed, verified above) — **no new cross-section contradiction**. §7.2/§7.3 lists re-checked against body: clean (see §E for two deflated candidates).

---

## §B — Corpus Delta (7 movers since C119, cited-hunk granularity)

| Mover (C#, commit) | Change | Verdict |
|--------------------|--------|---------|
| **t3-v3 C122 `b2a98f7c`** | Re-anchored the §10.2 ATP-conservation row (L640) per **C118-N2** — the exact fix C118 routed there | **REINFORCING; closes N2.** Remediated-mover read at rationale level (C140 lesson) + all 3 anchors verified token-by-token (verifier Item 1): §3.1/§3.2 supply equation (L227–231 instantiation + L266 explicit invariant), §2.4 per-transfer form (`initial == final + fees` — grep confirms L214 is its ONLY occurrence) with slashing-exception (L211–215), §6.3 fee-recycling (L604–605 verbatim). No residual mis-anchor **in t3-v3** — but see N1: the §2.4 note it now leans on has its own wording defect. |
| **mcp C117 `afab0c43`** | 1 line: mcp §12 item 6 R7-witnessing rescope | **DISJOINT.** atp-adp cites mcp only at L436–439 + L801–802, both §7.7. |
| **reputation C124 `4d1594ea`** | Fail-open rule-condition note + 2 clock-skew floors | **DISJOINT.** No hunk touches `min_atp_stake`/`required_atp`/`atp_consumed`; stronger, atp-adp contains zero citations of reputation-computation.md (disjoint-by-non-citation). |
| **acp C126 `aabe4457`** | resourceCaps guard keys snake→camel (`max_atp`→`maxAtp` etc.) | **DISJOINT.** atp-adp has no resourceCaps surface (grep = 0); acp's §2.3 citation of atp-adp untouched by the diff (grep = 0). Directionally consistent with atp-adp's own camelCase illustrative JSON. |
| **presence-README C128 `cf0d6cc5`** | Schema gap-ledger completion | **DISJOINT** (zero ATP/ADP occurrences). |
| **FRACTAL_ROLE_IDENTITY C130 `4e3feb26`** | mrh line-anchor fix | **DISJOINT** (zero ATP/ADP occurrences). |
| **NEW `rfcs/RFC-SHARED-POLICY-SUBSTRATE.md` `43c90d3e`** | 222-line RFC, 6 ATP mentions | **DISJOINT** (verifier Item 5, refute attempt failed): all mentions are hub-lib Rust inventory (`AtpIssuancePolicy`, `atp_issuance.mint_authority` as a validate() role-vocabulary rule, `HubPolicy` peel proposal). No claim about token states/supply/conservation/minting *semantics*; `mint_authority` validated by law is consistent with §3.2 L261 `law.permits_minting(...)` — an implementation of, not a redefinition of, §2.1/§6.1 territory. |

### N1 — §2.4 supply-accounting note mislabels the conservation invariant's scope as "ATP→ADP transfers" — LOW, LATENT (pre-existing since C34), newly load-bearing, AUTONOMOUS-candidate

**Live text (L213–214)**: slashing "sits **outside** the transfer-conservation invariant (`initial == final + fees`), which scopes only **ATP→ADP transfers**".

**Defect**: "ATP→ADP transfers" is a category error. In this doc's own conventions, the arrow form "ATP→ADP" means *discharge* (§2.3 heading L124; §3.3 note L323 "performs the ATP→ADP discharge of §2.3"), while entity→entity *transfers* are written arrow-free (§7.3 #6 L658 "transfer fees on ATP transfers"; §6.3 throughout). The invariant `initial == final + fees` coherently applies only to **transfers** — corroborated by the SDK canonical (`atp.py` L310–323 `check_conservation`, tied to `transfer()` with `fee = amount * fee_rate`; header L10 "total ATP + fees always equals initial") — and does **not** coherently apply to a discharge, which reduces the ATP total feelessly by design. L214 is the doc's sole arrow+transfer hybrid.

**Provenance (snapshot guard)**: phrase entered at C34's remediation `f854e0e` (#277) — present and unflagged through C78, C118 (C118-N2 even quoted this note as the `initial == final + fees` home without catching the scope phrase). So: **NOT net-new**; a genuine 3-audit latent, per the [[feedback_prior_finding_path_provenance]] family (content real, label wrong).

**Why it surfaced now / why it matters now**: C122 re-anchored t3-v3's ATP-conservation row **onto this exact note** as the "per-transfer invariant" home. t3-v3's reading (transfer-scoped) is correct per the SDK; §2.4's literal wording (discharge-scoped) now disagrees with the sibling that cites it. The wording is newly load-bearing.

**Adversarial verification**: CONFIRMED as real by the independent verifier (Item 4), corroborated three ways (SDK conservation check; doc-internal arrow convention; C34-L5's own deflation rationale "the SDK conservation invariant is scoped to *transfers*, not slashing").

**Routing — AUTONOMOUS (next atp-adp remediation turn, C151-candidate), NOT self-applied (read-only audit)**: one-phrase fix aligning the note with the doc's own conventions, e.g. *"…which scopes only ATP transfers between entities (§6.3)"*. No semantic change; verifier notes §7.3 #6 already models the correct arrow-free form.

---

## §C — Routing Summary

| ID | Severity | Classification | Owner / next step |
|----|----------|----------------|-------------------|
| **N1** | LOW | AUTONOMOUS (latent wording, spec-local) | Next atp-adp remediation (C151-candidate): reword §2.4 L214 scope phrase to "ATP transfers between entities (§6.3)". |
| ~~C118-N2~~ | — | **CLOSED** | Applied by t3-v3 C122 `b2a98f7c`; application verified correct at all 3 anchors. |
| B1 / B2b / M2 / ISP-B10 | — | DESIGN-Q | **Operator** (open, unchanged). |
| B3 / B4 / I2 / B6-SDK | — | SDK-track | SDK (open; `atp.py` frozen). |
| X1 | — | CROSS-TRACK | C33 corpus identifier decision (open). |

**Autonomous remediation set (C151-candidate)**: **N1 only** (1 one-phrase spec edit).

---

## §D — Lessons / Method Notes

- **A carry can be closed by a sibling's remediation** — first instance in this file's lineage: C118-N2 was atp-adp-raised, t3-v3-owned, and C122 closed it. The delta re-audit's job flipped from "is the carry still open?" to "is the *application* correct?" — which is exactly where the C140 remediated-mover lesson (read the rationale, verify token-by-token) paid off.
- **The C146 yield-shape recurs**: on a byte-frozen, corpus-disjoint target, the finding was a **years-old mislabel made newly load-bearing by the delta** (C146: a path; here: a scope phrase). The productive question on clean deltas is not "what changed?" but "what does the change now *lean on*, and does that support hold?"
- **Remediation-introduced-regression check came back clean for the first time in three firings of this rotation**: C119's scope note survived token-by-token re-reading (unlike C121/C123's targets). The C119 practice plausibly responsible: quoting its canonical sources verbatim rather than paraphrasing.
- **Proportionality**: single auditor + one independent adversarial verifier subagent (6 items, refute-by-default, all primary-source). Right cost for a frozen target with a 7-mover disjoint delta; the verifier's Item-4 corroboration (SDK + arrow-convention + C34-L5 rationale) upgraded a "wording quibble" candidate into a confirmed routed finding.

---

## §E — INFO / Deflated (anti-overcall record)

- *C119 scope note says §4.3 "Levels 4–5" are "tracked via the `aggregate_value` channel in §4.2", but §4.2 code has no parent-society (Level 5) leg* — **deflated to INFO** (verifier Item 2): the note's normative payload (society-level rollups are non-T3/V3 and outside MUST #6) is true for both levels; the doc's established convention (§4.3 role note: "Level 2 is empty" in the simple example) is that the simple example omits legs. Not the C121/C123 over-reach class. Residual INFO: unlike the §4.3 note, it doesn't flag Level 5's absence explicitly.
- *§7.2 SHOULD #5 "Slashing SHOULD require evidence" vs §2.4 impl hard-failing (`raise InsufficientEvidence()`) and §8.2 "must have evidence trails"* — **deflated to INFO** (verifier Item 3): an illustrative impl stricter than a SHOULD floor is permitted; §8.2's lowercase "must" is non-keyword security prose (no RFC2119 boilerplate in doc; C118 §E precedent); the two clauses govern different objects (precondition vs audit trail).
- *§4.2 loop applies `apply_tensor_update()` to the non-tensor `aggregate_value` leg* — **deflated** (function-naming tension in illustrative code; present at the C78/C118 snapshots, unflagged there; snapshot-presence guard → not net-new; no normative content).

---

## §F — Methodology Note

Single-auditor delta-re-audit, refute-by-default, proportioned to a byte-frozen target (HEAD blob == `e99b419e` blob, git-verified) with a 7-mover corpus delta, each mover diffed at cited-hunk granularity. §A = persistence verification at live HEAD (greps re-run, not cached) + C56 claim-vs-canonical re-read of C119's own new prose (remediation-introduced-regression check: **clean**). §B = snapshot-presence guard on every candidate + rationale-level read of the one remediated mover (C122). Independent adversarial verifier subagent attacked all 6 interpretation-bearing rulings against primary sources (target file, sibling diffs, SDK `atp.py`, the new RFC): 5 rulings CONFIRMED with cited evidence, 1 candidate (Item 4) upgraded from deflate-leaning to a confirmed LOW routed finding. 0 HIGH / 0 MEDIUM — the numeric/normative core remains sound; the sole live defect is a pre-C78 wording mislabel that the corpus delta just made load-bearing.

*Audit complete. Recommended next step: C151 atp-adp remediation turn applying **N1** (one-phrase §2.4 edit); all DESIGN-Q / SDK-track / corpus carries remain operator- or track-gated.*
