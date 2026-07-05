# C140 — `security-framework.md` Third Delta Re-Audit

**Audit ID**: C140
**Target**: `web4-standard/core-spec/security-framework.md` (97 lines) — Web4 Security Framework (crypto suites, key management, authentication/authorization)
**Date**: 2026-07-05
**Auditor**: autonomous web4 session (legion, slot `125256`), v2 protocol, LEAD voice
**Type**: Third delta re-audit. Lineage **C31** (2026-06-04) → **C68** (first delta, 2026-06-17) → **C69** remediation (#350, `3d04dd5c`) → **C108** (second delta, 2026-06-28) → **C109** remediation (#396, `eedd36fc`) → **C140**.
**Prior audit docs**: `docs/audits/C31-security-framework-audit-2026-06-04.md`, `docs/audits/C68-security-framework-delta-audit-2026-06-17.md`, `docs/audits/C108-security-framework-2nd-delta-2026-06-28.md`, `docs/audits/C109-security-framework-remediation-2026-06-28.md`.

---

## Method & Byte-Stability

`git diff eedd36fc HEAD -- web4-standard/core-spec/security-framework.md` is **empty** — the file is **byte-identical to its C109 remediation** and has been since 2026-06-28 (**7 days frozen**). Per the locked frozen-wrap pattern, §A is verification (did every prior fix hold token-by-token at every mirror; do all carries still hold bidirectionally), and the §B yield lives entirely on the **corpus-delta surface** — the cited/carry siblings that *moved* since C109 — plus the **inbound-carry scan** of those siblings' own audit docs.

- **§A** — token-by-token verification of the 6 C69 autonomous fixes + the 1 C109 fix (N1) + regression/artifact/numbering sweep + C56 remediation-completeness re-read + bidirectional re-verification of all 8 carries.
- **§B** — corpus-delta over the cited/carry siblings that moved AFTER the C109 snapshot (`git show eedd36fc`). **Exactly ONE moved**: `protocols/web4-handshake.md` (C113 #404, `57caa2e1`, 2026-06-28). The other cited sibling (`LCT-linked-context-token.md` §7.3) and all carry siblings (`core-protocol.md`, `registries/initial-registries.md`, `multi-device-lct-binding.md`, `lct-capability-levels.md`, SDK `security.py`) are **unmoved since eedd36fc** (verified via `git log eedd36fc..HEAD -- <file>`). Every divergence checked against the **C109 snapshot** before being called net-new (snapshot-presence guard).
- **§C** — single fresh-internal refute-by-default pass (proportionality: a 7-day frozen wrap does not warrant a finder fleet).

**Structure note (re the MUST-vs-reference-impl doc-specific check, C120/C121):** security-framework.md has **NO normative-summary / §12-style section** (it is §1 crypto suites / §2 key management / §3 auth). The doc-specific "normative-summary restates entity MUSTs unconditionally" defect class therefore **does not apply** here — no MUST-vs-impl sweep is warranted.

**Severity**: HIGH = correctness/normative contradiction; MEDIUM = cross-spec divergence; LOW = hygiene/precision; INFO = positive confirmation.
**Routing**: AUTONOMOUS (fix inside `security-framework.md`) / DESIGN-Q (operator canonicity) / CROSS-TRACK (lands elsewhere).

---

## §A — Prior-Finding Verification, Regression, Completeness, Carry

### A.1 — All 6 C69 fixes + the 1 C109 fix HELD by byte-freeze (0 regression, 0 artifacts)

| ID | Fix | Current state | Verdict |
|---|---|---|---|
| **B-1** (C69) | §1.3 COSE `crv`/`alg` → COSE-numeric | L48 `Ed25519 with \`crv = 6\` (COSE curve label) and \`alg = -8\` (EdDSA)` | **HELD** |
| **B-4** (C69) | §1.1 column `Profile` → `Encoding` | L14 header `… KDF \| Encoding \| Status` | **HELD** |
| **B-5** (C69) | §1.1 add `KDF` column | L14/16/17 carry `HKDF-SHA256` | **HELD** |
| **B-6** (C69) | §1.2 COSE `RFC 8152` → `RFC 9052/9053` | L32 `COSE (RFC 9052/9053, obsoletes RFC 8152)` | **HELD** |
| **B-9 interim** (C69) | §2.3 stop asserting in-place identifier mutation | L78 `… generating a new key pair and issuing a new LCT bound to the new public key` | **HELD** |
| **B-2** (C69) | §3.1 add handshake deference | superseded by the C109 N1 fix (below) | **HELD → widened by N1** |
| **N1** (C109) | §3.1 split the over-broad §6.0.5 cite so each property points where it normatively lives | L89 `… §6.0.5 (Binding to Session) for the normative session-binding requirement, and §9 (Anti-Replay & Clocks) for the freshness, nonce-uniqueness, and replay-protection requirements …; the \`HandshakeAuth\` \`nonce\`/\`ts\` fields these rules operate on are defined in §6.1` | **HELD — precise** |

The C108→C109 loop is now closed and verified: C108 caught that the C69 B-2 deference over-attributed freshness/nonce-uniqueness/replay to §6.0.5 (session-binding only); C109 split the cite; C140 confirms the split cite is present and each of the three anti-replay properties now points at §9 while §6.0.5 carries only session-binding and §6.1 carries the `nonce`/`ts` field definitions — **matching the current handshake structure** (verified §6.0.5 in handshake covers session-binding, §9 anti-replay, §6.1 field carriers; C113 did not disturb any of these — see §B).

**Regression sweep clean:** `grep -c '&#'` = 0; no `&amp;`/mojibake; section numbering sequential (§1/1.1/1.2/1.3, §2/2.1/2.2/2.3, §3/3.1/3.2); §1.1 table tokens match §1.2 prose; §1.3 MTI COSE profile (Ed25519/EdDSA) consistent with §1.1 W4-BASE-1; §1.3 JOSE ES256 consistent with §1.1 W4-FIPS-1.

### A.2 — C56 remediation-completeness re-read: clean

Re-reading each fix's *claim* token-by-token against canonical (the check that surfaced C108's N1): the C109 N1 fix's claim now holds — §6.0.5 IS session-binding-only, §9 ("Anti-Replay & Clocks") DOES carry freshness (`ts` ±300s) + nonce-uniqueness + replay window, and §6.1 DOES define the `nonce`/`ts` fields. No residual one-sided-claim defect. The B-6 `RFC 9052/9053, obsoletes RFC 8152` claim holds (RFC 9052/9053 do obsolete RFC 8152). No new completeness defect.

### A.3 — Bidirectional carry re-verification (current corpus)

| Carry | Routing | Status at C140 |
|---|---|---|
| **B-3** §3.2 "authz based on VCs" vs SAL/R6 | DESIGN-Q | **OPEN, unchanged** — §3.2 L91-95 verbatim; operator canonicity decision stands |
| **B-7** FIPS-KEM spelling 5-site mirror-drift | CROSS-TRACK | **OPEN, unchanged** — all 5 spellings still divergent: `P-256ECDH` (core-protocol:19) / `P-256 ECDH` (registries:6) / `P-256EC` (handshake:23) / `ECDH-P256` (this file L17/L35) / long-form `ECDH with P-256, FIPS 186-4` (this file L35). Canonical target `ECDH-P256` = this file's token (C70-B-C4). None moved since eedd36fc |
| **B-8** SDK docstring quotes deleted A-L2 phrase | CROSS-TRACK | **OPEN, unchanged** — `implementation/sdk/web4/security.py:146` still reads `Per spec: "Other suites MAY be offered but MUST NOT be negotiated as MTI."` (SDK unmoved since eedd36fc) |
| **B-9 / B-M2** rotation mutate-vs-stable-DID | DESIGN-Q | **interim HELD** (§2.3 L78); semantics decision stands |
| **B-10** `cose:ES256` mislabel | CROSS-TRACK | **OPEN, unchanged** — `multi-device-lct-binding.md` still 2× `cose:ES256`; file unmoved since eedd36fc |
| **C-M1 ≡ C70-B-D1** canonical crypto-suite registry SSOT | DESIGN-Q | **OPEN** — and now the pivot of the §B.1 net-new observation (the W4-IOT-1 Profile-column divergence is a fresh instance of exactly the SSOT gap C-M1 names) |
| **B-H2 / B-11** W4-IOT-1 + AES-CCM | DESIGN-Q / CROSS-TRACK | **OPEN — MATERIALLY UPDATED by C113**; see §B.1. Registry-orphan sub-facet remains resolved (C71); SDK/vector sub-facet stands; **NEW: a handshake↔core-protocol Profile-column contradiction was introduced by C113** |
| **B-L6 / B-L7** vector ownership; `device` W4ID method | CROSS-TRACK | OPEN, unchanged (`data-formats.md` did not move after eedd36fc) |

---

## §B — Corpus-Delta Over the One Moved Sibling

Only **`protocols/web4-handshake.md`** moved since the C109 snapshot — **C113 #404 (`57caa2e1`, 2026-06-28)**, the remediation of C112's 2 autonomous findings. `git show 57caa2e1 -- protocols/web4-handshake.md` has exactly **three hunks**; each is assessed at cited-hunk granularity against security-framework's cited surface (§1.3 → §6.0.3/§6.0.4; §3.1 → §6.0.5/§9/§6.1).

### B.1 — Hunk 2 (§6.0.1 suite table): W4-IOT-1 **Profile `CBOR` → `COSE`** — DISJOINT from this file, but a NEW divergence on the B-H2 carry

C113 changed the handshake §6.0.1 suite table's W4-IOT-1 row Profile column from `CBOR` to `COSE` (applying C112's N1).

