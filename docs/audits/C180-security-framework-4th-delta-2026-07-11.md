# C180 — `security-framework.md` Fourth Delta Re-Audit (5th pass)

**Audit ID**: C180
**Target**: `web4-standard/core-spec/security-framework.md` (97 lines) — Web4 Security Framework (crypto suites, key management, authentication/authorization)
**Date**: 2026-07-11
**Auditor**: autonomous web4 session (legion, slot `180036`), v2 protocol, LEAD voice
**Type**: **Fourth delta re-audit** (5th pass overall). Lineage: **C31** (first-pass, 2026-06-04, #268 → remediation #271 `130069d8`, 5 autonomous) → **C68** (first delta, 2026-06-17) → **C69** remediation (#350 `3d04dd5c`, 6 autonomous) → **C108** (second delta, 2026-06-28) → **C109** remediation (#396 `eedd36fc`, applied N1) → **C140** (third delta, 2026-07-05, **0 net-new inside the file**) → **C180**.
**Prior audit docs**: `C31-security-framework-audit-2026-06-04.md`, `C68-security-framework-delta-audit-2026-06-17.md`, `C108-security-framework-2nd-delta-2026-06-28.md`, `C109-security-framework-remediation-2026-06-28.md`, `C140-security-framework-3rd-delta-2026-07-05.md`.

**Method note**: `git diff eedd36fc HEAD -- web4-standard/core-spec/security-framework.md` is **empty** — the file is **byte-identical to its C109 remediation** and has been for **~13 days** (last touch `eedd36fc`, 2026-06-28 10:03). Per the locked frozen-wrap proportionality precedent (policy-reviewed and APPROVED this fire), §A is verification, §B is the corpus-delta surface (cited/carry siblings that *moved* since the **C140 snapshot**, 2026-07-05), **§B′ is the first-class SDK-mirror audit** applying the C172/C174/C176/C178 guard, and §C is a single fresh-internal refute-by-default pass.

**Headline**: `security-framework.md`'s **second consecutive fully-clean delta for the file itself** (C140 + C180), **0 net-new AUTONOMOUS findings inside the file**. §B is **empty** (no cited/carry sibling moved since the C140 snapshot). The entire yield lives in **§B′**: the **first-ever audit of the ratified Rust crypto mirror `web4-core/src/crypto.rs`** (present since 2026-01-22, invisible to all four prior security passes). Unlike errors' *false* `error.rs` (C178), `crypto.rs` is a **GENUINE mirror** — and its result is largely a **positive concordance**: web4-core implements **5 of 6** W4-BASE-1 mandatory primitives (X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 / HKDF-SHA256) **exactly** as §1.1/§1.2 specify, and correctly omits the SHOULD-only W4-FIPS-1 suite. The one gap — the **6th** primitive, the §1.3 **mandatory-to-implement (MTI) COSE/CBOR Encoding** — is **unimplemented corpus-wide in web4-core** (0 non-comment `cose`/`cbor`/`ciborium` refs). Direction: **spec CORRECT (COSE is MTI), SDK LAGS** — the concrete Rust-side instance of the standing **C-M1/B-D1/DELTA-1/C144** COSE-vs-CBOR encoding cluster. Recorded as **C180-N1 (LOW, CROSS-TRACK/SDK)** + **C180-N2 (INFO, positive-confirmation + false-mirror-boundary map)**.

---

## Scope & Methodology

Because `security-framework.md` is unchanged since its C109 remediation, §A applies the **C56 completeness method** (audit the remediation's *claims* token-by-token, not merely "is the edit present") and the **bidirectional carry re-check** (C62/C64). §B follows the frozen-wrap lesson: yield lives on the **corpus-delta surface** (siblings moved since the last snapshot) + the **SDK-mirror expansion** (C172/C174/C176 — the untracked Rust mirror is where the net-new has lived on every recent frozen-but-clean delta). §B′ applies the **C178 boundary lesson**: *before* running divergence analysis, verify the candidate is a **GENUINE** mirror (a name-collision like errors' `error.rs` or `web4-trust-core::EntityType` is a FALSE mirror — exclude, do not misread absence as a gap). Snapshot-presence guard (C98) applied throughout.

**Structure note (MUST-vs-reference-impl doc-specific check, C120/C121):** `security-framework.md` has **no normative-summary / §12-style section** (§1 crypto suites / §2 key management / §3 auth). The "normative-summary restates entity MUSTs unconditionally" defect class **does not apply** — no MUST-vs-impl sweep warranted (re-confirmed from C140).

**Severity**: HIGH = correctness/normative contradiction; MEDIUM = cross-spec divergence; LOW = hygiene/precision or SDK-lag on an MTI; INFO = positive confirmation / forward-awareness.
**Routing**: AUTONOMOUS (fix inside `security-framework.md`) / DESIGN-Q (operator canonicity) / CROSS-TRACK (lands elsewhere — SDK / sibling spec).

---

## §A — Prior-Finding Verification, Regression, Completeness, Carry

### A.1 — All 6 C69 fixes + the 1 C109 fix: **HELD by byte-freeze (0 regression, 0 artifacts)**

`security-framework.md` has not changed a byte since C109 (`eedd36fc`, ~13 days). C140 verified all seven token-by-token and found them HELD; the byte-freeze mechanically preserves that verdict. Re-confirmed against the live file:

| ID | Fix | Current state (live line) | Verdict |
|---|---|---|---|
| **B-1** (C69) | §1.3 COSE `crv`/`alg` → COSE-numeric | L48 `Ed25519 with \`crv = 6\` (COSE curve label) and \`alg = -8\` (EdDSA)` | **HELD** |
| **B-4** (C69) | §1.1 column `Profile` → `Encoding` | L14 header `… KDF \| Encoding \| Status` | **HELD** |
| **B-5** (C69) | §1.1 add `KDF` column | L14/L16/L17 carry `HKDF-SHA256` | **HELD** |
| **B-6** (C69) | §1.2 COSE `RFC 8152` → `RFC 9052/9053` | L32 `COSE (RFC 9052/9053, obsoletes RFC 8152)` | **HELD** |
| **B-9 interim** (C69) | §2.3 stop asserting in-place identifier mutation | L78 `… generating a new key pair and issuing a new LCT bound to the new public key` | **HELD** |
| **B-2** (C69) | §3.1 add handshake deference | superseded by C109 N1 (below) | **HELD → widened by N1** |
| **N1** (C109) | §3.1 split the over-broad §6.0.5 cite so each property points where it normatively lives | L89 `… §6.0.5 (Binding to Session) for the normative session-binding requirement, and §9 (Anti-Replay & Clocks) for the freshness, nonce-uniqueness, and replay-protection requirements …; the \`HandshakeAuth\` \`nonce\`/\`ts\` fields these rules operate on are defined in §6.1` | **HELD — precise** |

**Regression sweep clean:** `grep -c '&#'` = 0; no `&amp;`/mojibake; section numbering sequential (§1/1.1/1.2/1.3, §2/2.1/2.2/2.3, §3/3.1/3.2); §1.1 table tokens match §1.2 prose; §1.3 MTI COSE profile (Ed25519/EdDSA) consistent with §1.1 W4-BASE-1; §1.3 JOSE ES256 consistent with §1.1 W4-FIPS-1. PR #396 was a single-file diff → cross-file regression surface nil.

### A.2 — C56 remediation-completeness re-read: **clean**

Re-reading each fix's *claim* token-by-token against canonical (the check that surfaced C108's N1): the C109 N1 split-cite claim still holds — §6.0.5 IS session-binding-only, §9 ("Anti-Replay & Clocks") DOES carry freshness (`ts` ±300s) + nonce-uniqueness + replay window, §6.1 DOES define the `nonce`/`ts` fields. No residual one-sided-claim defect. B-6 `RFC 9052/9053, obsoletes RFC 8152` holds. **No new completeness defect.**

