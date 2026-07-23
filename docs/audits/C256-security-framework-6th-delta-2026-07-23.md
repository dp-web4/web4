# C256 — `security-framework.md` Sixth Delta Re-Audit (7th pass)

**Audit ID**: C256
**Target**: `web4-standard/core-spec/security-framework.md` (97 lines) — Web4 Security Framework (crypto suites, key management, authentication/authorization)
**Date**: 2026-07-23
**Auditor**: autonomous web4 session (legion, slot `web4-20260723-060036`), v2 protocol, LEAD voice
**Type**: **Sixth delta re-audit** (7th pass overall). Lineage: **C31** (first-pass, 2026-06-04, #268 → remediation #271 `130069d8`, 5 autonomous) → **C68** (first delta) → **C69** remediation (#350 `3d04dd5c`, 6 autonomous) → **C108** (second delta) → **C109** remediation (#396 `eedd36fc`, applied N1) → **C140** (third delta, 0 net-new) → **C180** (fourth delta, 0 net-new; first audit of the Rust `crypto.rs` mirror) → **C218** (fifth delta, 0 net-new; `attestation.rs` false-for-security + C218-N1 corroboration) → **C256**.
**Prior audit docs**: `C31-…`, `C68-…`, `C108-…`, `C109-…remediation…`, `C140-…3rd-delta…`, `C180-security-framework-4th-delta-2026-07-11.md`, `C218-security-framework-5th-delta-2026-07-18.md`.

**Method note**: `git diff eedd36fc HEAD -- web4-standard/core-spec/security-framework.md` is **empty** — the file is **byte-identical to its C109 remediation** and has been for **25 days** (last touch `eedd36fc`, 2026-06-28). The live blob is `2880e643f4d7b9899dca38d97dee3358b0f38237`, **byte-identical to the blob C218 verified**. Per the locked frozen-wrap proportionality precedent (policy-reviewed and APPROVED this fire), **§A** is verification (freeze-preserves-verdict + carry re-check + C56 completeness — recorded compactly, held by construction), **§B** is the corpus-delta surface (cited/carry siblings that *moved* since the **C218 snapshot**, 2026-07-18), **§B′** is the first-class SDK-mirror audit applying the C172/C174/C176/C178/C180/C216/C218 genuine-mirror gate, and **§C** is a single fresh-internal refute-by-default pass.

**Headline**: `security-framework.md`'s **4th consecutive fully-clean delta for the file itself** (C140 + C180 + C218 + C256), **0 net-new AUTONOMOUS findings inside the file**. §A: all 6 C69 fixes + 1 C109 fix HELD by byte-freeze (blob-identical to C218's verified blob), 0 regression; all 8 carries STAND (B-7 5-spelling drift + B-10 8-site `cose:ES256` re-verified live and unchanged). §B: **EMPTY corpus-delta surface** — **0** of the 6 cited/carry siblings moved since the C218 snapshot (`git log fd622824..HEAD` empty for every one) ⇒ 0 findings routed. §B′: the C180 genuine mirror `crypto.rs`/`pair_channel.rs` and the C218-adjudicated `attestation.rs`/`ratchet.rs` are **all frozen since ≤C218** (C180-N1 COSE-gap + C180-N2 concordance + C218-N1 corroboration + `attestation.rs` false-for-security verdict + `ratchet.rs` dismissal all HELD by construction); the guard's **sole new candidate** this interval — **`web4-core/src/role_extension.rs`** (moved `4f76f110` oracle-scope, 2026-07-18, the only web4-core `.rs` file to change since C218) — is adjudicated a **GENUINE mirror of the `role-extension.ttl` / entity-types *Role* spec, NOT of `security-framework.md`** — a **false mirror *for security*** by the C178/C216/C218 boundary rule (third-kind: genuine mirror of a *different* spec). It is a **downstream CONSUMER** of §1 crypto (it `use`s `crate::crypto::KeyPair` and calls `lct.sign_binding(&keypair)` at role issuance) with **0** suite-table / §2-key-management / §3-auth primitive definitions and **0** COSE/CBOR deps; it defines **no new signing site** (`sign_binding` lives in `lct.rs:410` — `role_extension.rs` merely calls it), so unlike `attestation.rs` it adds **no** 4th C180-N1 corroboration site. §C: 0 net-new internal contradictions.

---

## Scope & Methodology