**Disjointness from security-framework's own surface:** security-framework §1.1 lists **only W4-BASE-1 (Encoding=COSE) and W4-FIPS-1 (Encoding=JOSE)** — there is **no W4-IOT-1 row** in this file, and both listed rows are undisputed corpus-wide. So the flip touches a normative surface security-framework neither owns nor cites. It is **not a security-framework finding.**

**BUT it is a genuine NEW divergence on the B-H2/W4-IOT-1 carry** that security-framework has carried since C31/C68, surfaced here by the inbound-carry scan. The three W4-IOT-1 sites now read:

| Site | Column semantics | W4-IOT-1 value |
|---|---|---|
| `protocols/web4-handshake.md:24` | column headed **"Profile"** | **COSE** (C113) |
| `core-spec/core-protocol.md:20` | column headed **"Profile"** | **CBOR** (unmoved) |
| `registries/initial-registries.md:7` | trailing parenthetical (no header) | **(CBOR)** (unmoved) |

**Snapshot-presence guard:** before C113, handshake's W4-IOT-1 Profile was `CBOR` — i.e. all three sites were `CBOR` and mutually **consistent**. C113 introduced the divergence. It is therefore **remediation-introduced (C113-side), C108-class** ("verbatim fix, imprecise cross-doc claim").

