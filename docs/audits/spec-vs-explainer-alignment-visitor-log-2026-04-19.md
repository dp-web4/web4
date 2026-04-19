# Visitor-Log Friction Triage — 2026-04-19

**Date**: 2026-04-19
**Track**: web4 (Legion autonomous session, Sprint 43 T2)
**Authorization**: Inferred from `CLAUDE.md` "4-Life Feedback Loop" standing-mechanism language + PR #168 precedent. **NOT on issue #166 candidate menu** (which was closed as COMPLETED on 2026-04-19T11:07:35Z). Operator may retroactively reject this scope.
**Source**: `../4-life/visitor/logs/2026-04-19.md` friction table (13 items)
**Precedent**: `docs/audits/spec-vs-explainer-alignment-2026-04-19.md` (PR #168, T1)

---

## Scope Note — Not a Standing Obligation

This memo is a **one-off** discretionary follow-up to PR #168's precedent, applied to today's unprocessed visitor log. It does **NOT** establish a standing per-session or per-day obligation to generate memos. Future sessions must check whether today's log is already processed (by any PR) and prefer clean exit if so, rather than producing duplicate memos or reprocessing already-handled logs. The 4-Life Feedback Loop justifies processing *unprocessed friction signal*, nothing more.

## Purpose

Same as T1: categorize each friction item so downstream sprints (web4 for spec work, 4-life for explainer work) know which side owes the fix.

## Labels

- **SPEC GAP**: Core spec (or canonical documentation) is silent, ambiguous, or internally inconsistent. 4-life's friction reflects a real hole.
- **EXPLAINER GAP**: Spec is clear; 4-life simply does not surface the existing answer.
- **BOTH**: Spec is ambiguous *and* 4-life presents an uncanonical specific number or framing.

## Summary

| Label | Count | Share |
|-------|------:|------:|
| SPEC GAP | 0 | 0% |
| EXPLAINER GAP | 11 | 85% |
| BOTH | 2 | 15% |
| **Total** | **13** | |

**Today's log is overwhelmingly explainer-side.** This is itself a meaningful signal. T1 found 4 SPEC GAPs of 14 (29%); today 0 of 13 (0%). Different visitors surface different things — today's visitor engaged heavily with UX / information architecture / progressive disclosure, and the spec answers every substantive factual question they raised. The 4-life explainer carries more editorial debt than the spec carries gaps.

**Overlap with T1**: Both BOTH items today (community/society/federation, T3 half-lives) were also flagged by yesterday's visitor. This repeats-itself pattern corroborates T1's SPEC GAP / BOTH findings on those same topics — not new signal, reinforcing signal.

## Classifications

### 1. Why Web4 — Page too long (~15k words, 40+ FAQ items)
- **Severity**: MEDIUM
- **Label**: **EXPLAINER GAP**
- **Why**: Pure 4-life editorial / information architecture. No spec question.
- **Resolution**: 4-life IA task — split FAQ, front-load CTAs.

### 2. Why Web4 — "community" / "society" / "federation" used interchangeably
- **Severity**: LOW
- **Label**: **BOTH**
- **Evidence**: `web4-standard/core-spec/web4-society-authority-law.md:70-79` formally defines **Society** as a delegative entity (Authority Role + Law Oracle + Quorum Policy) and composes it fractally (`team ⊂ org ⊂ network ⊂ ecosystem`). `SOCIETY_SPECIFICATION.md:174-175` uses "Local Community" and "Regional Federation" informally in a tree diagram *without* definition or SAL mapping. Grep of `web4-standard/core-spec/` for "community" and "federation" finds uses in examples but no formal definitional entry. CLAUDE.md's canonical glossary (`whitepaper/sections/02-glossary/`) has zero matches for "society", "community", or "federation" (verified).
- **Resolution**:
  - **Spec side**: Either (a) define "community" and "federation" as SAL specializations of "Society" (e.g., federation = society-of-societies at a specific scope), or (b) normalize all instances to "society" and drop the other terms from normative text.
  - **Explainer side**: Whichever spec resolution applies, 4-life should mirror it and define the relationship in one sentence on the Why Web4 page.
- **Same as T1**: This is T1's item #6 rediscovered; corroborates the original finding.

### 3. ATP Economics — No comparison to cryptocurrency
- **Severity**: MEDIUM
- **Label**: **EXPLAINER GAP**
- **Evidence**: `atp-adp-cycle.md:33` *"Unlike traditional currencies designed for storage, ATP tokens must flow to maintain value. Stagnant ATP naturally decays, encouraging continuous value creation and circulation."* Spec makes the semantic distinction from storage-currency explicit; does not mention "Bitcoin" or "cryptocurrency" by name.
- **Resolution**: 4-life ATP page should lift the "must flow vs must be stored" contrast and name Bitcoin/crypto explicitly as the comparison (naming is editorial, not normative).

### 4. ATP Economics — "attention budget" vs "energy budget" wording alternates
- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Evidence**: `atp-adp-cycle.md:7` *"'Allocation' covers all resource types: energy, attention, work, compute, trust budgets."* Spec generalizes as "allocation"; 4-life picks context-specific terms inconsistently.
- **Resolution**: 4-life chooses one canonical term (recommend "energy" since the biological metaphor makes that the primary) and adds a one-line footnote listing the other resource types the allocation covers.

### 5. Trust Tensor — V3 introduced abruptly after T3
- **Severity**: MEDIUM
- **Label**: **EXPLAINER GAP**
- **Evidence**: `t3-v3-tensors.md` defines both tensors as sister concepts: T3 = actor capability, V3 = output quality. Spec has a clean bridge; 4-life's Trust Tensor page does not.
- **Resolution**: 4-life adds a bridging paragraph — "Trust has two sides: who you are as an actor (T3), and the quality of what you produce (V3). Together they form the Web4 trust pair."

### 6. LCT Explainer — "Device witnesses" — who runs witness infrastructure?
- **Severity**: MEDIUM
- **Label**: **EXPLAINER GAP**
- **Evidence**: Spec has TWO kinds of witnessing, both defined:
  - **Cross-device witnessing** (peer-to-peer within your own device constellation): `multi-device-lct-binding.md:18` *"How do devices witness each other to strengthen identity?"* and `§3.3` (line 492+) *"Cross-Device Witnessing: Devices periodically witness each other to strengthen constellation coherence"*. Your own devices witness each other.
  - **SAL Witness role** (society-level attestation): `web4-society-authority-law.md:183-187` *"Maintains the immutable record via co-signed ledger entries for SAL-critical events. Quorum policy defined by Law Oracle (e.g., requiresWitnesses: 3). MUST support timestamping, co-signing, and availability proofs."*
- **Resolution**: 4-life LCT page adds one line distinguishing: (a) your devices witness each other within your own constellation, (b) society-level witnesses (federation-operated or peer-elected) attest ledger events per the society's Law Oracle quorum policy.

### 7. MRH — Formal name + RDF/SPARQL code sample too early for naive readers
- **Severity**: MEDIUM
- **Label**: **EXPLAINER GAP**
- **Why**: Page ordering / progressive disclosure. Spec correctly puts RDF in the normative layer; 4-life mirrored the normative structure into a naive-visitor page where it doesn't belong.
- **Resolution**: 4-life MRH page — lead with "Trust Neighborhoods," defer the formal name, collapse RDF/SPARQL into `<details>`. Matches visitor's own suggestion.

### 8. Karma Journey — Can't preview outcome of a choice before committing
- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Why**: UX affordance for the simulator. Spec doesn't constrain the simulator's hint model.
- **Resolution**: 4-life — hover-tooltip with expected effect range on each action.

### 9. Society Simulator — Cognitive load spike (5 phases × 5 strategies × multi-dim stats)
- **Severity**: MEDIUM
- **Label**: **EXPLAINER GAP**
- **Why**: Simulator UX complexity. Spec does not mandate UI density.
- **Resolution**: 4-life — "first time here?" progressive-reveal mode; stage controls.

### 10. Karma Journey — "Raw trust" vs "effective trust" distinction surprises
- **Severity**: LOW
- **Label**: **BOTH**
- **Evidence**: Grep of `web4-standard/core-spec/` for `raw trust|effective trust|karma` = 0 hits (verified). Spec does not name this distinction. 4-life introduces it without framing or canonical mapping.
- **Resolution**:
  - **Spec side**: Same as T1's item #14 — decide whether raw-vs-effective is a canonical distinction worth naming (probably yes, given reputation decay), and if so, define in `reputation-computation.md` or `t3-v3-tensors.md`.
  - **Explainer side**: Until spec decides, 4-life should add one inline sentence when the distinction first appears ("raw = your cumulative history; effective = what counts after recency and context weighting").
- **Same as T1**: Corroborates T1's SPEC GAP #14 finding.

### 11. How It Works — ~40% overlap with prior concept pages
- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Why**: Information architecture — capstone page vs standalone. Spec doesn't constrain 4-life's page topology.
- **Resolution**: 4-life — mark sections as "recap" vs "new material"; optional but useful.

### 12. Trust Tensor — Temperament 30d vs Talent 365d half-life rationale
- **Severity**: LOW
- **Label**: **BOTH**
- **Evidence**: `t3-v3-tensors.md:108-110` (verified): *"Training Decay: -0.001 per month without practice"*, *"Temperament Recovery: +0.01 per month of good behavior"*, *"Talent Stability: No decay, represents inherent capability."* Spec has **no half-life semantics on T3** — it has per-month delta rates, and Talent has NO decay at all. 4-life's "30d vs 365d half-life" framing is **entirely invented** and contradicts the "Talent has no decay" spec. Additionally, spec does not provide intuition for why Training decays while Talent doesn't.
- **Resolution**:
  - **Spec side**: Either add a short rationale in `t3-v3-tensors.md` (§2.5 "Decay Rationale") explaining why Talent is stable while Training/Temperament drift, or keep it as a design decision and accept explainer framing.
  - **Explainer side**: 4-life must replace the invented half-life numbers with the actual spec values (Training -0.001/mo, Temperament +0.01/mo recovery, Talent no decay), and can add the "character slips faster than skill" intuition if spec remains silent on rationale.
- **Partial overlap with T1**: T1 item #5 flagged "half-life 365d on Talent" as BOTH with the same core evidence.

### 13. Landing — Acronym count builds fast (LCT, ATP, T3, MRH in first screen)
- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Why**: Progressive disclosure of jargon. Pure 4-life editorial.
- **Resolution**: 4-life — expand the "Shorthand:" pattern; consider 1-acronym-at-a-time progressive reveal on Landing.

---

## Appendix: 5 "Unanswered Questions" from visitor log

These appear below the friction table in a separate section. Handled as appendix, **not** as additional classifications.

| # | Question | Status |
|---|----------|--------|
| 1 | Is ATP tradeable? | **Subsumed by item #3** above (crypto comparison). Spec says ATP is "semifungible tokens" (`atp-adp-cycle.md:5`) and societies handle inter-society exchange (`§5.1`). The answer exists; 4-life doesn't surface it. EXPLAINER GAP. |
| 2 | Who runs the witness infrastructure? | **Subsumed by item #6** above. EXPLAINER GAP. |
| 3 | What does the actual product look like? | **Deferred.** Not a spec or explainer classification issue — this is a product-positioning question. Hardbound is the commercial expression; 4-life could link to hardbound-facing material once public-ready. Flag for operator: this question is recurring (visitor suspects so, based on log wording), worth a product-facing answer. |
| 4 | What stops a federation from capturing the rules? | **Partial SPEC coverage**: `web4-society-authority-law.md` §5.3 (Law Oracle) and §5.5 (Auditor) define governance, but visitor is right that "who evaluates alignment vs compliance" is acknowledged unproven in the explainer. Not yet a full SPEC GAP because spec has a design (Auditor appeals, rate limits, cool-down) — but the capture-resistance *argument* is thin. Flag for future memo consideration, not today. |
| 5 | What's the relationship between community/society/federation? | **Subsumed by item #2** above. BOTH. |

---

## Recommended Next Actions (for downstream sprints, not this session)

- **Web4 spec (11 items total counting T1)**: The two BOTH items flagged by both T1 and T2 (community/society/federation, T3 decay semantics) are strong signal — two independent visitors hit the same gaps. Candidate for a single spec-side sprint covering both. Also: T1's pure SPEC GAPs on ATP transfer-fee semantics, synthon lifecycle, and karma/raw-vs-effective trust.
- **4-life explainer (19 items total counting T1)**: Most concentrated in Trust Tensor bridge (V3 transition), MRH page ordering (defer formal name), ATP page (crypto comparison + budget terminology consistency), and Why Web4 page length. These cluster tightly — a single 4-life editorial pass could hit the majority.

---

## What this memo does NOT do

- Fix the spec or the explainer.
- Establish a daily memo-generation policy.
- Substitute for operator sprint-planning.
- Generate new friction items.

## Verification checklist (for peer review)

- [x] All 13 friction items appear in the memo by exact Location + Issue text from the visitor log
- [x] Every BOTH / SPEC GAP citation verified by Grep/Read of the referenced spec file
- [x] Line-number citations included for reviewer verification
- [x] 5 "Unanswered Questions" handled in appendix, not as additional classifications
- [x] No code, spec, or 4-life files modified
- [x] Filename follows log-date convention (not memo-authorship-date)
- [x] Scope explicitly framed as one-off, not standing policy
