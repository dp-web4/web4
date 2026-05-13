# Web4 Whitepaper - Publisher Context

**Purpose**: This document provides complete context for the Publisher subagent responsible for maintaining the Web4 whitepaper.

**Last Updated**: 2026-05-13
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

### Current Organization

```
sections/
├── 00-executive-summary/        # Overview and key value propositions
├── 00-introduction/             # Web4 vision and positioning
├── 01-title-authors/            # Document metadata
├── 02-glossary/                 # Canonical terminology
├── 03-part1-defining-web4/      # What Web4 is and isn't
├── 04-part2-foundational-concepts/
│   ├── Linked Context Tokens (LCTs)
│   ├── Dictionary Entities
│   ├── Trust Through Witnessing
│   └── Markov Relevancy Horizons
├── 05-part3-value-trust-mechanics/
│   ├── ATP/ADP Cycles
│   ├── T3 Trust Tensor
│   ├── V3 Value Tensor
│   └── Compression-Trust Dynamics
├── 06-part4-implications-vision/
│   ├── Privacy and Sovereignty
│   ├── Governance Models
│   └── Economic Implications
├── 07-part5-memory/             # Memory as temporal sensor
├── 08-part6-blockchain-typology/
│   ├── Four-Chain Hierarchy
│   ├── Fractal Lightchain
│   └── Compost/Leaf/Stem/Root
├── 09-part7-implementation-details/
├── 09-part7-implementation-examples/
├── 10-part8-web4-context/       # Integration with existing systems
├── 11-conclusion/
├── 12-references/
└── 13-appendices/
```

### Section Responsibilities

| Section | Purpose | Update Frequency |
|---------|---------|------------------|
| Executive Summary | Current state | Every major update |
| Glossary (02) | Canonical terms | Critical - rarely change |
| Foundational Concepts (04) | Core protocol | Stable - major changes only |
| Value-Trust Mechanics (05) | How it works | Updates with new mechanisms |
| Implementation (09) | How to build | Frequent - with new code |
| Memory (07) | Temporal sensing | Updates with HRM progress |
| Blockchain (08) | Chain architecture | Stable - major changes only |

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
| `make-md.sh` | `build/WEB4_Whitepaper_Complete.md` | Local + docs/ |
| `make-pdf.sh` | `build/WEB4_Whitepaper.pdf` | Local |
| `make-web.sh` | `build/web/` | metalinxx.io |

### Build Verification

After any change:
1. Run `./make-md.sh` - Check for errors
2. Run `./make-web.sh` - Verify navigation
3. Spot-check combined markdown for coherence
4. If PDF needed: `./make-pdf.sh`

---

## 6. Recent Changes

