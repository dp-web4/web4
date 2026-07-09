# Public Docs Posture

**Status:** Standing guidance · **Origin:** 2026-07-09 whitepaper structure review (dp)
**Applies to:** the whitepaper, README, and any outward-facing document that a first-time reader may land on.

Our public docs are read by people who do *not* already know Web4. The failure mode we keep hitting is
writing them for ourselves — leading with what we shipped instead of why a stranger should care. These are
the durable lessons. They are posture, not facts; they govern *order and framing*, never truth claims.

## 1. Lead with theory: why → what → how. Status is a footnote.
A first-time reader must meet, in this order: **why this matters** (the stakes / the concrete problem) →
**what the idea is** (the shift) → **how it works** (the mechanisms) → and only then, *as a footnote or a
clearly-labeled section*, **what is actually built today.**

- **Anti-pattern:** opening a public doc with a version/status/test-count block ("v0.2.0 published … 166
  tests passing … 17-day publish gap"). That reads like a PR merge report. It answers a question the reader
  hasn't asked yet.
- The project's own `docs/` tree is organized `why/ what/ how/`. Public docs should follow the same spine.
- Status *must still be there and must stay honest* (findings vs framings, per-component maturity). It just
  moves from **the lead** to **a footnote / an Implementation-Status section / an appendix.**

## 2. Build foundations fractally — and don't promote a mechanism to a foundation.
Introduce concepts in dependency order, each layer assuming only the ones before it:

> **presence (LCT)** → **capability & trust (T3/V3)** → **context (MRH)** → **grammar of action (R6/R7)** →
> **value feedback (ATP/ADP)** → **memory as temporal sensing**

- **ATP/ADP is a value-feedback mechanism, not a foundation.** It rides on the presence+trust layer, and it
  is (as of 2026-07) the *least-implemented* core component — operational only in the Hardbound CLI, no
  public reference implementation. Do **not** give it founding-pillar billing ("the beating heart," "the
  lifeblood," listing it ahead of T3/V3). It earns a full, prominent treatment in the *value mechanics*
  section — framed as feedback built on the foundation.
- General rule: **a component's prominence in the narrative should track its place in the dependency graph
  and, for a public doc, be honest about its maturity.** Don't front-load the least-built, most-metaphorical
  piece.

## 3. The doc is a public face — make the case, don't just catalog.
Start with why the reader would care, then build the case for the solution. A catalog of primitives is not a
case. The strongest "why" we have is concrete (e.g. the two agent-authorization questions in whitepaper
Part 1 §1.2 — *how do I know an agent will act appropriately before it acts, and prove what it did after?*).
Promote the concrete stakes to the front; let the primitives answer them.

## 4. Re-level and reorder; never dilute honesty.
When fixing posture, **move and reframe** material — don't delete truth. Keep every status marker, every
findings-vs-framings distinction, every maturity caveat. The goal is a reader who is *first* persuaded of the
why and *then* correctly informed of the what's-built. Confidence and honesty are not in tension; front-load
the confidence (the vision), keep the honesty (the status) exactly as rigorous, just later.

---
*If a naive first-time reader's first two paragraphs are version numbers and test counts, the posture is
wrong regardless of how correct the numbers are.*