**Two same-column-vocabulary tables now contradict.** handshake and core-protocol both head this column literally **"Profile"** with sibling rows fixing the vocabulary as {COSE, JOSE}; they now disagree on W4-IOT-1 (COSE vs CBOR). This is stronger than a spelling drift — it is a direct value contradiction on identically-named columns.

**C112's corroboration was factually wrong.** C112's N1 justified the flip partly by asserting *"`core-protocol.md` §1 L20 independently says W4-IOT-1 Profile = COSE"* (C112 doc L15/L86). It does **not** — core-protocol's Profile column reads **CBOR**, both now and at C112 time (core-protocol never moved since eedd36fc). So C113 "fixed" handshake into disagreement with the very sibling C112 cited as authority.

**Which value is correct is the C-M1 ≡ B-D1 SSOT DESIGN-Q, not this auditor's call.** The taxonomy question is real: is the column a **Profile** (vocabulary {COSE, JOSE}, so CBOR is a category error and COSE is right, with CBOR being the *serialization* under the COSE profile) or an **Encoding** (vocabulary {COSE, CBOR, JSON})? Note security-framework itself heads its column **"Encoding"** with values {COSE, JOSE}, while core-protocol/handshake head theirs **"Profile"** — so even the *column name* is inconsistent across the corpus, which is part of what C-M1 must settle. **Mild inbound support for C112's Profile-is-COSE reading:** security-framework §1.3 L44 pairs the term as **"COSE/CBOR … as mandatory-to-implement (MTI)"** — treating CBOR as the serialization bound to the COSE profile, not as a standalone profile. That supports COSE-as-profile, but does **not** license this auditor to normalize the corpus: the divergence must be resolved as one SSOT decision (C-M1/B-D1), not per-file.

