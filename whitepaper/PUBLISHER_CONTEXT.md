# Web4 Whitepaper - Publisher Context

**Purpose**: This document provides complete context for the Publisher subagent responsible for maintaining the Web4 whitepaper.

**Last Updated**: 2026-09-02
**Whitepaper Status**: Active Development

---

## 1. Whitepaper Purpose & Philosophy

### What Web4 Is

Web4 is a **trust-native distributed intelligence architecture** built on Synchronism principles. Its core thesis:

> Trust should be native to digital infrastructure, not bolted on. Identity, context, and value should flow together through Linked Context Tokens.

### Key Concepts

| Concept | Definition |
|---------|------------|
| **LCT** | Linked Context Token - verifiable digital presence |
| **T3** | Trust Tensor - 3 root dimensions (Talent/Training/Temperament) with fractal RDF sub-dimensions |
| **V3** | Value Tensor - 3 root dimensions (Valuation/Veracity/Validity) with fractal RDF sub-dimensions |
| **R6** | Rules + Role + Request + Reference + Resource → Result |
| **MRH** | Markov Relevancy Horizon - context boundaries |
| **ATP/ADP** | Allocation Transfer/Discharge Packets - value flow |

### Relationship to Synchronism

- **Synchronism** = Physics/philosophy (why coherence matters)
- **Web4** = Protocol/implementation (how to build trust-native systems)

Web4 inherits Synchronism's coherence framework but presents it in **domain-appropriate language** for enterprise/technical audiences.

### Audience

Primary: Engineers, architects, enterprise decision-makers
Secondary: Researchers, protocol designers, standards bodies

---

## 2. Section Structure

### Current Organization (2026-07-09 rewrite — equation-ordered technical introduction)

