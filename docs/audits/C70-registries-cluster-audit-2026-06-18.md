# C70 — Registries Cluster Audit (first C-series pass)

**Date**: 2026-06-18
**Auditor**: Legion autonomous web4 track (slot `000047`)
**Target**: `web4-standard/registries/` — `README.md`, `cipher-suites.md`, `error-codes.md`, `extensions.md`, `initial-registries.md`
**Prior C-series coverage**: NONE (first audit of this cluster). All core-spec files now have ≥1 delta cycle; this fills the largest never-audited coverage gap.
**Method**: §A prior cross-track carries that land here (verified against current registry bytes); §B multi-agent refute-by-default finder workflow, primitive-clustered. All cross-doc claims hand-verified with loose-pattern grep before assertion (C64 lesson). Audit-only — no spec edits this turn; findings routed to the C71 REMEDIATION turn.

---

## Headline

The `registries/` directory contains **two parallel, mutually divergent registry systems that the corpus never reconciles**:

| Concept | "Structured" registry (linked by README) | Canonical-by-usage registry | Corpus consumers of the structured form |
|---------|------------------------------------------|------------------------------|------------------------------------------|
| Cipher suites | `cipher-suites.md` — **numeric** `0x0001 WEB4_AES128_GCM_SHA256` … | `initial-registries.md` Suite IDs + `core-protocol.md` §1 (`W4-BASE-1/FIPS-1/IOT-1`) | **0** (orphan) |
| Error codes | `error-codes.md` — **numeric** `0x0001 INVALID_LCT` … | `errors.md` §2 (`W4_ERR_*`, declares itself SSOT) + `initial-registries.md` | **0** (orphan) |
| Extensions | `extensions.md` — **numeric** `0x0001 MRH_RDF` … | `initial-registries.md` (`w4_ext_*@1`) + `web4-handshake.md` | (handshake refs extension *negotiation*, not these IDs) |

The README links the three numeric files as "the registries" and demotes `initial-registries.md` (the file the rest of the corpus actually cites) to "Initial registry values." The top-level `web4-standard/README.md` (L118-121) goes further: it calls `registries/README.md` "IANA registry **templates**", lists the three numeric files, and **omits `initial-registries.md` entirely**. So the structured/linked artifacts are orphans, and the canonical-by-usage artifact is unlinked from the top-level index. This inversion is the spine of the cluster's findings.

---

## §A — Prior cross-track carries landing in `registries/`

Three findings from earlier core-spec audits were routed *toward* the registries from the other side. Per policy-review note, these are treated as prior findings (verify against current bytes; report confirm / refute / reframe — do not re-derive as fresh §B).

### A-1 — C66 B-H1 (numeric `error-codes.md` canonicity) → **CONFIRMED + SHARPENED**
- **Original**: "numeric `error-codes.md` canonicity vs `errors.md` string taxonomy."
- **Verified (bytes)**: `error-codes.md` names (`INVALID_LCT`, `HANDSHAKE_FAILED`, `INSUFFICIENT_TRUST`, `MRH_VIOLATION`, `BINDING_FAILED`, `PAIRING_FAILED`, `BROADCAST_FAILED`) appear in **no other file in the corpus** (`grep -rln` over `web4-standard` + `sdk` returns only `error-codes.md` itself). Meanwhile `errors.md` §1 states it is "the single source of truth for core protocol error codes" using the string `W4_ERR_*` form, and §2 is structured into 6 subsystems (Binding/Pairing/Witness/Authz/Crypto/Proto).
- **Sharpening**: the finding is stronger than "which is canonical" — the numeric registry is a **fully orphaned dead registry** (0 consumers) that competes with a file explicitly self-declared as SSOT. There is no numeric↔string mapping anywhere. Routing: this is the registry-side anchor for the operator's standing **errors-layer bundle** (B-H1).

