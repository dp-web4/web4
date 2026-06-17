# C68 — `security-framework.md` First Delta Re-Audit

**Audit ID**: C68
**Target**: `web4-standard/core-spec/security-framework.md` (97 lines) — Web4 Security Framework (crypto suites, key management, authentication/authorization)
**Date**: 2026-06-17
**Auditor**: autonomous web4 session (legion, slot `120047`), v2 protocol, LEAD voice
**Type**: First delta re-audit (prior coverage **C31**, 2026-06-04, `docs/audits/C31-security-framework-audit-2026-06-04.md`)
**Prior remediation**: **PR #271** (`130069d8`, "resolve 5 autonomous-actionable C31 findings") — applied the 5 AUTONOMOUS items (A-L1, A-L2, A-L3, B-H1+A-L4, B-M3).

---

## Method & Byte-Stability

`git diff 130069d8 HEAD -- web4-standard/core-spec/security-framework.md` is **empty** — the file is **byte-identical to its C31 remediation** and has been since 2026-06-04. Per the standing delta-method this triggers the **C56 completeness+mirror method**: when a file is byte-stable since its remediation, the audit's job is not "did the edit land" (it trivially did) but to re-read the remediation's **CLAIMS token-by-token against the canonical sources**, and to check whether each fix held **at every mirror** (SDK strings, sibling docs, docstrings) — not just inside the diff hunk (the C54/C56/C64 lesson). The audit also re-verifies **every prior C31 carry bidirectionally** against the *current* corpus: some carries resolve downstream and leave stale notes, some harden.

- **§A** — prior-finding verification + regression sweep extended to mirrors + C56 completeness + bidirectional carry re-verification.
- **§B** — multi-agent refute-by-default finder workflow (`wf_0b999e0f-5a2`, **38 agents**, 6 primitive-clustered lenses: internal-consistency / crypto-suite-registry-SSOT / key-rotation-identity / SDK+vector triangulation / cross-spec auth-authz / C56 completeness-mirror). **32 raw findings → 20 survived adversarial verification → 12 refuted**; synthesis-time dedup collapsed the 20 survivors to **10 distinct actionable + carry confirmations**. Every cross-doc contradiction claim was hand-verified with a loose-pattern grep before assertion (C64 false-positive guard).

**Severity**: HIGH = correctness/normative contradiction (esp. vs conformance vector/SDK); MEDIUM = cross-spec divergence needing reconciliation; LOW = hygiene/wording/naming; INFO = positive confirmation / forward-awareness.
**Routing**: AUTONOMOUS (fixable inside `security-framework.md`) / DESIGN-Q (operator canonicity, recorded not resolved) / CROSS-TRACK (fix lands in another artifact).

---

## §A — Prior-Finding Verification, Regression, Completeness, Carry

### A.1 — All 5 C31 AUTONOMOUS findings HELD (0 regression)

Verified token-by-token in the current file:

| C31 ID | Fix | Current state | Verdict |
|---|---|---|---|
| **A-L1** | drop `OPTIONAL/` from §1.3 JOSE status | L44 `JOSE/JSON (ES256) is SHOULD for bridge scenarios.` | **HELD** |
| **A-L2** | reword "MUST NOT be negotiated as MTI" | L22 `… MUST NOT be required in place of the mandatory W4-BASE-1 baseline` | **HELD** |
| **A-L3** | trim abstract over-claim | L3 covers only "cryptographic primitives, key management, and authentication and authorization" — no "comprehensive analysis" claim | **HELD** |
| **B-H1 + A-L4** | W4-FIPS-1 KEM → `ECDH-P256` | L17 table + L35 prose both `ECDH-P256`; token-exact with SDK `SUITE_FIPS.kem` and vector `sec-002` | **HELD** |
| **B-M3** | add `See LCT §7.3` rotation deference | L78 carries the deference + parenthetical | **HELD** (but see B-9) |

**B-H1 triangulation re-confirmed**: `security-framework.md §1.1/§1.2` = `ECDH-P256` = `implementation/sdk/web4/security.py:117 SUITE_FIPS.kem` = `test-vectors/security/security-primitives.json` `sec-002.expected.kem`. The C-series flagship pattern (spec vs its own conformance vector) is resolved for this file. **W4-BASE-1 remains token-exact** across spec/SDK/vector (C31 C-I1 holds).

### A.2 — C56 completeness check: the FIX held in-file but TWO mirrors are stale