The whitepaper was rewritten from scratch on 2026-07-09 (dp directive: "the paper has drifted too far
and needs a fresh rewrite"). It is now a **scoped technical introduction to the canonical Web4 standard**,
organized around the canonical equation. The pre-rewrite sections are preserved at
`archive/sections-2026-07-09-pre-rewrite/`.

```
sections/
├── 01-title-authors/                 # Title page ("WEB4: A Technical Introduction")
├── 02-why-web4/                      # The stakes — the two agent-trust questions
├── 03-the-equation/                  # Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP (the spine)
├── 04-mcp/                           # Element 1: the I/O membrane
├── 05-rdf/                           # Element 2: the ontological backbone
├── 06-lct/                           # Element 3: the presence substrate
├── 07-t3v3/                          # Element 4: trust & value tensors
├── 08-mrh/                           # Element 5: the relevancy horizon
├── 09-atp-adp/                       # Element 6: value feedback (honest maturity note)
├── 10-composed-architecture/         # R6/R7, roles-as-entities, SAL/AGY/ACP, dictionaries
├── 11-standard-and-implementations/  # web4-standard tree + hub + hestia as living examples
├── 12-conclusion/                    # Equation read back, legal framework, invitation
├── 13-glossary/                      # Compact glossary scoped to the paper's terms
└── 14-references/
```

### Scope rules (2026-07-09, dp-ratified)

- The paper explains **the canonical standard** — every mechanism section links its normative spec in
  `web4-standard/`. If a concept has no normative spec, it does not get a section.
- **Cut as drift, do not reintroduce**: code examples, the coherence framework and its math (C×S×Φ×R, η,
  superconductivity), trust-as-gravity, blockchain typology (Compost/Leaf/Stem/Root), memory-as-temporal-
  sensor as a section, manifesto-flourish prose, duplicated status catalogs.
- Elements are explained **in equation order** (MCP → RDF → LCT → T3/V3 → MRH → ATP/ADP); composed
  concepts after; implementations (web4 core packages, web4/hub, hestia) linked as living examples.
- Web nav is **flat, one entry per section**; nav `data-section` ids must match the `sections` array in
  `make-web.sh` 1:1 (the drift of hand-injected sub-anchors is what broke navigation pre-rewrite).

### Section Responsibilities

| Section | Purpose | Update Frequency |
|---------|---------|------------------|
| Why Web4 (02) | The stakes | Rarely — posture-stable |
| The Equation (03) | The organizing spine | Only if the canonical equation changes |
| Elements (04–09) | One equation term each | When the corresponding core-spec changes materially |
| Composed (10) | R6/R7, roles, SAL, dictionaries | When those specs change materially |
| Standard & Implementations (11) | Repo map + living examples | When repos/status change (most volatile) |
| Glossary (13) | Compact canonical terms | Critical — rarely change |

---

### Posture Invariants (public-face ordering — dp, 2026-07-09)

The whitepaper is our public face. A first-time reader must meet ideas in this order, and every daily pass
should check the doc still holds it. Full guidance: `docs/best-practices/public-docs-posture.md`.

1. **why → what → how; status is a footnote.** The reader meets *why it matters* → *what the idea is* →
   *how it works*, and only then *what is built today*. A public surface must **not lead with a
   version/status/test-count block** — that reads as a PR merge report. Status stays honest and present, but
   demoted to an Implementation-Status section/appendix, never the lead.
2. **Foundations build fractally; ATP is not a foundation.** Dependency order:
   presence (LCT) → capability & trust (T3/V3) → context (MRH) → grammar (R6/R7) → **value feedback (ATP/ADP)**
   → memory. **ATP/ADP is a value-feedback mechanism, not a founding pillar** — and it is the least-
   implemented core component (Hardbound-only, no public reference impl). Do not give it billing ahead of
   T3/V3 or call it "the beating heart / lifeblood." It gets a full treatment in Part 3 as *feedback on the
   foundation*.
3. **Re-level and reorder; never dilute honesty.** Posture fixes move and reframe material; they never delete
   a truth claim, a status marker, or a findings-vs-framings distinction.

*Watch item:* if a future edit reintroduces a status block as the lead of the Exec Summary or Introduction,
or re-promotes ATP ahead of T3/V3, flag it as a posture regression.

---

## 3. Inclusion Criteria

### Content SHOULD be integrated when:

**Protocol Specification (High Priority)**
- New protocol element implemented in code
- Specification clarified based on implementation experience
- Security analysis identifies needed changes
- Interoperability requirements documented

**Implementation Evidence (Medium Priority)**
- hardbound-core implements new feature
- web4-core adds new module
- Python bindings expose new capability
- Real TPM/hardware integration achieved

**Architecture Clarity (Lower Priority)**
- Diagram or explanation improves understanding
- Example clarifies abstract concept
- Cross-reference connects related concepts

### Content should NOT be integrated when:

**Belongs Elsewhere**
- Physics/philosophy → Goes in Synchronism whitepaper
- SAGE-specific → Goes in HRM documentation
- Enterprise features → Goes in Hardbound documentation

**Too Early**
- Code not yet written
- Design still evolving
- No validation of approach

**Quality Issues**
- Adds complexity without proportional value
- Contradicts existing specification
- Uses non-canonical terminology

---

## 4. Terminology Protection

### CRITICAL: Canonical Terms

These terms are foundational. NEVER redefine:

| Term | Canonical Meaning | WRONG Expansions |
|------|-------------------|------------------|
| **LCT** | Linked Context Token | "Lifecycle-Continuous Trust" ❌ |
| **MRH** | Markov Relevancy Horizon | (none documented) |
| **T3** | Trust Tensor (3 root dims + fractal RDF sub-dimensions) | "Triple Trust" ❌ |
| **V3** | Value Tensor (3 root dims + fractal RDF sub-dimensions) | "Triple Value" ❌ |
| **R6** | Rules/Role/Request/Reference/Resource/Result | "R6 Protocol" (ok as shorthand) |
| **ATP** | Allocation Transfer Packet | "Audit Trail Point" ❌, "Attention Transfer Packet" ❌ |
| **ADP** | Allocation Discharge Packet | "Alignment Discharge Protocol" ❌ |

### Historical Drift Incidents

| Date | Term | Wrong | Correct | Lesson |
|------|------|-------|---------|--------|
| 2026-01-03 | LCT | "Lifecycle-Continuous Trust" | Linked Context Token | Always check glossary |
| 2026-01-23 | ATP | "Audit Trail Point" | Allocation Transfer Packet | Hardbound uses different terms |

### Resolution: Hardbound vs Web4 Terminology

Hardbound (enterprise product) uses slightly different framing:
- "Audit bundle" instead of "ATP record"
- "Team ledger" instead of "society blockchain"
- "Policy engine" for governance rules

These are **presentation differences**, not protocol differences. The underlying Web4 protocol terms remain canonical.

---

## 5. Build Process

### Quick Build

```bash
cd /mnt/c/exe/projects/ai-agents/web4/whitepaper

# Generate markdown
./make-md.sh

# Generate PDF
./make-pdf.sh

# Generate web version
./make-web.sh
```

### Build Outputs

| Script | Output | Destination |
|--------|--------|-------------|
| `make-md.sh` | `build/WEB4_Whitepaper_Complete.md` | also copied to `docs/whitepaper-web/` |
| `make-pdf.sh` | `build/WEB4_Whitepaper.pdf` | also copied to `docs/whitepaper-web/` |
| `make-web.sh` | `build/web/` (`index.html`, `assets/`) | also copied to `docs/whitepaper-web/` (GitHub Pages) |

*(Table corrected 2026-08-28: all three scripts copy into `docs/whitepaper-web/`; the earlier rows read "Local" / "metalinxx.io", which was stale on every line.)*

### Publishing — the contract since `#789` (2026-08-27)

**CI does not publish.** `build_whitepaper.yml` runs with `contents: read`, builds for a *parity check* only, and pushes nothing. `whitepaper/build/` (gitignored but tracked — `git add -f`) and `docs/whitepaper-web/` reach `main` **only by being committed inside a reviewed PR.** A pass that edits `sections/` and does not rebuild and commit all six artifact files leaves the published paper stale, and nothing in CI will say so.

1. Rebuild in a fresh worktree (`git worktree add --detach /tmp/<name> origin/main`, then a branch with `--set-upstream-to=origin/main` so the scripts print "Already up to date" instead of pulling). Building in the shared `/mnt/c` checkout emits CRLF against LF-committed artifacts and every line reads as changed.
2. Run all three scripts; `git diff` must show **only** the `*Generated:*` line (both monoliths; `pdftotext` the PDFs — the binaries always differ) when `sections/` is unchanged. Anything else is real drift.
3. Content change → commit the artifacts with the source in the same PR. No content change → `git checkout --` the four timestamp-churn files by explicit path; do not commit churn.
4. `make-web.sh` requires Pygments and now fails loud without it (`d9cc3507`); the CI parity step compares against committed HTML, so an artifact built without Pygments will fail the PR.

### Build Verification

After any change:
1. Run `./make-md.sh` - Check for errors
2. Run `./make-web.sh` - Verify navigation
3. Spot-check combined markdown for coherence
4. If PDF needed: `./make-pdf.sh`

---

## 6. Recent Changes

**The run log lives in [`log/PUBLISHER_LOG.md`](log/PUBLISHER_LOG.md).** New entries go there, newest first — not here.

This section used to carry the log inline. On 2026-09-03 it held 590,764 bytes across
90 dated entries — 96% of this file — while §11 instructs the Publisher subagent to read
the whole document as its context. A pass's *history* is not a pass's *context*; keeping them in one
file made the second unreadable to get at the first. The entries were moved verbatim, none dropped.

Everything else in this document is context the next pass needs before it acts. Keep it that way:
append run history to the log file, and edit this file only when the *standing* picture changes
(structure, criteria, terminology, build process, current state).

---

## 7. Related Repositories

### Primary Sources for Updates

| Repository | What to Check | Update Triggers |
|------------|---------------|-----------------|
| **web4-core** | `src/*.rs`, `ARCHITECTURE.md` | New modules, API changes |
| **hardbound-core** | `src/*.rs`, docs/ | Enterprise features |
| **HRM/sage** | `sage/docs/` | SAGE integration changes |

### Checking for Updates

```bash
# Check web4-core for new files
git -C /path/to/web4 log --oneline --since="2 weeks ago" -- web4-core/

# Check hardbound for new features
git -C /path/to/hardbound log --oneline --since="2 weeks ago"
```

---

## 8. Quality Standards

### Technical Accuracy

- All protocol descriptions must match implementation
- Code examples must be tested and working
- Security claims must be justified
- Performance claims must cite measurements

### Audience Appropriateness

- NO Synchronism physics terminology in main text
- Domain-appropriate language for each section
- Enterprise-friendly presentation
- Implementation-focused over theoretical

### Formatting

- Tables for comparisons
- Code blocks for examples
- Diagrams for architecture
- Clear section numbering

---

## 9. Integration Workflow

### Standard Update Process

```
1. IDENTIFY trigger
   ├── New code in web4-core or hardbound-core
   ├── Specification clarification needed
   └── Gap identified in documentation

2. ASSESS scope
   ├── Which sections affected?
   ├── Terminology impact?
   └── Build implications?

3. DRAFT changes
   ├── Edit specific section files
   ├── Update glossary if new terms
   └── Add cross-references

4. VERIFY
   ├── ./make-md.sh passes
   ├── ./make-web.sh passes
   ├── Terminology matches canonical

5. COMMIT
   ├── Clear commit message
   └── Reference issue/PR if applicable
```

### Governance Model

Web4 whitepaper uses **direct edit** model (simpler than Synchronism):
- Minor changes: Direct edit with commit message
- Major changes: Document rationale in commit
- Breaking changes: Discussion required before implementation

---

## 10. Current State Summary

### Implementation Status

| Component | Status | Documentation |
|-----------|--------|---------------|
| web4-core (Rust) | ✅ Complete | ARCHITECTURE.md |
| hardbound-core (Rust) | ✅ Complete | ARCHITECTURE.md |
| Python bindings | ✅ Complete | README.md |
| Claude Code plugin | ✅ Complete | README.md |
| R6 framework | ✅ Implemented | r6-implementation-guide.md |
| TPM integration | ✅ Working | tpm.rs, docs/ |

### Whitepaper vs Implementation Gap

The whitepaper should reflect implementation reality. Current gaps:

> **Re-anchored 2026-07-27.** Every item below previously named a *pre-rewrite* anchor — "Part 7 body
> examples", "the status table", "§7.0.2" — none of which have existed since the 2026-07-09 rewrite
> replaced Parts 1–8 + Executive Summary with the 14-section equation-ordered structure. The gap list
> was describing a document that had been deleted three weeks earlier. Verified by grep over live
> `sections/*/index.md`: "Executive Summary" → 0 hits, `Part [0-9]` → 0 hits.

1. **R6/R7 Framework**: **CLOSED by the rewrite.** The old gap was "Part 7 body examples still use R6
   language". The rewrite's `10-composed-architecture` opens with "The R6/R7 action grammar" and gives
   R7 a first-class treatment (Reputation as output, Request↔Result delta feeding T3/V3); `13-glossary`
   carries the R7 definition. No R6-only body examples remain.
2. **Governance Stack Detail**: 10-layer stack operational in Hardbound CLI. The status table that
   documented it was **cut by the rewrite** (posture invariant #1 — no version/status/test-count block).
   Currently absent from the paper by design, not by oversight; re-open only if dp wants an
   Implementation-Status appendix.
3. **AttestationEnvelope**: **Regressed, not resolved.** The 2026-04-06 entry claimed §7.0.2 + glossary
   coverage; the rewrite dropped both. `AttestationEnvelope` now has **zero hits** in live sections —
   it survives only as the lowercase phrase "attestation envelope" in the §11 core-package list. This is
   consistent with the rewrite's scope rule (its spec is `docs/specs/attestation-envelope.md`, not a
   `web4-standard/core-spec/` normative document), so the removal is defensible — but it is a *removal*,
   and the tracker was recording it as coverage.
4. **Claude Code Plugins**: `claude-code-plugin/` in-repo is a pointer README to
   [anthropics/claude-code#20448](https://github.com/anthropics/claude-code/pull/20448); the code is
   maintained as an upstream PR. Not integrated into the paper; low priority.

### Pending Updates

> **Anchor warning (2026-07-27).** Rows below were written against the pre-2026-07-09 structure and
> still name integration targets that no longer exist — "Executive Summary", "Part 3 narrative",
> "Part 6 / Part 8", "a new Part 7 §7.7/§7.8 paralleling the outward §7.3-§7.6 structure". The *findings*
> in these rows remain valid; their *destinations* do not. Before acting on any Watch/Deferred row,
> re-map it onto the live 14-section structure (§2) — and note that rows marked "Resolved … integrated
> into Executive Summary" describe content the rewrite deliberately removed, so they are resolved as
> **out of scope**, not as **present in the paper**. Rows are left unedited rather than retro-fitted:
> rewriting the history to look correct is not a correction.

| Area | Priority | Status |
|------|----------|--------|
| R7 language in Part 7 body examples | Medium | Reference impl exists; Part 7 body examples (7.1-7.3) still use R6 language |
| ACP protocol section in Part 7 | Medium | Full lifecycle implemented; no dedicated whitepaper section yet |
| 10-layer governance diagram | Low | Described in status table; could benefit from visual representation |
| Plugin examples | Low | Nice to have |
| ATP transfer-fee semantics | Resolved (spec) | Sprint 44 T1 (#179, 2026-05-12) added §6.3 Transfer Fees to atp-adp-cycle.md as society-configurable MAY. Spec-level resolution; whitepaper Part 3 narrative does not enumerate society economic policies — no whitepaper integration warranted |
| CI/coherence as cost multiplier | Resolved (spec) | Sprint 46 T1 (#181, 2026-05-13) added §4.4 to multi-device-lct-binding.md clarifying constellation_coherence is canonical metric; "CI"/numeric multipliers are simulation parameters, NOT protocol primitives. Whitepaper does not use "CI" terminology — no integration warranted |
| Synthon lifecycle | Watch | Sprint 43 memo flagged as SPEC GAP; integrate when web4 spec work resolves |
| Karma-across-lives canonicity | Watch | Sprint 43 memo flagged as SPEC GAP; integrate when web4 spec work resolves |
| Heterogeneous-identity / constellation framing | Watch | docs/specs/heterogeneous-identity.md (commit 64adbe2, 2026-04-29); 4 open questions outstanding (constellation lower bound, divergence resolution, cross-domain witnessing, observability); integrate when constellation lifecycle and minimums resolve |
| web4-core SDK Society/Role/ATP/R6 types | Resolved (2026-05-16) | Integrated into Executive Summary "Currently Available" via v0.2.0 release (2026-05-15, commits beb2a9b + 1fb6c90). Society / SocietyRole / RoleAssignment, ATPAccount, R7Action types now shipped on crates.io + PyPI |
| inter-society-protocol.md (genesis/first-contact/federation/secession) | Partially Resolved (2026-05-16) | Spec shipped in v0.2.0 SDK and noted in Executive Summary calibration paragraph. Whitepaper-body Part 6 / Part 8 integration remains deferred — likely a future pass once secession/dissolution semantics gain more implementation evidence |
| MCP-as-inter-society-protocol per canonical equation | Partially Resolved (2026-05-16) | MCP §7.3-§7.6 (cross-society envelope, witnessing/R7 reputation propagation, failure modes) shipped in v0.2.0 SDK; §7.7 (WIP) referent-grounded exchange-rate negotiation remains. **§7.7 promotion gate formalized** at `docs/audits/s7.7-promotion-tracking-2026-05-16.md` (Sprint 54 C3, #202): 3 hard prerequisites (PR #200 ✓ 2026-05-17 + F11 signing authority + F8 verify), 5 open design questions, and 2-implementations + interop + error-catalogue evidence criteria. Integrate when §7.7 reaches `status: Normative` per that memo's checklist |
| Sprint 52 conformance gaps (5 NEW operator-architectural-decision items) | Watch (architectural decision) | Sprint 52 memo (c09d0d2, 2026-05-15) flags 5 NEW surface gaps not in prior audits: constraint enforcement, V3 valuation behavioral vs economic, role-004 assigner predicate, fed-001 child- vs parent-initiated federation, sub-dimension rollup. v0.2.0 SDK ships the 35-vector conformance runner with 8 xfailed gaps. Each requires an operator architectural decision before implementation. Integrate when decisions land in spec |
| WASM bindings for Society/Role/ATP/R7 primitives | Resolved (2026-05-16) | Integrated into Executive Summary + Conclusion via v0.2.0 npm release of `web4-trust-core` (commit 1fb6c90, 2026-05-15). First npm publish; bundle ~337KB |
| `docs/proof/PUBLISHED.md` refresh to v0.2.0 | Resolved (2026-05-21) | Closed by #214 (088a0d6, 2026-05-21): PUBLISHED.md refreshed v0.1.1 → v0.2.0, now leads with "Current Release: v0.2.0 (2026-05-15)" and lists all package surfaces (crates.io/PyPI/npm web4-core/web4-trust-core 0.2.0, web4-sdk PyPI 0.27.0), v0.1.1 history preserved. Executive Summary's dual PUBLISHED.md + CHANGELOG.md citation is now fully accurate (the dual cite was a 2026-05-16 workaround for the stale record). No Executive Summary edit required |
| presence-protocol (inward MCP surface) | Watch (2026-05-17) | New core spec at `web4-standard/core-spec/presence-protocol.md` capturing the inward MCP surface (presence ↔ cognition), distinct from the outward `mcp-protocol.md` (society ↔ society). v0 (2026-05-16) → v1 policy-engine (2026-05-16) → v1 wait protocol (2026-05-16) → v1 §3.1 synthetic flag (2026-05-17). Two implementations: Hestia (software-bound, AGPL) + Hardbound (hardware-bound, private). Per "Design still evolving" exclusion (4 versions in <24h, Hestia daemon at 0.0.3 pre-1.0), DEFER. Integrate once spec stabilizes AND Hestia/Hardbound ship a registry-published release — likely as a new Part 7 §7.7/§7.8 paralleling the outward §7.3-§7.6 structure. The MCP-bifurcation framing (inward vs outward) is itself a whitepaper-worthy clarification once it settles |

---

## 11. Subagent Instructions

When reviewing this whitepaper:

1. **Read this entire document first** - It's your complete context
2. **Check implementation repos** for changes since last update
3. **Compare whitepaper to implementation** - Identify gaps
4. **Apply inclusion criteria** - Is this whitepaper-worthy?
5. **Protect terminology** - Never drift from canonical
6. **Draft minimal viable changes** - Conservative approach
7. **Verify builds** before proposing
8. **Report clearly** with:
   - Needs update: yes/no
   - Specific proposals with rationale
   - Sections affected
   - Implementation evidence for each change
   - Any terminology concerns

### Key Differences from Synchronism

- Web4 is **protocol/implementation** focused
- Simpler governance (direct edit)
- Must match code reality
- Enterprise-friendly language required
- Updates triggered by code, not research sessions

---

*"The Web4 whitepaper is the bridge between vision and implementation. Keep it grounded in what actually works."*
