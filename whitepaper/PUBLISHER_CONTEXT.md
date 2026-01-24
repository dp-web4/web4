# Web4 Whitepaper - Publisher Context

**Purpose**: This document provides complete context for the Publisher subagent responsible for maintaining the Web4 whitepaper.

**Last Updated**: 2026-01-23
**Whitepaper Status**: Active Development

---

## 1. Whitepaper Purpose & Philosophy

### What Web4 Is

Web4 is a **trust-native distributed intelligence architecture** built on Synchronism principles. Its core thesis:

> Trust should be native to digital infrastructure, not bolted on. Identity, context, and value should flow together through Linked Context Tokens.

### Key Concepts

| Concept | Definition |
|---------|------------|
| **LCT** | Linked Context Token - unforgeable digital presence |
| **T3** | Trust Tensor - 6-dimensional trust calculation |
| **V3** | Value Tensor - 6-dimensional value calculation |
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
| **T3** | Trust Tensor (6 dimensions) | "Triple Trust" ❌ |
| **V3** | Value Tensor (6 dimensions) | "Triple Value" ❌ |
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

1. **R6 Framework**: Recently documented, needs whitepaper section update
2. **TPM Integration**: Now real (was stub), whitepaper mentions hardware binding
3. **Policy Engine**: Implemented, may need whitepaper documentation
4. **Claude Code Plugins**: New, consider adding to implementation examples

### Pending Updates

| Area | Priority | Status |
|------|----------|--------|
| R6 section expansion | High | New docs available |
| Hardware binding update | Medium | TPM now real |
| Policy engine docs | Medium | Implemented in hardbound |
| Plugin examples | Low | Nice to have |

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
