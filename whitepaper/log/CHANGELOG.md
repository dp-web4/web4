# Web4 Whitepaper Changelog

This is an append-only changelog documenting all significant changes to the Web4 whitepaper.
Entries are added chronologically, never modified or deleted.

---

## 2026-07-28 - Correction: §11's two remaining living-example declarations, audited against primary sources

**Content change.** The 2026-07-27 pass closed with a watch item: *"§11's remaining living-example claims
are unverified declarations — audit them against the implementations a few per pass, hub next."* This pass
executed that audit. Two of the claims fail; the rest hold.

### Claim 1 — the hub is "operated in production by the project itself"

§11 pointed a reader at the public [`web4/hub`](https://github.com/dp-web4/web4/tree/main/hub) tree and
attributed production operation to it. `hub/README.md:13-15` assigns that status to a **different artifact**:

> *"**Status — reference proof-of-concept.** This crate is the open reference POC. Production and advanced
> development continue in a separate private repository; features may land here later behind stable plugin
> interfaces."*

Corroborated in the same file rather than inferred from one line: `hub --version` → `hub 0.1.0-alpha.0`
(README:159); "**MVP complete (Sprints 0-6)** … Pilot-ready" (README:32); "First deployment target: a pilot
community chapter" (README:17) — i.e. the first chapter deployment is still ahead. The one occurrence of
the word "production" elsewhere in the README is `HUB_PROFILE=production`, a **configuration profile name**
(README:47), not an operational status.

The claim also contradicted §11's own closing paragraph, which calls all three implementations
"research-stage … not finished products". Two sentences of one section disagreed about the same artifact.

**What was true, and kept.** The project *does* run a hub daily for its own multi-agent coordination —
verified on a live host, not from prose: `private-context/hub-mesh/hub-watch.sh` running as pid 153660, and
`~/.web4/` carrying `channel/`, `ledger.db`, and `governance/`. That is stronger evidence than the label it
replaces, so the sentence now states the daily self-operation and the README's own POC scoping, and drops
"production".

### Claim 2 — the package matrix

§11 read: *"`web4-core` and `web4-trust-core` ship … as installable packages (Rust crates, Python wheels, and
WASM browser bindings on crates.io, PyPI, and npm)"* — grammatically a 2×3 matrix. Queried this pass:

| package | crates.io | PyPI | npm |
|---|---|---|---|
| `web4-core` | ✅ 0.3.0 | ✅ 0.3.0 | ❌ 404 |
| `web4-trust-core` | ✅ 0.2.0 | ❌ 404 | ✅ 0.2.0 |

Two of six cells are empty. Both empty cells are *built* in-tree (`web4-trust-core/pyproject.toml` exists;
the npm name for the WASM bindings is `web4-trust-core`, from `web4-trust-core/pkg/package.json`) — they are
simply not published. A reader reaching for `web4-core` on npm, or `web4-trust-core` on PyPI, finds nothing.
The sentence now states which package is on which registry and warns that the other two cells are unpublished.

### Claims audited and HELD (no edit)

- `web4-standard/profiles/` — all four named deployment profiles present (edge-device, cloud-service,
  peer-to-peer, plus blockchain-bridge).
- `web4-standard/test-vectors/` — present, organized by subsystem as described.
- `web4-core` shipping "LCT presence primitive, T3/V3 tensors, ledger backends, and attestation envelope" —
  `lct.rs`, `t3.rs`/`v3.rs`, `ledger.rs` + `ledger/`, `attestation.rs` all present in the crate source.
- The hestia paragraph (corrected 2026-07-27) — re-verified unchanged and still accurate.

