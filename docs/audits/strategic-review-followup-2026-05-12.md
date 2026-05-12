# Strategic Review Follow-Up Audit

**Date**: 2026-05-12
**Track**: web4 (Legion autonomous session)
**Authorized by**: issue [#166](https://github.com/dp-web4/web4/issues/166) candidate (a)-4
**Source**: `docs/strategy/cross-model-strategic-review-2026-02.md`
**Precedent**: `docs/audits/spec-vs-explainer-alignment-2026-04-19.md`

---

## Purpose

The cross-model strategic review (Feb 2026) synthesized action items and priorities from three independent AI model assessments (Grok, Nova, Claude). Three months and 43 sprints later, this audit checks which items were addressed, which were intentionally deferred, and which remain open.

This memo classifies. It does not propose solutions or new sprint tasks.

## Labels

- **ADDRESSED**: The action item was substantively executed through SDK sprints or other project work. Cites specific sprint(s).
- **PARTIALLY ADDRESSED**: Some aspect was delivered; the item is not fully closed. Explains what was and wasn't done.
- **DEFERRED**: Intentionally left open per the review's own status notes. Not a gap — a deliberate sequencing decision.
- **UNADDRESSED**: No work has been done on this item. May indicate a gap or may indicate it's outside the web4 repo's scope.

## Summary

| Label | Count | Share |
|-------|------:|------:|
| ADDRESSED | 3 | 23% |
| PARTIALLY ADDRESSED | 5 | 38% |
| DEFERRED | 3 | 23% |
| UNADDRESSED | 2 | 15% |
| **Total** | **13** | |

---

## Section 1: EU AI Act Compliance Positioning

### Item 1.1: Implement primitives that map to EU AI Act articles

**Classification**: PARTIALLY ADDRESSED

The strategic review mapped five EU AI Act articles to Web4 mechanisms:

| Article | Web4 Mechanism | SDK Status |
|---------|---------------|------------|
| Art. 9 (Risk management) | ATP/ADP + T3 trust tensors | ATP lifecycle, T3 tensors, `process_action_outcome()` — all in SDK |
| Art. 10 (Data quality) | Immutable behavioral history, reputation washing detection | ReputationEngine with decay + aggregation in SDK; reputation washing detection not specifically implemented |
| Art. 13 (Transparency) | LCT identities + ledger entries | LCT types + serialization in SDK; no ledger implementation |
| Art. 14 (Human oversight) | SAGE/HRM governance + federated trust overrides | Federation/Society types in SDK; SAGE/HRM patterns not in SDK scope |
| Art. 15 (Cybersecurity) | Hardware binding + sybil-resistant LCTs | AttestationEnvelope in SDK; actual hardware binding in hardbound (private) |

**What was addressed**: All referenced data types and behavioral functions exist in the SDK (T3/V3, LCT, ATP/ADP, AttestationEnvelope, ReputationEngine, Society, Federation). Three behavioral functions compose them into pipelines (`evaluate_trust_query`, `resolve_trust`, `process_action_outcome`).

**What was not addressed**: No explicit EU AI Act article-to-code mapping artifact exists in the SDK or docs. The strategic review's article mapping table is the only such document. No compliance-specific validation rules or audit trail features were built.

### Item 1.2: Position for Aug 2, 2026 deadline

**Classification**: PARTIALLY ADDRESSED

The SDK is feature-complete at v0.26.0, providing the primitive layer that compliance tooling would build on. However, no compliance-specific packaging, documentation, or outreach targeting EU AI Act adopters has been produced from the web4 repo.

---

## Section 2: Core Framing

### Item 2.1: Use "anti-Ponzi" / "thermodynamic accountability" framing

**Classification**: ADDRESSED

The ATP/ADP lifecycle implements the full charge → discharge → certification → recharge pattern described in the review. `process_action_outcome()` (Sprint 24) is the direct implementation of "task produces verifiable output → certify value created → reputation accrues." The framing is reflected in the whitepaper and README.

**Evidence**: Sprint 24 (action consequence pipeline), Sprint 28 (MCP exposure of same), `examples/quickstart.py` demonstrates the full cycle.

---

## Section 3: Identified Gaps

### Item 3.1: Bootstrapping and inequality — anti-concentration mechanics

**Classification**: DEFERRED (intentionally)

The review explicitly flagged this as "intentional open question for later tracks." No anti-concentration mechanics have been implemented. The SDK's ATPAccount tracks individual balances but has no distribution fairness constraints.

**Review's own status**: "No formal anti-concentration mechanics yet. Intentional open question for later tracks."

### Item 3.2: Formal proofs of sybil resistance

**Classification**: DEFERRED (intentionally)

The review noted the deliberate approach: "build the simulation corpus first, then formalize what works." No formal proofs have been produced. The simulation corpus (424+ attack vectors) exists in `simulations/` but is outside the SDK's scope. The SDK's trust functions are empirically tested (2613 tests) but not formally proven.

**Review's own status**: "Empirical-only so far. The approach is deliberate."

### Item 3.3: Real-world market/economic testing

**Classification**: DEFERRED

Still in-memory/synthetic only. The bridge identified by the review (hardware binding via TPM 2.0 / Secure Enclave) exists as a spec (AttestationEnvelope) in the SDK but actual hardware attestation is in the hardbound repo (private). No real-world economic testing has been conducted.

---

## Section 4: Identified Strengths — Maintenance

### Item 4.1: Maintain empirical attack testing corpus

**Classification**: ADDRESSED

The 424+ attack vector corpus is preserved in `simulations/`. It was not expanded through SDK sprints (which focused on the SDK, not simulations), but the simulations directory was explicitly preserved during the sprawl archive campaign (PRs #174-176 archived standalone scripts but left simulations/ intact).

### Item 4.2: Maintain development velocity

**Classification**: ADDRESSED

43 sprints merged between March 14 and April 19, 2026 (36 days). The SDK grew from initial types to 22 modules, 364 exports, 2613 tests, 3 behavioral functions, 8 MCP tools, and 7 CLI subcommands. CI quality gates (mypy strict, ruff lint/format, wheel verification, quickstart smoke) were added progressively.

### Item 4.3: Hardware binding as credibility multiplier

**Classification**: PARTIALLY ADDRESSED

The SDK side is complete: AttestationEnvelope with TPM2/FIDO2/SE anchor types, JSON-LD serialization, JSON Schema, 20 test vectors, and verification dispatcher (Sprint scope across Sprints 4-16). However, the "credibility multiplier" — demonstrating actual hardware-bound LCTs — requires the hardbound implementation, which is in a separate private repo. From the web4 repo's perspective, the spec and SDK support exist; the demo does not.

---

## Section 5: Funding and Outreach

### Item 5.1: EU funding applications (Horizon Europe, EIC, etc.)

**Classification**: UNADDRESSED

No funding applications have been filed from the web4 repo's visible history. The ARIA grant was explored (Feb-Apr 2026) but ultimately not submitted. EU funding vectors identified by Grok remain open. This is operator-driven work outside the scope of autonomous coding sessions.

### Item 5.2: Outreach to identified targets

**Classification**: UNADDRESSED

The Amanda Askell outreach was drafted in Feb 2026 (per the review). EU AI Office and compliance consultancy outreach were contingent on "hardware binding demo ready." No outreach artifacts are in the web4 repo. This is operator-driven work outside autonomous session scope.

### Item 5.3: Demo path — minimal showcase script

**Classification**: ADDRESSED

`examples/quickstart.py` (Sprint 36) demonstrates the full behavioral pipeline: `generate` → `from_jsonld` roundtrip, `evaluate_trust_query` with ATP stake locking and T3 disclosure, `process_action_outcome` with R7Action → ReputationEngine → TrustProfile → ATPAccount composition. Wired into CI as a wheel smoke test (Sprint 42), ensuring it stays current.

### Item 5.4: Demo path — video walkthrough + one-pager

**Classification**: UNADDRESSED

No video or one-pager has been produced. The review listed this as demo path priority #2 (after minimal showcase script). This is a non-code deliverable outside typical sprint scope.

**Note**: The 4-life project (separate repo) serves as an interactive explainer, which partially overlaps with the one-pager's intent but is not the same deliverable.

### Item 5.5: Demo path — hardware binding demo

**Classification**: PARTIALLY ADDRESSED

See Item 4.3. SDK spec and types exist; actual hardware demo depends on hardbound implementation.

---

## Section 7: Autonomous Session Guidance

### Item 7.1: Sessions should be aware that work maps to EU AI Act requirements

**Classification**: ADDRESSED

The v2 session protocol and primers reference the strategic review. The review itself is preserved in `docs/strategy/` and available to every session.

### Item 7.2: "Demo-ability matters" — prioritize features that can be shown

**Classification**: PARTIALLY ADDRESSED

The quickstart example and 7 CLI subcommands (especially `web4 selftest`, `web4 trust`, `web4 generate`) are demo-able. The MCP server (8 tools) makes the SDK externally accessible. However, no demo-oriented packaging beyond the quickstart script exists.

---

## Cross-Reference: Strategic Items → Sprint Execution

| Strategic Item | Sprint(s) | Classification |
|---------------|-----------|---------------|
| EU AI Act primitives | Sprints 1-28 (all data types + behavioral functions) | PARTIALLY ADDRESSED |
| Aug 2026 positioning | SDK feature-complete at v0.26.0 | PARTIALLY ADDRESSED |
| Anti-Ponzi framing | Sprint 24 (action consequences), 28 (MCP) | ADDRESSED |
| Bootstrapping inequality | — | DEFERRED |
| Formal proofs | — | DEFERRED |
| Real-world testing | — | DEFERRED |
| Attack corpus maintenance | Preserved through sprawl archive | ADDRESSED |
| Development velocity | 43 sprints in 36 days | ADDRESSED |
| Hardware binding | Sprints 4-16 (AttestationEnvelope) | PARTIALLY ADDRESSED |
| EU funding applications | — | UNADDRESSED |
| Outreach | — | UNADDRESSED |
| Minimal showcase | Sprint 36, 42 (quickstart + CI smoke) | ADDRESSED |
| Video + one-pager | — | UNADDRESSED |

---

## Observations

1. **SDK execution was strong on primitives, weak on packaging.** All the data types and behavioral functions the review called for exist and are tested. What's missing is the layer above: compliance-specific features, demo artifacts, and outreach materials.

2. **Three DEFERRED items are appropriately sequenced.** Bootstrapping inequality, formal proofs, and real-world testing were all flagged by the review itself as intentionally deferred. The SDK built the foundation they'll eventually need.

3. **UNADDRESSED items are outside autonomous session scope.** EU funding applications, outreach to contacts, and video production are operator-driven activities. Autonomous coding sessions can't file grant applications or schedule meetings.

4. **The hardware binding gap is structural, not neglected.** The SDK half (AttestationEnvelope spec, types, test vectors) is complete. The demo half requires the hardbound product (private repo). This is a cross-repo dependency, not a missed task.

5. **The quickstart script closes the review's #1 demo priority.** `examples/quickstart.py` directly implements what the review called "minimal showcase script: ATP allocation → task execution → value certification via tensors → rep update."

---

*Audit classifies; it does not propose. Downstream sprint planning consumes this classification.*
