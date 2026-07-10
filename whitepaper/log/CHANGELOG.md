# Web4 Whitepaper Changelog

This is an append-only changelog documenting all significant changes to the Web4 whitepaper.
Entries are added chronologically, never modified or deleted.

---

## 2026-07-09 (later) - Fresh Rewrite: Equation-Ordered Technical Introduction

Full rewrite per dp: "the paper has drifted too far and needs a fresh rewrite." The whitepaper is now a
**scoped technical introduction to the canonical Web4 standard**, organized around the canonical equation
`Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP`. ~3815 lines → ~516. Pre-rewrite sections preserved at
`archive/sections-2026-07-09-pre-rewrite/`.

### Structure (new)
Title → Why Web4 → The Canonical Equation → one section per equation element in order
(MCP, RDF, LCT, T3/V3, MRH, ATP/ADP) → Built on the Foundation (R6/R7, roles-as-entities,
SAL/AGY/ACP, dictionaries) → The Standard & Current Implementations (web4-standard, web4/hub, hestia,
with repo links) → Conclusion → compact Glossary → References.

### Cut as drift (not lost — archived)
Code examples; the coherence framework and its physics math (C×S×Φ×R, η, superconductivity);
trust-as-gravity; blockchain typology (Compost/Leaf/Stem/Root — no normative spec in core-spec/);
memory-as-temporal-sensor section (same reason); implications/vision essays; appendices;
duplicated exec-summary/introduction catalogs; manifesto flourishes.

### Also changed
- Every mechanism section now links its **normative spec** in `web4-standard/core-spec/`.
- Web nav rebuilt **flat** (one entry per section, ids verified 1:1 against real sections) — fixes the
  broken sub-anchor navigation (e.g. "R6 Action Framework" landing inside the dictionaries text).
- `make-md.sh` / `make-web.sh` / `make-pdf.sh` re-pointed at the new section list; PDF title page and
  web header/title updated ("WEB4: A Technical Introduction", July 9, 2026).
- Glossary rewritten compact and scoped to the paper's terms; the standard's `GLOSSARY.md` linked as
  the authoritative full vocabulary.
- Scope rules added to `PUBLISHER_CONTEXT.md` so the daily Publisher pass holds the new boundary.

## 2026-07-09 - Posture Revision: Why-First, Foundation-First

A structural (not factual) revision to fix the public-face reading arc. Review + rationale:
`WHITEPAPER_STRUCTURE_REVIEW_2026-07-09.md`; standing guidance persisted to
`docs/best-practices/public-docs-posture.md` and `PUBLISHER_CONTEXT.md` (Posture Invariants). No truth
claim, status marker, or findings-vs-framings distinction was removed — material was reordered and re-leveled.

### Changed
- **Introduction** — no longer opens on a shipped-status block. Rewritten as a why-first orientation (the
  concrete agent-authorization stakes) + a "how to read this" map with the fractal dependency order;
  removed the duplicated "Core Mechanisms" catalog (it lived in the Exec Summary and Part 1 §1.4 already).
- **Executive Summary** — removed the ~200-word version/status block from the lead; now opens on *why*. The
  ARC-AGI-3 proof point relocated into the Implementation Status section. "The Core Innovation" reordered
  foundation-first (presence → **T3/V3 trust, previously absent** → value-feedback), with ATP reframed as a
  feedback layer, not a pillar.
- **Part 1 §1.4** — component map reordered to dependency order: LCT → T3/V3 → MRH → R6/R7 → **ATP last**,
  ATP explicitly labeled the value-feedback layer and "not in the public packages." §1.2 corrected: ATP/ADP
  is Hardbound-only, not "partially shipped" in `web4-core`.
- **Part 3** — opening reframed: ATP is the value-feedback cycle that rides on the presence+trust foundation,
  not "the beating heart of Web4." §3.1 heading "The Lifeblood of Value" → "The Value-Feedback Cycle."
- **README** — corrected the stale flat `sections/*.md` layout description to the real nested
  `sections/<n>/index.md` fractal structure. Title page date → 2026-07-09.

