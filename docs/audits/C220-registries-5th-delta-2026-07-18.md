# C220 — Registries `initial-registries.md` 5th-Delta Re-Audit

**Date**: 2026-07-18
**Auditor**: Legion autonomous web4 track (slot `180036`)
**Target**: `web4-standard/registries/initial-registries.md`
**Lineage**: C70 (cluster first-pass, #353) → C71 (remediation, #354) → C110 (2nd-delta) → C142 (3rd-delta) → C182 (4th-delta) → **C220** (5th-delta)
**Method**: §A prior-finding verification (token-by-token hold on the C71 fixes B-A1/B-A5/B-A6 + **C56 claim-vs-canonical** re-read of all 3 Suite-ID rows vs `core-protocol.md` §1 at live HEAD) + regression sweep. §B corpus-delta scan since the C182 snapshot (2026-07-12) with snapshot-presence guard; re-route (do NOT apply) all operator/sibling-gated carries. **§B′ SDK-mirror-expansion applying the C178/C182 genuine-mirror gate** — verify a GENUINE registry-taxonomy mirror exists at live HEAD (incl. the NEW post-C182 modules `attestation.rs`/`ratchet.rs`) before any divergence analysis. Audit-only — no spec edits (B-D1 flagship gates any registries remediation and is UNANSWERED).

---

## Headline

**0 net-new internal.** `initial-registries.md` is byte-frozen since the C71 remediation (`3f1d6fad`, 2026-06-18 — **30 days**). All C71 fixes held token-by-token and passed the claim-vs-canonical re-read against live `core-protocol.md` §1. This is the file's **fourth consecutive fully-clean delta** (C110 + C142 + C182 + C220).

**§B corpus-delta is EMPTY (for registry surface).** The corpus *did* move since the C182 snapshot — W4IP Effector work (#521/#522/#523/#525), the LCT §1.2 "Inspectable Evidence" canonization (#531), mcp §7.8 mailbox, and the C214/C195 remediations all landed. **None touch a registries-cited sibling** (`core-protocol.md`, `errors.md`, `web4-handshake.md`, `security-framework.md`, or the registry sibling files — all predate the snapshot), and **none introduce a new registry value** (0 new suite IDs, 0 new extension IDs, 0 new `W4_ERR_*` codes in the entire `web4-standard/` delta). The W4IP additions are governance *response vocabulary* (`notice|warn|quarantine|correct|rehabilitate`) and a Coercive/Extractive *rule category* — neither belongs in `initial-registries.md` (Suite IDs / Extension IDs / wire Error Codes), so the frozen registry has no inbound obligation from the moved corpus. All standing carries (B-D1, B-C4, B-C1, DELTA-1) re-verified at live HEAD, unchanged, owners unchanged.

**§B′ genuine-mirror gate — NEGATIVE, and it holds across two new modules.** For this DATA/taxonomy registry there is still **no code-level mirror at all**: `web4-core` (Rust `src/` **and** the `python/` tree) contains **ZERO** registry tokens — no suite IDs, no `W4_ERR_` codes, no extension IDs anywhere. Two modules landed since C182 (`attestation.rs`, #527/#538; `ratchet.rs`, #529) — both encode **0** registry tokens, so the C182 negative gate is not merely still-true-by-staleness, it is **re-confirmed against the crate's growth edge**. The only live artifacts pinned to a registry value remain the two handshake conformance fixtures (`handshakeauth_{cose,jose}.json`, `suite: "W4-BASE-1"`) — both still concordant, not findings. Logged as a CROSS-TRACK / SDK-readiness observation (C220-N1, INFO), same shape as C182-N1.

---

## §A — C71 fix verification + claim-vs-canonical (C56)

Target byte-frozen since C71 `3f1d6fad` (2026-06-18). Canonical re-read this turn: `core-protocol.md` §1 suite table (frozen since `3084e4d2`, 2026-06-05 — predates target, no inbound drift).

| C71 fix (this file) | Held byte-frozen? | Claim-vs-canonical (C56), live HEAD |
|---------------------|-------------------|-------------------------------------|
| **B-A1** — L7 `W4-IOT-1 : X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF (CBOR)` | ✅ | ✅ **exact** vs core-protocol:20. Handshake outlier per DELTA-1 (§B). |
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

## §B — Corpus-delta + carry re-verification (0 net-new; §B EMPTY for registry surface)

**Registries-cited sibling movement since the C182 snapshot (2026-07-12):**

| Sibling cited/related | Last commit | Moved since 2026-07-12? |
|-----------------------|-------------|-------------------------|
| `core-protocol.md` (§1 suite table) | `3084e4d2` 2026-06-05 | No (predates) |
| `errors.md` (error-code SSOT ref) | `6189432d` 2026-06-17 | No (predates) |
| `web4-handshake.md` | `57caa2e1` 2026-06-29 | No (predates; DELTA-1 already booked) |
| `security-framework.md` | `eedd36fc` 2026-06-28 | No (predates; cleared C110/C140/C180/C218) |
| registries siblings (README/error-codes/cipher-suites/extensions) | `3f1d6fad` 2026-06-18 | No (all frozen with target) |

**Corpus moved, registry surface did not.** New commits since the snapshot were reviewed for any registry obligation:

| Corpus mover (since 2026-07-12) | Introduces a suite/ext/error-code registry value? | Disposition |
|---------------------------------|--------------------------------------------------|-------------|
| W4IP Effector #521/#522/#523/#525 | No — response verbs (`notice\|warn\|quarantine\|correct\|rehabilitate`) + Coercive/Extractive **rule category**; governance vocabulary, not wire taxonomy | Disjoint from `initial-registries.md` scope |
| LCT §1.2 "Inspectable Evidence" #531 | No | Disjoint |
| mcp §7.8 asynchronous mailbox | No new `W4_ERR_` code (accept-and-defer conformance prose) | Disjoint |
| C214 (entity-types) / C195 (reputation) remediations | No | Disjoint |

Verification: `git log --since=2026-07-12 -p -- web4-standard/ | grep '^+' | grep -oE 'W4_ERR_[A-Z_]+|w4_ext_[a-z0-9_]+@[0-9]+|W4-[A-Z]+-[0-9]+' | sort -u` → **empty**. Zero new registry values entered the corpus.

**Result: §B corpus-delta is EMPTY for the registry surface** — the same shape as C180/C182. A moved-but-disjoint corpus, so no CARRY-SCAN candidate this turn.

### Standing carries — re-verified at live HEAD, all OPEN, owners unchanged

- **B-D1 (FLAGSHIP) — Registry SSOT inversion** [MED, operator-gated]: README still ships two parallel registry systems and demotes `initial-registries.md` (the corpus-cited form) under the numeric orphan files. Still **UNANSWERED** (no trace in `SESSION_FOCUS.md` / forum this fire). Gates any registries remediation → this turn stays audit-only.
- **B-C4 ≡ C68 B-7 — W4-FIPS-1 KEM spelling drift** [MED, operator-gated]: three distinct spellings live-verified this turn — `ECDH-P256` (security-framework:17/35, recommended canonical) / `P-256ECDH` (core-protocol:19) / `P-256 ECDH` (registries:6). Unchanged. Folds into the security-framework C-M1 suite-registry SSOT carry.
- **B-C1 — errors.md missing `W4_ERR_WITNESS_REQUIRED` + `W4_ERR_PROTO_FORMAT`** [MED, errors/handshake-owned]: live-verified `errors.md` still holds **0** occurrences of both (`grep -c` → 0); both codes present here (L33/L52) → snapshot-guard, not net-new. STILL OPEN, owner = errors.md.
- **DELTA-1 (inbound C140/C142 carry) — handshake W4-IOT-1 `CBOR`→`COSE`** [MED, CROSS-TRACK, owned by handshake]: re-verified at live HEAD — `web4-handshake.md:24` = `COSE` (sole outlier); `registries:7` = `CBOR` corroborates `core-protocol:20` = `CBOR`. **registries:7 is the correct value and stays frozen.** Routes to handshake / the C-M1≡B-D1 SSOT bundle. Snapshot-guard: registries:7=CBOR present at the C70 blob → not net-new here.
- **B-D2 / B-D3 / B-C2 / B-C3 / B-C5 / B-C6 / B-C7**: unchanged, sibling/operator-gated (subordinate to B-D1 or a sibling delta cycle). No movement.

---

## §B′ — SDK-mirror-expansion (genuine-mirror gate: NEGATIVE, re-confirmed on the growth edge)

Per the C172–C180 method guard, re-derive the target-primitive implementers at live HEAD before declaring §B clean. For a **DATA/taxonomy** registry the candidate mirror is an SDK registry loader / enum / conformance fixture — **NOT** `web4-core/src/*.rs` crypto (that mirrors the *primitives*, audited at C180/C218, not the *registry strings*).

**Gate step 1 — does a genuine mirror exist?**

| Candidate mirror | Evidence (live HEAD) | Verdict |
|------------------|----------------------|---------|
| `web4-core/src/` (Rust crate) | `grep -rE 'W4_ERR\|W4-BASE\|W4-FIPS\|W4-IOT\|w4_ext' web4-core --include=*.rs` → **0 hits** anywhere. `error.rs` = 0 `W4_ERR_` codes (C178's confirmed FALSE mirror). `crypto.rs` implements the primitives but names **no** suite-ID strings. | **NO mirror** |
| **NEW post-C182 modules** `attestation.rs` (#527/#538), `ratchet.rs` (#529) | `grep -cE 'W4_ERR\|W4-BASE\|W4-FIPS\|W4-IOT\|w4_ext'` → **0 / 0** | **No mirror** — the crate's growth edge still does not encode registry taxonomy |
| `web4-core/python/` | 0 registry tokens | **NO mirror** |
| `web4-standard/testing/test-vectors/handshakeauth_{cose,jose}.json` | each carries `suite: "W4-BASE-1"` — a registry *value* | **Concordant fixture**, not a mirror (uses one value; `W4-BASE-1` ∈ registry) |
| `forum/nova/.../registries/initial-registries.md` | frozen parallel spec, `1bac7d7f` 2025-09-11 — pre-B-A6 | Frozen parallel sibling → B-D1 / [[feedback_frozen_parallel_spec]] territory (sync-vs-supersede lifecycle), NOT a line-diff finding, NOT net-new |

**Gate step 2 — divergence analysis:** N/A. The gate returned NEGATIVE, so there is no genuine mirror to diff. Per the C178/C180 discipline, a false/absent mirror is excluded from divergence analysis; the *result itself* is the finding.

### C220-N1 (INFO, CROSS-TRACK / SDK-readiness) — the registry taxonomy still has no code-level consumer, confirmed against a growing crate

The three Web4 registries (Suite IDs, Extension IDs, Error Codes) exist **only** in the spec corpus. `web4-core` (Rust + Python) does not encode any suite-ID string, extension-ID string, or `W4_ERR_*` code. C182 established this negative; C220 strengthens it: the crate **grew** by two wire-adjacent modules (`attestation.rs` does raw-string Ed25519 signing with 0 COSE/CBOR deps per C218-N1; `ratchet.rs` does HKDF chaining) and *still* names zero registry tokens. This is a genuine standing condition of the SDK, not a stale artifact of a frozen crate.

- **No drift surface** — the frozen registry strings cannot be contradicted by the crate, because the crate never names them (contrast C180/C218 `crypto.rs`, which *implements* the BASE-1 primitives and thus *could* diverge — 5/6 concordant + 1 COSE gap).
- **No code-side validation** — nothing in the SDK asserts that an over-the-wire `suite`/error-code value is a registered one; the handshake fixtures are the only live artifacts pinned to a registry value, and both are concordant with `W4-BASE-1`.
- **SDK-readiness item, not a spec defect:** the spec is CORRECT; when the SDK grows a wire-facing suite negotiator or a typed error taxonomy, it will need a registry loader/enum generated from these files. Same *shape* as C176 (spec canonical, SDK lags), C180-N1 / C218-N1 (COSE codec unimplemented, raw-string signing), and C188-N1 (absent wire layer). Bundles naturally with the C-M1≡B-D1 SSOT decision (whichever registry form is declared SSOT is the one an SDK loader should read).

**Boundary mapped (fourth data point in the mirror-expansion series):**

| Turn | Target | Rust mirror | Kind | Divergence surface |
|------|--------|-------------|------|--------------------|
| C180/C218 | security-framework primitives | `crypto.rs` | **genuine** | yes → 5/6 concordant + 1 COSE gap |
| C178/C216 | errors (wire taxonomy) | `error.rs` | **false** (name-collision) | excluded |
| C182 | registries (taxonomy strings) | *(none)* | **absent** | none exists → INFO readiness item |
| **C220** | registries (taxonomy strings) | *(none — incl. new attestation.rs/ratchet.rs)* | **absent, re-confirmed on growth edge** | none exists → INFO readiness item |

---

## Routing summary

| Bucket | Disposition this turn |
|--------|----------------------|
| §A C71 fixes (B-A1/B-A5/B-A6) | Held byte-frozen + claim-vs-canonical CLEAN at live HEAD. 0 regression. No action. |
| All 3 Suite-ID rows vs core-protocol §1 | BASE-1/IOT-1 **exact**; FIPS-1 KEM = known B-C4 drift only. |
| §B corpus-delta | **EMPTY for registry surface** — corpus moved (W4IP/LCT/mcp) but disjoint; 0 new registry values. |
| DELTA-1 (handshake W4-IOT-1 COSE outlier) | Re-verified live: registries:7=CBOR correct + frozen; handshake:24=COSE is the outlier. Route to handshake / C-M1≡B-D1. Do NOT edit registries. |
| **C220-N1 (genuine-mirror gate NEGATIVE, re-confirmed on growth edge)** | **INFO / CROSS-TRACK. Registry taxonomy has NO code-level mirror in web4-core (Rust+Python), incl. new attestation.rs/ratchet.rs → no drift surface, no code-side validation. SDK-readiness item, bundles with C-M1≡B-D1. No spec mutation.** |
| Operator design-Qs (B-D1/B-D2/B-D3) | Re-confirmed OPEN. B-D1 gates future registries remediation. Surface in the standing operator memo. |
| Cross-track (B-C1/B-C4/B-C2…B-C7) | Re-confirmed OPEN, sibling-owned. Route inbound, do NOT apply. |
| **Net new (internal)** | **0** — honest clean result. |

**Pattern note (C220):** registries is now **4 consecutive clean deltas** (C110/C142/C182/C220). Its non-cleanness remains *entirely external* (DELTA-1, a sibling's regression on an invariant this frozen file corroborates). The value this turn: (1) the corpus visibly *moved* (W4IP Effector, LCT §1.2, mcp §7.8) yet the registry surface received **zero** obligations — a disjoint-mover result, not a stale-corpus one; (2) the genuine-mirror gate returns NEGATIVE **re-confirmed against the crate's growth edge** (two new wire-adjacent modules, still 0 registry tokens) — strengthening C182's "no registry loader/enum to keep in sync yet" from a snapshot into a standing SDK condition. Next rotation step after the C221 registries remediation slot (**NO-OP** — all buckets operator/sibling-gated, B-D1 unanswered) = **handshake cluster** next delta (where DELTA-1 becomes actionable at its owner).

---

## Review-gate self-audit

This audit creates no surface and drives no consequential act — it is a read-only analysis producing one Markdown record.

```
surface: C220 registries delta-audit doc   act: none (read-only audit; 0 spec/code edits)
S: low/reversible [construct: docs/audits/C220-registries-5th-delta-2026-07-18.md is additive-only]
R: n/a   W: n/a (no identity-bound act)
O: n/a   A: pass [construct: audit committed atomically with its evidence-basis, hash-chained via git]
V: n/a
verdict: PASS
```
