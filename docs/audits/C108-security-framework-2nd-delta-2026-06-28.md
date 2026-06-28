# C108 — `security-framework.md` Second Delta Re-Audit

**Audit ID**: C108
**Target**: `web4-standard/core-spec/security-framework.md` (97 lines) — Web4 Security Framework (crypto suites, key management, authentication/authorization)
**Date**: 2026-06-28
**Auditor**: autonomous web4 session (legion, slot `000036`), v2 protocol, LEAD voice
**Type**: Second delta re-audit. Lineage **C31** (2026-06-04) → **C68** (first delta, 2026-06-17) → **C69** remediation (#350, `3d04dd5c`) → **C108**.
**Prior audit docs**: `docs/audits/C31-security-framework-audit-2026-06-04.md`, `docs/audits/C68-security-framework-delta-audit-2026-06-17.md`.

---

## Method & Byte-Stability

`git diff 3d04dd5c HEAD -- web4-standard/core-spec/security-framework.md` is **empty** — the file is **byte-identical to its C69 remediation** and has been since 2026-06-17 (**11 days frozen**). This is the **9th consecutive frozen audit target** (after C92/C94/C96/C98/C100/C102/C104/C106). Per the locked frozen-wrap pattern, §A is verification (did every C69 fix hold token-by-token at every mirror; do all carries still hold bidirectionally), and the §B yield lives entirely on the **corpus-delta surface** — the cited siblings that *moved* since C69 — plus the **inbound-carry scan** of those siblings' own audit docs.

- **§A** — token-by-token verification of the 6 C69 autonomous fixes + regression/artifact/numbering sweep + C56 remediation-completeness (re-read each fix's *claim* against canonical) + bidirectional re-verification of all 8 C68 carries.
- **§B** — corpus-delta over the 3 cited siblings that moved AFTER C69 (`registries/initial-registries.md` C71 #354 2026-06-18; `protocols/web4-handshake.md` C73 #362 2026-06-18; `multi-device-lct-binding.md` C81 #372 2026-06-21) + inbound-carry scan of their audit docs (C70/C72/C80). Every divergence checked against the **C69 snapshot** (`git show 3d04dd5c`) before being called net-new (snapshot-presence guard).
- **§C** — single fresh-internal refute-by-default pass (proportionality: a 9th frozen wrap does not warrant a finder fleet).

**Severity**: HIGH = correctness/normative contradiction; MEDIUM = cross-spec divergence; LOW = hygiene/precision; INFO = positive confirmation.
**Routing**: AUTONOMOUS (fix inside `security-framework.md`) / DESIGN-Q (operator canonicity) / CROSS-TRACK (lands elsewhere).

---

## §A — Prior-Finding Verification, Regression, Completeness, Carry

### A.1 — All 6 C69 autonomous fixes HELD token-by-token (0 regression, 0 artifacts)

| C68 ID | C69 fix | Current state | Verdict |
|---|---|---|---|
| **B-1** | §1.3 COSE `crv`/`alg` → COSE-numeric | L48 `Ed25519 with \`crv = 6\` (COSE curve label) and \`alg = -8\` (EdDSA)` | **HELD** |
| **B-2** | §3.1 add handshake §6.0.5 deference | L89 cites `web4-handshake.md` Section 6.0.5 for session-binding/freshness/nonce/replay | **HELD** (but see N1) |
| **B-4** | §1.1 column `Profile` → `Encoding` | L14 header `… KDF \| Encoding \| Status` | **HELD** |
| **B-5** | §1.1 add `KDF` column | L14/16/17 carry `HKDF-SHA256` | **HELD** |
| **B-6** | §1.2 COSE `RFC 8152` → `RFC 9052/9053` | L32 `COSE (RFC 9052/9053, obsoletes RFC 8152)` | **HELD** |
| **B-9 interim** | §2.3 first clause stop asserting in-place identifier mutation | L78 `… generating a new key pair and issuing a new LCT bound to the new public key` | **HELD** |

Regression sweep clean: no `&#`/`&amp;`/mojibake artifacts; section numbering sequential (§1/1.1/1.2/1.3, §2/2.1/2.2/2.3, §3/3.1/3.2); §1.1 table tokens match §1.2 prose (`ECDSA-P256` table vs `ECDSA with P-256` prose is the long-standing benign wording variant for one algorithm, not a finding); §1.3 MTI COSE profile (Ed25519/EdDSA) consistent with §1.1 W4-BASE-1; §1.3 JOSE ES256 consistent with §1.1 W4-FIPS-1 (ECDSA-P256+JOSE).

### A.2 — C56 remediation-completeness: the B-2 fix's *claim* does not hold against the canonical handshake doc → N1

Re-reading the B-2 fix's claim token-by-token against the source it cites surfaces one **remediation-completeness defect** (the recurring one-sided-claim pattern, [[feedback_remediation_introduced_regression]]). §3.1 L89 (written by C69) defers thus:

> *See `web4-handshake.md` Section **6.0.5** for the normative session-binding, **freshness, nonce-uniqueness, and replay-protection** requirements that a conformant challenge-response MUST satisfy.*

But handshake **§6.0.5 "Binding to Session (MUST)"** normatively contains **only session-binding** (`Hash(TH || channel_binding)`, `channel_binding = epk_I || epk_R`, kid-authorization). The three other named properties live elsewhere in the handshake doc:
- **freshness** → §6.1 L198 (`check freshness (see §9)`) + §9 L242 (`Accept \`ts\` within ±300s`)
- **nonce-uniqueness** + **replay-protection** → **§9 "Anti-Replay & Clocks"** L235-241 (`nonce` MUST be unique within the HPKE `context_key` scope; replay window ≥300s).

So the deference over-attributes 3 of its 4 named properties to §6.0.5; a precise reader following the §6.0.5 pointer for replay-protection lands on a session-binding-only section. **Snapshot-presence guard: this was already true at the C69 snapshot** — `git show 3d04dd5c` shows §6.0.5 covered only session-binding then too, with nonce-uniqueness at §9 L210 and freshness at §6.1 L177. C73 did **not** introduce it; it is a self-contained imprecision in the C69 B-2 wording (C68's finding correctly cited §6.0.5 *plus* L177 *plus* L210, but C69 collapsed all three line-cites into the single anchor "Section 6.0.5"). → **N1**, LOW, AUTONOMOUS.

### A.3 — Bidirectional carry re-verification (current corpus)

| C68 carry | Routing | Status at C108 |
|---|---|---|
| **B-3** §3.2 "authz based on VCs" vs SAL/R6 | DESIGN-Q | **OPEN, unchanged** — §3.2 L91-95 verbatim; operator canonicity decision stands |
| **B-7** FIPS-KEM 1-vs-4 mirror-drift | CROSS-TRACK | **OPEN, CROSS-CONFIRMED + WIDENED to 5 sites** — see §B; canonical token `ECDH-P256` (= this file) validated by C70-B-C4 |
| **B-8** SDK docstring quotes deleted A-L2 phrase | CROSS-TRACK | **OPEN, unchanged** — `web4-standard/implementation/sdk/web4/security.py:146` still reads `Per spec: "Other suites MAY be offered but MUST NOT be negotiated as MTI."` (deleted from §1.1 by C31 A-L2) |
| **B-9 / B-M2** rotation mutate-vs-stable-DID | DESIGN-Q | **interim HELD** (§2.3 L78); mutate-vs-stable-DID semantics decision stands |
| **B-10** `cose:ES256` mislabel in LCT/multi-device | CROSS-TRACK | **OPEN, unchanged** — `multi-device-lct-binding.md:257/270` (line nums shifted by unrelated C81 edits; `git diff 3d04dd5c HEAD` shows the `cose:` labels themselves untouched) |
| **C-M1** canonical crypto-suite registry SSOT | DESIGN-Q | **OPEN = C70-B-D1**; registries auditor recommends operator decide before next security-framework remediation (see §B) |
| **B-H2 / B-11** W4-IOT-1 + AES-CCM orphan | DESIGN-Q | **SPLIT** — "registry orphan" sub-facet **RESOLVED** downstream (C71 #354 registered W4-IOT-1 at `initial-registries.md:7` + `core-protocol.md:20`, both `AES-CCM/HKDF/CBOR`); "absent from SDK `SUITES`/`CryptoSuiteId` + conformance vectors" sub-facet **STANDS** (grep of SDK+`test-vectors/` for `W4-IOT-1`/`AES-CCM` is empty) |
| **B-L6 / B-L7** vector ownership; `device` W4ID method | CROSS-TRACK | OPEN, unchanged (file-organization / `data-formats.md` did not move after C69) |

---

## §B — Corpus-Delta Over Moved Siblings (the only net-new yield surface)

Three cited siblings moved after the C69 snapshot. Each was diffed against `3d04dd5c` and its audit doc read for items routed back here.

### B.1 — `registries/initial-registries.md` (C71 #354, 2026-06-18) — REINFORCES B-5, B-7 spelling stands, C-M1 elevated
- The W4-FIPS-1 suite-summary line gained **`/ HKDF`** (`P-256 ECDH / ECDSA-P256 / AES-128-GCM / SHA-256 / HKDF (JOSE)`, L6) — the same KDF dimension C69's **B-5** added to this file's §1.1 table. The two remediations are mutually reinforcing; the corpus is converging on a uniform KEM/Sig/AEAD/Hash/**KDF**/Encoding column set.
- The FIPS-KEM **spelling** is unchanged (`P-256 ECDH`) → **B-7 1-vs-4 split STANDS**.
- **Inbound (C70-B-C4)**: the registries-cluster audit independently re-found the FIPS-KEM divergence and **explicitly cross-references the C68 B-7 carry** — counting it as **5 sites** (`P-256ECDH` / `P-256 ECDH` / `P-256EC` / `ECDH-P256` / long-form `ECDH with P-256, FIPS 186-4`) and recommending the short token **`ECDH-P256`** — i.e. *this file's* value. Independent confirmation hardens B-7 and validates the C31 B-H1 fix as the canonical anchor.
- **Inbound (C70-B-D1)**: the registries SSOT canonical-form decision is named the "registry-side root" of the suite/error divergences and the auditor recommends the operator **decide it before the next security-framework remediation** so C109 mirrors a settled SSOT rather than re-litigating per file. **C-M1 ≡ C70-B-D1** — same operator decision, now with a sequencing recommendation.

### B.2 — `protocols/web4-handshake.md` (C73 #362, 2026-06-18) — REINFORCES the B-1/B-2 anchor targets
Security-framework §1.3/§3.1 anchor their MTI COSE profile and auth requirements to this doc's §6.0.3/§6.0.4/§6.0.5. All three anchors **resolve and content-match**:
- §6.0.3 COSE/CBOR Profile (MUST) — `alg = -8` (EdDSA) L140, `crv = 6` L144 → token-exact with §1.3 L48.
- §6.0.4 JOSE/JSON Profile (SHOULD) — `alg = "ES256"` L150 → matches §1.3 L52-55.
- §6.0.5 Binding to Session (MUST) — session-binding L156 (see N1 for the non-binding properties).

C73 **improved** the anchor targets rather than breaking them: it **added** the `channel_binding = epk_I || epk_R` serialization to §6.0.5 (C72-B10) and **reshaped** the §6.1 `HandshakeAuth` example into a valid §6.0.3 `COSE_Sign1` envelope (C72-B3) — so the COSE profile this file mirrors is now internally consistent with its own wire example. This is the same reinforce-not-break dynamic seen in prior wraps (mcp-C77 / atp-adp-C79). No item in C72 routed back to security-framework.

### B.3 — `multi-device-lct-binding.md` (C81 #372, 2026-06-21) — B-10 untouched
`git diff 3d04dd5c HEAD` shows the `cose:ES256` labels (now L257/270) **unchanged**; C80/C81 routed nothing to security-framework (C80 scan: 0 hits). B-10 stands as a CROSS-TRACK carry on the multi-device side.

---

## §C — Fresh-Internal Refute-by-Default Pass

**0 net-new internal contradictions.** Verified: §1.1 table ⟷ §1.2 prose (KEM/Sig/AEAD/Hash/KDF/Encoding token-match for both suites); §1.3 MTI COSE/JOSE profiles ⟷ §1.1 W4-BASE-1/W4-FIPS-1 encoding column; §2.3 rotation prose ⟷ its own LCT §7.3 cross-ref (B-9 interim removed the self-contradiction); all `See …` cross-refs (LCT §7.3, handshake §6.0.3/§6.0.4/§6.0.5) resolve to live sections. The §3.1 anchor imprecision (N1) was surfaced by the C56 claim-vs-canonical re-read, not this pass.

---

## §B — Findings Summary

| ID | Sev | Routing | Relation | One-line |
|----|-----|---------|----------|----------|
| **N1** | LOW | AUTONOMOUS | NEW (C69 B-2 completeness) | §3.1 L89 over-attributes freshness/nonce-uniqueness/replay to handshake **§6.0.5**, which covers only session-binding; those properties live in **§6.1/§9 (Anti-Replay & Clocks)** |

**1 distinct net-new actionable (0 HIGH / 0 MED / 1 LOW).** All 8 prior carries re-verified (B-3/B-9/C-M1 DESIGN-Q stand; B-7 cross-confirmed+widened; B-8/B-10/B-L6/B-L7 stand; B-H2/B-11 split — orphan sub-facet resolved, SDK/vector sub-facet stands).

### N1 (LOW, AUTONOMOUS) — §3.1 deference over-attributes 3 properties to §6.0.5
**Routing**: AUTONOMOUS. Widen the §3.1 cite so each property points where it normatively lives, e.g. *"See `web4-handshake.md` §6.0.5 for session binding and §9 (Anti-Replay & Clocks) for the freshness, nonce-uniqueness, and replay-protection requirements …"* (§6.1 carries the `nonce`/`ts` fields; §9 carries the rules). Does **not** pre-empt any DESIGN-Q. Snapshot-guard: present since C69, not sibling-introduced — a self-contained refinement of the C69 B-2 wording.

---

## Disposition Ledger (for C109 remediation)

**AUTONOMOUS (fix inside `security-framework.md`) — 1:**
- **N1**: §3.1 L89 — split the deference cite to §6.0.5 (session binding) + §9 (Anti-Replay & Clocks); optionally name §6.1 for the `nonce`/`ts` carrier fields. *BC#5 corpus sweep before the token edit.*

**DESIGN-Q (operator canonicity, recorded not resolved) — carried forward:**
- **B-3**: authorization basis — VCs vs SAL law-oracle/rights-obligations.
- **B-9 / B-M2**: key-rotation mutate-identifier vs stable-subject-DID + new LCT.
- **C-M1 ≡ C70-B-D1**: canonical crypto-suite registry SSOT — registries auditor recommends the operator decide **before C109** so the suite-spelling normalization mirrors a settled SSOT. **If B-D1 resolves before C109, the C109 slot becomes the B-7 5-site normalization pass; if it stays open, C109 applies N1 only and leaves B-7 gated.**
- **B-H2 / B-11**: W4-IOT-1 + `AES-CCM` inclusion in SDK/vectors (orphan sub-facet already resolved by C71 registration).

**CROSS-TRACK (fix lands elsewhere) — carried forward:**
- **B-7**: normalize 5 sibling FIPS-KEM spellings to `ECDH-P256` (gated on C-M1/B-D1; cross-confirmed by C70-B-C4).
- **B-8**: update SDK `security.py:146` docstring quote to current §1.1 wording.
- **B-10**: `cose:ES256` → `cose:EdDSA` in `LCT-linked-context-token.md`, `lct-capability-levels.md`, `multi-device-lct-binding.md`.
- **B-L6 / B-L7**: vector-file ownership split; `device` W4ID method vs SDK `KNOWN_METHODS`.

---

## Outcome

**9th consecutive frozen target — but NOT zero net-new.** Unlike the prior 8 frozen wraps, C108 produced **one distinct LOW autonomous finding (N1)**: the C56 claim-vs-canonical re-read caught that the C69 B-2 deference points at the wrong handshake section for 3 of its 4 named properties. **C109 (security-framework remediation slot) is therefore NOT a no-op** — it applies N1 (and, if the operator resolves C-M1/B-D1 first, the gated B-7 5-site normalization). All other yield was on the corpus-delta + inbound-carry surface: C70-B-C4 cross-confirmed B-7 as a 5-site bundle with `ECDH-P256` as canonical; C70-B-D1 ≡ C-M1 gained an operator-sequencing recommendation; C71 reinforced B-5; C73 reinforced (did not break) the B-1/B-2 anchors; C71 resolved the B-H2 registry-orphan sub-facet while the SDK/vector sub-facet stands.

**Key lesson**: the frozen-wrap §A pass must include the **C56 claim-vs-canonical re-read even when the target is byte-stable and all fixes "held"** — a fix can land verbatim (B-2 deference present and correct on its face) yet its *claim* be imprecise against the canonical source (§6.0.5 doesn't contain 3 of the 4 properties it's cited for). "HELD token-by-token" verifies the edit is present; "claim holds against canonical" is a distinct, stronger check that catches remediation-introduced imprecision. Also confirms the C106 split-the-sub-facet discipline: a sibling's own remediation (C71) can resolve part of a carry (W4-IOT-1 registry orphan) while another part (SDK/vector absence) and the parent design-Q stay open.

---

*Audit produced under Autonomous Session Protocol v2 — slot `000036`, LEAD voice. Read-only: no spec, SDK, or test-vector files were modified this turn. Remediation (C109) is the next alternation turn.*
