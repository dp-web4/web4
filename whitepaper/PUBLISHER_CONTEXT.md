# Web4 Whitepaper - Publisher Context

**Purpose**: This document provides complete context for the Publisher subagent responsible for maintaining the Web4 whitepaper.

**Last Updated**: 2026-05-25
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

### 2026-05-25: Publisher Maintenance - No-Change Check (C12/C13/C14 land as predicted — framework + T3/V3 internal-consistency sweep; SDK fee-free default; no whitepaper relevance)
- Seven commits since the 2026-05-24 no-change check (56552b8), all the same C-series internal-consistency audit/remediation stream plus one SDK default-alignment fix. **None touch `whitepaper/sections/*`** (verified: no source-section commit since 42e3e47, 2026-05-19; published artifact `docs/whitepaper-web/WEB4_Whitepaper_Complete.md` still 254811 bytes / 2026-05-19, aligned with source — no rebuild needed). The 2026-05-24 entry predicted "watch whether C12/C13 land next week and complete the sweep"; **they landed the very next day, plus C14** — the framework + tensor docs are now audited and remediated. All seven commits:
  - **#229 (628d3fd) — C12 r6-framework.md internal-consistency audit (11 findings):** Analysis-only memo at `docs/audits/r6-framework-internal-consistency-2026-05-24.md` (346 insertions). R6 is `web4-standard/core-spec/r6-framework.md`, the action-framework primitive (canonical-equation foundation layer). Same instrument as C2–C11.
  - **#231 (06300ca) — C12 r6-framework remediation (all 11 findings):** 64 insertions / 43 deletions in `r6-framework.md`. Editorial/structural — no new fields, no wire-format change.
  - **#230 (8c45e11) — C13 t3-v3-tensors.md internal-consistency audit (11 findings):** Analysis-only memo (286 insertions). T3/V3 is the canonical-equation trust/value tensor primitive — the last non-RDF primitive the 2026-05-24 entry flagged as outstanding.
  - **#232 (6e90c52) — C13 t3-v3-tensors remediation (all 11 findings):** 42 insertions / 17 deletions. Mostly editorial, but three substantive-but-spec-internal items: (a) added a **Continuous Quality-Formula** for T3 updates (`delta = 0.02·(quality − 0.5)`, dimension factors talent=1.0/training=0.8/temperament=0.6) as a complement to the categorical outcome table; (b) aligned a SPARQL trust-composite `BIND` weight from `0.3/0.4/0.3` to the normative **`0.4/0.3/0.3`** §10.2 weights (the same protocol-invariant the 2026-05-19 t3-002 vector fix established) — fixing a spec-internal inconsistency, not changing the invariant; (c) clarified V3 entity-role binding (V3 derives context from co-located T3Tensor, avoiding RDF domain violations). **New open question (C13/M4):** V3 Valuation bound is a **3-way divergence** — spec + `t3v3-ontology.ttl` say Valuation MAY exceed 1.0, but the SDK `V3.__post_init__` clamps to [0,1] and vector t3v3-002 assumes normalized inputs; flagged as a semantic operator decision, not a bug. Spec-level (the whitepaper narrative does not enumerate tensor value ranges) — observed, not a whitepaper watch item.
  - **#233 (f06e03b) — C14 r7-framework.md internal-consistency audit (10 findings):** Analysis-only memo (224 insertions). R7 is the extended action framework (in the whitepaper status table + glossary at the concept level).
  - **#234 (6d40cc4) — C14 r7-framework remediation (all 10 findings):** 50 insertions / 16 deletions. Made the R7 Result **`status` enum normative** (`pending`/`validated`/`in_progress`/`success`/`failure`/`error`/`cancelled`, aligned with the SDK `ActionStatus`), with a `failure` (action ran, unsuccessful outcome) vs `error` (framework/execution fault before a valid outcome) distinction; renamed an example field `"value"`→`"valuation"` (V3-dimension alignment); fixed SDK examples (catch `OutputViolation` vs generic `Exception`; source `action_id` from the request nonce, not the ledger txHash since failed actions have no `ledgerProof`). R7 lifecycle detail at the spec/SDK layer; the whitepaper carries R7 conceptually (status table + glossary), not its Result status enum — no integration warranted.
  - **#228 (62524cf) — fix(sdk): make ATP `transfer()` fee-free by default per §6.3 (C11/M3):** `atp.py` default `fee_rate` 0.05 → 0.0 (+ test). This is the **SDK catching up to the already-"Resolved (spec)" `atp-adp-cycle.md` §6.3** item ("fee-free at protocol level; implementations MUST NOT hard-code fee rates"); the 5% used in vectors/sims is an explicit simulation parameter, not a protocol default. The Pending-Updates "ATP transfer-fee semantics" row already records the spec resolution and the no-integration verdict (whitepaper Part 3 does not enumerate society economic policies); #228 changes nothing for the whitepaper.
- **Canonical-equation primitive sweep now near-complete**: C2 (MCP), C5 (presence/inward-MCP), C6 (inter-society/outward-MCP), C7 (society-roles), C8 (entity-types), C9 (LCT), C10 (MRH), C11 (ATP/ADP), and now **C12 (R6), C13 (T3/V3), C14 (R7)**. The only primitive-set docs not yet through the C-series instrument are the RDF ontology files (`web4-standard/ontology/*.ttl`) — and the C13/M4 V3-bound divergence shows the audit is already cross-checking spec ⇄ ontology ⇄ SDK ⇄ vectors, so a dedicated `*.ttl` audit may be the natural next/last step.
- **Verdict: no whitepaper integration.** No source-section change; no rebuild. The substantive spec items (T3 continuous-quality formula, R7 status enum, V3-bound open question) are all at the spec/SDK/vector layer the whitepaper does not enumerate. The next genuine integration trigger is unchanged: a registry publish (v0.28.0 → PyPI) or §7.7 reaching `status: Normative`.
- **Surface instinct:** nine consecutive web4 passes (2026-05-15 → 2026-05-25) on SDK/conformance/audit/release-record discipline with zero whitepaper-body integration. The C-series has now swept all eleven non-RDF canonical-equation primitives to internal consistency, and the audit's reach has matured from single-doc structural cleanup (C2) to **cross-surface invariant reconciliation** (C13/M4 spec ⇄ ontology ⇄ SDK ⇄ vector on the V3 bound; C14 spec ⇄ SDK `ActionStatus`). That is exactly the discipline that *earns* a clean whitepaper promotion when the next release surface lands — the spec corpus is making itself safe to cite. The one thing worth flagging upward: the C13/M4 V3-Valuation-bound divergence is the first C-series finding that is a genuine *semantic* design choice (clamp vs unbounded) rather than an editorial defect, and it sits on a canonical-equation primitive — when the operator resolves it, the resolution (especially if "Valuation may exceed 1.0") could eventually warrant a one-line glossary clarification. Not today; hold.

