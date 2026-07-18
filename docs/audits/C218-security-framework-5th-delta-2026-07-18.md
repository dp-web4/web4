# C218 — `security-framework.md` Fifth Delta Re-Audit (6th pass)

**Audit ID**: C218
**Target**: `web4-standard/core-spec/security-framework.md` (97 lines) — Web4 Security Framework (crypto suites, key management, authentication/authorization)
**Date**: 2026-07-18
**Auditor**: autonomous web4 session (legion, slot `web4-20260718-120036`), v2 protocol, LEAD voice
**Type**: **Fifth delta re-audit** (6th pass overall). Lineage: **C31** (first-pass, 2026-06-04, #268 → remediation #271 `130069d8`, 5 autonomous) → **C68** (first delta, 2026-06-17) → **C69** remediation (#350 `3d04dd5c`, 6 autonomous) → **C108** (second delta, 2026-06-28) → **C109** remediation (#396 `eedd36fc`, applied N1) → **C140** (third delta, 2026-07-05, 0 net-new) → **C180** (fourth delta, 2026-07-11, 0 net-new; first audit of the Rust `crypto.rs` mirror) → **C218**.
**Prior audit docs**: `C31-…`, `C68-…`, `C108-…`, `C109-…remediation…`, `C140-…3rd-delta…`, `C180-security-framework-4th-delta-2026-07-11.md`.

**Method note**: `git diff eedd36fc HEAD -- web4-standard/core-spec/security-framework.md` is **empty** — the file is **byte-identical to its C109 remediation** and has been for **~20 days** (last touch `eedd36fc`, 2026-06-28 10:03). Per the locked frozen-wrap proportionality precedent (policy-reviewed and APPROVED this fire), **§A** is verification (freeze-preserves-verdict + carry re-check + C56 completeness), **§B** is the corpus-delta surface (cited/carry siblings that *moved* since the **C180 snapshot**, 2026-07-11), **§B′** is the first-class SDK-mirror audit applying the C172/C174/C176/C178/C180/C216 genuine-mirror guard, and **§C** is a single fresh-internal refute-by-default pass.

**Headline**: `security-framework.md`'s **third consecutive fully-clean delta for the file itself** (C140 + C180 + C218), **0 net-new AUTONOMOUS findings inside the file**. §A: all 6 C69 fixes + 1 C109 fix HELD by byte-freeze, 0 regression; all 8 carries STAND (B-7 5-spelling drift + B-10 8-site `cose:ES256` re-verified live). §B: **one** cited/carry sibling moved — `LCT-linked-context-token.md` (`#531` §1.2 "Inspectable Evidence, Not Prescribed Trust") — but it is **DISJOINT** from security's citation surface (§2.3→LCT §7.3 "Rotation" is byte-stable; the `cose:ES256` B-10 site untouched) ⇒ **0 findings routed**. §B′: the C180 genuine mirror `crypto.rs`/`pair_channel.rs` is **frozen since C180** (C180-N1 COSE-gap + C180-N2 concordance HELD by construction); the guard's new candidate this interval, **`web4-core/src/attestation.rs`** (landed #527 2026-07-15, refined #538 2026-07-17 — after C180), is adjudicated a **GENUINE mirror of the LCT/entity *witnessing* spec (§2.3/§4/§11.2), NOT of `security-framework.md`** — a **false mirror *for security*** by the C178/C216 boundary rule (topic-adjacency ≠ mirror-of-this-spec). Its only security-relevant signal — it signs a raw domain-separated *string* preimage with Ed25519 and carries **0** COSE/CBOR deps — **corroborates C180-N1** (web4-core has no COSE envelope) at a **3rd** signing site, recorded as **C218-N1 (INFO, CROSS-TRACK/SDK)**. §C: 0 net-new internal contradictions.

---

## Scope & Methodology

`security-framework.md` is unchanged since its C109 remediation, so §A applies the **C56 completeness method** (audit the remediation's *claims* token-by-token) + the **bidirectional carry re-check** (C62/C64). §B follows the frozen-wrap lesson: yield lives on the **corpus-delta surface** (siblings moved since the last snapshot) + the **SDK-mirror expansion** (C172–C216 — the untracked Rust mirror is where net-new has lived on every recent frozen-but-clean delta). §B′ applies the **C178/C216 boundary lesson**: *before* running divergence analysis, verify the candidate is a **GENUINE** mirror of **this** spec — a name-collision (errors' `error.rs`, C178) OR a genuine mirror of a **different** spec (this fire's `attestation.rs`) is a false mirror *for security*; exclude, do not misread absence as a gap. Snapshot-presence guard (C98) applied throughout.

**Structure note (MUST-vs-reference-impl doc-specific check, C120/C121):** `security-framework.md` has **no normative-summary / §12-style section**. The "normative-summary restates entity MUSTs unconditionally" defect class **does not apply** (re-confirmed from C140/C180).

**Severity**: HIGH = correctness/normative contradiction; MEDIUM = cross-spec divergence; LOW = hygiene/precision or SDK-lag on an MTI; INFO = positive confirmation / forward-awareness.
**Routing**: AUTONOMOUS (fix inside `security-framework.md`) / DESIGN-Q (operator canonicity) / CROSS-TRACK (lands elsewhere — SDK / sibling spec).

---

## §A — Prior-Finding Verification, Regression, Completeness, Carry

### A.1 — All 6 C69 fixes + the 1 C109 fix: **HELD by byte-freeze (0 regression, 0 artifacts)**

`security-framework.md` has not changed a byte since C109 (`eedd36fc`, ~20 days). C140 and C180 both verified all seven token-by-token and found them HELD; the continued byte-freeze mechanically preserves that verdict. Re-confirmed against the live file this fire:

| ID | Fix | Current state (live line) | Verdict |
|---|---|---|---|
| **B-1** (C69) | §1.3 COSE `crv`/`alg` → COSE-numeric | L48 `Ed25519 with \`crv = 6\` (COSE curve label) and \`alg = -8\` (EdDSA)` | **HELD** |
| **B-4** (C69) | §1.1 column `Profile` → `Encoding` | L16/L17 header carries `… KDF \| Encoding \| Status` | **HELD** |
| **B-5** (C69) | §1.1 add `KDF` column | L16/L17 carry `HKDF-SHA256` | **HELD** |
| **B-6** (C69) | §1.2 COSE `RFC 8152` → `RFC 9052/9053` | L32 `COSE (RFC 9052/9053, obsoletes RFC 8152)` | **HELD** |
| **B-9 interim** (C69) | §2.3 stop asserting in-place identifier mutation | §2.3 "new key pair … new LCT bound to the new public key" | **HELD** |
| **B-2** (C69) | §3.1 add handshake deference | superseded by C109 N1 (below) | **HELD → widened by N1** |
| **N1** (C109) | §3.1 split the over-broad §6.0.5 cite | L89 splits §6.0.5 (session-binding) / §9 (freshness+nonce+replay) / §6.1 (`nonce`/`ts` fields) | **HELD — precise** |

**Regression sweep clean:** live spot-check — §1.1 W4-BASE-1 row L16 (`X25519 | Ed25519 | ChaCha20-Poly1305 | SHA-256 | HKDF-SHA256 | COSE | MUST`) and W4-FIPS-1 row L17 (`ECDH-P256 | ECDSA-P256 | AES-128-GCM | SHA-256 | HKDF-SHA256 | JOSE | SHOULD`) intact; §1.3 MTI COSE profile (`crv = 6` / `alg = -8` EdDSA, L48) consistent with §1.1 W4-BASE-1; §1.2 COSE `RFC 9052/9053` (L32) intact. PR #396 was a single-file diff → cross-file regression surface nil.

### A.2 — C56 remediation-completeness re-read: **clean**

Re-reading each fix's *claim* token-by-token against canonical: the C109 N1 split-cite still holds — §6.0.5 IS session-binding-only, §9 ("Anti-Replay & Clocks") DOES carry freshness (`ts` ±300s) + nonce-uniqueness + replay window, §6.1 DOES define the `nonce`/`ts` fields. B-6 `RFC 9052/9053, obsoletes RFC 8152` holds. **No residual one-sided-claim defect; no new completeness defect.**

### A.3 — Bidirectional carry re-verification (against the current corpus)

All 8 standing carries re-verified live. **None resolved into a defect; none regressed.**

| Carry | Routing | Status at C218 (live evidence) |
|---|---|---|
| **B-3** §3.2 "authz based on VCs" vs SAL/R6 | DESIGN-Q | **OPEN, unchanged** — §3.2 verbatim; operator canonicity stands |
| **B-7** FIPS-KEM spelling 5-site mirror-drift | CROSS-TRACK | **OPEN, unchanged** — live grep re-confirms all divergent: `P-256ECDH` (core-protocol.md:19) / `P-256 ECDH` (initial-registries.md:6) / `P-256EC` (web4-handshake.md:23) / `ECDH-P256` ×2 (this file L17/L35). Canonical target `ECDH-P256`. None moved since `eedd36fc` |
| **B-8** SDK docstring quotes deleted A-L2 phrase | CROSS-TRACK | **OPEN, unchanged** — `implementation/sdk/web4/security.py` unmoved (pre-C140) |
| **B-9 / B-M2** rotation mutate-vs-stable-DID | DESIGN-Q | **interim HELD** (§2.3); semantics decision stands |
| **B-10** `cose:ES256` mislabel | CROSS-TRACK | **OPEN, unchanged** — live count = **8**: `lct-capability-levels.md` (5) + `LCT-linked-context-token.md` (1) + `multi-device-lct-binding.md` (2); target `cose:EdDSA`. Untouched by #531 (see §B) |
| **C-M1 ≡ C70-B-D1** canonical crypto-suite/encoding SSOT | DESIGN-Q | **OPEN** — C180-N1 Rust-side instance (web4-core has no COSE codec) STANDS by freeze; C218-N1 adds a 3rd corroborating site (`attestation.rs`) |
| **B-H2 / B-11** W4-IOT-1 + AES-CCM | DESIGN-Q / CROSS-TRACK | **OPEN, unchanged since C140** — C140 DELTA-1 W4-IOT-1 Profile contradiction intact; handshake §6.0.1 did **not** move |
| **B-L6 / B-L7** vector ownership; `device` W4ID method | CROSS-TRACK | OPEN, unchanged (`data-formats.md` unmoved) |

**C140 DELTA-1 status**: unchanged. Handshake §6.0.1 (the W4-IOT-1 Profile=COSE site) has not moved since C140 → DELTA-1 still open, still routed to the C-M1/B-D1 SSOT decision. No re-adjudication owed this cycle.

---

## §B — Corpus-Delta Pass (siblings moved since the C180 snapshot, 2026-07-11)

Checked every sibling `security-framework.md` cites or holds a carry-mirror in, via `git log 9d1933f8..HEAD -- <file>` (or the file's own last-touch):

| Sibling | Cited/carry role | Last touch | Moved since C180 (2026-07-11)? |
|---|---|---|---|
| `protocols/web4-handshake.md` | §1.3 → §6.0.3/§6.0.4; §3.1 → §6.0.5/§9/§6.1 | `57caa2e1` 2026-06-29 | No |
| `core-spec/core-protocol.md` | B-7 / W4-IOT-1 mirror | `3084e4d2` 2026-06-05 | No |
| `registries/initial-registries.md` | B-7 / W4-IOT-1 mirror | `3f1d6fad` 2026-06-18 | No |
| `core-spec/LCT-linked-context-token.md` | §2.3 rotation (§7.3); B-10 | **`d89595e8` 2026-07-16** | **YES — `#531` §1.2 "Inspectable Evidence"** |
| `core-spec/multi-device-lct-binding.md` | B-10 `cose:ES256` | `a6cbde92` 2026-06-21 | No |
| `core-spec/lct-capability-levels.md` | B-10 `cose:ES256` | `a3fee0e1` 2026-06-14 | No |
| `implementation/sdk/web4/security.py` | B-8 docstring | pre-C140 | No |

**The one mover — `LCT-linked-context-token.md` `#531` — is DISJOINT from security's citation surface.** `#531` ("canonize 'Inspectable Evidence, Not Prescribed Trust'") inserts a new §1.2 principle and renumbers the old §1.2→§1.3 (a **local** renumber, per C210). It does **not** touch the two places security-framework depends on:
- **§2.3 → LCT §7.3 "Rotation (Key Update)"**: the heading is still `### 7.3 Rotation (Key Update)` (LCT L497). `git diff 9d1933f8 HEAD` shows **no** hunk matching `7.3`/`rotation`. Security §2.3's cross-ref resolves unchanged.
- **B-10 `cose:ES256` site**: LCT still carries exactly **1** `cose:ES256` occurrence (unchanged count); `#531`'s diff touched **0** `cose:ES256`/`cose:EdDSA` lines.

This is the same disjoint-mover pattern the four sibling deltas this interval recorded for `#531`/`#523` (C208 SAL, C210 LCT-self, C212 ISP, C214 entity-types, C216 errors): a real corpus edit landing in a section the target does not cross-reference. **§B is effectively empty — 0 findings routed to `security-framework.md`.** (Other corpus movement since 2026-07-11 — LCT `#538` citizenship, W4IP `#523` Effector, `ratchet.rs` `#529`, `attestation.rs` `#527` — is either not cited by security-framework or is handled in §B′.)

---

## §B′ — SDK-Mirror Expansion (C172/C174/C176/C178/C180/C216 guard)

### B′.1 — The C180 genuine mirror `crypto.rs`/`pair_channel.rs`: **FROZEN since C180 → C180-N1 + C180-N2 HELD by construction**

`git log --since=2026-07-11 -- web4-core/src/crypto.rs web4-core/src/pair_channel.rs web4-core/src/vault/crypto.rs` is **empty**. The C180 §B′ verdict is preserved by freeze:
- **C180-N2 (concordance)**: web4-core implements **5/6** W4-BASE-1 primitives exactly (X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 / HKDF-SHA256), correctly omits the SHOULD-only W4-FIPS-1 suite. **HELD.**
- **C180-N1 (COSE gap, LOW/CROSS-TRACK)**: web4-core omits the §1.3 MTI COSE/CBOR *encoding* (0 `cose`/`cbor`/`ciborium` deps; `serde_json` is the sole serializer). **HELD** — direction unchanged: **spec CORRECT, SDK lags** (C176 shape); feeds the C-M1/B-D1 encoding-SSOT bundle.

### B′.2 — New candidate mirror `web4-core/src/attestation.rs`: **GENUINE mirror of the LCT *witnessing* spec, FALSE mirror *for security-framework* (C178/C216 boundary)**

The guard's premise: a frozen spec can be blind to a Rust module the earlier passes never saw. This interval web4-core grew **two** new files — `ratchet.rs` (#529) and **`attestation.rs`** (#527 added 2026-07-15, #538 refined 2026-07-17) — both landing **after** the C180 audit (2026-07-11). `attestation.rs` is the crypto-adjacent one (it `use`s `crate::crypto::{KeyPair, PublicKey, SignatureBytes}` and does signing/verification), so the genuine-mirror gate must be run on it.

**Genuine-mirror gate — decided FOR security-framework specifically (policy condition 1; do NOT import the errors verdict):**

`attestation.rs` models **witness attestations + birth certificates + citizenship-quorum verification** — its own module doc cites **"canon §2.3, §4, §11.2"** (the LCT/entity *witnessing* sections) and the dp 2026-07-16 citizenship-as-ledger-reference ruling. It is a **downstream CONSUMER** of the §1 crypto primitives (it calls `crypto.rs`'s `KeyPair::sign` / `PublicKey::verify`), **not** a mirror of security-framework's §1 suite table, §2 key-management, or §3 auth. Therefore:

- It **is** a genuine mirror — but of the **LCT/entity witnessing spec**, a *different* target than `security-framework.md`. (Contrast errors' `error.rs`, C178: that was a name-collision internal enum mirroring *nothing*. `attestation.rs` is not that — it faithfully mirrors real canon, just not *this* canon.)
- **For `security-framework.md` it is a FALSE mirror** by the C178/C216 boundary rule: topic-adjacency (it does Ed25519 signing) ≠ mirror-of-this-spec. Security-framework's mirror is `crypto.rs` (§B′.1); `attestation.rs` belongs to the **LCT/entity-types audit lineage's** SDK-mirror surface, not security's. Recorded here so the next security delta does not re-run this gate from scratch, and so the LCT lineage inherits the pointer (see Next-Turn Carry).

**Consistency with the four sibling deltas that already probed `attestation.rs`** (policy condition 3, prose-parking check): C216 (errors → 0 wire codes), C206 (metabolic → 0 lexicon), C204 (dictionary → 0 "dictionar"), C196 (acp → no ACP structs) each found it **disjoint under their lens**. None ran the **security/crypto** lens. This fire's verdict — genuine-mirror-of-a-different-spec, false-for-security — is the security-lens counterpart of those four disjointness findings, not a re-discovery.

### B′.3 — The one security-relevant signal: `attestation.rs` signing corroborates C180-N1 (C218-N1, INFO)

Even as a false mirror *for security*, `attestation.rs` carries one datapoint the C-M1/B-D1 encoding-SSOT bundle should absorb. Its signing message (`Attestation::message`, L64-84) is a **raw domain-separated string preimage**:

```
"web4:lct:attestation:v1\n" + subject_lct_id + "\n" + type + "\n" + ts(RFC3339)
```

signed with plain Ed25519 (`witness_keypair.sign(&message)`), and its module doc calls this a **"COSE-style signature"** (L60). But the crate carries **0** COSE/CBOR deps (`serde_json` only) — the preimage is a UTF-8 string, not a `COSE_Sign1` structure or a canonical CBOR map. This is the **same encoding-layer fact as C180-N1**, now at a **3rd** web4-core signing site (crypto.rs raw-sig → pair_channel.rs base64 seal → attestation.rs string-preimage sig): the ratified Rust core signs faithfully with the correct **algorithm** (Ed25519/EdDSA = COSE `alg = -8`) but has **no COSE/CBOR envelope anywhere**.

**Refute-by-default (policy condition 3, flagship):**
- Is it a security-framework **defect**? **No** — `attestation.rs` is not a security-framework mirror (§B′.2), so it cannot generate a finding *inside* this spec.
- Is the `"COSE-style"` comment itself a **defect** to route? **Under-reach, not a defect.** The signature genuinely IS EdDSA (the exact algorithm COSE `alg = -8` names); the `"-style"` hedge is defensible. Calling it a mislabel would be inflation. It is recorded only as **corroborating evidence** that web4-core's no-COSE-envelope posture is systemic (3 sites), not a `crypto.rs`-local quirk — the SDK-readiness signal the C-M1 bundle needs.
- Direction: **spec CORRECT, SDK lags** (identical to C180-N1). **Route to SDK / feed C-M1/B-D1.** No spec mutation, no `attestation.rs` mutation (out of bounds; SDK-track owns it).

→ **C218-N1 (INFO, CROSS-TRACK/SDK)**: `attestation.rs` (LCT-witnessing mirror, false-for-security) signs raw string preimages with Ed25519 and carries 0 COSE/CBOR deps — a 3rd web4-core site corroborating C180-N1's "web4-core has no COSE envelope" fact. Attach to the C-M1/B-D1 encoding-SSOT bundle as an SDK-readiness datapoint. Not a defect; not net-new inside `security-framework.md`.

### B′.4 — Considered-and-dismissed (anti-padding transparency)

- **`ratchet.rs` (#529)** — the other new web4-core file. **Dismissed as a security mirror**: it is a hash-ratchet / forward-secrecy primitive at the type layer with no §1 suite-table, §2 key-management, or §3 auth surface; C216 already recorded it carries 0 wire taxonomy. Not a security-framework §1/§2/§3 mirror. (A future security delta may probe whether ratchet's KDF chaining should cite §1.1 HKDF-SHA256 — noted, not opened; it is below the frozen spec's granularity today.)
- **`vault/crypto.rs` Argon2id KDF** — re-dismissed exactly as C180 §B′.3: passphrase-based at-rest storage layer ≠ the W4-BASE-1 *protocol* KDF (HKDF-SHA256). Category-correct, not a divergence. Frozen since C180 regardless.
- **`pair_channel.rs` 12-byte random nonce (Sprint-E MVP)** — re-dismissed as below §1.1 granularity (algorithm named, nonce-management is not). Frozen since C180.

---

## §C — Fresh-Internal Refute-by-Default Pass

**0 net-new internal contradictions.** Byte-freeze mechanically preserves C140/C180's clean §C; re-confirmed each candidate at its call site this fire:
- §1.1 table ⟷ §1.2 prose: KEM/Sig/AEAD/Hash/KDF/Encoding token-match for **both** suites (`ECDSA-P256` table vs `ECDSA with P-256` prose = long-standing benign wording variant, carried from C140/C180 — not a finding).
- §1.3 MTI COSE (`crv = 6` / `alg = -8`, L48) ⟷ §1.1 W4-BASE-1 Encoding=COSE / §1.2 COSE RFC 9052/9053 (L32): consistent.
- §2.3 rotation prose ⟷ `LCT-linked-context-token.md` §7.3 "Rotation (Key Update)" (L497, sibling `#531` mover disjoint): resolves.
- §3.1 L89 ⟷ live handshake §6.0.5 / §9 / §6.1 (handshake unmoved since C140): all resolve.
- No standalone W4-IOT-1 statement in this file (the C140 DELTA-1 divergence is corpus-side).

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| **C218-N1** | INFO | `web4-core/src/attestation.rs` (new #527/#538, **genuine mirror of the LCT *witnessing* spec — false mirror *for security-framework*** per C178/C216) signs raw domain-separated **string** preimages with Ed25519 and carries **0** COSE/CBOR deps. A **3rd** web4-core signing site corroborating **C180-N1** ("web4-core has no COSE envelope"). Spec CORRECT, SDK lags; feed the C-M1/B-D1 encoding-SSOT bundle as an SDK-readiness datapoint. Not a defect; **not net-new inside `security-framework.md`**. | CROSS-TRACK (SDK, forward-awareness) |

**Totals**: 0 HIGH, 0 MEDIUM, 0 LOW, **1 INFO** — **0 actionable net-new defects inside `security-framework.md`**.

**§A**: 6/6 C69 fixes + 1 C109 fix HELD by byte-freeze, 0 regressed; C56 completeness re-read clean. All 8 carries STAND (B-7 5-spelling drift + B-10 8-site `cose:ES256` re-verified live; C140 DELTA-1 unchanged). No carry resolved into a defect.
**§B**: 1 sibling moved (`LCT` `#531` §1.2) — **DISJOINT** from security's citation surface (§2.3→§7.3 rotation byte-stable; B-10 `cose:ES256` untouched) → **0 findings routed**.
**§B′**: C180 mirror `crypto.rs`/`pair_channel.rs` frozen → C180-N1/N2 HELD. New `attestation.rs` = genuine mirror of a **different** spec (LCT witnessing) ⇒ **false mirror for security** (C178/C216 boundary); its no-COSE-envelope signing corroborates C180-N1 (C218-N1, INFO).
**§C**: 0 net-new internal contradictions.

**This is `security-framework.md`'s 3rd CONSECUTIVE fully-clean delta for the file itself (C140 + C180 + C218), 0 actionable net-new inside the file.**

---

## Key Adjudication

1. **The genuine-mirror gate has three outcomes, and this fire exercises the third.** C178 mapped a *name-collision false mirror* (errors' `error.rs`). C180 mapped a *genuine mirror of this spec* (`crypto.rs`, mostly concordant). C218 maps the **third** kind: a **genuine mirror of a *different* spec** (`attestation.rs` mirrors LCT §2.3/§11.2 witnessing, not security §1). All three are "not a security-framework finding," but for distinct reasons — and recording *which* reason is what keeps the boundary crisp for the next delta and hands the pointer to the correct owning lineage (LCT/entity-types inherits `attestation.rs`).

2. **A false-mirror-for-security can still carry a real cross-track datapoint.** `attestation.rs` produces no *security-framework* finding, yet its raw-string Ed25519 signing (0 COSE/CBOR deps) is the **3rd** web4-core site confirming C180-N1's systemic no-COSE-envelope posture. The disciplined move is to route that corroboration to the C-M1/B-D1 SSOT bundle **without** inflating the loose `"COSE-style"` comment into a defect (refute-by-default: the signature genuinely IS EdDSA; the `"-style"` hedge is defensible). Evidence for the bundle, not a manufactured finding.

3. **Honest no-op, proportionate pass (policy condition 2).** The target is 20-day byte-frozen with two prior clean deltas; §A/§B/§C are freeze-verification. The pass was still worth running because §B′ audited a Rust module (`attestation.rs`) none of the prior 5 security passes saw — exactly where the C172–C216 method locates net-new. The result is a clean genuine/false-mirror adjudication + one INFO corroboration, and **no work was manufactured** to justify the fire.

---

## Next-Turn Carry

- **C219 `security-framework.md` remediation slot = NO-OP** (0 actionable net-new inside the file — consistent with the C140/C180/C218 frozen-clean triple). C218-N1 (INFO) is CROSS-TRACK/SDK; nothing to apply inside `security-framework.md`. Rotation advances.
- **Rotation advances to next-oldest = `registries/initial-registries.md` → its next delta (C220).** [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, SAL, LCT, ISP, entity-types, errors, security, **registries**, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.] Continue the SDK-mirror expansion at registries, but apply the C178/C180/C218 genuine-mirror gate first: registries is a data/taxonomy file; its "mirror" (if any) is SDK registry loaders / fixtures, NOT `web4-core/src/*.rs` crypto — the C182 pass already recorded a NEGATIVE-gate (no Rust registry mirror). Verify a GENUINE mirror exists before divergence analysis.
- **`attestation.rs` now belongs to the LCT / entity-types SDK-mirror surface** — hand this pointer forward: the next **LCT** (post-C210) or **entity-types** (post-C214) delta's §B′ should audit `attestation.rs` (+ `ratchet.rs`) under *its* lens (witnessing quorum / birth-certificate / citizenship-record shape vs LCT §2.3/§4/§11.2), where a genuine finding could actually live. Security's probe (this fire) only ruled it out for security and extracted the C180-N1 corroboration.
- **C218-N1 → attach to the C-M1/B-D1 encoding-SSOT bundle** as a 3rd SDK-readiness datapoint (web4-core has no COSE/CBOR envelope at crypto.rs, pair_channel.rs, OR attestation.rs). Route to SDK track. **Do not self-build the COSE layer** (SDK-track implementation, not an audit deliverable).
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: **DESIGN-Q** — C-M1 ≡ B-D1 crypto-suite/encoding SSOT (now C180-N1 + C218-N1 SDK-readiness + C140 DELTA-1 W4-IOT-1 Profile-vs-Encoding contradiction); B-3 authz basis (VCs vs SAL/R6); B-9/B-M2 rotation mutate-vs-stable-DID; B-H2/B-11 W4-IOT-1 + AES-CCM. **CROSS-TRACK** — B-7 normalize 5 FIPS-KEM spellings to `ECDH-P256` (gated on C-M1); B-8 SDK `security.py` docstring quote; B-10 `cose:ES256`→`cose:EdDSA` (8 sites across 3 LCT files); B-L6/B-L7 vector ownership + `device` W4ID method; **C180-N1** web4-core COSE gap (LOW); **C180-N2** crypto-mirror genuine/concordant (INFO); **C218-N1** attestation.rs COSE corroboration (INFO). **Do not self-apply any.**
- **D0 (protocols/ cluster) still operator-gated** — unrelated to security; do not touch.

---

*Audit produced under Autonomous Session Protocol v2 — slot `web4-20260718-120036`, LEAD voice. Read-only: no spec, SDK, or test-vector files were modified this turn. Remediation (C219) is the next alternation turn and is a no-op (0 AUTONOMOUS findings) → rotation advances to `registries/initial-registries.md`.*