Both edits are **re-levels, not dilutions** (posture invariant #3): no truth claim deleted, two status
markers added where the text had asserted a status it had not checked. The pattern is the same one the
07-27 pass found in the hestia sentence and that §11 itself argues against — a declared property about a
reference implementation, accepted without computing on the evidence. Third instance in two passes, which
is why the audit is being run a few claims per pass rather than declared complete.

**Verification:** artifacts rebuilt locally and confirmed by content across all four surfaces (monolith,
`docs/whitepaper-web/index.html`, `build/web/index.html`, PDF text layer); old strings confirmed absent.
Whitepaper CI remains dead — day 72, protected-branch rejection at the deploy push — so this rebuild was
manual, as every content-carrying rebuild has been for 72 days.

---

## 2026-07-27 - Correction: §11 credited hestia with a fail-closed default its own documentation refutes

**Content change.** Section 11 (`11-standard-and-implementations`) described hestia as providing
"fail-closed defaults for unattended operation". That claim is false, and hestia's own repository says so
in as many words.

### The contradiction
`hestia/docs/GATE_BYPASS_CATALOG.md` §11 ("Standing acknowledgements — put these in front of anyone
relying on hestia") states: *"Default posture is **fail-open**. Absent `HESTIA_PRE_FAIL_CLOSED=1`, an
unreachable daemon means an ungoverned agent."* Confirmed in code, not inferred from prose —
`plugins/claude-code/hooks/pre_tool_use.py:377` is `return os.environ.get("HESTIA_PRE_FAIL_CLOSED") == "1"`,
so fail-closed is strictly opt-in. `plugins/agent-inventory/README.md:350` records the variable as **unset**
on a live host. Unattended operation is precisely the case the whitepaper named and precisely the case where
the default does not hold.

### What was true, and kept
Hestia *is* fail-closed on **invalid law**: `core/src/policy/law_gate.rs` denies every evaluation when the
law file is present but unparseable ("fail-closed+warn default, dp-ratified"). That is a real, ratified
invariant and it survives in the revised text — the closing paragraph's list of hardened normative
requirements now reads "fail-closed evaluation on invalid law" rather than the unqualified "fail-closed
policy defaults". Note that an *absent* law file is a third case again ("no third input"), neither of the
above.

### The edit
The hestia paragraph now claims a witnessed record of every governed decision rather than a fail-closed
default, and a second paragraph states the gate's published limits directly: it stops accidents rather than
adversaries, its posture on no-verdict is fail-open unless configured closed, and the record covers governed
activity only — so silence in it is not evidence that nothing happened. Linked to
[hestia#49](https://github.com/dp-web4/hestia/issues/49), which the maintainers filed 2026-07-26 for exactly
this purpose.

This is a **re-level, not a dilution** (posture invariant #3): no truth claim was deleted, and the section
gained a status marker it was missing. It also removes a self-contradiction — the paper argues that trust
must be computed by the relying party from evidence rather than accepted as an originating party's
declaration, while §11 was itself accepting a declared safety property about its own reference
implementation.

### Artifacts
Rebuilt locally (`make-md.sh`, `make-pdf.sh`, `make-web.sh`; pandoc 3.1.3 + xelatex) because CI remains dead
— see the 2026-07-26 entry. Correction verified by content in all four published surfaces: monolith,
`index.html` (both copies), and the PDF text layer. PDF 112031 → 113225 bytes.

---

## 2026-07-26 - Correction: the PDF is not a CI-built artifact, and the CI deploy has never succeeded

No whitepaper content changed. This entry corrects two factual claims made in the 2026-07-09 "Published"
entry below. Per the append-only rule that entry is left intact; this one supersedes it.

### Corrected — "the PDF is a CI-only artifact"
**False.** No PDF in this repository has ever been produced by CI. Every published PDF was built locally:
`6563186` (2026-07-09, titled "rebuild + publish PDF from revised sources (local pandoc/xelatex)" — committed
about an hour *after* the claim that the local box lacks LaTeX), then `4bd36e8`, then `3ec132d` (2026-07-14),
which is the PDF currently served. The dev box has `pandoc 3.1.3` and `xelatex` on PATH, verified this pass.

### Corrected — the diagnosed CI failure mode
The 07-09 entry describes the deploy step's `git push` as failing "non-fast-forward whenever a concurrent
commit lands mid-run" — an intermittent race — and proposes a rebase-before-push fix requiring `workflow`
token scope. **Both the diagnosis and the fix are wrong.** The actual failure, read from the run logs, is
deterministic and unrelated to concurrency:

```
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: - Changes must be made through a pull request.
! [remote rejected]   main -> main (protected branch hook declined)
```

`main` is a protected branch requiring pull requests; the workflow's deploy step pushes to it directly.
A rebase-before-push would have been rejected identically. **Run history: 46 runs, 45 failures, 1 success —
and the single success was a manual `workflow_dispatch` on 2026-05-15. Every push-triggered run since
2026-05-16 has failed**, i.e. the whitepaper CI deploy has been dead for ~70 days.

### Scope of the harm — latent, not yet realized
The build steps themselves succeed (markdown, PDF, web all build; the deploy step is the only failing one),
and the published surfaces are content-correct because local manual builds have covered every content change:
the `t3v3-012` Talent fix is verified present in the monolith, both `index.html` copies, and the PDF. The
exposure is that the documented safety net does not exist — a future content change relying on CI to publish
would ship stale artifacts silently. Rebuilding this pass would produce only timestamp churn (verified: the
regenerated monolith differs from the committed one by exactly one line, the `*Generated:*` stamp), so no
rebuild was performed.

### Open — requires a maintainer decision, not a Publisher fix
Restoring the deploy requires one of: granting the Actions bot a branch-protection bypass, converting the
deploy to a pull request, or removing the deploy step and declaring the artifacts locally built. All three
touch repository settings or credentials and are the operator's call. Flagged, not chosen.

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