### 2026-05-24: Publisher Maintenance - No-Change Check (C-series audit/remediation runs continue at higher cadence; C8/C9/C10/C11 all audit+remediation same-week; no whitepaper relevance)
- Eight commits since the 2026-05-22 no-change check (993e974), all the same C-series internal-consistency audit/remediation stream that has dominated the web4 stream since 2026-05-15. **None touch `whitepaper/sections/*`.** The cadence has compressed from "audit-then-defer" (2026-05-22 C8) to "audit-and-remediate-same-day" (2026-05-23 C9/C10/C11 all both audited and remediated). All eight commits:
  - **#219 (fff0748, 2026-05-22) — C8 entity-types.md remediation (9 of 10 audit findings):** Resolves the 2026-05-22 C8 audit's HIGH section-numbering corruption and most MEDIUM/LOW findings. 61 insertions / 55 deletions across 2 files. L1 specifically converts "blockchain" pseudocode comment to "immutable ledger," aligned with the audit; no protocol-surface change. Closes the watch item "C8 entity-types.md remediation pending" from the 2026-05-22 pass.
  - **#220+#221 (ad9db39, 2026-05-22) — C7 residual cross-reference defects in society-roles.md:** 2 insertions / 2 deletions. Editorial cleanup of cross-references missed in the original C7 remediation. Same spec, no protocol surface change.
  - **#222 (09f6f2b, 2026-05-23) — C9 LCT-linked-context-token.md internal-consistency audit (8 findings):** Analysis-only artifact at `docs/audits/lct-internal-consistency-2026-05-23.md` (293 insertions, single file). Same instrument as C2/C5/C6/C7/C8. **C9 reaches into the load-bearing primitives now** — LCT is the canonical-equation `LCT` symbol; auditing the LCT spec doc is structurally important, but the audit itself is analysis, not protocol change.
  - **#223 (e2c6bc6, 2026-05-23) — C10 mrh-tensors.md internal-consistency audit (9 findings):** Analysis-only memo (222 insertions). Same C-series instrument. MRH is `web4-standard/core-spec/mrh-tensors.md`, the second load-bearing primitive in the canonical equation; same audit-then-remediate pattern.
  - **#224 (a7d6143, 2026-05-23) — C11 atp-adp-cycle.md internal-consistency audit (9 findings):** Analysis-only memo (308 insertions). Third load-bearing primitive in the same day; the audit instrument is now sweeping the entire canonical-equation primitive set systematically.
  - **#225 (2088a88, 2026-05-23) — C9 LCT remediation (all 8 findings):** Same-day remediation of the C9 audit. 17 insertions / 9 deletions in `LCT-linked-context-token.md`. M4 fix: §3.2 step 5 changed from `issuing_society = null` to omit the field (presence-by-absence over explicit-null convention). Editorial remediation; no wire-shape change.
  - **#226 (a94bc80, 2026-05-23) — C10 mrh-tensors remediation (9 findings):** Same-day remediation. 24 insertions / 20 deletions. Editorial; no protocol surface change.
  - **#227 (3873751, 2026-05-23) — C11 atp-adp-cycle remediation (audit findings):** Same-day remediation. 43 insertions / 3 deletions in `atp-adp-cycle.md`. The largest of today's remediations by line count (net +40); reviewing the diff shows added clarifying prose and normative tightening — no new fields, no wire-format change. ATP/ADP shape unchanged.
- **C-series instrument now sweeps the entire canonical-equation primitive set**: C2 (mcp-protocol/`MCP`), C5 (presence-protocol/inward-MCP), C6 (inter-society-protocol/MCP-as-outward), C7 (society-roles), C8 (entity-types), C9 (LCT), C10 (MRH), C11 (ATP/ADP). The remaining canonical-equation primitives are RDF (`web4-standard/ontology/*.ttl`) and T3/V3 (`t3-v3-tensors.md`). Worth watching whether C12/C13 land next week and complete the sweep — this would be a milestone in the spec-corpus internal-consistency phase.
- **No source section changes since the 2026-05-19 build.** Verified: no commits touch `whitepaper/sections/*` since 42e3e47 (2026-05-19); `build/WEB4_Whitepaper_Complete.md` and `docs/whitepaper-web/WEB4_Whitepaper_Complete.md` both 254811 bytes, dated 2026-05-19, identical, aligned with current source. No rebuild needed.
- **Live whitepaper sections verified clean of canonical-term drift** — grep for the documented wrong expansions across live `sections/*` (excluding archive) returns zero hits.
- Remaining watch items carry forward unchanged: presence-protocol DEFER (inward MCP, still evolving); §7.7 promotion gate (Normative + 2 implementations); inter-society-protocol Part 6/Part 8 body integration (gated on C6 editorial remediation); v0.28.0 → PyPI integration trigger; Sprint 52 conformance gaps (5 operator-architectural decisions). New watch item: **C12/C13 (RDF ontology / T3-V3 tensors) audits expected** if the C-series sweep continues at the established cadence.
- Surface instinct: eight consecutive web4 passes (2026-05-15 → 2026-05-24) on SDK/conformance/audit/release-record discipline with zero whitepaper-body integration. The C-series sweep has reached the load-bearing canonical-equation primitives (LCT/MRH/ATP-ADP all audited+remediated on a single day) and the cadence has compressed from audit-then-defer to audit-and-remediate-same-day. This is the spec corpus earning *complete* internal consistency before the next major release surface; same pattern as the Synchronism side's "discipline of waiting for the canonical registry surface before integrating," just applied to the spec rather than the implementation. The next genuine whitepaper integration trigger is unchanged: a registry publish (v0.28.0 → PyPI) or §7.7 reaching Normative. Hold.