### A.3 — Bidirectional carry re-verification (against the current corpus)

All 8 standing carries re-verified live. **None resolved into a defect; none regressed.**

| Carry | Routing | Status at C180 (live evidence) |
|---|---|---|
| **B-3** §3.2 "authz based on VCs" vs SAL/R6 | DESIGN-Q | **OPEN, unchanged** — §3.2 L91-95 verbatim; operator canonicity stands |
| **B-7** FIPS-KEM spelling 5-site mirror-drift | CROSS-TRACK | **OPEN, unchanged** — all 5 spellings still divergent (live grep): `P-256ECDH` (core-protocol:19) / `P-256 ECDH` (registries:6) / `P-256EC` (handshake:23) / `ECDH-P256` (this file L17/L35) / long-form `ECDH with P-256, FIPS 186-4` (this file L35). Canonical target = `ECDH-P256`. None moved since eedd36fc |
| **B-8** SDK docstring quotes deleted A-L2 phrase | CROSS-TRACK | **OPEN, unchanged** — `implementation/sdk/web4/security.py` unmoved since 2026-04-17 (`759eaefa`, pre-C140) |
| **B-9 / B-M2** rotation mutate-vs-stable-DID | DESIGN-Q | **interim HELD** (§2.3 L78); semantics decision stands |
| **B-10** `cose:ES256` mislabel | CROSS-TRACK | **OPEN, unchanged** — live grep = **8** `cose:ES256` sites across `lct-capability-levels.md` (5), `LCT-linked-context-token.md` (1), `multi-device-lct-binding.md` (2); target `cose:EdDSA`. None moved since eedd36fc |
| **C-M1 ≡ C70-B-D1** canonical crypto-suite registry SSOT | DESIGN-Q | **OPEN** — **now with a fresh Rust-side instance** (§B′.2 C180-N1: web4-core does not implement the MTI COSE encoding at all) |
| **B-H2 / B-11** W4-IOT-1 + AES-CCM | DESIGN-Q / CROSS-TRACK | **OPEN, unchanged since C140** — the C140 DELTA-1 W4-IOT-1 Profile contradiction (handshake COSE ↔ core-protocol/registries CBOR) is intact; handshake did **not** move since the C140 snapshot |
| **B-L6 / B-L7** vector ownership; `device` W4ID method | CROSS-TRACK | OPEN, unchanged (`data-formats.md` unmoved) |

