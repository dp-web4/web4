# C142 — Registries `initial-registries.md` 3rd-Delta Re-Audit

**Date**: 2026-07-05
**Auditor**: Legion autonomous web4 track (slot `180036`)
**Target**: `web4-standard/registries/initial-registries.md`
**Lineage**: C70 (cluster first-pass, #353) → C71 (remediation, #354) → C110 (cluster 2nd-delta, #398-era) → **C142** (3rd-delta)
**Method**: §A prior-finding verification (token-by-token hold on the C71 fixes that touch this file) + **C56 claim-vs-canonical re-read** of all 3 Suite-ID rows vs `core-protocol.md` §1 (run even though the target is byte-frozen — per the C108 lesson that a byte-stable target can still yield). §B corpus-delta scan since the C110 snapshot (2026-06-28): diff sibling movement, apply the **C140 CARRY-SCAN** to the sole remediated mover (read its remediation rationale, not just its byte-diff), snapshot-presence guard on standing carries, re-route (do NOT apply) cross-track/operator-gated carries. Audit-only — no spec edits.

---

## Headline

**0 net-new inside the target.** `initial-registries.md` is byte-frozen since the C71 remediation (`3f1d6fad`, 2026-06-18 — 17 days). All C71 fixes that touch this file (B-A1 IOT-1 row, B-A5 status line, B-A6 HKDF tokens) held token-by-token AND passed the claim-vs-canonical re-read against current `core-protocol.md` §1. This is the file's **second consecutive fully-clean delta** (C110 + C142).

The one substantive result is an **inbound cross-track carry**, not a net-new internal defect: the C140 **DELTA-1** (handshake-C113 flipped W4-IOT-1 Profile `CBOR`→`COSE`) lands directly on this file's L7. Re-verified this fire at cited-hunk granularity from first-hand git evidence: **registries:7 (`CBOR`) corroborates core-protocol:20 (`CBOR`); handshake:24 (`COSE`) is the sole outlier.** The defect is owned by handshake — registries:7 is the *correct* value and stays frozen. Re-routed, not applied.

---

## §A — C71 fix verification + claim-vs-canonical (C56)

Target byte-frozen since C71 `3f1d6fad` (2026-06-18). Canonical re-read this turn: `core-protocol.md` §1 suite table (frozen since `3084e4d2`, 2026-06-05 — predates target, no inbound drift).

| C71 fix (this file) | Held byte-frozen? | Claim-vs-canonical (C56) |
|---------------------|-------------------|--------------------------|
| **B-A1** — L7 `W4-IOT-1 : X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF (CBOR)` | ✅ | ✅ **exact** vs core-protocol:20 (`X25519\|Ed25519\|AES-CCM\|SHA-256\|HKDF\|CBOR`). See §B for the handshake outlier. |
| **B-A5** — uniform `Status: Draft • Last-Updated: …` (L2) | ✅ | ✅ neutral on the B-D1 canonical-form decision, as intended |
| **B-A6** — `HKDF` KDF token on BASE-1/FIPS-1 (L5/L6) | ✅ | ✅ matches core-protocol §1 (BASE-1 KDF=HKDF L18, FIPS-1 KDF=HKDF L19) |

**Full Suite-ID claim-vs-canonical (all 3 rows):**

| Row | registries | core-protocol §1 | Verdict |
|-----|-----------|------------------|---------|
| **W4-BASE-1** | `X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 / HKDF (COSE)` (L5) | L18 `X25519\|Ed25519\|ChaCha20-Poly1305\|SHA-256\|HKDF\|COSE` | ✅ **exact** |
| **W4-FIPS-1** | `P-256 ECDH / ECDSA-P256 / AES-128-GCM / SHA-256 / HKDF (JOSE)` (L6) | L19 `P-256ECDH\|ECDSA-P256\|AES-128-GCM\|SHA-256\|HKDF\|JOSE` | ⚠️ KEM spelling only: `P-256 ECDH` vs `P-256ECDH` — the **known B-C4 carry**, operator-gated (see §B) |
| **W4-IOT-1** | `X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF (CBOR)` (L7) | L20 `X25519\|Ed25519\|AES-CCM\|SHA-256\|HKDF\|CBOR` | ✅ **exact** — registries agrees with core-protocol; handshake is the divergent site |

**Regression sweep**: 0. No `&#` HTML-entity artifacts. Error-code catalog (L14-59) unchanged; the two codes B-C1 tracks (`W4_ERR_WITNESS_REQUIRED` L33, `W4_ERR_PROTO_FORMAT` L52) remain present here.

---

## §B — Corpus-delta + carry re-route (0 net-new internal)

**Sibling movement since the C110 snapshot (2026-06-28):**

| Sibling cited/related | Last commit | Moved since 2026-06-28? |
|-----------------------|-------------|-------------------------|
| `core-protocol.md` (§1 suite table) | `3084e4d2` 2026-06-05 | No (predates) |
| `errors.md` (error-codes ref target) | `6189432d` 2026-06-17 | No (predates) |
| `security-framework.md` | `eedd36fc` 2026-06-28 | On-snapshot; §3.1 citation only, no suite-table change (already cleared C110 + C140) |
| **`web4-handshake.md`** | **`57caa2e1` 2026-06-29** | **YES — sole mover. C113 remediation.** |

### The sole mover: handshake C113 `57caa2e1` — CARRY-SCAN, not disjointness

Two tests, per the C140 lesson:

- **Disjointness test** (did the mover touch a section this file *cites*?): the registries cluster cites handshake **§5** (Capability & Suite Negotiation — via `extensions.md`'s B-A2 anchor). C113 touched handshake's **§ suite table (~L24)** and **§ signature-structure (~L164)** — *different sections*. Disjointness says "no impact."
- **CARRY-SCAN** (did the mover disturb a *corpus invariant this file tracks*?): **YES.** C113's hunk (own git evidence):
  ```
  -| W4-IOT-1 (MAY)    | X25519  | Ed25519    | AES-CCM   | SHA-256 | CBOR    |
  +| W4-IOT-1 (MAY)    | X25519  | Ed25519    | AES-CCM   | SHA-256 | COSE    |
  ```
  W4-IOT-1's encoding was `CBOR` (consistent with core-protocol + registries) **before** C113 and `COSE` **after**. The invariant "W4-IOT-1 uses CBOR" — tracked at registries:7 — is now contradicted by handshake alone.

**Disposition — DELTA-1 (MED, CROSS-TRACK, owned by handshake; = the inbound C140 carry):**
- registries:7 (`CBOR`) is **byte-frozen and correct** — it corroborates core-protocol:20 (`CBOR`). The three-site state pre-C113 was fully consistent (all CBOR); C113 introduced the only divergence.
- Per the C140 finding, C113's driving rationale ("core-protocol says COSE") was **false** — core-protocol:20 says CBOR. So the remediation that produced the mover introduced a contradiction that did not previously exist.
- **This is NOT registries' to fix.** registries stays frozen; the outlier byte is handshake:24. Routed to the handshake track / the C-M1≡B-D1 crypto-suite SSOT bundle. **Snapshot-presence guard**: registries:7=CBOR was present at the C70 blob and every snapshot since → **not net-new here**.

### Standing carries — re-confirmed OPEN, unchanged owners

- **B-D1 (FLAGSHIP) — Registry SSOT inversion** [MED, operator-gated]: README still ships two parallel registry systems and demotes `initial-registries.md` (the corpus-cited form) under the numeric orphan files. Still **UNANSWERED** (no trace in SESSION_FOCUS / forum). Gates any future registries remediation. Sharpening (unchanged from C110): initial-registries.md remains *more* complete than the declared-SSOT `errors.md` on the two B-C1 codes.
- **B-C4 ≡ C68 B-7 — W4-FIPS-1 KEM spelling drift** [MED, operator-gated]: live-verified 3 spellings this turn — `ECDH-P256` (security-framework:17/35, recommended canonical) / `P-256ECDH` (core-protocol:19) / `P-256 ECDH` (registries:6). Unchanged; folds into the security-framework C-M1 suite-registry SSOT carry.
- **B-C1 — errors.md missing `W4_ERR_WITNESS_REQUIRED` + `W4_ERR_PROTO_FORMAT`** [MED, errors/handshake-owned]: live-verified `errors.md` still holds **0** occurrences of both; `W4_ERR_PROTO_FORMAT` is still a live MUST-abort at handshake:164. STILL OPEN; both codes present here (L33/L52) → snapshot-guard, not net-new. Owner = errors.md.
- **B-D2 / B-D3 / B-C2 / B-C3 / B-C5 / B-C6 / B-C7**: all unchanged, sibling/operator-gated (subordinate to B-D1 or to a sibling delta cycle). No movement.

---

## Routing summary

| Bucket | Disposition this turn |
|--------|----------------------|
| §A C71 fixes (B-A1/B-A5/B-A6) | Held byte-frozen + claim-vs-canonical CLEAN. 0 regression. No action. |
| All 3 Suite-ID rows vs core-protocol §1 | BASE-1/IOT-1 exact; FIPS-1 KEM = known B-C4 drift only. |
| **DELTA-1 (inbound C140 carry)** | **CONFIRMED at cited-hunk granularity; owned by handshake (C113 outlier); registries:7=CBOR is correct + frozen. Route to handshake / C-M1≡B-D1 SSOT. Do NOT edit registries.** |
| Operator design-Qs (B-D1/B-D2/B-D3) | Re-confirmed OPEN. B-D1 gates future registries remediation. Surface in the standing operator memo. |
| Cross-track (B-C1/B-C4/B-C2…B-C7) | Re-confirmed OPEN, sibling-owned. Route inbound, do NOT apply. |
| **Net new (internal)** | **0** — honest clean result. |

**Pattern note (C142):** registries' non-cleanness is *entirely* external — a sibling's remediation (C113) disturbed a corpus invariant (W4-IOT-1 encoding) that this frozen file tracks, and the frozen file holds the *correct* value. This is the mirror-image of the C121/C123 "frozen file's own prior remediation over-reached" pattern: here the frozen file is the corroborating witness and a *different* file's remediation is the regression. The CARRY-SCAN (not the disjointness test) is what catches it. Next rotation step after the C143 registries remediation slot (no-op — all buckets operator/sibling-gated) = **handshake cluster 2nd/3rd-delta** — where DELTA-1 becomes actionable at its owner.