`security-framework.md` is unchanged since its C109 remediation, so §A applies the **C56 completeness method** (blob-identity → the remediation's claims are preserved token-for-token) + the **bidirectional carry re-check** (C62/C64). §B follows the frozen-wrap lesson: yield lives on the **corpus-delta surface** (siblings moved since the last snapshot) + the **SDK-mirror expansion** (C172–C218 — the untracked/newly-landed Rust mirror is where net-new has lived on every recent frozen-but-clean delta). §B′ applies the **C178/C216/C218 boundary lesson**: *before* running divergence analysis, verify the candidate is a **GENUINE** mirror of **this** spec — a name-collision (errors' `error.rs`, C178), a genuine mirror of a **different** spec (`attestation.rs`, C218; `role_extension.rs`, this fire), OR a downstream consumer of §1 primitives is a **false mirror *for security***; exclude, do not misread absence as a gap. Snapshot-presence guard (C98) applied throughout.

**Structure note (MUST-vs-reference-impl doc-specific check, C120/C121):** `security-framework.md` has **no normative-summary / §12-style section**. The "normative-summary restates entity MUSTs unconditionally" defect class **does not apply** (re-confirmed from C140/C180/C218).

**Severity**: HIGH = correctness/normative contradiction; MEDIUM = cross-spec divergence; LOW = hygiene/precision or SDK-lag on an MTI; INFO = positive confirmation / forward-awareness.
**Routing**: AUTONOMOUS (fix inside `security-framework.md`) / DESIGN-Q (operator canonicity) / CROSS-TRACK (lands elsewhere — SDK / sibling spec).

---

## §A — Prior-Finding Verification, Regression, Completeness, Carry

### A.1 — All 6 C69 fixes + the 1 C109 fix: **HELD by byte-freeze (blob-identical to C218's verified blob)**

The live blob `2880e643` is **byte-identical to the blob C218 verified** (and to the C109 remediation `eedd36fc`, 25 days). C140, C180, and C218 each verified all seven fixes token-by-token and found them HELD; blob-identity mechanically preserves that verdict. No re-derivation is owed — the compact record:

| ID | Fix | Verdict at C256 |
|---|---|---|
| **B-1** (C69) | §1.3 COSE `crv = 6` / `alg = -8` (EdDSA) | **HELD** (blob-identical) |
| **B-4** (C69) | §1.1 column `Profile` → `Encoding` | **HELD** |
| **B-5** (C69) | §1.1 add `KDF` column (`HKDF-SHA256`) | **HELD** |
| **B-6** (C69) | §1.2 COSE `RFC 8152` → `RFC 9052/9053` | **HELD** |
| **B-9 interim** (C69) | §2.3 stop asserting in-place identifier mutation | **HELD** |
| **B-2** (C69) | §3.1 handshake deference | **HELD → widened by N1** |
| **N1** (C109) | §3.1 split §6.0.5 / §9 / §6.1 cite | **HELD — precise** |

