# Sprint 43 Planning Analysis — Strategic Review + Reference File Triage

**Date**: 2026-04-19
**Triggered by**: Issue #166 (Sprint 43 planning needed — autonomous queue exhausted)
**Scope**: Analysis only — no code changes. Operator approval gates follow-up actions.

---

## Part 1: Strategic Review Cross-Reference

The [Cross-Model Strategic Review](../strategy/cross-model-strategic-review-2026-02.md)
(Feb 2026) identified gaps, strengths, and action items from independent reviews by
Grok, Nova, and Claude. Below is a structured cross-reference against SDK Sprints 1-42
and current repo state.

### Action Items Status

| # | Strategic Review Item | Status | Evidence |
|---|----------------------|--------|----------|
| 1 | EU AI Act article-by-article mapping | **DONE** | `docs/strategy/eu-ai-act-compliance-mapping.md` (Feb 19, 2026). Art. 6/9/10/11/12/13/14/15/17 mapped. `docs/compliance/art9-risk-register-template.md` also exists. |
| 2 | ATP/ADP "anti-Ponzi" framing | **DONE** | SDK modules `web4.atp` + `web4.metabolic`. Conservation laws tested. `process_action_outcome()` behavioral function. |
| 3 | Hardware binding = #1 priority | **ADDRESSED** | `AttestationEnvelope` in SDK with JSON-LD + JSON Schema. 5 TPM reference files in `reference/`. TPM2 validated on Legion. Further work is hardbound scope. |
| 4 | Demo Path #1: Minimal showcase script | **DONE** | `examples/quickstart.py` (Sprint 36). CI-wired (Sprint 42). Covers trust query, action outcome, generate/roundtrip. |
| 5 | Demo Path #2: Short video walkthrough | **NOT DONE** | Operator/marketing task, not SDK scope. |
| 6 | Demo Path #3: Hardware binding demo | **PARTIAL** | TPM validated on Legion. No standalone demo harness. Reference files exist but aren't runnable demos. |

### Identified Gaps Status

| # | Gap (from Feb 2026 review) | Status | Notes |
|---|---------------------------|--------|-------|
| 3a | Bootstrapping and inequality | **CLOSED** | Formal analysis (84 checks, Session 20). Composite model proves Web4 does NOT recreate BTC concentration dynamics. |
| 3b | Formal proofs vs empirical testing | **OPEN** | BMC provides exhaustive bounded verification. Full theorem proving remains a research track. Not SDK scope. |
| 3c | Real-world market testing | **OPEN** | Synthetic only. ACT real blockchain needed. Not SDK scope — requires infrastructure deployment. |

### Session Directives Status

| # | Directive (§7) | Status | Notes |
|---|----------------|--------|-------|
| 1 | Hardware binding = #1 credibility priority | **ADDRESSED** | SDK + reference files + TPM2 work. Next step: hardbound product integration. |
| 2 | "Anti-Ponzi" is the clearest value prop | **ADDRESSED** | ATP/ADP conservation in SDK. Framing documented in strategic review. |
| 3 | Track bootstrapping inequality | **CLOSED** | Formal analysis completed and documented. |
| 4 | Demo-ability matters | **ADDRESSED** | `quickstart.py` as demo + CI-verified. |

### Assessment

**7 of 9 items are addressed or closed.** The two remaining gaps (formal proofs, real-world market testing) are out-of-scope for the SDK — they require either academic research or infrastructure deployment. No SDK-level follow-up is needed from the strategic review.

---

## Part 2: Reference File Triage

The `implementation/reference/` directory contains 31 `.py` files retained from the
Sprint S4 triage (Mar 2026). Of these, 14 have zero external references — nothing
outside `reference/` imports them. Analysis follows.

### Methodology

- "External reference" = imported by any file outside `implementation/reference/`
- Files referenced only by `archive/` are noted but treated as effectively zero-ref
  (archive is dead code)
- Each file assessed for: web4-specific value, reuse potential, documentation value

### Files With External References (17 files) — No Action Needed

These 17 files are imported by SDK services, integration tests, simulations, or core
modules. They serve as the protocol-layer reference that the SDK data-type layer builds
on. Not candidates for archiving.

### Files With Zero External References (14 files, 6,093 lines total)

#### TPM / Hardware Binding (5 files, 2,454 lines)

| File | Lines | Purpose | Recommendation |
|------|-------|---------|---------------|
| `tpm_binding.py` | 739 | TPM 2.0 LCT binding using tpm2-pytss. Comprehensive but has TCTI initialization issues. | **KEEP** — Documents the full TPM binding design. Historical iteration (pytss approach). |
| `tpm_cli_bridge.py` | 414 | Working TPM binding using tpm2-tools CLI subprocess. The approach that actually works. | **KEEP** — This is the working hardware binding implementation. Strategic review #1 priority. |
| `tpm_lct_identity.py` | 545 | Phase 2 TPM integration with PCR sealing and remote attestation. | **KEEP** — Documents PCR sealing approach. Future hardbound reference. |
| `tpm_lct_simple.py` | 272 | Simplified tpm2-pytss high-level API attempt. | **ARCHIVE** — Superseded by `tpm_cli_bridge.py`. Iteration artifact with no unique design content. |
| `hardware_binding_detection.py` | 484 | Platform detection for TPM/TrustZone/SecureBoot availability. | **KEEP** — Useful as-is for capability detection. Potential SDK module candidate. |

#### Security / Attack Corpus (2 files, 969 lines)

