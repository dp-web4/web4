# C258 — Registries `initial-registries.md` 6th-Delta Re-Audit

**Date**: 2026-07-23
**Auditor**: Legion autonomous web4 track (slot `120036`)
**Target**: `web4-standard/registries/initial-registries.md`
**Lineage**: C70 (cluster first-pass, #353) → C71 (remediation, #354) → C110 (2nd-delta) → C142 (3rd-delta) → C182 (4th-delta) → C220 (5th-delta) → **C258** (6th-delta)
**Method**: §A prior-finding verification (byte-frozen hold on the C71 fixes B-A1/B-A5/B-A6 + **C56 claim-vs-canonical** re-read of all 3 Suite-ID rows vs `core-protocol.md` §1 at live HEAD) + regression sweep. §B corpus-delta scan since the C220 snapshot (2026-07-18) with snapshot-presence guard; re-route (do NOT apply) all operator/sibling-gated carries. **§B′ genuine-mirror gate FIRST** — verify a GENUINE registry-taxonomy mirror exists at live HEAD (incl. the two web4-core movers since C220, `lct.rs` #544 + `role_extension.rs` oracle-scope) before any divergence analysis. Audit-only — no spec edits (B-D1 flagship gates any registries remediation and is UNANSWERED).

---

## Headline

**0 net-new internal.** `initial-registries.md` is byte-frozen since the C71 remediation (`3f1d6fad`, 2026-06-18 — **35 days**; live blob `00a37a88`, 59 lines). All C71 fixes held by construction and passed the claim-vs-canonical re-read against live `core-protocol.md` §1. This is the file's **fifth consecutive fully-clean delta** (C110 + C142 + C182 + C220 + C258).

**§B corpus-delta is EMPTY for the registry surface.** No registries-cited sibling moved since the C220 snapshot (2026-07-18), and **zero** new registry values (0 suite IDs, 0 extension IDs, 0 `W4_ERR_*` codes) entered the entire `web4-standard/` delta this interval. The frozen registry has no inbound obligation.

**§B′ genuine-mirror gate — NEGATIVE, re-confirmed a third time on the crate's growth edge.** `web4-core` (Rust `src/` **and** the `python/` tree) still encodes **ZERO** registry tokens. Two `.rs` modules moved since C220 — `lct.rs` (#544 `authority_ratchet`) and `role_extension.rs` (`4f76f110` oracle-scope) — and **both encode 0 registry tokens**. These are the *same* modules the C256 security delta (one fire earlier) adjudicated as a ratchet-face and a §1-crypto *consumer* respectively; neither names a suite ID, extension ID, or `W4_ERR_` code. Anti-inflation discipline (per C256): a crypto-adjacent mover that carries no registry taxonomy is **not** a registry-mirror finding. Logged as CROSS-TRACK / SDK-readiness observation (C258-N1, INFO) — same shape as C182-N1 / C220-N1.

---

## §A — C71 fix verification + claim-vs-canonical (C56)

Target byte-frozen since C71 `3f1d6fad` (2026-06-18); `3f1d6fad..HEAD` touches this file 0 times → the C71 fixes hold **by construction** (blob identity `00a37a88`). Canonical re-read this turn: `core-protocol.md` §1 suite table (frozen since `3084e4d2`, 2026-06-05 — predates target, no inbound drift).

| C71 fix (this file) | Held byte-frozen? | Claim-vs-canonical (C56), live HEAD |
|---------------------|-------------------|-------------------------------------|
| **B-A1** — L7 `W4-IOT-1 : X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF (CBOR)` | ✅ | ✅ **exact** vs core-protocol:20. Handshake outlier per DELTA-1 (§B). |
| **B-A5** — uniform `Status: Draft • Last-Updated: …` (L2) | ✅ | ✅ neutral on the B-D1 canonical-form decision, as intended |
| **B-A6** — `HKDF` KDF token on BASE-1/FIPS-1 (L5/L6) | ✅ | ✅ matches core-protocol §1 (BASE-1 KDF=HKDF L18, FIPS-1 KDF=HKDF L19) |

**Full Suite-ID claim-vs-canonical (all 3 rows, live HEAD):**

| Row | registries | core-protocol §1 (live) | Verdict |
|-----|-----------|-------------------------|---------|
| **W4-BASE-1** | `X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 / HKDF (COSE)` (L5) | L18 `X25519\|Ed25519\|ChaCha20-Poly1305\|SHA-256\|HKDF\|COSE` | ✅ **exact** |
| **W4-FIPS-1** | `P-256 ECDH / ECDSA-P256 / AES-128-GCM / SHA-256 / HKDF (JOSE)` (L6) | L19 `P-256ECDH\|ECDSA-P256\|AES-128-GCM\|SHA-256\|HKDF\|JOSE` | ⚠️ KEM spelling only: `P-256 ECDH` vs `P-256ECDH` — the **known B-C4 carry**, operator-gated (see §B). NOT re-opened as net-new. |
| **W4-IOT-1** | `X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF (CBOR)` (L7) | L20 `X25519\|Ed25519\|AES-CCM\|SHA-256\|HKDF\|CBOR` | ✅ **exact** — registries agrees with core-protocol; handshake is the divergent site (DELTA-1) |

**Regression sweep**: 0. No HTML-entity artifacts (`&#`/`&amp;`/`&lt;`/`&gt;` → none). Extension-ID block intact (L10-12: `w4_ext_sdjwt_vp@1`, `w4_ext_noise_xx@1`, `w4_ext_93f07f2a@0`). Error-code catalog (L14-59) unchanged; both B-C1 codes (`W4_ERR_WITNESS_REQUIRED` L33, `W4_ERR_PROTO_FORMAT` L52) remain present here.

---

## §B — Corpus-delta + carry re-verification (0 net-new; §B EMPTY for registry surface)

**Registries-cited sibling movement since the C220 snapshot (2026-07-18):**

| Sibling cited/related | Last commit | Moved since 2026-07-18? |
|-----------------------|-------------|-------------------------|
| `core-protocol.md` (§1 suite table) | `3084e4d2` 2026-06-05 | No (predates) |
| `errors.md` (error-code SSOT ref) | `6189432d` 2026-06-17 | No (predates) |
| `web4-handshake.md` | `57caa2e1` 2026-06-29 | No (predates; DELTA-1 already booked) |
| `security-framework.md` | `eedd36fc` 2026-06-28 | No (predates; cleared C110/C140/C180/C218/C256) |
| registries siblings (README/error-codes/cipher-suites/extensions) | `3f1d6fad` 2026-06-18 | No (all frozen with target) |

**Zero new registry values entered the corpus.** Verification:
`git log --since=2026-07-18 -p -- web4-standard/ | grep '^+' | grep -oE 'W4_ERR_[A-Z_]+|w4_ext_[a-z0-9_]+@[0-9]+|W4-[A-Z]+-[0-9]+' | sort -u` → **empty**. No suite ID, extension ID, or error code was added, removed, or renamed in the interval.

**Result: §B corpus-delta is EMPTY for the registry surface** — the same shape as C182/C220. The registry surface received no obligations; no CARRY-SCAN candidate this turn.

### Standing carries — re-verified at live HEAD, all OPEN, owners unchanged

- **B-D1 (FLAGSHIP) — Registry SSOT inversion** [MED, operator-gated]: README still ships two parallel registry systems and demotes `initial-registries.md` (the corpus-cited form) under the numeric orphan files. Still **UNANSWERED** (no trace in `SESSION_FOCUS.md` / forum this fire). Gates any registries remediation → this turn stays audit-only.
- **B-C4 ≡ C68 B-7 — W4-FIPS-1 KEM spelling drift** [MED, operator-gated]: three distinct spellings still live — `ECDH-P256` (security-framework, recommended canonical) / `P-256ECDH` (core-protocol:19) / `P-256 ECDH` (registries:6). Unchanged. Folds into the security-framework C-M1 suite-registry SSOT carry. **NOT re-opened as net-new** (per C258 guard).
- **B-C1 — errors.md missing `W4_ERR_WITNESS_REQUIRED` + `W4_ERR_PROTO_FORMAT`** [MED, errors/handshake-owned]: `errors.md` frozen `6189432d` (predates snapshot); both codes present here (L33/L52) → snapshot-guard, not net-new. STILL OPEN, owner = errors.md.
- **DELTA-1 (inbound C140/C142 carry) — handshake W4-IOT-1 `CBOR`→`COSE`** [MED, CROSS-TRACK, owned by handshake]: re-verified — `registries:7` = `CBOR` corroborates `core-protocol:20` = `CBOR`; `web4-handshake.md:24` = `COSE` is the sole outlier. **registries:7 is the correct value and stays frozen.** Routes to handshake / the C-M1≡B-D1 SSOT bundle.
- **B-D2 / B-D3 / B-C2 / B-C3 / B-C5 / B-C6 / B-C7**: unchanged, sibling/operator-gated (subordinate to B-D1 or a sibling delta cycle). No movement.

---

## §B′ — SDK-mirror-expansion (genuine-mirror gate FIRST: NEGATIVE, re-confirmed on growth edge)

Per the C172–C182 method guard, re-derive the target-primitive implementers at live HEAD before declaring §B clean. For a **DATA/taxonomy** registry the candidate mirror is an SDK registry loader / enum / conformance fixture — **NOT** `web4-core/src/*.rs` crypto (that mirrors the *primitives*, audited at C180/C218/C256, not the *registry strings*).

**Gate step 1 — does a genuine mirror exist?**

| Candidate mirror | Evidence (live HEAD) | Verdict |
|------------------|----------------------|---------|
| `web4-core/src/` (Rust crate) | `grep -rE 'W4_ERR\|W4-BASE\|W4-FIPS\|W4-IOT\|w4_ext' web4-core --include=*.rs` → **0 hits**. `error.rs` = 0 `W4_ERR_` codes (C178's confirmed FALSE mirror). `crypto.rs` implements the primitives but names **no** suite-ID strings. | **NO mirror** |
| **web4-core `.rs` movers since C220** `lct.rs` (#544 `authority_ratchet`), `role_extension.rs` (`4f76f110` oracle-scope) | `grep -cE 'W4_ERR\|W4-BASE\|W4-FIPS\|W4-IOT\|w4_ext'` → **0 / 0**. These are the same modules C256 (one fire earlier) adjudicated: `lct.rs` #544 = the society-ratchet face; `role_extension.rs` = a §1-crypto **consumer** (`use crate::crypto::KeyPair`), FALSE-for-security. Neither names registry taxonomy. | **No mirror** — crypto-adjacent ≠ registry-mirror (anti-inflation, C256) |
| `web4-core/python/` | 0 registry tokens | **NO mirror** |
| `web4-standard/testing/test-vectors/handshakeauth_{cose,jose}.json` | each carries `suite: "W4-BASE-1"` — a registry *value* | **Concordant fixture**, not a mirror (uses one value; `W4-BASE-1` ∈ registry) |
| `forum/nova/.../registries/initial-registries.md` | frozen parallel spec, `1bac7d7f` 2025-09-11 — pre-B-A6 | Frozen parallel sibling → B-D1 / [[feedback_frozen_parallel_spec]] territory (sync-vs-supersede lifecycle), NOT a line-diff finding, NOT net-new |

**Gate step 2 — divergence analysis:** N/A. The gate returned NEGATIVE, so there is no genuine mirror to diff. Per the C178/C180 discipline, a false/absent mirror is excluded from divergence analysis; the *result itself* is the finding.

### C258-N1 (INFO, CROSS-TRACK / SDK-readiness) — registry taxonomy still has no code-level consumer, re-confirmed against a growing crate

The three Web4 registries (Suite IDs, Extension IDs, Error Codes) exist **only** in the spec corpus. `web4-core` (Rust + Python) encodes zero suite-ID string, extension-ID string, or `W4_ERR_*` code. C182 established this negative; C220 re-confirmed it on `attestation.rs`/`ratchet.rs`; **C258 re-confirms it a third time** on the two newest movers (`lct.rs` #544, `role_extension.rs`) — the crate keeps growing wire-adjacent modules and *still* names zero registry tokens.

- **No drift surface** — the frozen registry strings cannot be contradicted by the crate, because the crate never names them.
- **No code-side validation** — nothing in the SDK asserts an over-the-wire `suite`/error-code value is a registered one; the handshake fixtures are the only live artifacts pinned to a registry value, both concordant with `W4-BASE-1`.
- **SDK-readiness item, not a spec defect** — the spec is CORRECT; when the SDK grows a wire-facing suite negotiator or a typed error taxonomy, it will need a registry loader/enum generated from these files. Bundles naturally with the C-M1≡B-D1 SSOT decision (whichever registry form is declared SSOT is the one an SDK loader should read).

**Boundary mapped (fifth data point in the mirror-expansion series):**

| Turn | Target | Rust mirror | Kind | Divergence surface |
|------|--------|-------------|------|--------------------|
| C180/C218/C256 | security-framework primitives | `crypto.rs` | **genuine** | yes → 5/6 concordant + 1 COSE gap |
| C178/C216 | errors (wire taxonomy) | `error.rs` | **false** (name-collision) | excluded |
| C182 | registries (taxonomy strings) | *(none)* | **absent** | none exists → INFO readiness item |
| C220 | registries (taxonomy strings) | *(none — incl. attestation.rs/ratchet.rs)* | **absent, re-confirmed** | none → INFO |
| **C258** | registries (taxonomy strings) | *(none — incl. lct.rs #544 / role_extension.rs)* | **absent, re-confirmed on growth edge (3rd time)** | none → INFO |

---

## Routing summary

| Bucket | Disposition this turn |
|--------|----------------------|
| §A C71 fixes (B-A1/B-A5/B-A6) | Held by construction (byte-frozen) + claim-vs-canonical CLEAN at live HEAD. 0 regression. No action. |
| All 3 Suite-ID rows vs core-protocol §1 | BASE-1/IOT-1 **exact**; FIPS-1 KEM = known B-C4 drift only, NOT net-new. |
| §B corpus-delta | **EMPTY for registry surface** — no cited sibling moved; 0 new registry values corpus-wide. |
| DELTA-1 (handshake W4-IOT-1 COSE outlier) | Re-verified: registries:7=CBOR correct + frozen; handshake:24=COSE is the outlier. Route to handshake / C-M1≡B-D1. Do NOT edit registries. |
| **C258-N1 (genuine-mirror gate NEGATIVE, 3rd re-confirm on growth edge)** | **INFO / CROSS-TRACK. Registry taxonomy has NO code-level mirror in web4-core (Rust+Python), incl. new lct.rs #544 / role_extension.rs → no drift surface, no code-side validation. SDK-readiness item, bundles with C-M1≡B-D1. No spec mutation.** |
| Operator design-Qs (B-D1/B-D2/B-D3) | Re-confirmed OPEN. B-D1 gates future registries remediation. Surface in the standing operator memo. |
| Cross-track (B-C1/B-C4/B-C2…B-C7) | Re-confirmed OPEN, sibling-owned. Route inbound, do NOT apply. |
| **Net new (internal)** | **0** — honest clean result. |

**Pattern note (C258):** registries is now **5 consecutive clean deltas** (C110/C142/C182/C220/C258). Its non-cleanness remains *entirely external* (DELTA-1, a sibling's regression on an invariant this frozen file corroborates). The value this turn: (1) the genuine-mirror gate returns NEGATIVE **a third consecutive time on the crate's growth edge** — the two newest web4-core movers (`lct.rs` #544, `role_extension.rs`) are crypto-adjacent yet name zero registry tokens, so the anti-inflation catch from C256 held (crypto-adjacent ≠ registry-mirror; the same movers C256 security adjudicated do not create a registry face); (2) an EMPTY corpus-delta surface confirms the frozen registry accrued no inbound obligation. **Next rotation step**: the C259 registries remediation slot is a declared **NO-OP** (all buckets operator/sibling-gated, B-D1 unanswered — do NOT self-fix), and rotation advances +2 → **handshake cluster** next delta (`web4-handshake.md`, where DELTA-1 becomes actionable at its owner; last handshake audit C222, 2026-07-18). Guard for the next registries delta (~C296): apply the genuine-mirror gate FIRST — the mirror if any = SDK registry loader/enum, NOT crypto; do NOT re-open `initial-registries.md:6` `P-256 ECDH` as net-new (= B-7/B-C4 cross-track carry, gated on C-M1); do NOT re-run a registry gate on `lct.rs`/`role_extension.rs` unless one gains a registry token.

---

## Review-gate self-audit

This audit creates no surface and drives no consequential act — it is a read-only analysis producing one Markdown record.

```
surface: C258 registries delta-audit doc   act: none (read-only audit; 0 spec/code edits)
S: low/reversible [construct: docs/audits/C258-registries-6th-delta-2026-07-23.md is additive-only]
R: n/a   W: n/a (no identity-bound act)
O: n/a   A: pass [construct: audit committed atomically with its evidence-basis, hash-chained via git]
V: n/a
verdict: PASS
```