Re-reading each fix's *claim* against its mirrors surfaced two **remediation-left-stale** mirrors (the recurring one-sided-mirror lesson, [[feedback_remediation_introduced_regression]]):

- **A-L2 mirror-drift → B-8**: the SDK `negotiate_suite` docstring (`security.py:146`) still quotes the **exact pre-remediation phrase** A-L2 deleted: `Per spec: "Other suites MAY be offered but MUST NOT be negotiated as MTI."` The spec text it cites no longer exists.
- **B-H1 mirror-drift → B-7**: the FIPS-KEM fix landed only in `security-framework.md`. It is now the **lone** core-spec file aligned with SDK+vector; the four sibling spellings are unchanged (`core-protocol.md` `P-256ECDH`, `registries/initial-registries.md` `P-256 ECDH`, `cloud-service-profile.md` `P-256ECDH`, `web4-handshake.md §3` `P-256EC`). The C31 fix **widened** the divergence from a uniform-wrong set to a 1-vs-4 split.

### A.3 — Bidirectional carry re-verification (current corpus)

| C31 carry | C31 routing | Status at C68 |
|---|---|---|
| **C-M1** no canonical crypto-suite registry | DESIGN-Q | **OPEN, HARDENED** — B-H1's in-file fix made the SSOT gap *more* acute (1-vs-4, A.2/B-7) |
| **B-H2** W4-IOT-1 orphan + `P-256ECDH` typo in core-protocol | DESIGN-Q | **OPEN, unchanged** — still in `core-protocol.md §1` + `edge-device-profile.md §3`, absent from SDK/vectors. AEAD `AES-CCM` also still absent from SDK/vectors (B-11) |
| **B-M2** rotation semantics vs LCT §7.3 | DESIGN-Q | **OPEN, SHARPENED** — the B-M3 deference pointer was *appended to* the contradicting prose, not reconciled; §2.3 L78 is now self-contradictory in one sentence (B-9) |
| **B-M3** add LCT §7.3 deference | AUTONOMOUS (done) | **HELD** — survived the post-C31 C61 (#338) LCT remediation; LCT §7.3 still defines the cited lifecycle |
| **B-L5** `cose:ES256` labels in LCT files | CROSS-TRACK | **OPEN, WIDER** — *not* picked up by C57 (#328) or C61 (#338) LCT remediations; persists at `LCT-linked-context-token.md:169`, `lct-capability-levels.md:114/267/363/463/525`, and additionally `multi-device-lct-binding.md:255/268` (C31 under-enumerated) (B-10) |
| **B-L6** vector-file ownership | CROSS-TRACK | OPEN, unchanged (file-organization, not re-litigated) |
| **B-L7** `device` W4ID method vs SDK `KNOWN_METHODS` | CROSS-TRACK | OPEN, unchanged — `data-formats.md §1.2` still names `device`; SDK `KNOWN_METHODS = {"key","web"}` |

**INFO carries held**: C-I4 (§1.3 cross-refs to handshake §6.0.3/§6.0.4 still resolve and content-match — but see B-1 for a notation seam C-I4 missed); C-I6 (no version/date header — corpus-wide, not an outlier).

---

## §B — Findings Summary

| ID | Sev | Routing | Relation | One-line |
|----|-----|---------|----------|----------|
| **B-1** | MED | AUTONOMOUS | NEW (contradicts C31 C-I4) | §1.3 MTI COSE profile writes JOSE-string `crv: Ed25519`/`alg: EdDSA` where the handshake §6.0.3 profile it cites as canonical uses COSE numeric `crv = 6`/`alg = -8` |
| **B-2** | MED | AUTONOMOUS | NEW | §3.1 authentication under-specifies vs handshake §6.0.5 "Binding to Session (**MUST**)" + replay window — no mention of session binding, freshness, nonce, or replay |
| **B-3** | MED | DESIGN-Q | NEW | §3.2 "Authorization in Web4 is based on Verifiable Credentials" diverges from the corpus SAL law-oracle / rights-obligations + R6 grant authorization model |
| **B-4** | LOW | AUTONOMOUS | NEW | §1.1 table column header `Profile` vs §1.2 prose + SDK serialized key + vector key `Encoding`/`encoding` |
| **B-5** | LOW | AUTONOMOUS | NEW | §1.1 "Suite Definitions" table omits the **KDF** dimension that §1.2, SDK, and vector all carry (`HKDF-SHA256`) |
| **B-6** | LOW | AUTONOMOUS | NEW | §1.2 cites COSE as **RFC 8152**, obsoleted by RFC 9052/9053; the handshake profile it defers to pins no COSE RFC |
| **B-7** | MED | CROSS-TRACK | C-M1 hardened | FIPS-KEM mirror-drift **1-vs-4**: B-H1 fix made `security-framework.md` the lone aligned file; 4 sibling spellings stale |
| **B-8** | MED | CROSS-TRACK | NEW (A-L2 mirror) | SDK `security.py:146` `negotiate_suite` docstring quotes the exact pre-remediation A-L2 phrase deleted from the spec |
| **B-9** | MED | DESIGN-Q | B-M2 sharpened | §2.3 L78 is self-contradictory in one sentence: "update the identifier" (mutate-in-place) immediately cites LCT §7.3's stable-subject-DID / new-LCT model |
| **B-10** | LOW | CROSS-TRACK | B-L5 widened | `cose:ES256` mislabel spread is wider than C31 enumerated (+`multi-device-lct-binding.md`); unresolved by C57/C61 |
| **B-11** | INFO | DESIGN-Q | B-H2 confirm | W4-IOT-1 orphan + `AES-CCM` AEAD still absent from SDK/vectors; no downstream resolution |

**10 distinct actionable (0 HIGH / 6 MED / 4 LOW) + 1 INFO carry-confirm.** 12 candidates refuted at verification (see ledger).

---

## §B — Finding Detail

### B-1 (MEDIUM, AUTONOMOUS) — COSE profile states `crv`/`alg` in JOSE-string notation, not COSE numeric ⭐ flagship NEW

§1.3 L48: *"Ed25519 with `crv: Ed25519` and `alg: EdDSA`"*. The §1.3 COSE subsection (L50) **explicitly defers** to `web4-handshake.md §6.0.3` as "the complete profile." That normative profile reads (handshake L140) *"Key curve: Ed25519 (`crv = 6`)"* and (L136) *"`alg = -8` (EdDSA)"*. In COSE (RFC 8152/9052/9053) `crv` is a numeric label (Ed25519 = 6 in the COSE Elliptic Curves registry); the bare string `Ed25519` is the **JOSE/JWK** form. So inside the MTI COSE profile, this file states the curve/alg in JOSE notation while the file it anchors to states them in COSE notation.

- **Relation**: GENUINELY NEW. C31's C-I4 (audit L170) counted handshake's `crv=6`/`alg=-8` as a *positive content-match* for §1.3 but never read this file's L48 string form — the notation seam was hidden behind a green INFO. Distinct from B-L5/B-10 (which is `cose:ES256` **algorithm-name** labels in other files).
- **Severity note**: the verifier moderated the finder's interop rationale — `crv` is not actually carried in the COSE_Sign1 *protected headers* (handshake L135-138 lists only `alg`/`kid`/`content-type`), so the "non-interoperable envelope" claim is overstated; `crv` appears as descriptive key metadata at both sites. Held at MEDIUM as a real notation divergence inside an explicitly-anchored MTI profile, not promoted to HIGH.
- **Routing**: AUTONOMOUS. §1.3 L50 already cites §6.0.3 as canonical, so mirror its notation: e.g. *"Ed25519 with `crv = 6` (COSE label) and `alg = -8` (EdDSA)"*.

### B-2 (MEDIUM, AUTONOMOUS) — §3.1 authentication under-specifies vs handshake §6.0.5 MUSTs

§3.1 (L89) describes authentication as *"signing a challenge with its private key … verified … using the entity's public key"* — and stops there. The normative handshake **§6.0.5 "Binding to Session (MUST)"** (L150) plus L177 (*"Receivers MUST verify `sig` … and check freshness"*) and L210 (*"`nonce` values MUST be unique per key; maintain a replay window"*) mandate session/channel binding and replay protection. §3.1 — in the document titled "Authentication and Authorization" — mentions none of session binding, freshness, nonce, or replay, so a reader treating it as authoritative gets an under-specified, replayable challenge-response.

- **Routing**: AUTONOMOUS. Uses the file's own established deference pattern (cf. §1.3 → §6.0.3): add *"See `web4-handshake.md §6.0.5` for the normative session-binding and replay-protection requirements."* No design decision.
- **Relation**: NEW.

### B-3 (MEDIUM, DESIGN-Q) — §3.2 "authorization is based on VCs" diverges from the SAL/R6 authz model

§3.2 (L91-95): *"Authorization in Web4 is based on Verifiable Credentials (VCs)."* The corpus's actual authorization substrate is the **SAL law-oracle + rights/obligations** model — `web4-society-authority-law.md` defines *Authority* as "the binding capability of a society to create roles, delegate permissions, and enforce law" (L17), with rights granted via the **Birth Certificate** + **Law Oracle** (L41, L57, L182) — and **R6** grant evaluation. VCs are at most *one* credential carrier, not the basis of Web4 authorization. The blanket "based on VCs" statement in the security framework contradicts the more-developed governance model.

- **Routing**: DESIGN-Q. Whether authorization is VC-based, SAL/law-oracle-based, or VCs-carry-SAL-rights is an operator canonicity decision; recorded, not resolved. `security-framework.md` is what implementers read first, so the divergence is load-bearing.
- **Relation**: NEW.

### B-4 / B-5 / B-6 (LOW, AUTONOMOUS) — §1.1 table hygiene + stale RFC

- **B-4**: §1.1 column header is `Profile` (L14) but the identical dimension is `**Encoding**` in §1.2 (L32/L40), the SDK serialized key `encoding` (`security.py:100`), and the vector key `encoding` (`security-primitives.json`). Rename the column → `Encoding`.
- **B-5**: the §1.1 "Suite Definitions" table carries KEM/Sig/AEAD/Hash/Profile/Status but **no KDF**, while §1.2, the SDK `CryptoSuite.kdf` field, and the vector all carry `HKDF-SHA256`. Either add a KDF column or note the table is a partial view.
- **B-6**: §1.2 (L32) cites COSE as **RFC 8152**, which RFC 9052/9053 obsoleted; the handshake profile §6.0.3 pins no COSE RFC. Update to `RFC 9052/9053` (or both with "obsoletes").

### B-7 (MEDIUM, CROSS-TRACK) — FIPS-KEM mirror-drift hardened to 1-vs-4

B-H1's in-file fix is correct but one-sided. Current W4-FIPS-1 KEM spellings: `security-framework.md` **`ECDH-P256`** (= SDK + vector) vs `core-protocol.md:19` `P-256ECDH` vs `registries/initial-registries.md:6` `P-256 ECDH` vs `cloud-service-profile.md:19` `P-256ECDH` vs `web4-handshake.md:23` `P-256EC`. Four divergent siblings remain. This is the downstream-normalization item in C31's disposition ledger, now load-bearing because the canonical token is settled (`ECDH-P256` per SDK+vector). Couples to the **C-M1** SSOT DESIGN-Q.

- **Routing**: CROSS-TRACK. Normalize the four siblings to `ECDH-P256` (gated on the C-M1 registry decision for *where* the SSOT lives).

### B-8 (MEDIUM, CROSS-TRACK) — SDK docstring quotes deleted A-L2 spec text

`security.py:146` `negotiate_suite` docstring: *Per spec: "Other suites MAY be offered but MUST NOT be negotiated as MTI."* — the **exact phrase A-L2 removed** from §1.1 (now "MUST NOT be required in place of the mandatory W4-BASE-1 baseline"). The SDK quotes a spec sentence that no longer exists. Pure documentation drift (the `negotiate_suite` *logic* is unaffected), but it propagates the conceptual error A-L2 was raised to kill (MTI as a negotiable property).

- **Routing**: CROSS-TRACK (SDK). Update the docstring quote to the current §1.1 wording.

### B-9 (MEDIUM, DESIGN-Q) — §2.3 is self-contradictory in a single sentence (B-M3 bolted onto B-M2)

§2.3 L78: *"The key rotation process involves generating a new key pair and **updating the entity's Web4 Identifier to use the new public key**. See `LCT-linked-context-token.md §7.3` for the normative rotation lifecycle (new LCT issuance, `lineage` to the parent, … before the parent is retired as `superseded`)."* The first clause asserts **mutate-the-identifier-in-place**; the cited §7.3 keeps the subject DID **stable** and issues a **new LCT**. C31's B-M3 (add the deference) was applied by *appending* the pointer to the *unchanged* B-M2-contradicting prose, so the remediation produced a sentence that contradicts the very reference it adds. This is a **remediation-introduced juxtaposition** (the prose and its corrective pointer now sit adjacent and disagree).

- **Routing**: DESIGN-Q (the mutate-vs-stable-DID semantics is the unresolved B-M2 operator decision). **Autonomous interim available**: reword the first clause to not assert in-place identifier mutation (e.g. "issuing a new LCT bound to the new key, with `lineage` to the parent") so the sentence stops contradicting its own cross-reference even before B-M2 resolves.
- **Relation**: B-M2 sharpened; documents an instance of [[feedback_remediation_introduced_regression]].

### B-10 (LOW, CROSS-TRACK) — `cose:ES256` mislabel spread wider than C31 enumerated

C31's B-L5 enumerated `cose:ES256` placeholder labels in `lct-capability-levels.md` + `LCT-linked-context-token.md`. They **persist** (not touched by C57 #328 or C61 #338), and `multi-device-lct-binding.md:255/268` also carries the label — under-enumerated by C31. The MTI-consistent label is `cose:EdDSA` (COSE envelope + non-MTI ES256 alg is the mismatch). Example placeholders only — LOW.

- **Routing**: CROSS-TRACK (lands in the LCT/multi-device docs).

### B-11 (INFO, DESIGN-Q) — W4-IOT-1 + AES-CCM still orphaned from SDK/vectors

Confirms B-H2 unchanged: `core-protocol.md`/`edge-device-profile.md` define W4-IOT-1 (incl. `AES-CCM` AEAD) but neither the suite nor `AES-CCM` appears in the SDK `SUITES`/`CryptoSuiteId` or the conformance vectors. No downstream resolution since C31. Forward-awareness for the C-M1/B-H2 operator decision.

---

## Refuted at Verification (12 — folded or rejected)

The adversarial pass refuted 12 of 32 raw candidates. Notable folds:
- Several **dup framings of B-7** (island-of-correctness / suite-count divergence / registries-list-form) — folded into B-7 + C-M1 carry, not raised separately.
- The **`web4-handshake.md` path-without-`protocols/`** observation — refuted as a re-raise of C31's C-I4 minor nicety (already recorded), not a new finding.
- **B-L7 device-method** re-raises — folded into the A.3 carry table.
- A claimed **"dual-validity overlap window" inaccuracy** in the §2.3 parenthetical — refuted: LCT §7.3 does keep both LCTs valid during overlap; the parenthetical is accurate (the real issue is B-9's first clause, not the parenthetical).
- A **core-protocol.md self-citation path error** attributed to C31 — refuted as not material to this file.

---

## Disposition Ledger (for C69 remediation)

**AUTONOMOUS (fix inside `security-framework.md`) — 5 + 1 interim:**
- **B-1**: §1.3 L48 → COSE numeric `crv = 6` / `alg = -8` to mirror handshake §6.0.3.
- **B-2**: add §3.1 deference to `web4-handshake.md §6.0.5` (session binding + replay).
- **B-4**: rename §1.1 column `Profile` → `Encoding`.
- **B-5**: add KDF to the §1.1 table (or annotate it as a partial view).
- **B-6**: update §1.2 COSE cite `RFC 8152` → `RFC 9052/9053`.
- **B-9 interim**: reword §2.3 L78 first clause to stop asserting in-place identifier mutation (does not pre-empt the B-M2 DESIGN-Q).
- *BC#5 corpus sweep mandatory before writing each token edit.*

**DESIGN-Q (operator canonicity, recorded not resolved):**
- **B-3**: authorization basis — VCs vs SAL law-oracle/rights-obligations vs VCs-carry-SAL-rights.
- **B-9 / B-M2**: key-rotation semantics (mutate-identifier vs stable-subject-DID + new LCT) + `did:web4:key`-subject behavior.
- **C-M1** (carry): canonical crypto-suite registry — now ≥5 files, 4 FIPS-KEM spellings.
- **B-H2 / B-11** (carry): W4-IOT-1 + `AES-CCM` inclusion in SDK/vectors vs removal from `core-protocol.md`.

**CROSS-TRACK (fix lands elsewhere):**
- **B-7**: normalize 4 sibling FIPS-KEM spellings to `ECDH-P256` (gated on C-M1).
- **B-8**: update SDK `security.py:146` docstring quote to current §1.1 wording.
- **B-10**: `cose:ES256` → `cose:EdDSA` in `LCT-linked-context-token.md`, `lct-capability-levels.md`, `multi-device-lct-binding.md`.
- **B-L6 / B-L7** (carry): vector-file ownership split; `device` method vector + SDK `KNOWN_METHODS`.

---

*Audit produced under Autonomous Session Protocol v2 — slot `120047`, LEAD voice. Read-only: no spec, SDK, or test-vector files were modified this turn. Remediation (C69) is the next alternation turn.*