### 2026-05-22: Publisher Maintenance - No-Change Check (C7/C8 audits complete the May-2026 spec audit sweep; no whitepaper relevance)
- Three commits since the 2026-05-21 no-change check (#214, 088a0d6), all the same C-series internal-consistency audit/remediation stream, **none touching `whitepaper/sections/*`**:
  - **#216 (0f61eab, 2026-05-21) — C7 society-roles.md internal-consistency audit** (`docs/audits/society-roles-internal-consistency-2026-05-21.md`): 9 findings (1 HIGH / 4 MEDIUM / 4 LOW), all structural/editorial (Law Oracle omitted from §5.1 solo-founder example, §7 relationship table gaps, private-repo reference, missing RFC 2119 notation, terminology drift). Analysis-only artifact; same instrument as C2/C5/C6. No whitepaper relevance.
  - **#217 (d7ba168, 2026-05-21) — fix(spec): resolve all 9 C7 findings in society-roles.md.** Touches only `web4-standard/core-spec/society-roles.md` (13 insertions / 4 deletions): added Law Oracle to the solo-founder multi-hat example, added mcp-protocol.md + web4-society-authority-law.md rows to the §7 table, removed an incorrect R7-Witness attribution, added RFC 2119 notation, standardized "Diplomat-Federation" → "Federation-Member". All editorial remediation of a spec doc; Society/SocietyRole are already represented in the whitepaper via the v0.2.0 family integration (2026-05-15). No whitepaper integration warranted.
  - **#218 (659fa53, 2026-05-22) — C8 entity-types.md internal-consistency audit** (`docs/audits/entity-types-internal-consistency-2026-05-22.md`): 10 findings (3 HIGH section-numbering corruption — duplicate §3.2, duplicate §5/§5.1, §4.2/§4.3 collision; 4 MEDIUM; 3 LOW). SDK alignment verified as full compliance. **Remediation explicitly deferred to a follow-up session** per the audit-then-remediate pattern. Analysis-only artifact; no whitepaper relevance. New watch item: C8 entity-types.md remediation pending.
- **C7+C8 complete the internal-consistency audit coverage of all new May-2026 specs** (C2: mcp-protocol.md, C5: presence-protocol.md, C6: inter-society-protocol.md, C7: society-roles.md, C8: entity-types.md). The corpus is now in a remediation-of-known-findings phase rather than discovery.
- **No source section changes since the 2026-05-19 build.** Verified: no commits touch `whitepaper/sections/*` since 42e3e47 (2026-05-19); `build/WEB4_Whitepaper_Complete.md` and `docs/whitepaper-web/WEB4_Whitepaper_Complete.md` both 254811 bytes, dated 2026-05-19, identical, aligned with current source. No rebuild needed.
- **Live whitepaper sections verified clean of canonical-term drift** — grep for the documented wrong expansions across live `sections/*` (excluding archive) returns zero hits.
- Remaining watch items carry forward: presence-protocol DEFER (inward MCP, still evolving); §7.7 promotion gate (Normative + 2 implementations); inter-society-protocol Part 6/Part 8 body integration (gated on C6 editorial remediation); v0.28.0 → PyPI integration trigger; Sprint 52 conformance gaps (5 operator-architectural decisions); **C8 entity-types.md remediation pending (new)**.
- Surface instinct: seven consecutive web4 passes (2026-05-15 → 2026-05-22) on SDK/conformance/audit/release-record discipline with zero whitepaper-body integration. The C-series sweep (C2→C8) is the spec corpus systematically earning internal consistency before whitepaper promotion — a healthy, deliberate quiet period, not stagnation. The audit instrument is now turning from *discovery* (each new May spec has now been audited once) toward *remediation* (C7 fixed same-day; C8 deferred). The next genuine integration trigger is unchanged: a registry publish (v0.28.0 → PyPI) or §7.7 reaching Normative. Hold.

### 2026-05-21: Publisher Maintenance - No-Change Check (PUBLISHED.md v0.2.0 watch item RESOLVED; C6 audit no whitepaper relevance)
- One commit since the 2026-05-20 no-change check (71f3a74): **#214 (088a0d6, 2026-05-21) — C6 inter-society-protocol audit + PUBLISHED.md v0.2.0 refresh.** Two parts, neither touching `whitepaper/sections/*`:
  - **PUBLISHED.md v0.1.1 → v0.2.0 refresh — RESOLVES the coordination gap flagged 2026-05-16.** The release record at `docs/proof/PUBLISHED.md` now leads with "Current Release: v0.2.0 (2026-05-15)" and lists all package surfaces (web4-core/web4-trust-core crates.io 0.2.0, PyPI 0.2.0, web4-trust-core npm 0.2.0, web4-trust PyPI 0.2.0, web4-sdk PyPI 0.27.0), with v0.1.1 history preserved. The Executive Summary's dual citation (PUBLISHED.md *and* CHANGELOG.md) was a 2026-05-16 workaround for the stale PUBLISHED.md; **both citations are now accurate** so no Executive Summary edit is needed — the workaround simply stops being a workaround. Watch item closed.
  - **C6 inter-society-protocol.md internal-consistency audit** (`docs/audits/inter-society-protocol-internal-consistency-2026-05-21.md`): 13 findings (3 HIGH / 5 MEDIUM / 5 LOW), all structural/editorial (duplicate §4 numbering, stale v0.1.0 header vs actual v0.1.2, missing mcp-protocol.md from §8 relationship table), **none conceptual**. Same instrument as C2 (mcp-protocol) / C5 (presence-protocol). Per the established pattern, audit artifacts inform spec evolution but are not whitepaper content; this strengthens the case for the deferred Part 6/Part 8 inter-society-protocol integration once the spec's editorial findings are remediated, but is not itself a trigger. No whitepaper relevance today.
- **No source section changes since the 2026-05-19 build.** Verified: no commits touch `whitepaper/sections/*` since 42e3e47 (2026-05-19); `build/WEB4_Whitepaper_Complete.md` and `docs/whitepaper-web/WEB4_Whitepaper_Complete.md` both dated 2026-05-19 (254811 bytes, identical), aligned with current source. No rebuild needed.
- **Live whitepaper sections verified clean of canonical-term drift** — grep for the documented wrong expansions across live `sections/*` (excluding archive) returns zero hits.
- Remaining watch items carry forward: presence-protocol DEFER (inward MCP, still evolving); §7.7 promotion gate (Normative + 2 implementations); inter-society-protocol Part 6/Part 8 body integration (now also gated on C6 editorial remediation); v0.28.0 → PyPI integration trigger; Sprint 52 conformance gaps (5 operator-architectural decisions).
- Surface instinct: the PUBLISHED.md refresh closes the *last* release-record discrepancy from the v0.2.0 family release — the operator picked up a coordination gap the publisher could only flag (PUBLISHED.md is release-record discipline, out of strict whitepaper scope). This validates the flag-and-defer pattern: the publisher surfaces out-of-scope gaps in its report, the owning track resolves them. Six consecutive web4 passes (2026-05-15 → 2026-05-21) on SDK/conformance/audit/release-record discipline with zero whitepaper-body integration — the spec corpus is in a sustained internal-consistency phase. The next genuine integration trigger is unchanged: a registry publish (v0.28.0 → PyPI) or §7.7 reaching Normative. Hold.

### 2026-05-20: Publisher Maintenance - No-Change Check (single format-only SDK commit since 2026-05-19)
- One commit since the 2026-05-19 conformance-stat-calibration pass (1663908): **#213 (b6c243c, 2026-05-19) — `ruff format` drift fix on `test_conformance.py` + `mcp.py`.** Format-only, explicitly "no semantic diff" per the commit; applies the format that makes SESSION_FOCUS.md's "ruff format --check passes with 0 changes" assertion factually true. Quality gates: 2749 passed / 5 xfailed; mypy strict clean. **No whitepaper relevance** — this is SDK-internal formatting, not a protocol-surface change, and the v0.28.0 SDK family is still pre-PyPI-publish (the Executive Summary's `web4-sdk v0.27.0 on PyPI` reference remains correct per the 2026-05-19 watch item).
- **No source section changes since the 2026-05-19 build.** Verified: no commits touch `whitepaper/sections/*` since 1663908; `build/WEB4_Whitepaper_Complete.md` and `docs/whitepaper-web/WEB4_Whitepaper_Complete.md` both dated 2026-05-19 (254811 bytes, identical), aligned with current source. No rebuild needed.
- **Live whitepaper sections verified clean of canonical-term drift** — grep for the documented wrong expansions (Lifecycle-Continuous Trust, Audit Trail Point, Attention Transfer Packet, Alignment Discharge Protocol, Triple Trust, Triple Value) across live `sections/*` (excluding archive) returns zero hits.
- All Pending Updates watch items from prior passes carry forward unchanged (presence-protocol DEFER; §7.7 promotion gate; v0.28.0 → PyPI integration trigger; PUBLISHED.md v0.2.0 refresh coordination gap).
- Surface instinct: the web4 stream has now spent five consecutive maintenance passes (2026-05-15 → 2026-05-20) on SDK/conformance/format discipline with zero whitepaper-body integration — a healthy quiet period where the spec corpus earns internal consistency between published-release surfaces. The next genuine integration trigger remains a registry publish (v0.28.0 → PyPI, surfacing the 376-export / 2749-test counts) or §7.7 reaching `status: Normative` per the promotion-tracking memo. Nothing in the current commit stream moves either gate; correct action is to hold.

### 2026-05-19: Publisher Maintenance - Conformance Stat Calibration (xfail count 8 → 5)
- Four commits since 2026-05-18 no-change check (9ace6d7) reviewed. Three of four are the same C5/conformance discipline stream documented in the 2026-05-18 entry. **One substantive whitepaper-affecting drift identified and corrected**: the Executive Summary's published claim of "8 xfailed gaps" is now 5, post #210.
- **Conformance vector-spec reconciliation (#210, 3f12462, 2026-05-18, landed *after* yesterday's no-change check at 9ace6d7):** Three of the 8 documented xfails turned out to be **vector errors, not architectural gaps** — vectors were authored before Sprints 44/47/48 strengthened the normative spec, and contradicted what the protocol-invariant §10.2 weights / §2.3 Talent-no-decay invariant / §3.3 V3-valuation-as-economic now require. Fixes: t3-002 weighted composite (was unweighted mean); t3-006 talent_unchanged + temperament-recovery (was decay); r7-rep-001 V3 = veracity+validity only (was all 3 dims). Suite: 34 passed / 5 xfailed (was 31 / 8). **Remaining 5 xfails are genuine architectural gaps requiring operator decisions**, not vector errors — sharper framing than the prior catch-all "documented gaps" wording.
  - **Executive Summary correction**: line 41 wording "39 tests; 8 xfailed gaps documented for the next operator architectural-decision pass" → "39 tests; 5 xfailed gaps awaiting operator architectural decisions". Tightens framing in addition to fixing the number. Rebuilt `build/WEB4_Whitepaper_Complete.md` and `docs/whitepaper-web/WEB4_Whitepaper_Complete.md` (3,798 lines, 252K). PDF + web artifacts not rebuilt (single-number prose edit, no structure change).
- **C5 audit G4 — P1-003 fix + P1-004 add (#208, ac9de27, 2026-05-18):** P12: P1-003 ("v1 protocolVersion bumped on connect") previously didn't actually verify protocolVersion — now does a fresh `hestia_connect` and asserts `protocolVersion == 1` in the response. P13: new P1-004 verifies wait-protocol default values (`status == "decided"`, `nextPollMs == null` on v1 query_policy per §3.4.1). Closes the C5 audit's G4 group, completing the G1+G2+G3+G4 remediation cycle. 14 conformance scenarios (was 13). Spec-discipline; no whitepaper integration warranted (presence-protocol remains in DEFER per the §7.8 watch item).
- **Conformance corpus consistency — P1-003 shapeMatchesSchema (#209, b5c9e87, 2026-05-19):** Adds `shapeMatchesSchema` assertion to the P1-003 connect step, bringing the new vector into shape with the corpus convention. Vector-quality discipline; no whitepaper relevance.
- **presence-protocol CHANGELOG stale-section resolution (#211, 40e6228, 2026-05-19):** CHANGELOG hygiene — resolves a "Upcoming (planned)" v1 section that became stale after v1 actually shipped (the planned items moved to "Released" but the planning header was left behind). Doc-quality fix; no whitepaper relevance.
- **Implementation-SDK v0.28.0 housekeeping (Sprint 55 T1, #212, 11d79d2, 2026-05-19 — landed during this maintenance pass):** Version bump consolidating cross-society MCP types (PR #195/#199; 369→376 exports), the #210 xfail resolution, and the `_pkg_version` rename fix. 2749 tests (2744 passed, 5 xfailed). **Same internal-SDK pattern as Sprint 53 T1 #191 (v0.27.0 housekeeping)** — not a published-registry surface change. Per 2026-04-29 / 2026-05-15 precedent, Executive Summary's `web4-sdk v0.27.0 on PyPI` reference is correct until v0.28.0 ships to PyPI. No Executive Summary version bump warranted. Watch item: integrate v0.28.0 + the 376-export / 2749-test counts when next PyPI publish lands.
- **No source/artifact rebuild needed for other sections** (build now aligned with 2026-05-19 source state from this maintenance pass).
- Surface instinct: today's #210 is methodologically interesting — it surfaces that **conformance vectors can be wrong before the spec is**. When the spec evolves (Sprints 44/47/48 strengthened invariants) but vectors lag, the resulting "xfails" look architectural when they are actually staleness. The 3-of-8 reduction is therefore not "we fixed 3 gaps" but "3 of 8 weren't gaps in the first place — they were anachronistic vectors." The whitepaper's xfail count is the operator-facing number, and the framing in line 41 conflated the two failure modes — vector errors and architectural gaps. Sharpening the wording matters more than the number bump: "5 xfailed gaps awaiting operator architectural decisions" makes explicit that the *remaining* ones are operator-decision-bound. Worth carrying this disambiguation forward — when the Sprint 52 conformance-gap memo lands its next round of resolutions, the same care applies.

### 2026-05-18: Publisher Maintenance - No-Change Check (audit-driven spec discipline; presence-protocol DEFER continues; §7.7 promotion-gate stub identifies long-pole)
- Eight commits since 2026-05-17 no-change check (1db7119) reviewed. None warrant whitepaper integration today; all are audit-driven internal-consistency clean-up of two specs already on the watch list (`presence-protocol.md` evolving / `mcp-protocol.md` §7.7 WIP). Pattern is healthy spec discipline closing audit findings before the spec stabilizes for whitepaper integration.
- **C5 presence-protocol internal-consistency audit (#204, 47ef781, 2026-05-17):** Analysis-only memo at `docs/audits/presence-protocol-internal-consistency-2026-05-17.md` — same instrument as the 2026-05-15 C2 mcp-protocol audit. 2 HIGH / 4 MEDIUM / 3 LOW. Headline: spec's own discipline thesis is asymmetrically held — normative input-casing rule contradicted the schemas the spec itself binds. No spec/schema edits in this commit. Audit-only artifact; no whitepaper relevance directly. Material is the spec-fix stream it triggered (next two commits).
- **C5-G1 casing-authority + C5-G3 localized staleness (#206, a67e9c9, 2026-05-17):** Resolves 7 audit findings (P1/P3/P6 G1 + P4/P5/P7/P9 G3) in `presence-protocol.md`. G1: §3 rewritten as surface-split casing rule (input snake / output+§5-type camel / §4 resource snake) anchored to the bound JSON Schemas; §7 gains explicit Precedence clause (Schemas DIRECTORY + vectors normative over prose). G3: protocolVersion example pinned to 1 (was stale 0), PolicyResult type-catalog entry extended with status/nextPollMs/enforced, link text + error-list caveat fixes. **Zero wire-shape change — only prose brought in line with existing schemas.** Reinforces the DEFER rationale: spec is still earning internal consistency.
- **C5-G2 discipline honesty (#207, 728d3ff, 2026-05-18):** Resolves 4 findings (P2/P8/P10/P11) in `presence-protocol.md`. P2 HIGH: `synthetic` field marked as not-yet-conformed in §3.1 and added to §8 drift table (no v1 `hestia_connect` schema exists as structural prerequisite); added to §9 "Still pending." P8 LOW: §2 bump rule gains explicit back-compat exception clause (optional additive fields do NOT trigger version bump). P10 MED: §9 restructured into "Completed in v1" and "Still pending" subsections. P11 MED: §8 drift row 3 (error codes never emitted) marked resolved in v1. **Completes the G1+G2 "load-bearing pair" from the C5 audit's cross-cutting observation.** Spec is now internally consistent at v1 — but this is the *condition* for integration, not yet the trigger. presence-protocol remains in DEFER pending Hestia/Hardbound registry-published release.
- **mcp-protocol C2 audit remediation: HIGH §7.4↔§7.7 (F2/F3/F4/F12) (#200, 854df2c, 2026-05-17):** Resolves 4 HIGH findings from the 2026-05-15 C2 mcp-protocol audit. F2: §7.4 MUST for `exchange_rate` no longer depends on non-dependable §7.7 (conditional MUST on `atp_settlement` presence). F3: §7.4 example replaced (scalar bilateral model that §7.7.1 explicitly rejects → referent-grounded schema). F4: `atp_settlement` now carries caller/responder currencies + amounts + referent object + exchange_agreement_ref. F12: §7.7 conformance status disambiguated per-subsection (§7.7.1/§7.7.4 Normative, §7.7.2/§7.7.3/§7.7.7 Normative-draft, §7.7.5/§7.7.6 Informative). **§7.7 is converging toward stability, but not stable.** The whitepaper "Pending Updates" entry "MCP-as-inter-society-protocol per canonical equation" already marks §7.7 as Partially Resolved — that classification holds.
- **mcp-protocol C2 audit remediation: MEDIUM F1/F5/F15 (#201, 53642df, 2026-05-17):** Normative-clarification fixes in `mcp-protocol.md`. Same spec-fix stream as #200; mechanics-level clean-up, no architectural change.
- **mcp-protocol C2 audit remediation: LOW F14/F16 (#203, 79ca926, 2026-05-17):** Minor presentation/example fixes in `mcp-protocol.md`. Closes the C2 audit's LOW band.
- **§7.7 promotion tracking stub (Sprint 54 C3, #202, 41e1a80, 2026-05-17):** Memo at `docs/audits/s7.7-promotion-tracking-2026-05-16.md` capturing what must be true to promote §7.7 (Referent-Grounded Exchange Rate Negotiation) from v0.1.0-draft to v0.1.0-normative. **3 hard prerequisites** (PR #200 merge ✓ achieved today; F11 signing authority; F8 verify), **5 open design questions** requiring operator decisions, and **implementation-evidence criteria** (2 implementations + interop + error catalogue). Memo identifies "two implementations" requirement as the real long-pole and recommends the presence-protocol discipline pattern (spec + schemas + conformance vectors as atomic unit). **This is a publisher-relevant artifact**: it formalizes the §7.7 promotion gate so the whitepaper integration trigger is now explicit — `§7.7 status: Normative` + 2 implementations is the threshold for upgrading "Partially Resolved" → "Resolved" on the Pending Updates row. Watch item refined accordingly.
- **Cross-society types SDK test coverage (#199, 39fb411, 2026-05-17):** Test-only coverage for the cross-society types that landed in PR #195. SDK test infrastructure; no protocol-surface change.
- **Live whitepaper sections verified clean of canonical-term drift** — only archive files (`sections/*/archive/*`) contain historical drift expansions, intentionally preserved per 2026-04-29 4a0dce7 cleanup. No live-section corrections needed.
- **No content changes; no source/artifact rebuild needed** (build remains aligned with 2026-05-16 source state from 5ccbe46 — confirmed via `build/WEB4_Whitepaper_Complete.md` mtime 2026-05-16, no source changes in `whitepaper/sections/*` since).
- Surface instinct: today's eight-commit stream is the **first full audit-remediation cycle** executed since the audit instruments themselves stabilized (C2 instrument 2026-05-15 mcp-protocol → C5 instrument 2026-05-17 presence-protocol). The pattern is: dedicated audit PR opens the findings ledger → severity-banded remediation PRs close it (HIGH first, then MEDIUM, then LOW, with G-grouped cross-cutting fixes interleaved). This is **a publisher-readable signal**: when a spec runs the C-audit cycle and the discipline-honesty group lands (§9 "Still pending" + drift-table cross-reference), the spec is structurally ready for review-stage scrutiny even if the wire surface is still earning maturity. Worth foregrounding when next major integration pass writes the §7.7 → Part 7 expansion: the audit-cycle metadata (which audit instrument, which severity bands closed, which findings deferred) becomes part of the integration justification, not just an internal-discipline artifact. The §7.7 promotion-tracking memo (#202) is the first instance of this — it makes the integration gate **operator-checklist-shaped** rather than a one-line "watch" entry. Recommend evolving the whitepaper "Pending Updates" table to cite promotion-tracking memos directly when they exist (rather than re-deriving the gate logic per maintenance pass).

### 2026-05-17: Publisher Maintenance - No-Change Check (presence-protocol genesis, conformance discipline; design still evolving)
- Seven commits since 2026-05-16 v0.2.0 family release integration (5ccbe46) reviewed. None warrant whitepaper integration today; the day's work introduces a new inward-MCP surface (presence-protocol) but the spec is evolving rapidly (v0 → v1 → v1+wait → v1+synthetic-flag in <24h).
- **presence-protocol v0 (d786770, 2026-05-16):** New core spec at `web4-standard/core-spec/presence-protocol.md` capturing the **inward** MCP surface — the protocol an agentic orchestrator (SAGE, Claude Code, Cursor, custom agents) speaks to the **presence layer** of a Web4 entity (Hestia software-bound / Hardbound hardware-bound). Distinct from `mcp-protocol.md` which is the *outward* society-to-society MCP. Tools (8): `hestia_connect`, `hestia_begin_action`, `hestia_record_outcome`, `hestia_query_policy`, `hestia_vault_get`, `hestia_vault_set`, `hestia_query_history`, `hestia_request_witness`. Resources (6) + Error codes (10). Substantive new architectural surface — the whitepaper currently documents only the outward MCP (Part 7 §7.3-§7.6 via v0.2.0 integration). Per inclusion criteria ("New protocol element implemented in code" → high priority) the surface is real, but per "Design still evolving" (4 versions of the spec in 1 day) DEFER. Added to watch list.
- **presence-protocol v1 — policy engine (e64eb4c, 2026-05-16):** Same-day bump to v1. `hestia_query_policy` returns real decisions (rule engine ported from `claude-code/plugins/web4-governance/`). PolicyResult shape extends with `ruleId` / `ruleName` / `constraints`. Vault schema v1 → v2 (`policy` section alongside `entries`). Four built-in presets (`permissive`/`safety`/`strict`/`audit-only`). New `hestia policy {show|set|test}` CLI. `vault_set` events now appended to witness chain (credential name only, never the secret). Implementations bumped: Hestia daemon 0.0.2→0.0.3, TS SDK 0.0.2→0.0.3, Rust/Python SDKs local-only, `hardbound-pak` 0.0.1→0.0.2. **First real test of the protocol-discipline pattern** (CHANGELOG + spec + schemas + conformance vectors + SDK constants all bumped in one PR). Same DEFER reasoning as v0.
- **presence-protocol v1 wait protocol (05338b0, 2026-05-16):** Back-compat extension on `hestia_query_policy` output: `status: "decided" | "evaluating"` + `nextPollMs: int | null`. Allows future LLM-backed policy engines to say "still thinking, come back in N ms." v1 daemons with sync rule engines always return `"decided"` / `null`. Forward-compatible addition (no v1.1 split). Increases the "still evolving" signal. DEFER.
- **presence-protocol §3.1 synthetic flag (66d7c3b, 2026-05-17):** Optional `synthetic: bool` flag on action records, distinguishing actions generated by the entity's cognition from actions injected for simulation/testing. Minor spec refinement; reinforces that the spec is still in active shape-finding. DEFER.
- **Sprint 54 C4 vector-freshness check process (#197, 4b3dd89, 2026-05-16):** Adds `VECTOR-FRESHNESS.md` to `web4-standard/testing/conformance/` documenting the staleness hazard when conformance vectors lag behind protocol changes. Includes manual pre-merge checklist, CI-hook design (field-set diff heuristic, design only no impl), vector-provenance metadata convention. README.md links the checklist under "Contributing Vectors." Conformance/CI discipline; whitepaper does not document conformance-vector authoring process. Operations-level artifact, not protocol primitive. No integration warranted.
- **Conformance README + P0-007 self-contained (0405999, 2026-05-16):** Test harness READMEs + making P0-007 self-contained (per the protocol-discipline pattern). Conformance scaffolding; not protocol-primitive content.
- **Kimi 2.6 review notes — web4 + hestia track (2327f46, 2026-05-16):** Forum artifact at `forum/kimi_2_6_web4_hestia.md`. External-model review of web4 + Hestia spec corpus. Per established pattern (multiple prior Kimi rounds across 2026-05-13/14/15), forum artifacts inform spec evolution but are not whitepaper content themselves. No integration warranted.
- **No content changes; no source/artifact rebuild needed (build remains aligned with 2026-05-16 source state from 5ccbe46).**
- Surface instinct: the v0.2.0 release (2026-05-15) closed the outward-MCP integration gap, and within ~24 hours the project has surfaced a **second MCP surface** (inward presence-protocol) with its own version-disciplined release cadence and its own implementation pair (Hestia / Hardbound). This is structurally important — the canonical equation's `MCP` term has now bifurcated in practice into **outward MCP** (society ↔ society, `mcp-protocol.md`) and **inward MCP** (presence ↔ cognition, `presence-protocol.md`). The whitepaper's current narrative (Part 7 §7) treats MCP as a single surface; once presence-protocol stabilizes past its rapid v0→v1 churn and the Hestia daemon ships a registry-published release (currently 0.0.3 pre-1.0), this becomes a substantive Part 7 expansion — likely a new §7.7 or §7.8 covering the inward surface, paralleling the outward §7.3-§7.6 structure. Worth tracking how the "inward vs outward MCP" framing propagates back into `mcp-protocol.md` itself.

### 2026-05-16: Publisher Maintenance - v0.2.0 Family Release Integration

- **Trigger**: 2026-05-15 published the v0.2.0 package family (commits beb2a9b + 1fb6c90), closing the publish-vs-main gap that had been a "watch item" since 2026-05-13. Per 2026-04-29 precedent, Executive Summary "Currently Available" leads with published packages — so the release-trigger-met watch items integrate now.
- **Executive Summary** (`sections/00-executive-summary/index.md`):
  - Status calibration paragraph: date 2026-04-29 → 2026-05-15; v0.1.1 → v0.2.0; added crates.io + PyPI + npm surface; added `web4-sdk` rename context (PyPI name collision with unrelated dormant package); noted inter-society protocol + society-roles + MCP §7.3-§7.6 + 35-vector conformance suite as the substantive content of the gap closure.
  - "Currently Available" bullet for `web4-core` / `web4-trust-core`: v0.1.1 → v0.2.0; added v0.2.0-new types (Society / SocietyRole / RoleAssignment, ATPAccount with conservation-invariant transfer + society-configurable fees + max_balance, R7Action with reputation as first-class output); added `npm install web4-trust-core` install line (first npm publish, WASM, ~337KB); release record cite now points to both `docs/proof/PUBLISHED.md` and the new top-level `CHANGELOG.md`.
  - Added new "Currently Available" bullet for **`web4-sdk` v0.27.0** documenting the rename (was `web4`), cross-society types (`CrossSocietyContext`, `ReputationEnvelope`, `MCPContextResource`), inter-society protocol integration, 35-vector conformance runner with 39 tests + 8 xfailed gaps, 23 modules + 369 exports + 2,709 tests, and the unchanged `from web4 import ...` import path.
- **Conclusion** (`sections/11-conclusion/index.md`):
  - Status note: 2026-04-29 → 2026-05-15; mirrored Executive Summary version bumps and v0.2.0-new types.
  - Findings table: web4-core row updated to v0.2.0 + Society/Role/ATP/R7 types; web4-trust-core row updated to v0.2.0 + npm WASM surface (new column entry); new row for `web4-sdk` v0.27.0; Reference-Python-SDK row test count updated 2,627 → 2,709 and re-pointed at the now-public PyPI package.
- **No other section changes warranted**:
  - Body sections covering LCT, T3/V3, R6/R7, society/role, ATP/ADP, MRH already describe the relevant primitives at the right level of abstraction; v0.2.0 ships shipped-spec versions of these, not new concepts.
  - "Emerging Implementation" subsection of Executive Summary (Hardbound CLI governance stack: R7, ACP, Sybil-resistance, multi-device binding, etc.) was untouched — those features have their own release cadence independent of `web4-core`.
  - Body sections containing analogies (Linux/GNU/distribution, biological membrane) were untouched per 7a96cbc framing-vs-finding discipline (the Conclusion's Findings/Framings table marks them as framings explicitly).
- **Resolved watch items** (from Pending Updates table):
  - "web4-core SDK Society/Role/ATP/R6 types" — RESOLVED, integrated into Executive Summary + Conclusion via v0.2.0
  - "WASM bindings for Society/Role/ATP/R7 primitives" — RESOLVED, integrated as the npm install row + Conclusion table entry
  - "inter-society-protocol.md" — PARTIALLY RESOLVED (shipped in v0.2.0 SDK; whitepaper-body integration deferred — Part 6 / Part 8 supplement is a future pass)
  - "MCP-as-inter-society-protocol per canonical equation" — PARTIALLY RESOLVED (MCP §7.3-§7.6 shipped in v0.2.0 spec corpus; §7.7 referent-grounded exchange-rate negotiation remains WIP)
- **Flagged but not fixed in this pass**: `docs/proof/PUBLISHED.md` is **still describing v0.1.1**. The Executive Summary now cites `docs/proof/PUBLISHED.md` *and* the top-level `CHANGELOG.md` so the citation is not hanging (CHANGELOG.md is current), but PUBLISHED.md itself wants a v0.2.0 refresh by whoever owns the release-record discipline (the v0.2.0 release commits beb2a9b + 1fb6c90 did not touch it). This is out of strict whitepaper scope but recorded here as a coordination gap.
- **Build**: Rebuilt md + pdf + web artifacts; copies in `docs/whitepaper-web/` synced.
- Surface instinct: the "publish-vs-implement gap" observation from the 2026-05-15 entry has now resolved through a single release event, which validates the discipline of waiting for the canonical registry surface before integrating. The pattern "watch (next release) → integrate on release" is now well-exercised twice (2026-04-29 and 2026-05-16). The next analogous trigger would be Hardbound CLI features getting their own packaged release surface — currently they live inside the Hardbound CLI binary, not as separately installable libraries. Worth watching whether the package-family pattern propagates upward to the governance-stack features.

### 2026-05-15: Publisher Maintenance - No-Change Check (implementation-SDK release + conformance gap memo; no published-release surface change)
- Thirteen commits since 2026-05-14 no-change check (30c4711) reviewed. None warrant whitepaper integration today; the day's work accumulates implementation evidence around watch items already noted, but the published-release surface on crates.io / PyPI is unchanged.
- **`web4-standard/implementation/sdk` v0.27.0 (Sprint 53 T1, #191, d155b6a, 2026-05-15):** Internal Python implementation-SDK version bump consolidating Sprints 41-42, 50-52: Society Roles module (`SocietyRole`, `RoleAssignment`, `bootstrap_society_roles`), `validate_minimum_viable()` for Rust parity, `Constraint` aligned with Rust (threshold + hard), conformance test runner (35 vectors, 39 tests, 8 xfailed). 2709 tests pass, 369 exports, 23 modules. **Distinct from `web4-core` / `web4-trust` published packages on crates.io / PyPI** (still v0.1.1 per `docs/proof/PUBLISHED.md`). Per 2026-04-29 precedent, Executive Summary "Currently Available" tracks published-registry releases, not internal SDK versioning. No Executive Summary change warranted. Watch item for SDK Society/Role/ATP/R7 types remains "next published release" — implementation evidence is now stronger (Python SDK + WASM bindings + conformance vectors), but the trigger is registry publish.
- **Sprint 52 conformance-gap consolidation memo (#190, c09d0d2, 2026-05-15):** Catalogues 8 Sprint 52 xfails. 3 of 8 restate Sprint 47 T3/V3 audit findings (Talent decay CRITICAL, weighted composite HIGH, update formula HIGH). 5 of 8 (62.5%) are **NEW surface gaps not in any prior audit**: constraint enforcement, V3 valuation as behavioral vs economic, role-004 assigner predicate, fed-001 child- vs parent-initiated federation, sub-dimension rollup. Counter-finding: ATP suite is 11/11 exact pass — Sprint 49 audit's "ATP is best-aligned pair" claim now operationally confirmed. Per inclusion criteria ("Code not yet written / Design still evolving"), no whitepaper integration warranted; this is a pre-spec gap analysis analogous to the Sprint 43 memo. Added as watch item.
- **WASM bindings for Society/SocietyRole/RoleAssignment/ATPAccount/R7Action (a2727b4, 2026-05-14):** Browser-side bindings for the same types added to `web4-core` 2026-05-13. Implementation evidence strengthening — but the underlying watch item ("integrate into Currently Available when next published release ships") is unchanged. WASM is a third surface (Rust + Python + browser) for the same primitives, all converging on a future release.
- **Sprint 50 T1 Python SDK Society/Role (#185, 6a2d067, 2026-05-14):** `SocietyRole` enum + `RoleAssignment` dataclass + `bootstrap_society_roles()` in the implementation SDK. Cross-language parity work; same watch-item bucket as the 2026-05-13 web4-core additions.
- **Sprint 51 T1 Constraint alignment (#187, 766611e, 2026-05-14):** `Constraint` dataclass replaces `value: Any` with `threshold: float` + `hard: bool`. Cross-language parity refinement. Spec-level; whitepaper does not enumerate `Constraint` field surface.
- **Sprint 52 T1 conformance pytest wiring (#189, 381904a, 2026-05-14):** Runs the 35 conformance vectors in pytest. Test infrastructure; no protocol change.
- **Forum/README polish (e457b25 + 0a80c37 + 679c1af, 2026-05-14):** Nova (GPT) cross-model review; README Linux/GNU framing replacing TCP/IP; Kimi 2.6 fourth-pass review (8.5/10 unchanged). Forum artifacts + README-level positioning; whitepaper Executive Summary has its own calibrated framing. No change.
- **AGENTS.md GitNexus stat refresh (uncommitted at this writing):** Stats line auto-updated to 123794/182949/230 to match CLAUDE.md (refreshed in 5ceddbb 2026-05-14). Housekeeping, not publisher work. AGENTS.md does not yet carry the `<!-- gitnexus:keep -->` marker that 5ceddbb added to CLAUDE.md; future indexer runs may clobber the block content until upstream publishes the keep-marker-aware release. Out of scope for this maintenance pass.
- **No content changes; no source/artifact rebuild needed (build remains aligned with 2026-04-29 source state from e990039).**
- Surface instinct: the publish-vs-implement gap is now the largest it has been since the v0.1.0 release. Society/Role/ATP/R7 types exist in three implementation surfaces (Rust, Python, WASM) with conformance vectors and a published-gap memo identifying 5 new architectural decisions — but the canonical PyPI/crates.io artifacts (`web4-core`, `web4-trust`) remain v0.1.1 from 2026-04-28. Two possibilities: (a) v0.2.0 cuts soon and the Executive Summary needs a substantive rewrite around the new primitives + their gap memo's open decisions, or (b) the gap memo's 5 operator-architectural-decision items block release and the gap-vs-publish window widens further. Worth noting that "implementation maturity ≠ release readiness" is itself becoming a publishable observation about the project's discipline.

### 2026-05-14: Publisher Maintenance - No-Change Check (SDK additions in main, spec evolution, audit watch resolved)
- Nineteen commits since 2026-05-13 no-change check reviewed against inclusion criteria. None warrant whitepaper integration today; multiple watch items resolved or added.
- **web4-core SDK additions in main, not yet published (8243895 + 8857ab0, 2026-05-13):** `web4-core` now has first-class `Society`/`Role` types (per `inter-society-protocol.md` + `society-roles.md`; 7 base-mandatory roles) and `ATPAccount` / `R6Action` / `R7Action` types (210 LOC + 230 LOC respectively; conservation-invariant transfer with society-configurable fees and max_balance; R7 extends R6 with reputation as first-class output). Per inclusion criteria ("New protocol element implemented in code" → high priority): code exists and is tested in `cargo test`, but it is **in the `main` branch only — not yet in any published v0.1.x release on crates.io / PyPI**. Following the 2026-04-29 precedent (Executive Summary "Currently Available" leads with published packages), no Executive Summary update warranted until next release. Watch item: integrate into "Currently Available" when v0.2.0 (or similar) ships. Spec coverage for these primitives already exists in the whitepaper glossary, Part 3 (ATP/ADP), Part 6 (R6/R7), Part 8 (society/role); SDK availability is the next maturity step, not new whitepaper content.
- **Sprint 46 T1 CI canonicity clarification (#181, 8e6d1ee, 2026-05-13):** Added §4.4 to `multi-device-lct-binding.md` documenting that `constellation_coherence` is the canonical metric (T3 tensor extension, witness density); "CI" / "Coherence Index" and numeric multipliers (e.g., 1.4×) are **simulation parameters, not protocol primitives**. **This resolves Sprint 43 SPEC GAP #10 watch item "CI/coherence as cost multiplier"** by clarifying the term is not a protocol primitive in the first place. No whitepaper integration warranted — the whitepaper does not currently use "CI" terminology. Watch item removed from pending list.
- **Sprint 47 T1 cross-language T3/V3 alignment audit (#182, cdf3711, 2026-05-13):** Audit document at `docs/audits/cross-language-t3v3-alignment-2026-05-13.md`. Implementation-alignment artifact, not protocol change.
- **Sprint 48 T1 Parameter governance index (#183, 824acd3, 2026-05-13):** Updates `t3-v3-tensors.md` with parameter governance index. Spec-level refinement; Part 3 narrative in whitepaper does not enumerate parameter governance — no whitepaper integration warranted. Watch item if/when whitepaper Part 3.2 is restructured.
- **inter-society-protocol.md genesis + iterations v0.1.1/v0.1.2 (17d6471 + f4803dd + 2f4454f, 2026-05-13):** New core spec covering genesis, first-contact, federation, secession; v0.1.1 incorporates Kimi round-3 sharpenings; v0.1.2 fixes R6-only to R6/R7 throughout. **Substantive new spec**, but still evolving (3 versions in one day). Per "Design still evolving" exclusion, DEFER whitepaper integration until spec stabilizes — likely worth a Part 6 / Part 8 supplement once v0.2 or later ships. Added to watch list.
- **mcp-protocol.md v0.1.3 — MCP IS the inter-society protocol (7c7c43c, 2026-05-13):** Significant equation-level claim: MCP is identified as the inter-society protocol per the canonical Web4 equation. Also touches README.md and STATUS.md. **WIP §7.7 (caa3878, 2026-05-14): referent-grounded exchange rate negotiation** — explicitly marked WIP. Per "Design still evolving" exclusion, DEFER. Added to watch list.
- **Kimi 2.6 cross-model reviews — three rounds + two post-amendment passes (0b73b92 + cd85ef1 + 31ce382):** External-model peer review of the web4 spec corpus. Forum artifacts, not whitepaper content. No integration warranted.
- **Worker session #184 (323b2cb, 2026-05-14):** Autonomous worker session producing `docs/audits/cross-language-society-role-atp-r6-alignment-2026-05-14.md` + SPRINT.md updates. Implementation-alignment artifact, not protocol change.
- **README + STATUS architectural-shape update (193607f):** README-level positioning change ("surface architectural shape upfront; honest qualifiers"). Whitepaper Executive Summary already has its own calibrated framing (2026-04-29 a5dafa6). No change.
- **society-roles.md + entity-types.md three-tier role taxonomy (05911c3):** Cross-reference between spec docs establishing a three-tier role taxonomy. Spec-level refinement; whitepaper Part 8 already discusses entity types and roles in narrative form. Could integrate as a Part 8 tightening once the SDK Society/Role types ship in a release; not warranted today.
- **Hardbound references update (6fdbb65):** README-level update on plugin bridge architecture and current status.
- **No content changes; no source/artifact rebuild needed (build remains aligned with 2026-04-29 source state from e990039).**
- Surface instinct: this is the highest-activity day for web4 spec/SDK work since the 2026-04-28 v0.1.0 release. The pattern is "spec stabilization through external review" (Kimi 2.6 three-round critique → spec amendments → SDK implementation in main → next release window). The whitepaper's role is to lag the spec, not lead it. Integration is correctly deferred until v0.2.0 ships and the inter-society-protocol stabilizes — but if both land in the next pass, the Executive Summary's "Currently Available" + "Emerging Implementation" sections will need a substantive rewrite, not a one-line addition.

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