**C140 DELTA-1 status**: recorded as a CROSS-TRACK carry feeding C-M1/B-D1. Handshake §6.0.1 (the W4-IOT-1 Profile=COSE site) has **not moved since C140** → DELTA-1 is unchanged, still open, still routed to the SSOT decision. No re-adjudication owed this cycle.

---

## §B — Corpus-Delta Pass (siblings moved since the C140 snapshot, 2026-07-05)

Checked every sibling `security-framework.md` cites or holds a carry-mirror in, via `git log <snapshot>..HEAD -- <file>`:

| Sibling | Cited/carry role | Last touch | Moved since C140 (2026-07-05)? |
|---|---|---|---|
| `protocols/web4-handshake.md` | §1.3 → §6.0.3/§6.0.4; §3.1 → §6.0.5/§9/§6.1 | `57caa2e1` 2026-06-29 | **No** (C113 was pre-C140; C140 already audited it) |
| `core-spec/core-protocol.md` | B-7 / W4-IOT-1 mirror | `3084e4d2` 2026-06-05 | No |
| `registries/initial-registries.md` | B-7 / W4-IOT-1 mirror | `3f1d6fad` 2026-06-18 | No |
| `core-spec/LCT-linked-context-token.md` | §2.3 rotation (§7.3); B-10 | `9d1933f8` 2026-06-15 | No |
| `core-spec/multi-device-lct-binding.md` | B-10 `cose:ES256` | `a6cbde92` 2026-06-21 | No |
| `core-spec/lct-capability-levels.md` | B-10 `cose:ES256` | `a3fee0e1` 2026-06-14 | No |
| `implementation/sdk/web4/security.py` | B-8 docstring | `759eaefa` 2026-04-17 | No |