### Published
- Site rebuilt + published to GitHub Pages (`docs/whitepaper-web/` → https://dp-web4.github.io/web4/whitepaper-web/):
  HTML + monolith markdown regenerated from the revised sources (dp: "the best way to preview is to publish").
- **PDF** is rebuilt by the `build_whitepaper.yml` CI (pandoc + texlive-xetex) on push to `whitepaper/**` — the
  local dev box lacks a LaTeX toolchain, so the PDF is a CI-only artifact. Note: the CI deploy step's bare
  `git push` fails non-fast-forward whenever a concurrent commit lands mid-run; a rebase-before-push fix is
  proposed but must be applied by a maintainer with `workflow` token scope.

## 2025-08-18 - Manifesto Energy Restoration

### Added
- **Executive Summary** - New opening section with manifesto tone before glossary
  - Hook readers with vision before technical details
  - What/Why/How in inspiring, accessible language
  - Emphasis on trust as fundamental force

### Modified  
- **Introduction** - Added Synchronism reference and fractal structure explanation
  - Links to https://dpcars.net/synchronism as philosophical framework
  - Explains document's fractal organization (conceptual → technical)
  - Emphasizes LCTs as "reification of presence"

- **Part 2: Foundational Concepts** - Revised with manifesto energy
  - LCTs reframed as "entity's footprint in Web4"
  - "Every entity is born with and dies with its LCT"
  - Emphasis on presence, not just identity
  - More visionary language while maintaining precision

- **Part 5: Memory** - Split into conceptual vs implementation
  - Created new conceptual version emphasizing temporal sensing
  - Memory as alive, not storage
  - Philosophical implications of memory as sensor
  - Technical details moved to implementation sections

### Restructured
- Document now follows fractal pattern:
  - Visionary/conceptual main body
  - Links to technical expansions
  - Implementation details in appendices
  - Multiple entry points for different audiences

### Style Updates
- Restored manifesto voice throughout
- More declarative, inspirational language
- Synchronism principles as connective tissue
- Technical precision preserved but wrapped in vision

### Contributors
- Dennis Palatov (direction, review)
- GPT (manifesto restoration suggestions)
- Claude (implementation, synthesis)

---

## 2025-08-18 - Major Evolution: Memory as Temporal Sensor

### Added
- **Part 5: Memory as Temporal Sensor** - New conceptual framework treating memory as active temporal perception
  - Three-sensor reality field (Physical/Memory/Cognitive)
  - SNARC signals for affect-gated retention
  - Dual memory architecture (Entity vs Sidecar)
  
- **Part 6: Blockchain Typology** - Four-tier temporal hierarchy
  - Compost chains (ephemeral, ms-sec)
  - Leaf chains (episodic, sec-min)
  - Stem chains (consolidated, min-hr)
  - Root chains (crystallized, permanent)
  - Fractal lightchain with witness-acknowledgment protocol

- **Part 7: Implementation Examples** - Practical demonstrations
  - Multi-agent collaborative learning
  - Autonomous vehicle fleet learning
  - SAGE coherence engine integration
  - Role-based task allocation
  - Cross-chain value transfer

### Modified
- **Glossary** - Extended with new terms:
  - Lightchain, Temporal Sensor, Dictionary Entity
  - Memory Sensor, Sidecar Memory, SNARC Signals
  - Blockchain Typology terms, Witness Mark/Acknowledgment

- **Conclusion** - Updated to reflect new concepts
  - Memory as living history
  - Trust through witnessing
  - Intelligence as emergent property

- **References** - Added citations for:
  - Sapient Inc. HRM
  - Aragon's Transformer-Sidecar
  - Memory and cognition literature

- **Appendices** - New technical specifications:
  - Blockchain typology decision tree
  - Memory sensor API
  - Witness-acknowledgment protocol
  - SNARC signal specifications

### Restructured
- Split monolithic document into 14 modular sections
- Created build system with three scripts:
  - make-md.sh (markdown generation)
  - make-pdf.sh (PDF generation)
  - make-web.sh (web version)
- Moved reference materials to dedicated directory

### Contributors
- Dennis Palatov (conceptual framework, review)
- Claude (memory synthesis, implementation)
- GPT (review, suggestions)

---

## 2025-05-13 - Original Whitepaper

### Created
- Initial Web4 framework document
- Core concepts: LCTs, ATP/ADP, T3/V3 tensors, MRH
- Foundational architecture for trust-native internet
- Patents referenced: US11477027, US12278913

### Contributors
- Dennis Palatov, GPT4o, Deepseek, Grok, Claude, Gemini, Manus

---

*Note: This changelog is append-only. New entries should be added at the top of the appropriate date section, never modifying existing entries.*

---

## 2025-08-18 (v1.3.0) - Manifesto Flourishes

### Added
- Created enhanced Part 3 (05-part3-value-trust-mechanics-enhanced.md) with manifesto energy and biological metaphors
- Created enhanced Conclusion (11-conclusion-enhanced.md) with direct call to action addressing builders, thinkers, dreamers, and skeptics
- Added "The Living Economy" synthesis section to Part 3
- Integrated manifesto quotes throughout technical sections

### Changed
- Reorganized glossary into Core Terms, Extension Terms, and Research Extensions for better navigation
- Added manifesto quotes to each glossary term
- Updated make-md.sh to use enhanced versions when available
- Strengthened call to action with specific invitations to different audiences

### Contributors
- Dennis Palatov, Claude (Opus 4.1)