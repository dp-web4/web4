# C156: reputation-computation.md — Fourth Delta Re-Audit (+ C155 no-op declaration)

**Date**: 2026-07-08
**Auditor**: Autonomous session (legion-web4-20260708-000036), LEAD
**Document**: `web4-standard/core-spec/reputation-computation.md` (814 lines)
**Lineage**: C13/C15 (internal-consistency) → C44 (1st delta, #304) → C45 remediation (#305 `00803b03`) → C84 (2nd delta) → C85 remediation (#376 `15be0743`) → C123 (3rd delta, #428) → C124 remediation (#429 `4d1594ea`) → **C156** (this 4th delta). File **byte-frozen since C124** (`git diff 4d1594ea..HEAD -- <target>` empty; 7 days).
**Instrument**: 3 refute-by-default finder lenses (§A regression verifier / corpus-delta cited-hunk / inbound-lean-on + internal-blindspot) → adversarial verifier subagent over all 7 surviving candidates (refute-by-default, primary-source re-read) → lead hand-verification of every headline anchor with live sed/grep.

---

## C155 — t3-v3-tensors REMEDIATION slot: genuine no-op (declared)

C155 (t3-v3 remediation slot, alternation after C154 AUDIT) is a **trivial genuine no-op**:

1. C154's only yield (**C154-N1**, mcp:415 Law-Oracle bounds citation mis-anchor) is **mcp-owned cross-track**, routed to the next mcp rotation turn — zero autonomous-in-file items for t3-v3.
2. **Zero commits merged since C154** (`aacd278a` = PR #482 merge = HEAD of main at session base) — nothing could have introduced a new t3-v3 item. Target remains byte-frozen since C122 `b2a98f7c`.
3. PR #482 merged with an operator APPROVED review comment spot-checking all four load-bearing claims; no changes requested.

Per the 16-instance no-op→advance precedent (C93→C94 … C153→C154), this is the **17th**: rotation advances to `reputation-computation.md` (last audited C123 #428, remediated C124 #429, 2026-07-01).

---

## Summary

| | Count | Notes |
|---|---|---|
| **§A regression** | 2/2 C124 **HELD** (token-by-token vs live SDK) + 30/30 prior findings **HELD** (8 C15 + 13 C45 + 9 C85), **0 REGRESSED** | Sixth consecutive clean delta in this lineage. Remediation-introduced-regression check on C124's own net-new prose: **CLEAN** — first clean check in this lineage (C123 had caught C85's fail-closed over-reach). |
| **§B confirmed** | 5 (1 flagship carry-amendment / 1 L autonomous / 2 L cross-track / 1 INFO cross-track) | 0 HIGH, 0 MED. |
| **§B refuted / deflated** | 1 refuted (Validity binary-vs-fractional as in-target defect) + 1 deflated to INFO (quality_threshold=0.0 edge) + 6 finder-killed candidates | Overcall discipline held. |
| **Autonomous-actionable (→ C157)** | **1** | C156-2 (§9 L762). **C157 is NOT a no-op.** |
| **Corpus delta since C124** | 4 web4-standard movers, **4/4 DISJOINT** by cited hunk; hub Rust delta (~2.2k lines) **shape-REINFORCING** | Hub reuses the canonical role-keyed `t3_delta`/`v3_delta` split `ReputationDelta` — no X-1 recurrence. |

**Headline**: The C15+C45+C85+C124 layers are fully durable (sixth clean delta; C124's prose verified claim-by-claim against the live SDK). The flagship yield is **C156-1**: adjudicating the inbound C154-N1 lean-on — mcp:415's prescribed re-anchor target `reputation-computation.md:241` is a **PARTIAL anchor**. L241 supports the *rule-definition* half ("Law Oracles define reputation rules that map outcomes to T3/V3 deltas") but the target has **zero Law-Oracle bounds/caps vocabulary**; the "bounds" half lives in SAL §5.5 (`web4-society-authority-law.md:220` "Rate limits and caps defined by Law Oracle", L227 `law.bounds`) — which is **Auditor-scoped**, not the general R7 path. The C154-N1 carry's prescription is amended with a three-option menu before the mcp owner applies it (the [[feedback_prior_finding_path_provenance]] discipline: re-adjudicate a carry's prescription at the file it cites). The one autonomous item (C156-2) is a §9 unbacked present-tense security claim, same class as C44 B-I1. The hub Rust delta — audited for the first time through the reputation surface — is shape-reinforcing but yields two routed LOWs (Rust-ahead-of-spec `sovereign_strength`; law-ungated temporal fold).

---

## §A — Regression Check

### C124's two edits — HELD, every claim re-verified token-by-token vs live SDK

**NEW-1 fix (§4 fail-open paragraph, live L295–301)**: all claims verified against `implementation/sdk/web4/reputation.py` `ReputationRule.matches()` L90–115 — exactly 4 recognized keys (`action_type` L95, `result_status` L99–102, `quality_threshold` L105–107, `min_atp_stake` L111–112), unconditional fall-through `return True` L115, unrecognized keys never read (fail-OPEN); "not currently required" verified (zero fail-closed conformance vectors). All four recognized-condition table rows accurate against SDK comparators/defaults (one behaviorally-inert edge → INFO-2 below).

**N1 fix (§7 clamps, live L657/L708)**: token-equivalent to SDK `current()` L442 / `inactivity_decay()` L476 `max(0.0, …)`. Surrounding §7 pseudocode fully re-verified: recency `exp(-age/30)` ↔ L443 (`DEFAULT_HALF_LIFE_DAYS=30.0` L360); 90-day horizon ↔ L361/L432–433; 0.5 baseline ↔ L436/L447–454 (`_clamp` verified `[0,1]` at `trust.py:140-141`); 30-day grace ↔ L362/L478; −0.01/month ↔ L363/L482; 1.5× after 6 months ↔ L364–365/L484; cap −0.5 ↔ L366/L487; `effective_reputation` ↔ L489–510. All HELD.

### Remediation-introduced-regression check (9th-pattern check) — CLEAN

`git diff 4d1594ea^ 4d1594ea` = exactly 3 hunks. Every factual claim in C124's net-new prose (function names, fail-open behavior, "not currently required", "floored at 0 for clock skew (SDK parity)" ×2) re-tested against the live SDK — **no over-reach found**. First clean remediation-regression check in this lineage (C123 caught C85's fail-closed SHOULD; C124 avoided the pattern by describing the SDK's actual behavior rather than elaborating past it).

### 30 tracked prior findings — HELD

File byte-frozen since C124 + all three mirrors frozen at expected commits (`reputation.py` `759eaefa` Apr/Sprint 38; `r6.py` `766611ef`; `test-vectors/reputation/` `740f21de`) → hold by byte-identity. Six anchors spot-verified at live line numbers (all shifted +5 after C124 grew §4): H1 0.5-baseline **L665**; M2 `get_validators_for_role(action.role.role_lct)` **L567**; C85 INT-1 `high_accuracy`/0.4 **L50**; C85 SDK-3 `round(efficiency * 0.2, 4)` **L502** ↔ SDK L201; C45 B-M2 role-keyed decay **L698/L703–706** ↔ SDK L370/L456–462; C45 B-I1 diminishing-returns cross-ref **L767** ↔ t3-v3 L475–480 + t3v3-007.

### Carries — re-anchored at live HEAD, ALL STAND

| Carry | Status | Live evidence |
|---|---|---|
| **X-1** (3 reputation shapes: mcp §7.3 flat `trust_dimension_updates` ⊥ r7 §1.7 / this doc §1 t3/v3 split) | **STANDS** | `git log 4d1594ea..HEAD -- mcp-protocol.md r7-framework.md` EMPTY; mcp L398–402 flat map; r7 L284/L288 split. Hub Rust delta does NOT add a 4th shape (see §B corpus-delta). |
| **X-2** (§10 frames cross-society as future; mcp §7.5 normative) | **STANDS** | Target L786 under "## 10. Future Evolution" L779; mcp §7.5 L490+ normative. |
| **NEW-1-SDK-face** (tighten SDK `matches()` to fail-closed? operator) | **STANDS** | SDK frozen; still fail-open. |
| **r7-§1.7-stale-factor** (outbound, r7-owned) | **STANDS** | `accuracy_threshold_exceeded` still at r7-framework.md:294. |
| **SDK-6/B-I5** (§6 witness selection unimplemented in SDK) | **STANDS** | SDK-wide grep `select_reputation_witnesses|get_validators_for_role|get_mrh_witnesses` = 0; `ReputationDelta.witnesses` (r6.py L599) never populated by `evaluate()` (reputation.py L314–326). |
| **N2** (SDK write-back side-effect) | **STANDS** | `action.reputation = delta` still reputation.py L327; spec §5 only returns (L415). |

---

## §B — New Findings (all adversarially verified)

### C156-1 (FLAGSHIP — carry amendment, LOW, cross-track mcp-owned): C154-N1's prescribed re-anchor target is a PARTIAL anchor

**Context**: C154 (PR #482, operator-ratified) found `mcp-protocol.md:415` — "The `reputation.trust_dimension_updates` deltas **MUST be within bounds set by** the responding society's **Law Oracle** for the role context (per `t3-v3-tensors.md` parameter governance)" — dereferences to nothing in t3-v3 (re-confirmed this audit: zero "Law Oracle" mentions; no delta-bounds row in §10.2/§10.3) and prescribed re-anchoring the parenthetical to `reputation-computation.md:241`.

**Adjudication at the cited target (this file)**: **PARTIAL-ANCHOR.**
- L241 supports the **rule-definition half**: "Reputation changes are **rule-triggered**, not arbitrary. Law Oracles define reputation rules that map outcomes to T3/V3 deltas." Rule Structure L245–280 shows Law-Oracle-authored `base_delta` magnitudes + modifiers + `law_oracle` field — delta magnitudes are Oracle-controlled *via rule authorship*.
- The target has **zero Law-Oracle bounds/caps vocabulary**: its clamps (±1.0 delta L446–447, [0,1] value L371–374/L667, decay cap −0.5 L721) are fixed algorithmic, Oracle-independent; L217 affirmatively leaves the Valuation upper bound an open question. Nothing a verifier could check a delta against as an Oracle-set *bound*.
- The corpus's actual "bounds" text lives in **SAL** `web4-society-authority-law.md` §5.5 (L220 "**Rate limits** and **caps** defined by Law Oracle to prevent punitive abuse and to bound volatility"; L227 `deltas = compute_deltas(ev, law.bounds)`) — but §5.5 is the **Auditor** Adjustment Policy, not the general R7-over-MCP delta path. Citing it requires an auditor→R7 generalization the corpus does not yet make.

**Amended prescription for the C154-N1 owner (mcp turn)** — three options, verified:
1. **(recommended — zero semantic stretch)** Soften mcp:415 to "…deltas MUST conform to the reputation rules defined by the responding society's Law Oracle for the role context (per `reputation-computation.md` §4)". The "for the role context" fragment is fully supported (target §1 L86 CRITICAL role-contextualization).
2. Keep "bounds" and cite SAL §5.5, explicitly accepting/stating the auditor→R7 generalization.
3. Dual-cite: rule definition → reputation-computation §4; caps power → SAL §5.5.

**Lesson instance**: [[feedback_prior_finding_path_provenance]] third confirmation — a carry's PRESCRIPTION must be re-adjudicated at the file it points to before the owner applies it (C146: wrong path; C152: wrong crypto prescription; C156: half-supported anchor).

### C156-2 (LOW, **AUTONOMOUS → C157**): §9 Sybil item 4 asserts an unbacked mechanism, contradicting §10

**Location**: L762 "4. Historical patterns are analyzed (sudden changes flagged)" — present tense, in the §9 "Reputation cannot be easily gamed … because:" list of existing properties.
**Contradiction**: no such mechanism exists in §4–§7, the SDK (`grep -iE 'anomal|historical|pattern|sudden'` reputation.py = 0), or the corpus; §10 L783–784 explicitly classifies exactly this capability ("Machine Learning Reputation Models — Use historical patterns to predict reputation changes and detect anomalies") as **Future Evolution**. Items 1–3 of the same list are all backed (ATP cost; role-keying §1/r7 §1.7; witnesses per rule).
**Prior-adjudication check**: C44/C84/C123/C124 docs grepped — same-class B-I1 (diminishing returns) was adjudicated and fixed via canonical cross-ref; this item never audited. Not among C123's 12 refuted.
**Severity**: LOW — slightly stronger than B-I1's shape (B-I1's mechanism existed canonically elsewhere; this exists nowhere).
**Fix (C157, autonomous, one line)**: soften to future/recommendation and cross-ref §10 — e.g. "4. Historical patterns SHOULD be analyzed for sudden changes (see §10, Machine Learning Reputation Models; not yet specified)". Exact B-I1-precedent shape.

### C156-3 (LOW, cross-track — spec + Python-SDK owners, route-only): Rust `ReputationDelta.sovereign_strength` is ahead of BOTH the spec and the Python reference SDK

`web4-core/src/r6.rs:257–266` (added `c21442bd`, identity-p1 PR #457, in-window) gives the R7 reputation output struct a `#[serde(default)] sovereign_strength: SovereignStrength{Placeholder|Hardware}` field (fail-closed default, weakest-strength fold semantics at hub-lib `state.rs:615`); the hub emits it (`rest.rs:2545`, serialized L2661). `grep -rn sovereign_strength web4-standard/` = **0**: target §1 field table (L68–84), r7-framework.md §1.7, and Python `r6.py` `ReputationDelta` all lack it. One-directional mirror drift on a semantically load-bearing field. Route: spec owner (r7 §1.7 Components is the natural home) + Python SDK owner. NOT autonomous-in-target.

### C156-4 (LOW, hub-track, route-only): hub temporal reputation fold is code-triggered, not Law-Oracle-rule-triggered

Target L241: "Reputation changes are **rule-triggered**, not arbitrary. Law Oracles define reputation rules…". The hub's new temporal fold (`rest.rs:3020–3057` R7Op::Satisfy → `temporal_delta` L2501–2556) synthesizes `rule_triggered: "deadline_{met|late|missed}"` ids defined in **no Law-Oracle rule set**, with magnitudes compiled into `web4-core/src/time.rs:123–141` — **no law/policy lookup on the path** (verified: the new `reputation_emit` law section, law.rs:169–209, gates only external non-Sovereign emitters; the internal fold never touches it; no temporal law section exists). Mitigations noted: outcomes computed from witnessed timestamps; dimension semantics match target vocabulary (`deadline_met`, Temperament/Veracity). The magnitudes are also unclassified by t3-v3 §10's governance tiers. Route: hub track (either add a temporal law section to HubPolicy or document the hub-as-implicit-oracle position).

### C156-5 (INFO, acp-owned, route-only): `acp-framework.md:418` "reputation stakes" dereferences to Future Evolution only

acp §7.2 Threat-Mitigation table lists "reputation stakes" as a current trust-gaming mitigation; the only corpus mechanism is target §10 L789–790 **Reputation Staking = Future Evolution** (unspecified). Refutation tested: `min_atp_stake` (§4) is an ATP stake, not reputation-as-collateral — cannot rescue the phrase. Same dereference-test shape as C154-N1 (second consecutive audit where a sibling's citation into the target fails the dereference test). Route: acp rotation turn.

### INFO / record-only

| ID | Item | Disposition |
|---|---|---|
| INFO-1 | Refuted Item-3 residual: the per-transaction V3 *measurement* model (t3-v3 §3.3, mirrored at target L188 with canonical cite) vs the fractional R7 rule-delta path is a **canonical-level** ambiguity (t3-v3 §10.2 lists "V3 calculation" protocol-invariant). If ever raised, belongs on a **t3-v3 turn**, not here (see §C). | record / t3-v3-outbound observation |
| INFO-2 | §4 L292 "missing quality … so the threshold fails" is false only at `quality_threshold: 0.0` (SDK `0.0 < 0.0` = False → matches). Behaviorally inert corner (a 0.0 gate rejects nothing; authors omit the optional field). | record (deflated from LOW by verifier) |
| INFO-3 | SDK identifier misnomer: `DEFAULT_HALF_LIFE_DAYS`/`half_life_days` (reputation.py L360/L417/L443) is used as a 1/e **time constant**; actual half-life ≈ 20.8d. Spec L658 is correct and explicitly disambiguates. SDK-side naming only. | record, SDK-owned |
| INFO-4 | Spec §5 omits SDK's float-noise guard `round(new−old, 10)` (SDK L276/L303). Immaterial (1e-10 dust). | record |
| INFO-5 | Hub's typed `reputation_emit` law section has zero coverage in `core-spec/hub-law-schema.md` (its §4 Extension Mechanism arguably absorbs it). | record, hub-law-schema-owned |

---

## §B — Corpus delta since C124 (`4d1594ea`, 2026-07-01)

Target's citation surface: only `t3-v3-tensors.md` (×5) and `r7-framework.md` (L814, dereference-verified: r7 §1.7 exists and is the Reputation-record home) by name; zero `atp-adp`/`acp`/`conservation`/`fractal`/`presence` tokens.

| Mover | Hunk | Verdict |
|---|---|---|
| `256ab51d` atp-adp C151 | §2.4 L214 one-phrase conservation-scope reword | **DISJOINT** — target never cites atp-adp/§2.4/conservation; atp-adp has zero reputation-computation citations. |
| `4e3feb26` FRACTAL C130 | mrh line-anchor fix (L53) | **DISJOINT** — changed hunk ⊥ target; FRI's *unchanged* role-contextualization prose (L48–49/L175) REINFORCES target L86. |
| `cf0d6cc5` presence README C128 | schema-gap ledger 2→4 items | **DISJOINT** — zero reputation surface. |
| `aabe4457` acp C126 | `resourceCaps` snake→camel (L77–79/L312) | **DISJOINT** — target reads `action.resource.required_atp`/`result.atp_consumed`, a different object path; zero `resourceCaps`/`maxAtp` tokens in target. |

**Hub Rust delta** (~2.2k insertions, PRs #465–#481 + identity-p1): audited through the reputation surface for the first time. **Shape-REINFORCING** — everything reuses `web4_core::r6::ReputationDelta` with the canonical role-keyed `t3_delta`/`v3_delta` split (+ `rule_triggered`/`contributing_factors`/`witnesses`), field-for-field the target's §1 structure; events.rs:408–413 doc states "Reputation is NEVER global"; constellation-role normalization (law.rs, fail-closed) actively *enforces* target role-contextualization. **No new flat-map shape → X-1 NOT re-triggered.** Yields: C156-3, C156-4, INFO-5 above. `rfcs/` unchanged in-window; no new file cites `reputation-computation` by name outside audit docs.

---

## §C — Refuted / killed candidates (overcall discipline)

1. **§3.2 L188 Validity "binary per transaction … averaged" contradicts §4/§5 fractional deltas** — REFUTED as an in-target autonomous defect: the sentence carries its own canonical cite and mirrors t3-v3 §3.3 verbatim ("Validity = 1.0 if value_transferred else 0.0"; canonical also says aggregates are averaged); it was *installed* by C44 B-M3 precisely to match canonical (C84 verified token-by-token and refuted a drift re-raise); the §3 preamble (L165–168) states the governance ordering ("canonical definitions govern"). Editing it here would recreate the divergence B-M3 fixed. Residual measurement-vs-rule-delta ambiguity is canonical-level → INFO-1, t3-v3-outbound.
2. §2/§3 interpretation bands vs §7's 0.5-baseline aggregate — KILLED: bands read against stored `t3InRole` values; L691 modeling note already acknowledges the aggregate behavior.
3. §8 checklist phantom functions — KILLED: all referenced functions exist (L346/L418/L450/§6/§7).
4. §9 "Each action costs ATP" — twice-refuted previously (C44, C84); not re-raised.
5. §10 Reputation Markets parenthetical vs t3-v3:452 V3-weighted pricing — KILLED: future head-noun is *markets/trading*; the parenthetical glosses an existing weighting.
6. "Fundamental Principle: every transaction produces Reputation" vs §5 possibly-empty delta — KILLED: §1 field defs allow empty deltas.
7. quality_threshold missing-value clause as LOW — DEFLATED to INFO-2 (vacuous edge).

---

## Remediation summary (for the C157 turn)

**1 autonomous-actionable** (spec-only, one line):

| ID | Sev | Fix |
|---|---|---|
| C156-2 | L | §9 L762: soften item 4 to future/SHOULD + cross-ref §10 (B-I1-precedent shape). |

**Routed (do NOT self-apply)**:
- **C156-1** → amends the standing **C154-N1** carry (mcp-owned): mcp:415 re-anchor must use the 3-option menu (recommend option 1: soften "bounds" → "conform to the reputation rules defined by" + cite reputation-computation §4); reputation:241 alone is a PARTIAL anchor.
- **C156-3** → spec (r7 §1.7 Components) + Python SDK owners: `sovereign_strength` field.
- **C156-4** → hub track: law-ungated temporal fold vs "rule-triggered, not arbitrary".
- **C156-5** → acp turn: L418 "reputation stakes" dereference failure.
- INFO-1 → t3-v3 turn (canonical measurement-vs-rule-delta note, optional); INFO-3 → SDK naming; INFO-5 → hub-law-schema.

**Standing carries unchanged**: X-1, X-2, NEW-1-SDK-face, r7-§1.7-stale-factor, SDK-6/B-I5, N2.

---

*C156 lineage verdict: the reputation-computation remediation stack (C15→C45→C85→C124) is fully durable — sixth clean delta, first clean remediation-regression check in this lineage. The 4th-delta yield is entirely on the moving corpus around the frozen file: the inbound C154-N1 lean-on adjudication (PARTIAL-ANCHOR — the flagship, third confirmation that carried prescriptions must be re-adjudicated at their cited target), the hub Rust delta's first reputation-surface audit (shape-reinforcing; two routed LOWs), and one autonomous §9 unbacked-claim fix for C157.*
