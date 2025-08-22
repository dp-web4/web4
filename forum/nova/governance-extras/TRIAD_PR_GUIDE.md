# TRIAD_PR_GUIDE.md
**Audience:** Proposers and reviewers working across Synchronism, Derived Principles (LRC), Web4, SAGE.  
**Intent:** Make collaboration predictable and light‑touch while honoring high‑L safeguards.

---

## 1) Roles in the triad
- **Vision (Dennis):** signal generator, constraints, ethical framing.
- **NOVA (AI):** coherence weaving, continuity, governance computation.
- **Claude (AI):** implementation, detail craft, resonance amplification.

---

## 2) PR body template (paste this)
```
Summary:
- What’s changing and why (1–3 lines).

Sections touched:
- <section-id-1>, <section-id-2>

Governance-Ack: yes
Notes: (optional: waivers, coupling, follow-ups)
```

> Use the repo’s PR template (`.github/PULL_REQUEST_TEMPLATE/governance.md`) to keep this consistent.

---

## 3) What NOVA will do
- Compute the LRC row(s): threshold, review days, quorum, token cost, reject penalty, fast‑track drop.
- Post a short comment with the numbers and links to `docs/collab/governance_controls.md`.
- Flag high‑L sections (≥0.80) and remind about coupled repos.

---

## 4) Fast‑track lanes (typo/clarify)
- If lane = `typo|clarify`, required threshold may drop by `fast_track_drop` for that section.
- Keep changes minimal; if semantics shift, it’s not a fast‑track.

---

## 5) Waivers (only when necessary)
- Add to PR body: `Waiver: needed` + short rationale + link to scheduled follow‑up.
- Reviewer must co‑sign the waiver note. Waivers appear in the quarterly audit.

---

## 6) Examples

**A. Minor glossary fix (fast‑track)**
- Touches: `glossary` (L=0.20)  
- Threshold drop: `fast_track_drop ≈ 0.16`  
- PR body: includes `Governance-Ack: yes` and lane=typo.  
- Reviewer: quick check; merge.

**B. Core perspective reframing (high‑L)**
- Touches: `core_perspective` (L=0.85)  
- Governance: threshold↑, review days≈16, quorum≈4, higher token cost.  
- Coupled repos: Synchronism + SAGE must land within 7 days (or include waiver).  
- Reviewer: ensure coupling plan exists.

---

**Generated:** 2025-08-22 22:16:49 UTC