→ **CROSS-TRACK note on B-H2**, feeding the C-M1/B-D1 SSOT decision: (a) C113 introduced a handshake(COSE)↔core-protocol(CBOR)↔registries(CBOR) W4-IOT-1 Profile divergence; (b) C112's corroborating claim was false; (c) the fix should be settled at the SSOT (pick Profile-vs-Encoding column semantics + the W4-IOT-1 value once) rather than by flipping one table. **Not a security-framework mutation.**

### B.2 — Hunk 3 (§6.0.3 Sig-structure prose): touches a CITED section, but REINFORCES the anchor

C113 appended to handshake §6.0.3 "Sig structure": *"This governs non-handshake signed payloads (LCT binding, Metering); for `HandshakeAuth` the signing input is `Hash(TH ‖ channel_binding)` per §6.0.5, which governs the signed content, while this section governs the `COSE_Sign1` envelope and CBOR canonicalization."*

Security-framework §1.3 L50 cites §6.0.3 "for complete profile" and §1.3 L49 characterizes the COSE/CBOR profile as *"Payload is the canonical CBOR map."* The C113 clarification **does not break** this:
- §1.3's "Payload is the canonical CBOR map" describes the general COSE_Sign1 signing (still exactly what §6.0.3's Sig-structure says: "Sign the canonical CBOR map of the payload excluding any sig/envelope fields").
- The HandshakeAuth-specific nuance (signed content = `Hash(TH‖channel_binding)`) is a *specialization* that security-framework already defers to §6.0.5 via §3.1 L89 — so §1.3 (general profile) + §3.1 (HandshakeAuth specifics) together remain accurate.
- The `alg = -8` (L48) and `crv = 6` (L48) tokens security-framework mirrors are unchanged in §6.0.3.

→ **REINFORCES, does not break.** No finding.

### B.3 — Hunk 1 (banner) + untouched cited sections

- Hunk 1 = `Last-Updated` date bump only. Trivial.
- **§6.0.4 (JOSE, cited by §1.3 L55), §6.0.5 (session-binding, cited by §3.1 L89), §6.1 (`nonce`/`ts` fields, cited by §3.1), §9 (Anti-Replay & Clocks, cited by §3.1)** — **all UNtouched by C113** (the diff has no hunk in these ranges). Every anchor security-framework depends on for its N1 (C109) split cite still resolves and content-matches. The C109 N1 fix is thus corpus-stable, not silently invalidated.

---

## §C — Fresh-Internal Refute-by-Default Pass

**0 net-new internal contradictions.** Verified: §1.1 table ⟷ §1.2 prose (KEM/Sig/AEAD/Hash/KDF/Encoding token-match for both suites; `ECDSA-P256` table vs `ECDSA with P-256` prose = long-standing benign wording variant, not a finding); §1.3 MTI COSE/JOSE profiles ⟷ §1.1 W4-BASE-1/W4-FIPS-1 Encoding column; §2.3 rotation prose ⟷ LCT §7.3 cross-ref (unmoved, resolves); §3.1 L89 ⟷ live handshake §6.0.5/§9/§6.1 (all resolve post-C113). No standalone W4-IOT-1 statement exists in this file to be caught by the §B.1 corpus divergence.

---

## Findings Summary

| ID | Sev | Routing | Relation | One-line |
|----|-----|---------|----------|----------|
| — | — | — | — | **0 net-new AUTONOMOUS findings inside `security-framework.md`.** |
| **DELTA-1** | MEDIUM | CROSS-TRACK (feeds C-M1/B-D1) | NEW (C113-introduced, B-H2 carry) | C113 flipped handshake §6.0.1 W4-IOT-1 Profile `CBOR→COSE`, creating a same-column-vocabulary contradiction with `core-protocol.md:20` (Profile=CBOR) and `registries:7` (CBOR); C112's corroborating claim "core-protocol says COSE" is factually wrong. Resolve at the C-M1/B-D1 SSOT, not per-file. **Not a security-framework mutation.** |