**Regression sweep**: blob-identity → cross-file regression surface nil (PR #396 was single-file; nothing has touched the file since).

### A.2 — C56 remediation-completeness re-read: **clean (held by construction)**

Blob-identity preserves the C218 completeness verdict: the C109 N1 split-cite holds (§6.0.5 = session-binding-only, §9 = freshness/nonce/replay, §6.1 = `nonce`/`ts` fields); B-6 `RFC 9052/9053, obsoletes RFC 8152` holds. No residual one-sided-claim defect.

### A.3 — Bidirectional carry re-verification (against the current corpus, live)

All 8 standing carries re-verified against live HEAD. **None resolved into a defect; none regressed.** The two with a live corpus footprint were re-grepped this fire:

| Carry | Routing | Status at C256 (live evidence) |
|---|---|---|
| **B-3** §3.2 "authz based on VCs" vs SAL/R6 | DESIGN-Q | **OPEN, unchanged** — §3.2 verbatim (frozen). *Forward-awareness this fire (§B′.2): `role_extension.rs` realizes role/scope-based authz in the Rust core — a consumer landing on the SAL/R6/role side of the B-3 question, not the VC side. Informative for the eventual operator decision; not a defect, not a resolution.* |
| **B-7** FIPS-KEM spelling 5-site mirror-drift | CROSS-TRACK | **OPEN, unchanged** — live grep re-confirms all divergent: `P-256ECDH` (core-protocol.md:19) / `P-256 ECDH` (initial-registries.md:6) / `P-256EC` (web4-handshake.md:23) / `ECDH-P256` ×2 (this file L17/L35). Canonical target `ECDH-P256`. None moved since `eedd36fc` |
| **B-8** SDK docstring quotes deleted A-L2 phrase | CROSS-TRACK | **OPEN, unchanged** — `implementation/sdk/web4/security.py` unmoved (pre-C140; 0 commits since C218) |
| **B-9 / B-M2** rotation mutate-vs-stable-DID | DESIGN-Q | **interim HELD** (§2.3); semantics decision stands |
| **B-10** `cose:ES256` mislabel | CROSS-TRACK | **OPEN, unchanged** — live count across the 3 tracked LCT files = **8** (`lct-capability-levels.md` 5 + `multi-device-lct-binding.md` 2 + `LCT-linked-context-token.md` 1); target `cose:EdDSA` still 0-present. Unchanged since C218 |
| **C-M1 ≡ C70-B-D1** canonical crypto-suite/encoding SSOT | DESIGN-Q | **OPEN** — C180-N1 (web4-core no COSE codec) + C218-N1 (`attestation.rs` 3rd site) STAND by freeze; no 4th site this fire (§B′.2) |
| **B-H2 / B-11** W4-IOT-1 + AES-CCM | DESIGN-Q / CROSS-TRACK | **OPEN, unchanged** — C140 DELTA-1 W4-IOT-1 Profile contradiction intact; handshake §6.0.1 did **not** move (0 commits since C218) |
| **B-L6 / B-L7** vector ownership; `device` W4ID method | CROSS-TRACK | OPEN, unchanged (`data-formats.md` unmoved) |

**C140 DELTA-1 status**: unchanged. Handshake §6.0.1 (the W4-IOT-1 Profile=COSE site) has not moved since C140 → DELTA-1 still open, still routed to the C-M1/B-D1 SSOT decision. No re-adjudication owed.

---

## §B — Corpus-Delta Pass (siblings moved since the C218 snapshot, 2026-07-18): **EMPTY**

Checked every sibling `security-framework.md` cites or holds a carry-mirror in, via `git log fd622824..HEAD -- <file>`:

| Sibling | Cited/carry role | Moved since C218 (fd622824)? |
|---|---|---|
| `protocols/web4-handshake.md` | §1.3 → §6.0.3/§6.0.4; §3.1 → §6.0.5/§9/§6.1; B-H2 | **No** (0 commits) |
| `core-spec/core-protocol.md` | B-7 / W4-IOT-1 mirror | **No** (0) |
| `registries/initial-registries.md` | B-7 / W4-IOT-1 mirror | **No** (0) |
| `core-spec/LCT-linked-context-token.md` | §2.3 rotation (§7.3); B-10 | **No** (0) |
| `core-spec/multi-device-lct-binding.md` | B-10 `cose:ES256` | **No** (0) |
| `core-spec/lct-capability-levels.md` | B-10 `cose:ES256` | **No** (0) |
| `implementation/sdk/web4/security.py` | B-8 docstring | **No** (0) |

**§B is EMPTY — 0 of 7 tracked siblings moved since the C218 snapshot → 0 findings routed.** This is the **first security delta with an empty corpus-delta surface** — the same signature C254 (errors) recorded one fire earlier: the `#531` LCT mover that C218 adjudicated (disjoint) predates this snapshot, and no cited sibling has moved since. The one thing that *did* move in the corpus this interval, `web4-core/src/role_extension.rs` (`4f76f110`), is not a `.md` sibling `security-framework.md` cites — it is a Rust module, handled in §B′.

---

## §B′ — SDK-Mirror Expansion (C172/C174/C176/C178/C180/C216/C218 guard)

### B′.1 — The C180/C218 mirrors `crypto.rs` / `pair_channel.rs` / `attestation.rs` / `ratchet.rs`: **ALL frozen since ≤C218 → every prior verdict HELD by construction**

Re-derived live: last-touch of each is **before** the C218 snapshot (2026-07-18):
- `web4-core/src/crypto.rs` → `bcff32fb` (2026-06-08); `web4-core/src/pair_channel.rs` → `bcff32fb` (2026-06-08); `web4-core/src/vault/crypto.rs` → `090739f6` (2026-06-15) — **frozen since before C180**.
- `web4-core/src/attestation.rs` → `0e997079` (2026-07-17); `web4-core/src/ratchet.rs` → `7b048a78` (2026-07-16) — **present at C218, adjudicated there, unmoved since.**

Therefore all prior §B′ verdicts are preserved by freeze:
- **C180-N2 (concordance)**: web4-core implements **5/6** W4-BASE-1 primitives exactly (X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 / HKDF-SHA256), correctly omits SHOULD-only W4-FIPS-1. **HELD.**
- **C180-N1 (COSE gap, LOW/CROSS-TRACK)**: web4-core omits the §1.3 MTI COSE/CBOR *encoding* (0 `cose`/`cbor`/`ciborium` deps). **HELD** — spec CORRECT, SDK lags; feeds C-M1/B-D1.
- **C218-N1 (INFO, CROSS-TRACK)**: `attestation.rs` (false-for-security, genuine LCT-witnessing mirror) signs raw string preimages with Ed25519, 0 COSE/CBOR — a 3rd web4-core no-COSE-envelope site. **HELD.**
- **`ratchet.rs` dismissal (C218 §B′.4)**: hash-ratchet/forward-secrecy primitive with no §1/§2/§3 suite surface. **HELD** (unmoved; the noted-not-opened "should ratchet's KDF chaining cite §1.1 HKDF-SHA256?" remains below the frozen spec's granularity — still noted, still not opened).

### B′.2 — New candidate mirror `web4-core/src/role_extension.rs`: **GENUINE mirror of the `role-extension.ttl` / entity-types *Role* spec — FALSE mirror *for security-framework* (C178/C216/C218 third-kind boundary)**

`role_extension.rs` (moved `4f76f110` "oracle consult/write sets on Scope — Piece B for oracle-scope gating", 2026-07-18, **the only web4-core `.rs` file to change since C218**) is the guard's sole live candidate this interval. The genuine-mirror gate must run on it because it `use`s `crate::crypto::KeyPair` and does signing — the same crypto-adjacency that triggered the gate on `attestation.rs`.

**Genuine-mirror gate — decided FOR security-framework specifically (do NOT import another lens's verdict):**

Its own module doc (L1-19) declares it "the Rust representation of the canonical `web4-standard/ontology/role-extension.ttl` schema (Phase-0 concord, #486), plus role-LCT issuance and a registry … turns an orchestration role from a bare string into a first-class `EntityType::Role` LCT entity carrying its law extension (affordances / responsibilities / scope)." It models **role affordances / responsibilities / scope-gating + role-LCT issuance** — the entity-types §4 *Role* / SAL / `role-extension.ttl` surface. Its security footprint is **7 tokens, all consumer calls**: `use crate::crypto::KeyPair` (L23); `issue()` mints a role LCT via `LctBuilder::new(EntityType::Role)`, obtains its keypair, and calls `lct.sign_binding(&keypair)` (L244-251). Therefore:

- It **is** a genuine mirror — but of the **`role-extension.ttl` / entity-types *Role* spec**, a *different* target than `security-framework.md`. (Contrast errors' `error.rs`, C178: a name-collision mirroring *nothing*. `role_extension.rs` faithfully mirrors real canon, just not *this* canon — exactly the C218 `attestation.rs` third-kind.)
- **For `security-framework.md` it is a FALSE mirror** by the C178/C216/C218 boundary rule: it defines **0** §1.1/§1.3 suite-table primitives, **0** §2 key-management (no rotation/derivation/lifecycle), **0** §3 auth-crypto handshake, and carries **0** COSE/CBOR deps. It is a **downstream CONSUMER** of §1 crypto (calls `crypto.rs`'s `KeyPair` and `lct.rs`'s `sign_binding`), not a mirror of security's suite/key-mgmt/auth surface. Security-framework's mirror remains `crypto.rs` (§B′.1); `role_extension.rs` belongs to the **entity-types / SAL / role-orchestration** SDK-mirror surface. (This is the same file the entity-types C252 guard tracks as the Effector/Role mirror and the mrh C238 guard noted `4f76f110` added "0 MRH token" to — the security lens likewise finds it adds **0 security-suite primitive**.)

**No new C180-N1 corroboration site (refute-by-default, anti-inflation).** Unlike `attestation.rs` — which defines its *own* raw-string preimage `Attestation::message` and signs it — `role_extension.rs` defines **no signing primitive of its own**: `sign_binding` lives in `lct.rs:410`; `role_extension.rs` merely **calls** it. The signing path it exercises is the existing `lct.rs`→`crypto.rs` binding-signature family already covered by C180. So it is **not** a 4th distinct no-COSE-envelope site, and it adds **nothing** to the C-M1/B-D1 bundle beyond what C180-N1/C218-N1 already record. Recording the non-corroboration explicitly so the next security delta does not re-mine it.

**B-3 forward-awareness (not a finding).** `role_extension.rs` realizing role/scope-based authorization in the Rust core is a datapoint that the SDK's authz model is going the **role/scope (SAL/R6)** route rather than the VC route §3.2 names — informative for the standing B-3 DESIGN-Q's eventual operator decision. It neither resolves nor contradicts §3.2 (frozen); recorded as forward-awareness under B-3 in §A.3, **not** opened as a defect.

### B′.3 — Considered-and-dismissed (anti-padding transparency)

- **`vault/crypto.rs` Argon2id KDF** — re-dismissed exactly as C180/C218: passphrase-based at-rest storage ≠ the W4-BASE-1 *protocol* KDF (HKDF-SHA256). Frozen since C180.
- **`pair_channel.rs` 12-byte random nonce (Sprint-E MVP)** — re-dismissed as below §1.1 granularity. Frozen since C180.
- **`ratchet.rs` KDF chaining** — the C218 noted-not-opened item (should it cite §1.1 HKDF-SHA256?) — unmoved, still below the frozen spec's granularity. Not opened.

---

## §C — Fresh-Internal Refute-by-Default Pass

**0 net-new internal contradictions.** Blob-identity (`2880e643`) mechanically preserves C140/C180/C218's clean §C; the candidates re-confirmed at their frozen call sites:
- §1.1 table ⟷ §1.2 prose: KEM/Sig/AEAD/Hash/KDF/Encoding token-match for both suites (`ECDSA-P256` table vs `ECDSA with P-256` prose = long-standing benign wording variant, carried from C140/C180/C218 — not a finding).
- §1.3 MTI COSE (`crv = 6` / `alg = -8`) ⟷ §1.1 W4-BASE-1 Encoding=COSE / §1.2 COSE RFC 9052/9053: consistent.
- §2.3 rotation prose ⟷ `LCT-linked-context-token.md` §7.3 "Rotation (Key Update)" (LCT frozen, 0 commits since C218): resolves.
- §3.1 ⟷ handshake §6.0.5 / §9 / §6.1 (handshake frozen since C140): all resolve.
- No standalone W4-IOT-1 statement in this file (the C140 DELTA-1 divergence is corpus-side).

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| — | — | **No net-new finding this fire.** (Sole web4-core mover `role_extension.rs` gated out as false-for-security; no new corroboration site; §B empty; carries all held.) | — |

**Totals**: 0 HIGH, 0 MEDIUM, 0 LOW, **0 INFO net-new** — **0 actionable net-new defects inside `security-framework.md`**.

**§A**: 6/6 C69 fixes + 1 C109 fix HELD by byte-freeze (blob-identical to C218's verified blob), 0 regressed; C56 completeness clean. All 8 carries STAND (B-7 5-spelling drift + B-10 8-site `cose:ES256` re-verified live and unchanged; C140 DELTA-1 unchanged). No carry resolved into a defect.
**§B**: **EMPTY** — 0 of 7 tracked siblings moved since the C218 snapshot → 0 findings routed (first security delta with an empty corpus-delta surface).
**§B′**: C180/C218 mirrors (`crypto.rs`/`pair_channel.rs`/`attestation.rs`/`ratchet.rs`) all frozen since ≤C218 → C180-N1/N2 + C218-N1 + false-for-security + ratchet-dismissal HELD by construction. Sole new mover `role_extension.rs` (`4f76f110` oracle-scope) = GENUINE mirror of `role-extension.ttl`/entity-types Role ⇒ **false mirror for security** (C178/C216/C218 third-kind); a §1-crypto CONSUMER with no §1/§2/§3 primitive and no own signing site ⇒ **no new C180-N1 corroboration**.
**§C**: 0 net-new internal contradictions.

**This is `security-framework.md`'s 4th CONSECUTIVE fully-clean delta for the file itself (C140 + C180 + C218 + C256), 0 actionable net-new inside the file.**

---

## Key Adjudication

1. **The genuine-mirror gate's "third kind" recurred, on a different consumer.** C218 mapped `attestation.rs` as a genuine mirror of the LCT *witnessing* spec (false-for-security). C256 maps `role_extension.rs` as a genuine mirror of the `role-extension.ttl` / entity-types *Role* spec (false-for-security). Both are §1-crypto **consumers**, not mirrors of security's §1/§2/§3 surface. The discipline is identical: run the gate on the crypto-adjacent mover, name *which* spec it genuinely mirrors, and hand the pointer to the owning lineage rather than misreading its presence as a security gap.

2. **A consumer that only *calls* the signing path is NOT a new corroboration site.** The one place C256 could have inflated is treating `role_extension.rs`'s `lct.sign_binding(&keypair)` as a 4th no-COSE-envelope datapoint for C-M1/B-D1. Refute-by-default kills it: `sign_binding` is defined in `lct.rs`, not here — `role_extension.rs` exercises the *existing* `lct.rs`→`crypto.rs` family C180 already counts. `attestation.rs` was a distinct site because it defined its *own* preimage; `role_extension.rs` does not. Recording the non-corroboration prevents the next delta from re-mining it.

3. **Empty corpus-delta surface + frozen mirror ≠ skip the pass.** §B was empty and every mirror frozen, yet the fire was still worth running because §B′ had exactly one live question — a Rust module (`role_extension.rs`) that landed *after* the C218 snapshot and that no prior security pass saw. That single genuine/false-mirror adjudication (plus its explicit non-corroboration ruling) is the pass's entire yield, and no work was manufactured beyond it (policy condition 2). This is the same proportionate no-op shape C254 (errors) recorded one fire earlier.

---

## Next-Turn Carry

- **C257 `security-framework.md` remediation slot = NO-OP** (0 actionable net-new inside the file — consistent with the C140/C180/C218/C256 frozen-clean quadruple). Nothing to apply inside `security-framework.md`. Rotation advances.
- **Rotation advances to next-oldest = `registries/initial-registries.md` → its next delta (C258).** [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, SAL, LCT, ISP, entity-types, errors, security, **registries**, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.] Registries last audited C220 (5th delta, 2026-07-18). Continue the SDK-mirror expansion, but apply the genuine-mirror gate first: registries is a data/taxonomy file; C182 recorded a NEGATIVE Rust-mirror gate (no `web4-core/src/*.rs` registry mirror). Verify a GENUINE mirror exists (SDK registry loaders/fixtures, NOT crypto) before divergence analysis. **Guard for C258**: `initial-registries.md` carries the B-7 FIPS-KEM spelling `P-256 ECDH` (line 6) — one of the 5 divergent sites; do NOT re-open as net-new (it is the CROSS-TRACK B-7 carry, gated on the C-M1 SSOT decision).
- **`role_extension.rs` belongs to the entity-types / SAL / role-orchestration SDK-mirror surface** — already tracked there (entity-types C252 Effector/Role mirror guard; SAL role-side). The next **entity-types** (post-C252) or **SAL** (post-C246) delta's §B′ owns any genuine finding in it (affordance/scope/role-LCT shape vs entity-types §4 / `role-extension.ttl`); security's probe (this fire) only ruled it out for security. **Do NOT re-run the security gate on it next security delta unless it gains a §1/§2/§3 primitive or its own signing preimage.**
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: **DESIGN-Q** — C-M1 ≡ B-D1 crypto-suite/encoding SSOT (C180-N1 + C218-N1 SDK-readiness + C140 DELTA-1 W4-IOT-1 Profile-vs-Encoding contradiction; no 4th site added C256); B-3 authz basis (VCs vs SAL/R6 — C256 forward-note: SDK `role_extension.rs` realizes the role/scope side); B-9/B-M2 rotation mutate-vs-stable-DID; B-H2/B-11 W4-IOT-1 + AES-CCM. **CROSS-TRACK** — B-7 normalize 5 FIPS-KEM spellings to `ECDH-P256` (gated on C-M1); B-8 SDK `security.py` docstring quote; B-10 `cose:ES256`→`cose:EdDSA` (8 sites across 3 LCT files); B-L6/B-L7 vector ownership + `device` W4ID method; **C180-N1** web4-core COSE gap (LOW); **C180-N2** crypto-mirror genuine/concordant (INFO); **C218-N1** attestation.rs COSE corroboration (INFO). **Do not self-apply any.**
- **D0 (protocols/ cluster) still operator-gated** — unrelated to security; do not touch.

---

*Audit produced under Autonomous Session Protocol v2 — slot `web4-20260723-060036`, LEAD voice. Read-only: no spec, SDK, or test-vector files were modified this turn. Remediation (C257) is the next alternation turn and is a no-op (0 AUTONOMOUS findings) → rotation advances to `registries/initial-registries.md` (C258).*
