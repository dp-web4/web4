# Whitepaper Structure Review — 2026-07-09

**Reviewer:** HUB-Claude · **Requested by:** dp · **Scope:** the reading arc, not the facts
**Lens (dp's three principles):**
1. **Lead with theory: why → what → how. Implementation status is a footnote.**
2. **Foundations build fractally: LCT → its components → *then* ATP as a value-feedback mechanism (NOT a foundation — it isn't even implemented in the public packages).**
3. **The whitepaper is our public face. Start with why the reader would care, then build the case for the solution.**

This is a *posture* review — a diagnosis of the order in which a first-time reader meets the ideas. The
facts are largely fine (the Publisher's daily discipline keeps findings-vs-framings honest and terminology
clean). The problem is **sequence**: the document is ordered roughly how→what, with *why* buried and
*status* front-loaded. A naive visitor's first ~500 words are release notes.

---

## The through-line

**The project already organizes its docs by `why/ what/ how/`** (the `docs/` tree has exactly those three
directories). The whitepaper — the most public artifact — is the one place that *inverts* it: it opens with
*how much is shipped* before it has said *why anyone should care*. Every finding below is a instance of that
inversion.

---

## Finding 1 — the naive reader lands on a PR merge report *(dp's point 1 & 3)*

Reading order today (`make-md.sh`): **Title → Executive Summary → Introduction → Glossary → Part 1…**

- **Executive Summary, sentence 1 after the H1** is a ~200-word *Status calibration* block: "`web4-core`
  0.2.0, `web4-trust-core` 0.2.0 … `web4-sdk` 0.27.0 … 17-day publish-vs-main gap … 166 passing tests …
  0% → 94.85% on ARC-AGI-3." Version numbers and a publish-gap changelog are the **first prose a reader
  sees.**
- **Introduction** then opens with *its own* status block ("shipped and installable … 166 passing tests …
  AttestationEnvelope"), before "This document presents WEB4…".

The "why" content **exists and is good** — Exec Summary §"Why Now?" and Part 1 §1.2 "The Problem Web4 Is
Trying to Address" are both strong. But they sit at reading-position ~4 and ~5, *after* the reader has waded
through two status dumps and two component catalogs. The stakes are buried under the receipts.

**Fix:** demote every status block to a clearly-labeled *Implementation Status* section (Exec Summary
already has one lower down — the top block is a duplicate) or an appendix. Lead each entry surface with the
*why*.

## Finding 2 — ATP is mis-leveled as a foundation in **four** places *(dp's point 2)*

ATP/ADP is a **value-feedback mechanism** built *on top of* the presence+trust foundation, and it is the
**least-implemented** core component (exec-summary itself files it under "Emerging — operational in Hardbound
CLI," with "public reference implementation: pending"). Yet it is repeatedly given founding-pillar billing:

| # | Location | How it's mis-leveled |
|---|---|---|
| 1 | **Introduction → "Core Mechanisms"** | ATP is co-equal bullet #3, between the T3/V3 and MRH primitives |
| 2 | **Exec Summary → "The Core Innovation"** | The three pillars are **LCT → ATP → Memory**. T3/V3 — shipped, and the actual trust representation — is **absent from the trio**, while ATP (unshipped) is pillar #2 |
| 3 | **Part 1 §1.4 "Overview of Key Components"** | Ordered LCT (#1) → **ATP (#2)** → T3/V3 (#3) → MRH (#4) → R6/R7 (#5). ATP is placed *ahead of the trust tensor it feeds* |
| 4 | **Part 3 opening** | "§3.1 ATP: **The Lifeblood of Value**" / "the **beating heart of Web4**" — foundational language for the value layer |

**The fractal order dp wants:** **LCT** (presence) → **its components** (T3/V3 trust, MRH context, R6/R7
grammar, roles-as-entities) → **then ATP/ADP** introduced as the *value-feedback loop that rides on that
foundation*, explicitly flagged as the least-mature piece. ATP earns a prominent home in Part 3 (value
mechanics) — but framed as *feedback built on the foundation*, not as the foundation or "the beating heart."

Note this is **re-leveling, not deletion**: ATP/ADP is a genuine and distinctive idea (thermodynamic
accountability, the "anti-Ponzi" framing). It keeps its full treatment — it just stops being introduced
before the trust layer it depends on.

## Finding 3 — the case for *why* is made late and defensively *(dp's point 3)*

When the "why" does arrive it's framed inward (hedges, status caveats, "positioning not science"
disclaimers) rather than as a confident reader-facing hook. Part 1 §1.2 has the strongest why in the
document — the two concrete agent-authorization questions — and it is excellent. It should be *near the
front*, powering the opening, not at position 5 behind the catalogs.

## Finding 4 (mine) — the Introduction and Executive Summary substantially duplicate each other

Both carry: a status block, a component catalog ("Core Mechanisms" vs "The Core Innovation"), a Synchronism-
grounding paragraph, and an "Invitation." A reader hits the same material twice before Part 1. Recommend the
**Executive Summary owns the persuasive why→what arc** and the **Introduction becomes a short orientation**
(what this document is, how it's structured, how to read it fractally) — not a second exec summary.

## Finding 5 (mine) — preserve the discipline while reordering

The Publisher's *findings-vs-framings* rule and per-section status markers are a real asset and the reason
the doc is trusted. The fix is **reordering and re-leveling, not removing** the honesty. Status stays — it
moves from *the lead* to *a footnote/section*. Framings (trust-as-gravity, memory-as-temporal-sensor,
biological ATP) stay as framings. Nothing here loosens a single truth claim.

## Minor drift found
- `whitepaper/README.md` describes a **stale flat `sections/00-metadata.md` layout**; the real structure is
  the nested `sections/<NN-name>/index.md` fractal layout (`make-md.sh` already migrated). Update the README.
- Title page "Updated: April 29, 2026" is stale relative to the 2026-05-15 content.

---

## Target arc (proposed)

```
Title
Executive Summary   → WHY (the stakes, Part-1 §1.2's concrete problem promoted here)
                       → WHAT (the shift: presence→trust→value, foundation-first)
                       → HOW (one paragraph: "the body builds it; here's how to read it")
                       → Implementation Status  (the honest table — demoted to here, not the lead)
Introduction        → short orientation + how-to-read (not a second exec summary)
Glossary
Part 1  Defining Web4       → why/what (problem-first; §1.4 reordered LCT→T3/V3→MRH→R6→ATP)
Part 2  Foundational Concepts → LCT → entities → roles → R6 → MRH  (already ~right; keep)
Part 3  Value/Trust Mechanics → ATP reframed as value-FEEDBACK on the foundation
Parts 4–8 … Conclusion … Appendices  (status/proof lives here)
```

**Fractal foundations order (the spine):** presence (LCT) → capability & trust (T3/V3) → context (MRH) →
grammar of action (R6/R7) → *value feedback* (ATP/ADP) → memory as temporal sensing. Each layer assumes only
the ones before it.

## Implementation plan (this pass)
1. **Introduction** → rewrite to lead with why, demote status to a one-line current-state pointer.
2. **Executive Summary** → move the top status block into the existing *Implementation Status* section;
   re-lead with why; fix "Core Innovation" to foundation-first (LCT → T3/V3 → MRH), ATP as feedback.
3. **Part 1 §1.4** → reorder components LCT → T3/V3 → MRH → R6/R7 → ATP; honest ATP status.
4. **Part 3 opening** → reframe ATP as value-feedback-on-the-foundation, drop "beating heart/foundation" leveling.
5. **README + title date** → fix the stale layout description and date.
6. **Hold the site rebuild/deploy** (`make-web.sh` → metalinxx.io) for dp — that's the outward-facing step.

Lessons persisted to `docs/best-practices/public-docs-posture.md` and folded into `PUBLISHER_CONTEXT.md` so
future daily passes hold the posture (why-first; status-is-a-footnote; ATP-is-not-a-foundation).
