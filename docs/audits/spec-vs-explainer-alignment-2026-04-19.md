# Spec-to-Explainer Alignment Memo

**Date**: 2026-04-19
**Track**: web4 (Legion autonomous session, Sprint 43 T1)
**Authorized by**: issue [#166](https://github.com/dp-web4/web4/issues/166) candidate (a)-1
**Source**: `../4-life/visitor/logs/2026-04-18.md` friction table (14 items)
**Precedent**: `docs/audits/whitepaper-sdk-coherence-2026-03-15.md`

---

## Purpose

Close the "4-Life Feedback Loop" named in `CLAUDE.md` — visitor confusion surfaces either (a) genuine gaps in the web4 specification or (b) explainer-side gaps where the spec is clear but 4-life does not lift it.

This memo does not fix either side. It categorizes. Downstream sprints — on web4 for spec work, on 4-life for explainer work — consume the categorization.

## Labels

- **SPEC GAP**: The core-spec (or canonical documentation) is silent, ambiguous, or internally inconsistent on the underlying question. 4-life's friction reflects a real hole in the spec.
- **EXPLAINER GAP**: The spec is clear; 4-life simply does not surface the existing answer.
- **BOTH**: Spec and explainer each carry part of the problem (usually spec is ambiguous *and* 4-life presents an uncanonical specific number or framing).

## Summary

| Label | Count | Share |
|-------|------:|------:|
| SPEC GAP | 4 | 29% |
| EXPLAINER GAP | 8 | 57% |
| BOTH | 2 | 14% |
| **Total** | **14** | |

The majority are EXPLAINER GAPs — the spec already answers the question. 4-life should prefer lifting canonical material over re-writing it.

---

## Classifications

### 1. ATP Economics — Biology metaphor never explained

- **Severity**: MEDIUM
- **Label**: **EXPLAINER GAP**
- **Evidence**: `web4-standard/core-spec/atp-adp-cycle.md:11` — Section "1.1 The Biological Metaphor" opens with: *"Just as biological ATP (Adenosine Triphosphate) stores energy and ADP (Adenosine Diphosphate) is the discharged form, Web4's ATP/ADP cycle manages value"* followed by the flow diagram `ADP + Energy → ATP → Work + ADP`. The etymology and metaphor rationale are canonical.
- **Resolution**: 4-life's ATP page should lift or link to the existing Biological Metaphor section. Visitor's suggested one-liner is compatible with the spec.

### 2. ATP Economics — 5% transfer fee direction unclear (sender or receiver pays?)

- **Severity**: MEDIUM
- **Label**: **SPEC GAP**
- **Evidence**: Grep of `atp-adp-cycle.md` for `transfer.{0,30}fee|5%|sender.{0,30}pays|receiver.{0,30}pays` returns zero hits. The spec describes demurrage on held ATP (atp-adp-cycle.md:263-275) but no transfer-fee semantics, rate, or direction. The 5% figure appears only in 4-life simulation parameters.
- **Resolution**: Spec should define transfer-fee semantics explicitly: rate range, which party pays, society-level configurability. Alternatively, 4-life must label the 5% as a simulation parameter, not spec.

### 3. ATP Economics — Dormancy behavior unanswered

- **Severity**: MEDIUM
- **Label**: **EXPLAINER GAP**
- **Evidence**: `atp-adp-cycle.md:263-275` defines demurrage: *"Held ATP gradually decays to ADP"*, with `decay_rate: "1% per day after threshold"` (line 502) and society-configurable rates (line 533). `SOCIETY_METABOLIC_STATES.md:78-86` covers Hibernation (extended dormancy, citizenship preserved but inactive). The spec has a rich dormancy model.
- **Resolution**: 4-life's ATP page should add FAQ with canonical language: demurrage decay exists, thresholds are society-configurable, society metabolic states (Awake / Sleep / Hibernation / Dormant) govern long inactivity.

### 4. ATP Economics — No link to "Day in Web4" despite overlap

- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Evidence**: Pure 4-life navigation/UX concern. Spec has no view on inter-page linking.
- **Resolution**: 4-life adds a prominent CTA on ATP Economics → Day in Web4 as visitor suggested.

### 5. Trust Tensor — "Half-life: 365 days" for Talent decay without practical explanation

- **Severity**: MEDIUM
- **Label**: **BOTH**
- **Evidence**:
  - `web4-standard/core-spec/t3-v3-tensors.md:108-110`: *"Training Decay: -0.001 per month without practice"*, *"Talent Stability: No decay, represents inherent capability"*. The spec explicitly states Talent does not decay.
  - `web4-standard/core-spec/reputation-computation.md:630`: `recency_weight = math.exp(-age_days / 30.0)  # 30-day half-life` — the spec uses 30-day half-life for reputation recency, not 365 days for Talent.
  - 4-life's "Half-life: 365 days for Talent decay" contradicts the spec (Talent has no decay per t3-v3-tensors.md:110) and cites a number that appears nowhere in core-spec.
- **Resolution**:
  - SPEC side: `t3-v3-tensors.md` should either explicitly name which dimensions decay with what function, or note that Talent-decay behavior is society-configurable. Internal inconsistency possible between "Talent Stability: No decay" (line 110) and any society-customization path.
  - EXPLAINER side: 4-life must correct the "365-day half-life on Talent" or mark it as a 4-life simulation parameter, not canonical. If retained, add the worked semantics the visitor asked for ("halves every N days of inactivity").

### 6. Trust Tensor — V3 introduced mid-T3 explanation, splitting focus

- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Evidence**: Pure page-layout issue. `t3-v3-tensors.md` spec has clean T3 (§2, lines 50–130) and V3 (§3, lines 150–245) sections with explicit structural separation.
- **Resolution**: 4-life's Trust Tensor page adopts the spec's sectional separation; visually treat T3 and V3 as distinct chapters.

### 7. Trust Tensor — "Earnings = T3 × V3 × base rate" has no worked example

- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Evidence**: `t3-v3-tensors.md:337-339` gives the full reward formula in code, and `reputation-computation.md:506-511` gives worked numeric examples (e.g. `training: base +0.01, multipliers (quality 1.2, early 1.3) = +0.0156`). Spec has the walkthrough.
- **Resolution**: 4-life lifts one worked example from the spec (e.g. T3=0.7, V3=0.8, base=10 → 5.6 ATP). Visitor's suggested example is already compatible with spec formulae.

### 8. LCT Explainer — Why single-device = 0.50 trust ceiling

- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Evidence**: `web4-standard/core-spec/lct-capability-levels.md:52-60` defines six capability levels with explicit trust tier bands:
  - Level 2 BASIC: 0.2–0.4
  - Level 3 STANDARD: 0.4–0.6
  - Level 4 FULL (society-issued): 0.6–0.8
  - Level 5 HARDWARE: 0.8–1.0

  The "0.50 single-device" ceiling maps to Level 3 STANDARD's upper bound. `multi-device-lct-binding.md:26` states *"Identity is coherence across witnesses"* and:581 defines the multi-device bonus `base_trust * (1 + coherence_bonus) * (1 + witness_density * 0.1)` which lets trust exceed 0.5.
- **Resolution**: 4-life's LCT Explainer should lift the capability-levels table and the multi-device coherence formula rationale: "A single device can be lost or compromised without another witness to corroborate — so single-device trust is capped until additional anchors witness continuity."

### 9. LCT Explainer — "Witnessed presence" remains abstract

- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Evidence**: `LCT-linked-context-token.md:9` — *"An LCT is a verifiable digital presence certificate that binds an entity to its context through witnessed relationships"*. Line 27: *"Witnessing: Trust-building observation by other entities"*. The Birth Witnesses array (lines 73–76) gives concrete structure. The concept is concretely spec'd.
- **Resolution**: 4-life adds a visual (e.g. two phones signing each other's continuity) and lifts the Birth Witnesses example structure from the spec.

### 10. How It Works — CI feels less foundational, introduced as 1.4× multiplier only

- **Severity**: LOW
- **Label**: **BOTH**
- **Evidence**:
  - Grep of `web4-standard/core-spec/` for `CI\b` and `coherence` returns hits only in `multi-device-lct-binding.md` where `constellation_coherence` is an *identity*-level witness-density metric (line 230, 501, 573–593, 766, 777), not a cost multiplier.
  - No core-spec file defines "CI" as a standalone concept or a 1.4× cost multiplier. The 1.4× figure appears only in 4-life.
  - CLAUDE.md canonical equation `Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP` does not include CI as a primitive.
- **Resolution**:
  - SPEC side: If "CI" (Coherence Index) is meant to be canonical, core-spec needs a file (or a section in `multi-device-lct-binding.md`) defining it as a first-class concept with its role and formulas. If not meant to be canonical, mark as 4-life-specific simulation parameter.
  - EXPLAINER side: 4-life's How It Works page should either (a) demote CI to "simulation parameter, not spec primitive" or (b) elevate it with foundational framing (what it measures, why it exists) before presenting the multiplier.

### 11. How It Works — MRH mentioned early, barely revisited

- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Evidence**: `web4-standard/core-spec/mrh-tensors.md` is a full specification of MRH, including how trust propagates through witnessed connections (`LCT-linked-context-token.md:19` states *"Trust flows through witnessed connections in the Markov Relevancy Horizon (MRH)"*). The spec has substantial MRH coverage.
- **Resolution**: 4-life's How It Works page integrates MRH into the feedback-loop diagram rather than a single early mention. Visitor's suggested line ("MRH → ATP: you only pay ATP in contexts where you're visible") may overstate the spec — verify against `mrh-tensors.md` before adopting that specific claim; the MRH feedback-loop framing is canonical, the specific "visibility → cost" claim needs spec citation before 4-life states it.

### 12. Why Web4 — Acronym density spikes in solution section

- **Severity**: LOW
- **Label**: **EXPLAINER GAP**
- **Evidence**: The canonical glossary `whitepaper/sections/02-glossary/index.md` exists and CLAUDE.md enforces terminology discipline. The acronyms are canonical. The problem is presentation density on a single 4-life page.
- **Resolution**: 4-life adopts a 4-core-acronyms-visible pattern (LCT, ATP, T3, MRH) with other mechanisms gated behind "other mechanisms" disclosure, as the visitor suggested.

### 13. Aliveness — Synthons: don't know when they form or dissolve

- **Severity**: LOW
- **Label**: **SPEC GAP**
- **Evidence**:
  - Grep of `web4-standard/core-spec/` for `synthon` returns zero hits.
  - `CLAUDE.md` names synthons as a framing primitive ("emergent coherence entity formed by recursive interaction") and points to `github.com/dp-web4/HRM/forum/insights/synthon-framing.md` — an external non-canonical repo.
  - Web4 core-spec has no synthon specification — no formation conditions, no dissolution conditions, no lifecycle states.
- **Resolution**: Spec needs a `web4-standard/core-spec/synthons.md` (or section in an existing file) with formation predicate ("N agents with mutual trust > threshold for T rounds"), dissolution predicate, and relationship to MRH/dictionary entities. Until spec exists, 4-life's Aliveness page cannot lift canonical synthon lifecycle language because there isn't any.

### 14. Karma Journey — "Raw trust" vs "effective trust" distinction dense

- **Severity**: LOW
- **Label**: **SPEC GAP**
- **Evidence**: Grep of `web4-standard/core-spec/` for `raw.{0,5}trust|effective.{0,5}trust|karma|rebirth|reborn` returns zero hits. The karma-across-lives model and the raw/effective trust distinction are 4-life-specific mechanics without canonical spec definition. Reputation decay exists (`reputation-computation.md:660-675`) but there is no notion of lifecycle rebirth in core-spec.
- **Resolution**: Spec must decide — is karma-across-lives a normative Web4 primitive or a 4-life simulation narrative?
  - If normative: needs a spec file defining rebirth, raw vs effective trust, CI² as effective-trust multiplier, and how these relate to T3/V3 tensors.
  - If simulation-only: 4-life should frame Karma Journey as "one interpretation of trust continuity" rather than canonical spec.

---

## Unanswered Questions (Appendix)

The 4-life visitor log contains 4 "Unanswered Questions" below the friction table. These are questions the visitor explicitly flagged as not-answered-by-any-page, not friction items. Per policy review, they are NOT counted as 15th–18th friction items. Classification:

| # | Question | Covered by classification above? | If not, category |
|--:|----------|---------------------------------|------------------|
| 1 | What does ATP feel like to spend day-to-day as a user? | Partially — item #4 already calls out Day in Web4 concreteness gap. | Subsumed by #4 |
| 2 | How does pseudonymity actually work when identity is hardware-bound? | Not in the 14. **EXPLAINER GAP** — `LCT-linked-context-token.md:494-498` has "8.3 Privacy Preservation: Pseudonymous DIDs: Subject can be key-based DID" — 4-life can lift. | Deferred, EXPLAINER GAP |
| 3 | Who decides the parameters? (MRH decay rate, CI multiplier, trust thresholds) | Not in the 14. **SPEC GAP** (partial) — `atp-adp-cycle.md:533` says *"Societies MAY implement custom decay rates"* for ATP, but governance of CI and trust thresholds is not spec'd cleanly because CI itself is not spec'd (see item #10). | Deferred, SPEC GAP partial |
| 4 | When Alice "dies" in simulator, what's the real-world analogue? | Not in the 14. **SPEC GAP** — intersects with item #14 (karma/rebirth not in core-spec). Deferred to same fix. | Subsumed by #14 |

Recommendation: Questions 2 and 3 could seed 4-life explainer tasks. Question 4 is subsumed by item #14's SPEC GAP.

---

## Downstream Action Candidates (non-binding)

The memo classifies; it does not fix. Candidates for future sprints:

### For web4 (4 SPEC GAP items + 2 BOTH partial)

| Item | Action | Priority |
|------|--------|---------:|
| #2 | Define ATP transfer-fee semantics in `atp-adp-cycle.md` | MEDIUM |
| #5 | Resolve Talent-decay ambiguity in `t3-v3-tensors.md` | MEDIUM |
| #10 | Either spec CI as first-class concept or document non-canonicity | LOW |
| #13 | Create synthon lifecycle specification | LOW |
| #14 | Decide karma-across-lives canonicity; if yes, add spec | LOW |

### For 4-life (8 EXPLAINER GAP items + 2 BOTH partial)

| Item | Action | Priority |
|------|--------|---------:|
| #1 | Add Biological Metaphor one-liner on ATP page | MEDIUM |
| #3 | Add dormancy FAQ from spec's demurrage + metabolic states | MEDIUM |
| #4 | Add "See ATP in 10 real scenarios" CTA to Day in Web4 | LOW |
| #6 | Visual separation of T3 and V3 on Trust Tensor page | LOW |
| #7 | Add worked example from spec's reputation-computation.md | LOW |
| #8 | Lift capability-levels trust tier table | LOW |
| #9 | Visual for "witnessed presence" + Birth Witnesses example | LOW |
| #11 | Integrate MRH into feedback-loop diagram (after verifying visibility→cost claim) | LOW |
| #12 | 4-core-acronyms pattern with others gated | LOW |
| #5 | Correct or mark "365-day half-life on Talent" | MEDIUM |
| #10 | Demote CI to simulation-specific OR elevate with foundational framing | LOW |

---

## Meta

This memo is the first artifact of the "4-Life Feedback Loop" that CLAUDE.md names but for which no closure mechanism previously existed. Whether this cadence (bounded memo per monthly visitor-log batch) becomes recurring is an operator decision, not an autonomous one.