| File | Lines | Purpose | Recommendation |
|------|-------|---------|---------------|
| `attack_demonstrations.py` | 412 | Practical exploit demos against web4 authorization/reputation/resources. Imports from other reference modules. | **KEEP** — Web4-specific security research, not generic CS. Documents real attack patterns. |
| `attack_mitigations.py` | 557 | 8 named mitigations for web4-specific attack vectors (demurrage bypass, cache poisoning, reputation washing, etc.). | **KEEP** — Web4-specific defense patterns. Complements `simulations/` attack corpus. |

#### Protocol Demos (4 files, 773 lines)

| File | Lines | Purpose | Recommendation |
|------|-------|---------|---------------|
| `web4_demo.py` | 177 | Toy handshake + ATP/ADP metering flow. Imports from `web4_crypto_stub.py`. | **KEEP** — Only existing wire-protocol demo. SDK covers data types, not the handshake protocol. |
| `web4_reference_client.py` | 38 | Minimal handshake + ATP roundtrip. | **KEEP** — Companion to `web4_demo.py`. Smallest complete protocol exercise. |
| `web4_crypto_stub.py` | 66 | Toy COSE/JWS facade used by demo files. Non-production. | **KEEP** — Required by `web4_demo.py` and `web4_reference_client.py`. |
| `web4_full_stack_demo.py` | 492 | Integrated demo showing all 7 reference tracks working together. | **KEEP** — Only existing full-system integration reference. Shows the design intent. |

#### Infrastructure / Production Patterns (3 files, 1,897 lines)

| File | Lines | Purpose | Recommendation |
|------|-------|---------|---------------|
| `demurrage_service.py` | 412 | Background ATP decay service (systemd/cron). PostgreSQL persistence. | **KEEP** — Production design pattern for ATP demurrage. Future hardbound reference. |
| `heartbeat_verification.py` | 664 | Cross-machine heartbeat chain verification with TPM integration. | **KEEP** — Presence verification is core LCT concept. Documents cross-machine trust. |
| `production_hardening.py` | 821 | P0 security mitigations: hardware-backed credentials, ledger integration, identity continuity, atomic budget ops. | **KEEP** — Production deployment patterns. Documents the bridge from reference to product. |

### Triage Summary

| Category | Files | Lines | Recommendation |
|----------|-------|-------|---------------|
| TPM / Hardware Binding | 5 | 2,454 | **KEEP 4, ARCHIVE 1** (`tpm_lct_simple.py`) |
| Security / Attack | 2 | 969 | **KEEP 2** |
| Protocol Demos | 4 | 773 | **KEEP 4** |
| Infrastructure | 3 | 1,897 | **KEEP 3** |
| **Total** | **14** | **6,093** | **KEEP 13, ARCHIVE 1** |

### Why "Zero External Refs" Is Expected

These files are not broken or orphaned. The "zero external refs" pattern is structural:

1. **They predate the SDK** — built in sessions 1-34 (Dec 2025 - Feb 2026), before the
   SDK existed (Sprint 1, Mar 2026). They import from each other within `reference/`,
   not from `web4.*`.
2. **Different layer** — The SDK implements data types + behavioral functions. These
   implement protocol mechanics (handshakes, key exchange), services (demurrage,
   heartbeat), and hardware binding (TPM). The layers don't import each other.
3. **Documentation-as-code** — They serve as design references showing how Web4
   components work together. The S4 triage correctly identified them as "genuine web4
   protocol implementations" worth keeping.

### The One Archive Candidate

**`tpm_lct_simple.py`** (272 lines) is the only file recommended for archiving:
- Superseded by `tpm_cli_bridge.py` (the approach that actually works)
- Contains no unique design content not covered by `tpm_binding.py` (full pytss) or
  `tpm_cli_bridge.py` (working CLI)
- It's a middle iteration: `tpm_binding.py` (full) → `tpm_lct_simple.py` (simplified) →
  `tpm_cli_bridge.py` (CLI, working). The endpoints are sufficient.

---

## Part 3: Sprint 43+ Candidate Tasks

Based on this analysis, here are concrete candidates for operator review:

### Candidates from this analysis:

1. **Archive `tpm_lct_simple.py`** — Move to `archive/reference-implementations/`.
   Trivial, bounded, ~1 line in MANIFEST.md update.

2. **Update `STATUS.md`** — Currently dated Feb 26, 2026 and references the old "Research
   Prototype" phase, outdated code metrics, and missing the SDK entirely. A refresh to
   reflect SDK v0.26.0 state would improve repo discoverability. Bounded deliverable.

3. **EU AI Act compliance mapping gap** — The mapping doc notes one gap: "No explicit
   Annex III category mapping in entity metadata. Recommend adding `annex_iii_category`
   optional field to LCT schema." This could be a schema-level change.

### Candidates from issue #166 not addressed here:

4. **Spec-to-explainer alignment** (issue #166 candidate a) — A parallel session
   (`worker/web4-20260419-000024`) is working on this as Sprint 43 T1.

5. **Cross-repo import target** (issue #166 candidate c) — Requires access to
   hardbound/4-life repos. Deferred pending operator input on cross-repo scope.

---

## Appendix: MANIFEST.md KEPT List Validation

The S4 triage (Sprint S4, PR #9, Mar 2026) archived 149 files and kept 39. The current
`reference/` directory contains 31 `.py` files (some S4-kept files may have been removed
in subsequent sprints). The triage was well-executed:
- All 17 externally-referenced files are genuinely used by services/tests
- 13 of 14 zero-ref files serve as documentation-as-code for protocol/hardware/security
- Only 1 file (`tpm_lct_simple.py`) is a superseded iteration artifact

The S4 KEPT list is validated as accurate. No wholesale archive pass is needed.