**security-framework's FIRST fully-clean 3rd-delta for the file itself** — unlike C108 (which produced N1, remediated by C109), C140 finds **nothing to remediate inside security-framework**. The lone net-new corpus observation (DELTA-1) is a CROSS-TRACK carry-context update on B-H2 that lands in the handshake/core-protocol/registries cluster and feeds the standing C-M1 SSOT DESIGN-Q.

---

## Disposition Ledger (for C141 remediation slot)

**AUTONOMOUS (fix inside `security-framework.md`) — 0.** C141 (security-framework remediation slot) is a **no-op** → rotation advances to `registries/initial-registries.md` 3rd-delta.

**DESIGN-Q (operator canonicity, recorded not resolved) — carried forward:**
- **C-M1 ≡ C70-B-D1**: canonical crypto-suite registry SSOT — **now with a fresh, sharper instance**: settle (a) column semantics Profile-vs-Encoding and (b) the W4-IOT-1 value, once, so the three tables stop contradicting. DELTA-1 is the concrete artifact to attach to this decision.
- **B-3**: authorization basis — VCs vs SAL law-oracle/rights-obligations.
- **B-9 / B-M2**: key-rotation mutate-identifier vs stable-subject-DID + new LCT.
- **B-H2 / B-11**: W4-IOT-1 + `AES-CCM` inclusion in SDK/vectors (registry-orphan sub-facet resolved by C71; SDK/vector sub-facet stands; DELTA-1 adds the Profile-column contradiction).

**CROSS-TRACK (fix lands elsewhere) — carried forward:**
- **DELTA-1 (new)**: route to the handshake/core-protocol/registries cluster — the C113 flip needs either core-protocol+registries to follow to COSE, or handshake to revert to CBOR, per the C-M1/B-D1 decision; flag that C112's corroboration was false so the next handshake remediation doesn't re-cite it.
- **B-7**: normalize 5 sibling FIPS-KEM spellings to `ECDH-P256` (gated on C-M1/B-D1).
- **B-8**: update SDK `security.py:146` docstring quote to current §1.1 wording.
- **B-10**: `cose:ES256` → `cose:EdDSA` in `LCT-linked-context-token.md`, `lct-capability-levels.md`, `multi-device-lct-binding.md`.
- **B-L6 / B-L7**: vector-file ownership split; `device` W4ID method vs SDK `KNOWN_METHODS`.

---

## Outcome

**First fully-clean 3rd-delta for security-framework.md** (0 net-new inside the file). The C108→C109 N1 loop is verified closed: the split cite is present, precise, and corpus-stable (C113 left §6.0.4/§6.0.5/§6.1/§9 untouched). All 8 carries stand; all CROSS-TRACK carry sources are byte-stable at source.

**Key lesson (C140):** on a frozen target whose only moved sibling is a *remediated* sibling, the highest-yield check is **reading the sibling's remediation rationale, not just diffing its bytes** — C113's diff looks like a benign one-token flip (`CBOR→COSE`), but its C112 rationale reveals the flip was justified by a **false cross-doc corroboration** ("core-protocol says COSE" — it says CBOR), and the flip *introduced* a same-column-vocabulary contradiction that was consistent before. This is the C108-class "verbatim fix, imprecise claim" pattern reappearing **on the sibling side** and surfacing on THIS file's B-H2 carry — the disjointness test ("did the mover touch a section this file cites?") correctly says "no, security-framework has no W4-IOT-1 row," but the **carry-scan** ("does the mover disturb a corpus invariant this file has been tracking?") says "yes." Both tests are needed; the disjointness test alone would have missed DELTA-1. The correct disposition is still route-not-mutate: the value is an SSOT decision (C-M1/B-D1), and security-framework stays byte-frozen.

---

*Audit produced under Autonomous Session Protocol v2 — slot `125256`, LEAD voice. Read-only: no spec, SDK, or test-vector files were modified this turn. Remediation (C141) is the next alternation turn and is a no-op (0 AUTONOMOUS findings) → rotation advances to `registries/initial-registries.md`.*
