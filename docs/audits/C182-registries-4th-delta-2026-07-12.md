# C182 — Registries `initial-registries.md` 4th-Delta Re-Audit

**Date**: 2026-07-12
**Auditor**: Legion autonomous web4 track (slot `000036`)
**Target**: `web4-standard/registries/initial-registries.md`
**Lineage**: C70 (cluster first-pass, #353) → C71 (remediation, #354) → C110 (cluster 2nd-delta) → C142 (3rd-delta, #402-era) → **C182** (4th-delta)
**Method**: §A prior-finding verification (token-by-token hold on the C71 fixes B-A1/B-A5/B-A6 + **C56 claim-vs-canonical** re-read of all 3 Suite-ID rows vs `core-protocol.md` §1 at live HEAD) + regression sweep. §B corpus-delta scan since the C142 snapshot (2026-07-05) with snapshot-presence guard; re-route (do NOT apply) all operator/sibling-gated carries. **§B′ SDK-mirror-expansion applying the C178/C180 genuine-mirror gate** — verify a GENUINE registry-taxonomy mirror exists before any divergence analysis. Audit-only — no spec edits (B-D1 flagship gates any registries remediation and is UNANSWERED).

---

## Headline

**0 net-new internal.** `initial-registries.md` is byte-frozen since the C71 remediation (`3f1d6fad`, 2026-06-18 — **24 days**). All C71 fixes held token-by-token and passed the claim-vs-canonical re-read against live `core-protocol.md` §1. This is the file's **third consecutive fully-clean delta** (C110 + C142 + C182).

**§B corpus-delta is EMPTY** — zero cited/related sibling moved since the C142 snapshot (2026-07-05); every sibling's last commit predates it. All standing carries (B-D1, B-C4, B-C1, DELTA-1) re-verified at live HEAD, unchanged, owners unchanged.

**§B′ genuine-mirror gate — NEGATIVE, and it maps a THIRD guard boundary.** For this DATA/taxonomy registry there is **no code-level mirror at all**: `web4-core/src/` contains **ZERO** registry tokens (no suite IDs, no `W4_ERR_` codes, no extension IDs anywhere in the crate). The only live artifacts that touch a registry value are two conformance fixtures (`handshakeauth_{cose,jose}.json`, `suite: W4-BASE-1`) — both concordant, not findings. This is the third distinct mirror outcome in the SDK-mirror-expansion series: C180 `crypto.rs` = **genuine** mirror; C178 `error.rs` = **false** mirror (name-collision, no wire taxonomy); C182 registries = **no** mirror (the taxonomy is spec-only; no implementation consumes the strings → no divergence surface, but also no code-side validation). Logged as a CROSS-TRACK/SDK readiness observation (C182-N1, INFO).

---

## §A — C71 fix verification + claim-vs-canonical (C56)

Target byte-frozen since C71 `3f1d6fad` (2026-06-18). Canonical re-read this turn: `core-protocol.md` §1 suite table (frozen since `3084e4d2`, 2026-06-05 — predates target, no inbound drift).

| C71 fix (this file) | Held byte-frozen? | Claim-vs-canonical (C56), live HEAD |
|---------------------|-------------------|-------------------------------------|
| **B-A1** — L7 `W4-IOT-1 : X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF (CBOR)` | ✅ | ✅ **exact** vs core-protocol:20 (`X25519\|Ed25519\|AES-CCM\|SHA-256\|HKDF\|CBOR`). Handshake outlier per DELTA-1 (§B). |
| **B-A5** — uniform `Status: Draft • Last-Updated: …` (L2) | ✅ | ✅ neutral on the B-D1 canonical-form decision, as intended |
| **B-A6** — `HKDF` KDF token on BASE-1/FIPS-1 (L5/L6) | ✅ | ✅ matches core-protocol §1 (BASE-1 KDF=HKDF L18, FIPS-1 KDF=HKDF L19) |

**Full Suite-ID claim-vs-canonical (all 3 rows, live HEAD):**

| Row | registries | core-protocol §1 (live) | Verdict |
|-----|-----------|-------------------------|---------|
| **W4-BASE-1** | `X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 / HKDF (COSE)` (L5) | L18 `X25519\|Ed25519\|ChaCha20-Poly1305\|SHA-256\|HKDF\|COSE` | ✅ **exact** |
| **W4-FIPS-1** | `P-256 ECDH / ECDSA-P256 / AES-128-GCM / SHA-256 / HKDF (JOSE)` (L6) | L19 `P-256ECDH\|ECDSA-P256\|AES-128-GCM\|SHA-256\|HKDF\|JOSE` | ⚠️ KEM spelling only: `P-256 ECDH` vs `P-256ECDH` — the **known B-C4 carry**, operator-gated (see §B) |
| **W4-IOT-1** | `X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF (CBOR)` (L7) | L20 `X25519\|Ed25519\|AES-CCM\|SHA-256\|HKDF\|CBOR` | ✅ **exact** — registries agrees with core-protocol; handshake is the divergent site (DELTA-1) |

**Regression sweep**: 0. No HTML-entity artifacts (`&#`/`&amp;`/`&lt;`/`&gt;` → none). Extension-ID block intact (L10-12: `w4_ext_sdjwt_vp@1`, `w4_ext_noise_xx@1`, `w4_ext_93f07f2a@0`). Error-code catalog (L14-59) unchanged; both B-C1 codes (`W4_ERR_WITNESS_REQUIRED` L33, `W4_ERR_PROTO_FORMAT` L52) remain present here.

---

## §B — Corpus-delta + carry re-verification (0 net-new; §B EMPTY)

**Sibling movement since the C142 snapshot (2026-07-05):**

| Sibling cited/related | Last commit | Moved since 2026-07-05? |
|-----------------------|-------------|-------------------------|
| `core-protocol.md` (§1 suite table) | `3084e4d2` 2026-06-05 | No (predates) |
| `errors.md` (error-code SSOT ref) | `6189432d` 2026-06-17 | No (predates) |
| `web4-handshake.md` | `57caa2e1` 2026-06-29 | No (predates; DELTA-1 already booked at C142) |
| `security-framework.md` | `eedd36fc` 2026-06-28 | No (predates; cleared C110/C140/C180) |
| registries siblings (README/error-codes/cipher-suites/extensions) | `3f1d6fad` 2026-06-18 | No (all frozen with target) |

**Result: §B corpus-delta is EMPTY** — the same shape as C180. No mover, so no CARRY-SCAN candidate this turn.

### Standing carries — re-verified at live HEAD, all OPEN, owners unchanged

- **B-D1 (FLAGSHIP) — Registry SSOT inversion** [MED, operator-gated]: README still ships two parallel registry systems and demotes `initial-registries.md` (the corpus-cited form) under the numeric orphan files. Still **UNANSWERED** (no trace in `SESSION_FOCUS.md` / forum). Gates any registries remediation → this turn stays audit-only.
- **B-C4 ≡ C68 B-7 — W4-FIPS-1 KEM spelling drift** [MED, operator-gated]: three distinct spellings live-verified this turn — `ECDH-P256` (security-framework:17/35, recommended canonical) / `P-256ECDH` (core-protocol:19) / `P-256 ECDH` (registries:6). Unchanged. Folds into the security-framework C-M1 suite-registry SSOT carry.
- **B-C1 — errors.md missing `W4_ERR_WITNESS_REQUIRED` + `W4_ERR_PROTO_FORMAT`** [MED, errors/handshake-owned]: live-verified `errors.md` still holds **0** occurrences of both; both codes present here (L33/L52) → snapshot-guard, not net-new. STILL OPEN, owner = errors.md.
- **DELTA-1 (inbound C140/C142 carry) — handshake W4-IOT-1 `CBOR`→`COSE`** [MED, CROSS-TRACK, owned by handshake]: re-verified at live HEAD — handshake:24 = `COSE` (sole outlier); registries:7 = `CBOR` corroborates core-protocol:20 = `CBOR`. **registries:7 is the correct value and stays frozen.** Routes to handshake / the C-M1≡B-D1 SSOT bundle. Snapshot-guard: registries:7=CBOR present at the C70 blob → not net-new here.
- **B-D2 / B-D3 / B-C2 / B-C3 / B-C5 / B-C6 / B-C7**: unchanged, sibling/operator-gated (subordinate to B-D1 or a sibling delta cycle). No movement.

---

## §B′ — SDK-mirror-expansion (genuine-mirror gate: NEGATIVE)

Per the C172–C180 method guard, re-derive the target-primitive implementers at live HEAD before declaring §B clean. For a **DATA/taxonomy** registry the candidate mirror is an SDK registry loader / enum / conformance fixture — **NOT** `web4-core/src/*.rs` crypto (that mirrors the *primitives*, audited at C180, not the *registry strings*).

**Gate step 1 — does a genuine mirror exist?**

| Candidate mirror | Evidence (live HEAD) | Verdict |
|------------------|----------------------|---------|
| `web4-core/src/` (Rust crate) | `grep -rE 'W4_ERR\|W4-BASE\|W4-FIPS\|W4-IOT\|w4_ext' web4-core/src/` → **0 hits** anywhere in the crate. `error.rs` = 0 `W4_ERR_` codes (C178's confirmed FALSE mirror). `crypto.rs` implements the primitives but names **no** suite-ID strings. | **NO mirror** — the crate does not encode the registry taxonomy |
| `web4-standard/testing/validator/validate_vectors.py` | 0 references to registries/suites/error-codes/cipher (frozen 2025-09-13) | Not a registry mirror |
| `web4-standard/testing/test-vectors/handshakeauth_{cose,jose}.json` | each carries `suite: "W4-BASE-1"` — a registry *value* | **Concordant fixture**, not a mirror (uses one value; `W4-BASE-1` ∈ registry) |
| `forum/nova/.../registries/initial-registries.md` | frozen parallel spec, `1bac7d7f` 2025-09-11 — pre-B-A6 (no HKDF token, no W4-IOT-1 row) | Frozen parallel sibling → **B-D1 / [[feedback_frozen_parallel_spec]] territory**, sync-vs-supersede lifecycle question, NOT a line-diff finding, NOT net-new |
| Archive / sprawl (`archive/`, `ledgers/`, `forum/nova/.../implementation/`) | scattered suite/error strings | Out of scope (archived/reference sprawl) |

**Gate step 2 — divergence analysis:** N/A. The gate returned NEGATIVE, so there is no genuine mirror to diff. Per the C178/C180 discipline, a false/absent mirror is excluded from divergence analysis; the *result itself* is the finding.

### C182-N1 (INFO, CROSS-TRACK / SDK-readiness) — the registry taxonomy has no code-level consumer

The three Web4 registries (Suite IDs, Extension IDs, Error Codes) exist **only** in the spec corpus. `web4-core` (the ratified Rust SDK) does not encode any of the suite-ID strings, extension-ID strings, or `W4_ERR_*` codes. Consequences:

- **No drift surface** — the frozen registry strings cannot be contradicted by the crate, because the crate never names them (contrast C180 `crypto.rs`, which *implements* the BASE-1 primitives and thus *could* diverge — and was 5/6 concordant).
- **No code-side validation** — nothing in the SDK asserts that an over-the-wire `suite`/error-code value is a registered one; the handshake fixtures (`handshakeauth_*.json`) are the only live artifacts pinned to a registry value, and both are concordant with `W4-BASE-1`.
- **SDK-readiness item, not a spec defect:** the spec is CORRECT; when the SDK grows a wire-facing suite negotiator or a typed error taxonomy, it will need a registry loader/enum generated from these files. This is the same *shape* as C176 (spec canonical, SDK lags) and C180-N1 (COSE codec unimplemented) — an SDK-track readiness observation, routed off-spec, no spec mutation. Bundles naturally with the C-M1≡B-D1 SSOT decision (whichever registry form is declared SSOT is the one an SDK loader should read).

**Boundary mapped (third data point in the mirror-expansion series):**

| Turn | Target | Rust mirror | Kind | Divergence surface |
|------|--------|-------------|------|--------------------|
| C180 | security-framework primitives | `crypto.rs` | **genuine** | yes → 5/6 concordant + 1 gap |
| C178 | errors (wire taxonomy) | `error.rs` | **false** (name-collision) | excluded |
| **C182** | registries (taxonomy strings) | *(none)* | **absent** | none exists → INFO readiness item |

---

## Routing summary

| Bucket | Disposition this turn |
|--------|----------------------|
| §A C71 fixes (B-A1/B-A5/B-A6) | Held byte-frozen + claim-vs-canonical CLEAN at live HEAD. 0 regression. No action. |
| All 3 Suite-ID rows vs core-protocol §1 | BASE-1/IOT-1 **exact**; FIPS-1 KEM = known B-C4 drift only. |
| §B corpus-delta | **EMPTY** — no sibling moved since the C142 snapshot (2026-07-05). |
| DELTA-1 (handshake W4-IOT-1 COSE outlier) | Re-verified live: registries:7=CBOR correct + frozen; handshake:24=COSE is the outlier. Route to handshake / C-M1≡B-D1. Do NOT edit registries. |
| **C182-N1 (genuine-mirror gate NEGATIVE)** | **INFO / CROSS-TRACK. Registry taxonomy has NO code-level mirror in web4-core → no drift surface, no code-side validation. SDK-readiness item, bundles with C-M1≡B-D1. No spec mutation.** |
| Operator design-Qs (B-D1/B-D2/B-D3) | Re-confirmed OPEN. B-D1 gates future registries remediation. Surface in the standing operator memo. |
| Cross-track (B-C1/B-C4/B-C2…B-C7) | Re-confirmed OPEN, sibling-owned. Route inbound, do NOT apply. |
| **Net new (internal)** | **0** — honest clean result. |

**Pattern note (C182):** registries is now **3 consecutive clean deltas** (C110/C142/C182). Its non-cleanness remains *entirely external* (DELTA-1, a sibling's regression on an invariant this frozen file corroborates). The SDK-mirror-expansion that surfaced net-new findings at C172–C176 and confirmed positive concordance at C180 here returns its **first fully-negative gate result** — and that negative is itself the value: it maps the boundary that a pure spec-side DATA/taxonomy registry has no implementation mirror at all, which is an SDK-readiness fact (there is no registry loader/enum to keep in sync yet), not a spec defect. Next rotation step after the C183 registries remediation slot (**NO-OP** — all buckets operator/sibling-gated, B-D1 unanswered) = **handshake cluster** next delta (where DELTA-1 becomes actionable at its owner).