### A-2 — C66 B-2 (`initial-registries.md` taxonomy adds §2-absent codes) → **CONFIRMED, but ESCALATED by §B** (correcting an earlier mis-read)
- **Original**: "`initial-registries.md` core-taxonomy mirror adds §2-absent `WITNESS_REQUIRED`/`PROTO_FORMAT`."
- **Verified (bytes)**: `grep -n "WITNESS_REQUIRED\|PROTO_FORMAT"` over `errors.md` returns **nothing** — both are absent from the file that self-declares SSOT. Both ARE present in `initial-registries.md`. Additionally `initial-registries.md` carries a **Metering Errors** block with a self-declared duplicate: `W4_ERR_RATE_LIMIT - Rate limit exceeded (same as W4_ERR_AUTHZ_RATE)`, plus `W4_ERR_SCOPE_DENIED`, `W4_ERR_BAD_SEQUENCE`, `W4_ERR_BAD_TIMESTAMP`, `W4_ERR_GRANT_EXPIRED`.
- **CORRECTION / escalation** (surfaced by §B finder E3 — an initial lead read of "registry-only" was WRONG): these two codes are **not registry-only**. They are emitted by **live sibling specs**: `web4-metering.md:109` lists `W4_ERR_WITNESS_REQUIRED`, and `web4-handshake.md:160` says endpoints **MUST** abort with `W4_ERR_PROTO_FORMAT`. So the file that claims to be "the single source of truth for core protocol error codes" is **missing two codes its own subsystem specs MUST/do emit**. This is a genuine SSOT-completeness gap, not a mere mirror over-definition. Routed as **B-C1** below (cross-track, owner = `errors.md`).
- **Reframe**: `initial-registries.md` is itself a *third* divergent error mirror (alongside `error-codes.md` numeric and `errors.md` string), and it predates the SSOT claim (its `Last-Updated: 2025-09-11` precedes errors.md's `2026-06-17`). It is the most authentic candidate for "the registry of record" by corpus usage, yet it is internally inconsistent with the declared SSOT.

### A-3 — C68 C-M1 / B-7 (canonical suite registry; FIPS-KEM spellings) → **CONFIRMED + REFRAMED**
- **Original**: "canonical suite registry now ≥5 files, 4 spellings"; B-7 "normalize FIPS-KEM sibling spellings."
- **Verified (bytes)**: `W4-BASE-1` appears 16× across 11 files, `W4-FIPS-1` 10×, `W4-IOT-1` 2×. Three different suite tables exist:
  - `core-protocol.md` §1 (canonical by MUST-language, "All implementations MUST support `W4-BASE-1`"): KEM column `X25519` / `P-256ECDH` / `X25519`; Profile `COSE/JOSE/CBOR`; includes **W4-IOT-1** (AES-CCM).
  - `initial-registries.md` Suite IDs: `W4-BASE-1 : X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 (COSE)` and `W4-FIPS-1 : P-256 ECDH / ECDSA-P256 / AES-128-GCM / SHA-256 (JOSE)` — **no W4-IOT-1, no KDF column**.
  - `cipher-suites.md`: numeric `WEB4_*` names, `DH = X25519` for all three rows, no P-256 row at all — a disjoint set.
- **Reframe**: not merely "spelling drift." `W4-IOT-1` is **used-but-undefined in the registry of record** (`initial-registries.md` lists only BASE-1/FIPS-1, but `core-protocol.md` §1 and `edge-device-profile.md` reference `W4-IOT-1`). The KEM spelling split (`X25519` vs `P-256ECDH` vs `P-256 ECDH`) is real but secondary to the missing-row defect. This is the registry-side anchor for C68's suite-registry DESIGN-Q.

---

## §B — Finder workflow (refute-by-default)

**Workflow** `wf_69a5e55c-8d7`: 5 primitive-clustered finder lenses (error-codes, cipher-suites, extensions, iana-meta, canonicity), each finding independently verified refute-by-default by a skeptical second agent. **28 raw → 27 survived / 1 refuted.** After synthesis dedup (heavy cross-lens overlap — the canonicity lens re-found the per-primitive orphan/SSOT findings) → **17 distinct** (3 DESIGN-Q, 7 AUTONOMOUS, 7 CROSS-TRACK) + 1 INFO + 1 refuted. All cross-doc claims re-grepped by the lead at synthesis.

### Refuted (recorded for the next finder pass)
- **CS-5** — claimed the `W4-GREASE-93f07f2a` suite-form is negotiated in handshake but unregistered. Verifier reproduced that the GREASE *extension* placeholder IS registered (`w4_ext_93f07f2a@0` in `initial-registries.md`) and the handshake GREASE convention is documented; no unregistered suite-name form. **Refuted.**

### DESIGN-Q (operator decision required — do NOT auto-apply)

**B-D1 (FLAGSHIP) — Registry SSOT inversion: the directory ships two parallel, mutually-disjoint registry systems and the README points at the orphan half.** [MED]
Consolidates finder findings E1 + CS-1 + EXT-1 + REG-CANON-1 — the same structural defect across all three primitives:
- *Error codes*: numeric `error-codes.md` (0 consumers) ⊥ string `W4_ERR_*` (`errors.md` SSOT + corpus-wide).
- *Cipher suites*: numeric `cipher-suites.md` (0 consumers) ⊥ named `W4-BASE-1/FIPS-1/IOT-1` (`core-protocol.md` §1 MUST + 11 files).
- *Extensions*: numeric `extensions.md` (0 consumers) ⊥ provisional string `w4_ext_*@<ver>` (`initial-registries.md` + handshake §10).
The structural choice (per finder REG-CANON-1, recommended **Option A — least corpus churn**): declare the **string/named form canonical** (it is what every normative spec, SDK, and test-vector already uses), demote the three numeric files to either (a) explicitly-labelled IANA-submission *templates* to be re-keyed to the named forms, or (b) retired. Either way the two READMEs (`registries/README.md`, `web4-standard/README.md` L118-121) must be corrected and `initial-registries.md` linked from the top-level index. **This single decision unblocks B-D2, B-A2/A3/A4/A5, and the EXT-3/EXT-4 disposition.**

**B-D2 — `error-codes.md` numeric class scheme is internally self-contradictory** (subordinate to B-D1; moot if the file is retired). [LOW]
Consolidates E2 + R-L1 + R-M4. The Error-Classes table reserves `0x0100` Security / `0x0200` Trust / `0x0300` Entity — all **empty** — while every registered code sits in `0x0000-0x00FF` Protocol; `INSUFFICIENT_TRUST` (0x0003) and `MRH_VIOLATION` (0x0007) are trust/relevancy errors mis-binned in the Protocol range though a dedicated Trust class exists; there is a `METERING_FAILED` code but no Metering class; and `0x0000` is `SUCCESS` here yet "reserved" in the suite/extension registries (reserved-range inconsistency). All cosmetic *until* B-D1 decides the file's fate; if retained, re-home the codes + add the missing class; if retired, delete the table.

**B-D3 — `extensions.md` forbids what it registers.** [MED]
(EXT-2) L34 asserts "Extensions MUST NOT change core protocol semantics," yet the registry's own entries `MRH_RDF` and `T3_V3` name **core Web4 primitives** (MRH per `mrh-tensors.md`, T3/V3 per `t3-v3-tensors.md` — both in the canonical equation). Either remove them (they are not optional negotiable behaviors) or rename the entries to the *wire-feature* they gate and scope the MUST-NOT so it does not contradict registering a core-surfacing feature.

### AUTONOMOUS (registries-file-only; safe for C71 REMEDIATION without operator decision)

- **B-A1 — Add `W4-IOT-1` to `initial-registries.md` Suite IDs.** [MED] (CS-2 / REG-CANON-2) The suite is normative — `core-protocol.md` §1 (`MAY`) and `edge-device-profile.md` §2 use it — but the registry that claims to be its home lists only BASE-1/FIPS-1. Add, verbatim from `core-protocol.md` §1 L20: `W4-IOT-1 : X25519 / Ed25519 / AES-CCM / SHA-256 (CBOR)`.
- **B-A2 — Replace the three `[Web4 Standard Section X.Y]` placeholder References** in `cipher-suites.md`/`error-codes.md`/`extensions.md` with real targets (cipher-suites→`core-protocol.md` §1; error-codes→`errors.md`; extensions→`web4-handshake.md` §10). [MED] (R-M1)
- **B-A3 — Replace placeholder contact `iana-web4@example.org`** in `README.md` with a `TBD-before-IANA-submission` marker (the whole tree is pre-IANA). [MED] (R-M2)
- **B-A4 — Fix `README.md` registration-procedure description.** [MED] (R-M3) It presents Expert Review AND Specification Required as universal; per RFC 8126 they are distinct, and each registry picks one. Make it a per-registry table (cipher-suites=Expert Review, error-codes=Expert Review, extensions=Specification Required, initial-registries=N/A).
- **B-A5 — Add a uniform `Status / Last-Updated` line to all five files** (only `initial-registries.md` has one). [LOW] (R-L2) For the three numeric files the honest status is "Draft / experimental — not the form used by the protocol corpus" (coordinate wording with B-D1).
- **B-A6 — Add the `HKDF` KDF token to `initial-registries.md` Suite IDs.** [LOW] (CS-4 registry-side) It is currently the only suite definition without a KDF, while `core-protocol.md` §1 and `cipher-suites.md` both carry a KDF column.

### CROSS-TRACK (touches `errors.md` / metering / handshake / security-framework / profiles / SDK — route to those owners)

- **B-C1 — Add `W4_ERR_WITNESS_REQUIRED` (→ §2.3) and `W4_ERR_PROTO_FORMAT` (→ §2.6) to `errors.md`.** [MED] (E3; escalates A-2) **Most actionable cross-track item**: these are live MUST/do-emit codes (`web4-metering.md:109`, `web4-handshake.md:160` MUST-abort) absent from the declared SSOT. Suggested status: WITNESS_REQUIRED=428/403, PROTO_FORMAT=400. Owner: `errors.md` (on its own delta cycle, C66/C67).
- **B-C2 — Canonicalize `W4_ERR_RATE_LIMIT` → `W4_ERR_AUTHZ_RATE`.** [MED] (E4 / R-L4) `web4-metering.md:106` consumes the self-declared duplicate; `initial-registries.md:55` admits "(same as W4_ERR_AUTHZ_RATE)". Drop the alias or mark it formally Deprecated. Folds into the standing errors-layer bundle (B-M1 centralized-vs-distributed ownership).
- **B-C3 — Resolve three competing "format" error names.** [MED] (E5) `W4_ERR_FORMAT` (`web4-metering.md:110`) vs `W4_ERR_PROTO_FORMAT` (`web4-handshake.md:160`) vs the `W4_ERR_CRYPTO_*` family. Canonicalize on `W4_ERR_PROTO_FORMAT` (couples with B-C1) and update metering §6.
- **B-C4 — Normalize the `W4-FIPS-1` KEM spelling across 5 sites.** [MED] (CS-3) `P-256ECDH` / `P-256 ECDH` / `P-256EC` / `ECDH-P256` / long-form `ECDH with P-256, FIPS 186-4`. `security-framework.md` §1.2 already gives the long form; recommend short token `ECDH-P256`. **This is the registry-side confirmation of the C68 B-7 carry** — coordinate as one corpus pass.
- **B-C5 — Harmonize suite-table column sets** across `core-protocol.md` / `web4-handshake.md` / `security-framework.md` / `initial-registries.md` (KEM/Sig/AEAD/Hash/KDF/Encoding). [LOW] (CS-4)
- **B-C6 — Register the live signature-profile extension IDs** `w4_sig_cose@1` / `w4_sig_jose@1` (`web4-handshake.md:122-124`, downgrade-protected) in whichever extension registry B-D1 makes canonical. [LOW] (EXT-5)
- **B-C7 — `extensions.md` "Specification Required" entries cite non-existent specs** (`MCP_BRIDGE`/`BLOCKCHAIN_BRIDGE`/`QUANTUM_READY` → `[Web4-X]` placeholders). [LOW] (EXT-4) Mark Provisional or cite real paths; entangled with B-D1's retain/retire decision for the file.

### INFO
- **E6 — `BROADCAST_FAILED` (0x000A) has no `W4_ERR_*` counterpart, but broadcast is NOT deprecated.** Corrects a lead working-assumption: broadcast remains a live mechanism (`core-protocol.md:155`, `mcp-protocol.md:690-706`). The gap is registry-only; no action unless B-D1 retains a numeric error registry. Recorded so the next pass does not re-flag broadcast as stale.

---

## Routing summary (for C71 REMEDIATION + operator)

| Bucket | Items | Disposition |
|--------|-------|-------------|
| **AUTONOMOUS** (C71 applies to `registries/` files) | B-A1, B-A2, B-A3, B-A4, B-A5, B-A6 | 6 registry-only fixes; none needs a design decision. B-A5 wording coordinates with B-D1. |
| **DESIGN-Q** (operator) | B-D1 (flagship SSOT inversion), B-D2 (numeric class scheme — subordinate to B-D1), B-D3 (extensions self-contradiction) | B-D1 is the keystone — it gates the disposition of all three numeric files and of B-A5/B-C7. |
| **CROSS-TRACK** (sibling-spec owners) | B-C1 (errors.md — *most actionable*), B-C2, B-C3 (errors/metering), B-C4 (= C68 B-7, suite spelling), B-C5, B-C6, B-C7 | B-C1/B-C2/B-C3 fold into the standing **errors-layer operator bundle** (C66/C30). B-C4 folds into the **security-framework suite-registry** carry (C68 C-M1/B-7). |

**Net new for the carry ledger**: B-D1 (registries SSOT canonical-form decision) is the single highest-leverage open question this audit produces — it is the registry-side root of the error/suite/extension divergences that C66/C68 saw downstream. Recommend the operator decide B-D1 (Option A: string/named canonical) before the next errors-layer or security-framework remediation, so those passes mirror a settled SSOT rather than re-litigating it per file.