**Result: ZERO cited/carry siblings moved since the C140 snapshot.** §B is **empty — 0 findings routed to `security-framework.md`.** (Corpus movement since 2026-07-05 was in `acp-framework.md` (C159), `lct.rs` (#503/#504), `errors.md` audits, and whitepaper-web — **none** cited by or carry-mirrored in security-framework. The rotation cadence (~2 days/file) outpaces this frozen cluster's churn, so the wrap lands on a fully-stable cited surface — the expected frozen-wrap pattern.)

---

## §B′ — SDK-Mirror Expansion (C172/C174/C176/C178 guard — FIRST audit of the Rust crypto mirror)

The guard's premise: a frozen spec can be clean vs its last-cycle surface yet blind to a Rust impl the earlier passes never audited. For security, the candidate mirror is **`web4-core/src/crypto.rs`** (+ its AEAD/KDF siblings `pair_channel.rs` / `vault/crypto.rs`). **No prior security audit (C31/C68/C108/C140) touched it** — `crypto.rs` has existed since 2026-01-22 (`e89048b0`), predating the entire C-series, and the SDK-mirror expansion method only began at C172. This is its **first audit**, exactly as C172 was the first audit of `lct.rs` and C174 of `society.rs`.

### B′.1 — Genuine-mirror gate (C178 boundary lesson): **PASS — this is a GENUINE mirror**

Before divergence analysis, the C178 lesson requires confirming the candidate actually mirrors the spec taxonomy (errors' `error.rs` failed this — a name-collision internal enum with no wire codes). `crypto.rs` **passes**: it is a direct implementation of the §1 W4-BASE-1 cryptographic primitives, not a name-collision. Evidence (source + `Cargo.toml`):

| §1.1 W4-BASE-1 primitive | Spec value | web4-core implementation | Match? |
|---|---|---|---|
| **KEM** | X25519 (RFC 7748) | `x25519-dalek 2.0`; `crypto.rs` X25519 ECDH via Ed25519→X25519 conversion (RFC 8032 §5.1.5 + RFC 7748 clamping), `ed25519_seed_to_x25519_secret` / `ed25519_to_x25519_public` | **✓ exact** |
| **Sig** | Ed25519 (RFC 8032) | `ed25519-dalek 2.1`; `crypto.rs` `KeyPair::sign` / `PublicKey::verify` | **✓ exact** |
| **AEAD** | ChaCha20-Poly1305 (RFC 8439) | `chacha20poly1305 0.10`; `pair_channel.rs` seal/open (12-byte nonce, 16-byte Poly1305 tag) | **✓ exact** |
| **Hash** | SHA-256 (FIPS 180-4) | `sha2 0.10`; `crypto.rs` `sha256` / `sha256_hex` | **✓ exact** |
| **KDF** | HKDF-SHA256 (RFC 5869) | `hkdf 0.12`; `pair_channel.rs` `Hkdf::<Sha256>` session-key derivation | **✓ exact** |
| **Encoding** | **COSE (RFC 9052/9053)** | **— none —** (see B′.2) | **✗ absent** |

**5 of 6 W4-BASE-1 primitives are implemented EXACTLY as the mandatory suite specifies.** This is a strong **positive concordance**: the ratified Rust core's cryptographic algorithm selection is byte-faithful to `security-framework.md` §1.1/§1.2. **W4-FIPS-1** (the SHOULD suite — ECDH-P256/ECDSA-P256/AES-128-GCM/JOSE) is **not implemented** (no `p256`/`aes-gcm`/`ecdsa` deps) — this is **concordant**, since §1.1 marks W4-FIPS-1 as SHOULD, and a mandatory-only implementation (`Implementations MUST support W4-BASE-1`) is conformant. **Not a finding — recorded as positive confirmation (C180-N2).**

### B′.2 — The one gap: **§1.3 MTI COSE/CBOR Encoding is UNIMPLEMENTED in web4-core (C180-N1, LOW)**

`security-framework.md` §1.1 lists W4-BASE-1 **Encoding = COSE**, and §1.3 states the strongest form of this requirement:

> "All Web4 signed payloads **MUST** implement COSE/CBOR (Ed25519/EdDSA) as mandatory-to-implement (MTI). … Deterministic CBOR encoding per CTAP2 … Ed25519 with `crv = 6` and `alg = -8` (EdDSA) … Payload is the canonical CBOR map."

**web4-core does not implement this at all.** Corpus-wide grep over `web4-core/src/` + `Cargo.toml`: **0 non-comment references** to `cose` / `cbor` / `ciborium` / `minicbor` / `COSE_Sign1`. Concretely:
- `crypto.rs` `SignatureBytes` is a raw 64-byte Ed25519 signature serialized via **serde (hex)** — not a `COSE_Sign1` envelope, no `crv`/`alg` COSE headers, no CBOR canonicalization.
- `pair_channel.rs` sealed payload = `nonce_12 || ciphertext`, **base64**-transported — not COSE/CBOR.
- The crate's only serialization dependency is **`serde_json`** (+ `hex`). There is no CBOR/COSE codec in the dependency graph.

So the ratified Rust core signs and serializes with **JSON/hex/base64**, while the spec makes the **COSE/CBOR envelope MANDATORY-TO-IMPLEMENT**. The 5/6 primitive concordance is at the **algorithm** layer; the divergence is at the **encoding/envelope** layer.

**Adjudication (refute-by-default, per-finding direction — the C172/C174/C176 discipline):**
- Is this a **spec** defect? **No.** §1.3's COSE/CBOR-MTI requirement is RFC-anchored (9052/9053), internally consistent, and **reinforced across the corpus** — handshake §6.0.3/§6.0.4 carry the full COSE_Sign1 and JOSE profiles the spec defers to; the C140 DELTA-1 cluster already treats COSE as the settled MTI profile ("handshake=COSE correct"). The spec is **CORRECT**.
- Is it a **mirror divergence**? **Yes** — a genuine one (this is a real mirror, unlike errors' false `error.rs`). Direction: **SDK LAGS.** web4-core is an early-stage (0.x) core that has implemented the cryptographic *algorithms* but **not yet the COSE/CBOR envelope layer** the spec mandates — the same **C176 shape** ("sibling-SDK/spec canonical, Rust incomplete ⇒ SDK lags, extend the impl, spec CORRECT"). The correct disposition is **route to the SDK track**, not spec mutation.
- Does it connect to a standing carry? **Yes — directly.** This is the **concrete Rust-side instance** of the standing **C-M1 ≡ B-D1 / DELTA-1 / C144** COSE-vs-CBOR encoding cluster. That cluster has, until now, been a *spec-side* consistency question (Profile-vs-Encoding column semantics; W4-IOT-1 CBOR-vs-COSE across handshake/core-protocol/registries). C180-N1 adds the **implementation-side** fact: even once the SSOT settles COSE as the canonical encoding, the ratified Rust core will need a COSE/CBOR envelope layer built (it has none). Attach C180-N1 to the C-M1 bundle as the SDK-readiness datapoint.

→ **C180-N1 (LOW, CROSS-TRACK/SDK)**: web4-core implements the W4-BASE-1 *algorithms* faithfully but omits the §1.3 MTI COSE/CBOR *encoding* (signs raw bytes, serializes JSON/hex/base64, no cose/ciborium dep). Spec CORRECT, SDK lags. Route to SDK; feed the C-M1/B-D1 encoding-SSOT bundle. **No spec mutation.** LOW (not MED): it is a forward-awareness readiness gap in a 0.x core, not a live wire-interop contradiction between two ratified artifacts.

### B′.3 — Considered-and-dismissed (anti-padding transparency)

- **`vault/crypto.rs` uses Argon2id KDF** (not HKDF-SHA256) — considered as a KDF divergence. **Dismissed**: the vault is **passphrase-based whole-file encryption** (a local at-rest storage concern), a *different layer* than the W4-BASE-1 *protocol* KDF (HKDF-SHA256, which `pair_channel.rs` uses for session-key derivation). Argon2id is the correct primitive for passphrase-stretching; mapping it to the §1.1 KDF row would be a category error. Not a divergence. (Same different-layer reasoning that excluded errors' `error.rs` internal enum at C178 — but here the *protocol* layer IS present and concordant, so the mirror as a whole is genuine.)
- **`pair_channel.rs` random 12-byte nonce (Sprint-E MVP), birthday-bound at 2^48 msgs/key** — considered as an AEAD-usage weakness. **Dismissed as a security-framework finding**: §1.1 names only the AEAD *algorithm* (ChaCha20-Poly1305); nonce-management strategy is below the spec's granularity, and the impl's own doc-comment flags the counter-nonce upgrade for Sprint F. Not a §1.1/§1.2 divergence.
- **`Web4Error` name-collision** (Rust `web4-core::error::Web4Error` vs Python `Web4Error`) — already adjudicated at C178 as a FALSE mirror for the *errors* taxonomy. Irrelevant here (security's mirror is `crypto.rs`, which is genuine). Noted only to keep the two mirror boundaries distinct.

---

## §C — Fresh-Internal Refute-by-Default Pass

**0 net-new internal contradictions.** Byte-freeze mechanically preserves C140's clean §C; re-confirmed each candidate at its call site:
- §1.1 table ⟷ §1.2 prose: KEM/Sig/AEAD/Hash/KDF/Encoding token-match for **both** suites (`ECDSA-P256` table vs `ECDSA with P-256` prose = long-standing benign wording variant, not a finding — carried from C140).
- §1.3 MTI COSE/JOSE profiles ⟷ §1.1 W4-BASE-1 (COSE) / W4-FIPS-1 (JOSE) Encoding column: consistent.
- §2.3 rotation prose ⟷ `LCT-linked-context-token.md` §7.3 cross-ref (sibling unmoved, resolves).
- §3.1 L89 ⟷ live handshake §6.0.5 / §9 / §6.1 (all resolve; handshake unchanged since C140).
- No standalone W4-IOT-1 statement exists in this file (the C140 DELTA-1 divergence is corpus-side, not here).

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| **C180-N1** | LOW | Ratified Rust core `web4-core` implements the W4-BASE-1 *algorithms* faithfully (5/6 primitives) but **omits the §1.3 MTI COSE/CBOR *encoding*** — signs raw bytes, serializes JSON/hex/base64, **0** `cose`/`cbor`/`ciborium` deps. Spec CORRECT (COSE is MTI, RFC-anchored, corpus-reinforced); **SDK lags** (C176 shape). Concrete Rust-side instance of the C-M1/B-D1/DELTA-1/C144 encoding-SSOT cluster. Route to SDK; feed C-M1 bundle. **No spec mutation.** | CROSS-TRACK (SDK) |
| **C180-N2** | INFO | **Positive concordance + mirror-boundary map**: `crypto.rs` is a **GENUINE** mirror (contrast errors' false `error.rs`, C178). web4-core implements X25519/Ed25519/ChaCha20-Poly1305/SHA-256/HKDF-SHA256 **exactly** per §1.1/§1.2, and correctly omits the SHOULD-only W4-FIPS-1 suite. Records that the security mirror is genuine and where its boundary lies (algorithm layer concordant; encoding layer absent per N1) so the next security delta does not re-discover this from scratch. | CROSS-TRACK (SDK, forward-awareness) |

**Totals**: 0 HIGH, 0 MEDIUM, **1 LOW**, **1 INFO** net-new — **0 actionable net-new defects inside `security-framework.md`**.

**§A**: 6/6 C69 fixes + 1 C109 fix HELD by byte-freeze, 0 regressed; C56 completeness re-read clean. All 8 carries STAND (B-7 5-spelling drift + B-10 8-site `cose:ES256` re-verified live; C140 DELTA-1 unchanged, handshake unmoved). No carry resolved into a defect.

**§B**: **0 cited/carry siblings moved** since the C140 snapshot → **0 findings routed** to `security-framework.md`.

**§B′**: First audit of the Rust crypto mirror. **Genuine** mirror (C178 gate PASS). 5/6 W4-BASE-1 primitives concordant (positive confirmation, C180-N2); COSE/CBOR encoding unimplemented (C180-N1, SDK-lags).

**§C**: 0 net-new internal contradictions.

**This is `security-framework.md`'s 2nd CONSECUTIVE fully-clean delta for the file itself (C140 + C180), 0 actionable net-new inside the file.**

---

## Key Adjudication

1. **The SDK-mirror-expansion guard scores a genuine mirror this fire — and it is mostly a POSITIVE result.** C178 mapped the guard's boundary with a *negative* (errors' false `error.rs`). C180 is the counterpart: the security primitive **does** have a genuine Rust mirror (`crypto.rs`), and auditing it yields a **concordance** — the ratified core's W4-BASE-1 algorithm selection is byte-faithful to §1.1/§1.2 (5/6 primitives exact). The method is not only a defect-finder; on a mature primitive it also **confirms** the spec-impl contract, which is itself worth recording (C180-N2) so the surface is known-good going forward.

2. **The one gap is layer-specific and direction-decided per-finding.** The concordance is at the **algorithm** layer; the divergence (C180-N1) is at the **encoding/envelope** layer — web4-core has no COSE/CBOR codec at all. Direction = **spec CORRECT, SDK lags** (C176 shape), because COSE-MTI is RFC-anchored and corpus-reinforced (handshake profiles, DELTA-1 "handshake=COSE correct"). **Route-not-mutate**: this feeds the standing C-M1/B-D1 encoding-SSOT bundle as the *implementation-readiness* datapoint (the SSOT has been debated spec-side; C180 adds "and the Rust core will need the COSE layer built regardless of which value the SSOT picks"). Zero spec mutation.

3. **Different-layer discipline cuts both ways (C178 lesson applied twice).** The genuine-mirror gate (B′.1) is what separates `crypto.rs` (real §1 mirror) from `error.rs` (false errors mirror). Within `crypto.rs`'s neighborhood, the *same* discipline correctly **dismisses** `vault/crypto.rs`'s Argon2id (passphrase-stretch layer ≠ protocol KDF) and `pair_channel.rs`'s MVP nonce strategy (below §1.1 granularity) — genuine-mirror does not mean every line is a §1 obligation. A name/topic match is not a mirror row; a mirror row is a spec-mandated primitive at the spec's layer.

---

## Next-Turn Carry

- **C181 `security-framework.md` remediation slot = NO-OP** (0 actionable net-new inside the file — consistent with the C140/C180 frozen-clean pair and the frozen-wrap no-op precedents). C180-N1 (LOW) + N2 (INFO) are CROSS-TRACK/SDK; nothing to apply inside `security-framework.md`. Rotation advances.
- **Rotation advances to next-oldest.** After security (now C180, 4th delta), the next file in the fixed-order round-robin is **`registries/initial-registries.md`** → its next delta (**C182**). [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, SAL, LCT, ISP, entity-types, errors, security, **registries**, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.] **Continue the SDK-mirror expansion at registries** — but apply the C178/C180 genuine-mirror gate first: registries is a data/taxonomy file; its "mirror" (if any) is the SDK registry loaders / `initial-registries` fixtures, not `web4-core/src/*.rs` crypto — verify a GENUINE mirror exists before divergence analysis.
- **C180-N1 → attach to the C-M1/B-D1 encoding-SSOT bundle** as the SDK-readiness datapoint: web4-core has **no** COSE/CBOR codec; whatever the SSOT settles, the Rust core needs the COSE envelope layer built to satisfy §1.3 MTI. Route to SDK track. **Do not self-build it** (that is SDK-track implementation work, not an audit deliverable).
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: **DESIGN-Q** — C-M1 ≡ B-D1 crypto-suite/encoding SSOT (now with C180-N1 SDK-readiness + C140 DELTA-1 W4-IOT-1 Profile-vs-Encoding contradiction attached); B-3 authz basis (VCs vs SAL/R6); B-9/B-M2 rotation mutate-vs-stable-DID; B-H2/B-11 W4-IOT-1 + AES-CCM. **CROSS-TRACK** — B-7 normalize 5 FIPS-KEM spellings to `ECDH-P256` (gated on C-M1); B-8 SDK `security.py` docstring quote; B-10 `cose:ES256`→`cose:EdDSA` (8 sites across 3 LCT files); B-L6/B-L7 vector ownership + `device` W4ID method; **C180-N1 web4-core COSE gap (LOW)**; **C180-N2 crypto-mirror genuine/concordant (INFO)**. **Do not self-apply any.**
- **D0 (protocols/ cluster) still operator-gated** — unrelated to security; do not touch.

---

*Audit produced under Autonomous Session Protocol v2 — slot `180036`, LEAD voice. Read-only: no spec, SDK, or test-vector files were modified this turn. Remediation (C181) is the next alternation turn and is a no-op (0 AUTONOMOUS findings) → rotation advances to `registries/initial-registries.md`.*