### 2026-05-13: Publisher Maintenance - No-Change Check
- Six commits since 2026-05-04 no-change check reviewed against inclusion criteria. None warrant whitepaper integration today.
- **Sprint 44 T1 (#179, d530060, 2026-05-12)**: Resolved Sprint 43 SPEC GAP #2 (ATP transfer-fee semantics) and #5 (T3 Talent-decay ambiguity).
  - `atp-adp-cycle.md` §6.3 adds Transfer Fees as society-configurable MAY (declared rate/bearer/destination, transfer_policy in economic_laws YAML).
  - `t3-v3-tensors.md` strengthens Talent no-decay to explicit normative invariant; Training/Temperament remain society-configurable.
  - **No whitepaper integration**: Part 3 ATP/ADP narrative is high-level ("Biology Made Digital", perpetual cycle framing) and does not enumerate society-level economic policies anywhere. Adding fees-only would be incongruous. Similarly, Part 3.2 T3 narrative does not discuss decay mechanics. Both are spec-level normative refinements, not new protocol primitives. Watch item for transfer-fees marked resolved at spec level.
- **Sprint 45 T1 (#180, 7c228fd, 2026-05-13)**: Archive stale implementation artifacts. Housekeeping; no protocol changes.
- **Sprint 43 follow-up (#178, 372b06a, 2026-05-09)**: Strategic review follow-up audit + archive 3 stray implementation/ markdowns. Housekeeping.
- **Autonomous safety net (#176, 12ee197, 2026-05-12)**: Autonomous session — housekeeping.
- **Reference impl triage (#174/#175, cbc951a/485eb4f, 2026-05-06–08)**: Archive 15 reference files + classify 31 files for archive/keep + triage 9 sprawl directories. Housekeeping.
- No content changes; no source/artifact rebuild needed (build remains aligned with 2026-04-29 source state from e990039).

### 2026-05-04: Publisher Maintenance - No-Change Check
- Four content-bearing commits since 2026-04-30 rebuild reviewed against inclusion criteria. None warrant whitepaper integration today.
- **Live whitepaper sections verified clean of ATP/LCT terminology drift** following 4a0dce7 (2026-04-29) cleanup across spec corpus / docs/what+why+how/ / demo. All remaining historical drift hits are confined to `whitepaper/sections/*/archive/*`, intentionally preserved per the cleanup commit's "would falsify historical record" exclusion. No live-section corrections needed.
- **cross_language_verify example (afe68ab)**: Python+Rust round-trip on shared LocalLedger, demonstrating on-disk-format-as-contract. Per the 2026-04-29 identity_bootstrap precedent (doc-only, not whitepaper-worthy on its own), this is a demonstration of existing primitives (Ledger trait + hash-chained on-disk format), not a new protocol primitive. Cross-language interop was always implicit in Rust core + Python bindings. No whitepaper change.
- **heterogeneous-identity design note (64adbe2)**: substantive content — "constellation, not credential" framing, "ATP from measurement" (answers recurring 4-life visitor friction), witness != vouch, salience-aware fingerprinting, access-mode tiers. Phase 1+1.5+A reportedly live across fleet. **DEFER**: the design note itself flags 4 open questions (constellation size lower bound, divergence resolution, cross-domain witnessing, constellation observability). Per "Design still evolving" exclusion, integrate when those resolve. Added to pending list.
- **README "Who this is for, and why" (e064554)**: README-level audience/positioning content. Whitepaper Executive Summary already has its own calibrated current-state framing (2026-04-29 a5dafa6). Belongs in README, not whitepaper. No change.
- No content changes; no source/artifact rebuild needed (build remains aligned with 2026-04-29 source state from e990039).

### 2026-04-30: Publisher Maintenance - Rebuild for Calibration-Framing Edits
- Five non-publisher commits on 2026-04-29 (after the morning publisher build) edited whitepaper sources without rebuilding artifacts: exec summary calibration framing + v0.1.1 fix (a5dafa6); Introduction + Part 1 + Part 2 rewrite to "current state, not past vision" (16c0e77); Part 7 §7.0.0 published-packages section (367caac); conclusion full rewrite (5edc79f); Part 2.8 + conclusion framing restoration (fdf7e63)
- Net effect across 6 section files: +134/-151 lines, framing-level shift from "vision/revolution" rhetoric → calibrated current-state language. No new canonical terms; no terminology drift; existing published-packages narrative (v0.1.1) reinforced
- Rebuilt md (3,738 lines, 240K) and pdf (408K). Build artifacts and docs/whitepaper-web/ copies now reflect 2026-04-29 evening source state
- No new content authored by publisher this pass — pure artifact-source reconciliation

### 2026-04-29: Publisher Maintenance - First Public Release Reflected
- web4-core and web4-trust-core v0.1.0 published to crates.io and PyPI on 2026-04-28 (commit 9744051, plus v0.1.1 Python-import fix in 7d25a9d)
- Per inclusion criteria ("New protocol element implemented in code" → high priority): Executive Summary "Currently Available" now leads with the published packages and install commands; release record cited at `docs/proof/PUBLISHED.md`
- **Ledger trait + InMemoryLedger + LocalLedger** (commit 068f448, 2026-04-27) introduced as first-class abstraction in web4-core. The whitepaper already documents "hash-chained ledger" infrastructure in §7.0.1; the Ledger trait is the implementation primitive backing it (no new whitepaper concept introduced — the Rust API surface is implementation detail). Published-package note in Executive Summary now mentions "in-memory and on-disk Ledger backends" so the v0.1.0 surface is accurately described.
- Title page date bumped April 9 → April 29
- Identity bootstrap example (`web4-core/python/examples/identity_bootstrap.py`, commit b86b719) is doc-only — not whitepaper-worthy on its own
- Rebuilt all artifacts (md, pdf)

### 2026-04-27: Publisher Maintenance - No-Change Check (Sprints 36-43)
- Reviewed all commits since 2026-04-13 (Sprints 36-43, autonomous cleanup, GitNexus reindex)
- All work is SDK/tooling (ruff lint+format, examples cleanup, dead code removal, CI wheel smoke job, SDK v0.26.0 release housekeeping) — not protocol changes
- **Sprint 43 (spec-to-explainer alignment memo, #168)** identified 4 SPEC GAPs from 4-life visitor friction log: ATP transfer-fee semantics, CI/coherence as cost multiplier, synthon lifecycle, karma-across-lives canonicity. Memo *classifies*, does not *fix* — these are pre-spec gap analyses. Per inclusion criteria ("Code not yet written / Design still evolving"), no whitepaper changes warranted yet. Track as pending: when spec work resolves any of the 4 gaps, integrate then.
- No content changes; no rebuild needed

### 2026-04-13: Publisher Maintenance - PDF Date Fix
- Fixed hardcoded PDF date in make-pdf.sh ("February 2026" → "April 2026")
- No content changes needed — SDK updates (v0.22-v0.25, trust CLI, selftest CLI, web4_process_action MCP) are tooling, not protocol
- Rebuilt all artifacts (md, pdf)

### 2026-04-06: Publisher Maintenance - AttestationEnvelope + Glossary
- Added AttestationEnvelope to §7.0.2 (unified hardware trust primitive, 4 anchor types)
- Added R6/R7 Action Framework glossary entry (canonical term, was missing)
- Added AttestationEnvelope glossary entry (implemented protocol primitive)
- Updated PUBLISHER_CONTEXT.md (recent changes, pending updates, governance stack 9→10-layer)
- Rebuilt all artifacts (md, pdf)

### 2026-02-21: Publisher Maintenance - R7/ACP/Federation Expansion
- Executive Summary: expanded "Emerging Implementation" with 10 new capabilities (R7, ACP, Sybil proofs, game theory, Dictionary Entity, federation, multi-device, trust decay, Law Oracle, MRH graph)
- Moved Dictionary Entity from "Vision" to "Emerging Implementation" (now has 30/30-check reference impl)
- Section 7.0.1 status table: added 8 new rows (R7, ACP, Sybil, Dictionary, federation, Law Oracle, MRH, 10-layer governance)
- Updated coherence regulation, blockchain consensus, hardware binding rows with new capabilities
- Softened "most features not yet implemented" note in Part 7 — governance stack is now operational
- Updated Part 7 examples header to acknowledge operational reference implementations
- Rebuilt all artifacts (md, pdf)

### 2026-02-20: Publisher Maintenance - Implementation Status Update
- Updated Appendix G, Section 7.0, and Executive Summary to reflect Hardbound CLI governance stack
- ATP/ADP, blockchain, and hardware binding statuses moved from "Not started" to "Partial"
- New "Emerging Implementation" section in Executive Summary for operational Hardbound CLI features
- Fixed Appendix H/I ordering (were swapped: I before H)
- Roadmap expanded with 11 completed items (policy-from-ledger, multi-sig, heartbeat blocks, etc.)
- Rebuilt all artifacts (md, pdf)

### 2026-02-19: Publisher Maintenance - Entity Type Expansion
- Updated date, expanded entity_type enum to 15 types
- Rebuilt all artifacts (md, pdf)

### 2026-02-18: Publisher Maintenance - LCT Reframe Cleanup
- Fixed 7 stale "identity" references missed by the witnessed presence reframe
- Affected files: 03-part1, 06-part4, 08-part6, 10-part8
- "Identity Coherence" (SAGE research concept) left as-is - distinct from protocol terminology
- Rebuilt all artifacts (md, pdf)

### 2026-02-17: Publisher Maintenance
- Rebuilt all artifacts (md, pdf, web) to reflect Feb 16 terminology reframe
- "Trust infrastructure" language now consistent across build artifacts

### 2026-02-16: Trust Infrastructure Reframe
- Systematic reframe from "governance" to "trust infrastructure" across 17 files
- Executive summary: "WEB4 is not an upgrade" → "WEB4 adds what was always missing"
- SAL: "Governance Framework" → "Trust Accountability Layer"

### 2026-01-23: R6 Framework Expansion
- Added R6 implementation guide
- Added R6 security analysis
- Updated implementation status

### 2026-01-20: ARCHITECTURE.md
- Added Rust + Python hybrid architecture documentation
- Explained web4-core structure

### 2026-01-18: Initial Web Version
- Complete web build with navigation
- All sections structured and indexed

### Earlier (2025)
- Memory as temporal sensor integration
- Fractal lightchain documentation
- SAGE coherence model integration

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

1. **R6/R7 Framework**: Documented; R7 in status table and glossary; Part 7 body examples still use R6 language
2. **Governance Stack Detail**: 10-layer stack operational in Hardbound CLI — documented in status table
3. **AttestationEnvelope**: Now documented in §7.0.2 and glossary (as of 2026-04-06)
4. **Claude Code Plugins**: Working, consider adding to implementation examples

### Pending Updates

| Area | Priority | Status |
|------|----------|--------|
| R7 language in Part 7 body examples | Medium | Reference impl exists; Part 7 body examples (7.1-7.3) still use R6 language |
| ACP protocol section in Part 7 | Medium | Full lifecycle implemented; no dedicated whitepaper section yet |
| 10-layer governance diagram | Low | Described in status table; could benefit from visual representation |
| Plugin examples | Low | Nice to have |
| ATP transfer-fee semantics | Resolved (spec) | Sprint 44 T1 (#179, 2026-05-12) added §6.3 Transfer Fees to atp-adp-cycle.md as society-configurable MAY. Spec-level resolution; whitepaper Part 3 narrative does not enumerate society economic policies — no whitepaper integration warranted |
| CI/coherence as cost multiplier | Watch | Sprint 43 memo flagged as SPEC GAP; integrate when web4 spec work resolves |
| Synthon lifecycle | Watch | Sprint 43 memo flagged as SPEC GAP; integrate when web4 spec work resolves |
| Karma-across-lives canonicity | Watch | Sprint 43 memo flagged as SPEC GAP; integrate when web4 spec work resolves |
| Heterogeneous-identity / constellation framing | Watch | docs/specs/heterogeneous-identity.md (commit 64adbe2, 2026-04-29); 4 open questions outstanding (constellation lower bound, divergence resolution, cross-domain witnessing, observability); integrate when constellation lifecycle and minimums resolve |

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
