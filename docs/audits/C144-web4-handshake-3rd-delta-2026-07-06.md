# C144 — `protocols/web4-handshake.md` Third-Delta Re-Audit (the DELTA-1-owner slot)

**Date**: 2026-07-06
**Auditor**: Legion autonomous web4 track (slot `180036`, LEAD voice)
**Target**: `web4-standard/protocols/web4-handshake.md` (269 lines; `Last-Updated: 2026-06-29`)
**Lineage**: C28 first-pass (#264 audit / #265 fix `8b3bbac3`) → C72 first delta (#360 `248a6c3e`) → C73 remediation (#362 `0179c470`) → C112 second delta (#401) → C113 remediation (#404 `57caa2e1`) → **C144** (third delta)
**Method**: §A prior-finding verification (C113's two fixes N1/N2 held token-by-token) + regression sweep + **C56 claim-vs-canonical re-read** of the §3 suite table against handshake's *own* §6.0 profile vocabulary. §B **re-adjudication of the inbound DELTA-1 carry at its owner** (this is the designed handoff: C140/C142 explicitly routed DELTA-1 "to the owner, actionable there"). Audit-only — **no spec edits**.

---

## Headline

**0 net-new internal defects. handshake is CLEAN and CORRECT.** But this fire produces a *substantive re-adjudication*: the C140/C142 **DELTA-1** disposition is **INVERTED**, and this audit **SUPERSEDES their adjudication direction** with owner-side evidence.

- **C140 (#454) / C142 (#459) concluded**: handshake's C113 flip of W4-IOT-1 Profile `CBOR`→`COSE` made handshake the *sole outlier*; `registries:7` / `core-protocol:20` (both `CBOR`) were the "correct, corroborating" majority; handshake should revert to `CBOR`.
- **C144 concludes**: **`handshake:24 = COSE` is CORRECT.** The real defect is **`core-protocol.md:20` + `registries/initial-registries.md:7` = `CBOR`** — a serialization value placed in a column whose vocabulary is `{COSE, JOSE}`. The 2-vs-1 majority is *agreement-in-error*, not corroboration: both `CBOR` cells are the same category error, propagated.

This is an **audit-catches-audit** reversal in the exact class the third-pass discipline exists to catch ([[feedback_auditor_blindspot_pattern]]). Independently adversarially verified this fire (refute-by-default verifier CONCEDED "COSE correct beyond reasonable doubt"). **No spec edited** — the corrective fix (`CBOR`→`COSE` at the two sibling sites) is routed to the operator-gated crypto-suite SSOT bundle (**C-M1 ≡ B-D1**), because it touches files referenced by the merged #454/#459 and lives on an unresolved-SSOT surface.

---

## §A — Prior-finding verification (C113 remediation of C112's N1/N2)

Target byte-frozen since C113 `57caa2e1` (2026-06-29, 7 days). Both C113 fixes verified in place:

| C112 finding | C113 fix | Current site | Verdict |
|--------------|----------|--------------|---------|
| **N1** (LOW, autonomous) — §3 W4-IOT-1 Profile column `CBOR`→`COSE` | applied | §3 L24: `W4-IOT-1 (MAY) \| X25519 \| Ed25519 \| AES-CCM \| SHA-256 \| COSE` | **HELD — and CORRECT** (see §B) |
| **N2** (LOW, autonomous) — §6.0.3 sig-structure scope contradiction with §6.0.5/§6.1 | applied | §6.0.3 L143: "…Sign the canonical CBOR map… **This governs non-handshake signed payloads** (LCT binding, Metering); for `HandshakeAuth` the signing input is `Hash(TH \|\| channel_binding)` per §6.0.5…, while this section governs the `COSE_Sign1` envelope and CBOR canonicalization" | **HELD** — the general/specific scope split is now explicit; the §6.0.3-vs-§6.0.5 signing-input ambiguity is resolved |

**Regression sweep**: 0 `&#` HTML-entity artifacts; 269 lines intact; C113 was single-file (handshake only), no cross-spec surface disturbed. No HELD fix introduced a new defect in a previously-clean region. The full C73 fix set (B1–B10) verified HELD at C112 remains byte-frozen through C113.

**C56 claim-vs-canonical (the §3 suite table vs handshake's own §6.0):** the §3 `Profile` column must draw from the vocabulary handshake itself defines in §6.0. It does, for all three rows — see §B. This is the decisive check the majority-vote heuristic skipped.

---

## §B — DELTA-1 re-adjudication at the owner (the inversion)

### The three sites (all use a column literally headed `Profile`)

| Site | W4-BASE-1 | W4-FIPS-1 | **W4-IOT-1** |
|------|-----------|-----------|--------------|
| `handshake.md` §3 (L20 header, L22-24) | COSE | JOSE | **COSE** |
| `core-protocol.md` §1 (L16 header, L18-20) | COSE | JOSE | **CBOR** |
| `registries/initial-registries.md` (L5-7, trailing parenthetical) | COSE | JOSE | **CBOR** |
| `security-framework.md` §… (L16-17) | COSE | JOSE | *(row absent)* |

### Why COSE is correct (four independent legs — none depends on any SSOT decision)

1. **Column vocabulary is `{COSE, JOSE}`.** handshake §6.0 (L120) — *"Web4 defines **two** canonicalization and signature profiles"*: `application/web4+cbor → w4_sig_cose@1` (**COSE/CBOR profile**) and `application/web4+json → w4_sig_jose@1` (**JOSE/JSON profile**) (L126-127). §12 Interop Profiles (L264-266) confirms only these two. **"CBOR" is the serialization half of the two-part name "COSE/CBOR" — it is not a profile name.** A `CBOR` value in a Profile column is a category error.

2. **No third profile exists.** A tree-wide search finds no bare/raw-CBOR profile distinct from COSE. §6.0.2 MTI (L132): *"All Web4 endpoints MUST implement COSE/CBOR."* There is nowhere for a `CBOR`-but-not-`COSE` suite to live.

3. **W4-IOT-1's signature is COSE-only.** The COSE/CBOR profile uses Ed25519/EdDSA (`alg=-8`, `crv=6`, §6.0.3 L138-144); the JOSE profile requires ES256/ECDSA-P256 (§6.0.4 L148). W4-IOT-1's SIG = Ed25519 → it **cannot** be JOSE and there is no third profile → its only spec-defined home is the COSE/CBOR profile → Profile = **COSE**.

4. **Internal inconsistency in the very docs that write `CBOR`.** In `core-protocol.md` and `registries` themselves, **W4-BASE-1** (also Ed25519, also the COSE/CBOR profile) is labeled **COSE** (`core-protocol:18`, `registries:5`), while **W4-IOT-1** — identical profile — is labeled **CBOR**. Two suites in the same profile are labeled differently *within one table*: IOT-1 writes the serialization-half, BASE-1 writes the profile-name-half. IOT-1=CBOR is the anomaly, self-evident from the table's own BASE-1 row.

### Why the C140/C142 majority-vote failed

C140/C142 reasoned: *"registries:7 (CBOR) corroborates core-protocol:20 (CBOR); handshake:24 (COSE) is the sole outlier → revert handshake to CBOR."* Two errors:

- **Agreement-in-error ≠ corroboration.** Both `CBOR` cells are the *same* propagated category error (serialization written where a profile name belongs). The C113 commit body itself already flagged that "registry L7 carries the same imprecision." A 2-vs-1 count is not a semantic argument and it collapses the moment you note both `CBOR` docs also label the sibling Ed25519 suite (BASE-1) as `COSE`.
- **It dropped C112's still-valid independent leg.** C112's N1 gave *two* reasons for COSE: (a) "core-protocol §1 says COSE" and (b) "handshake's own §6.0 vocabulary is {COSE, JOSE}." Reason (a) was a **misread** — `core-protocol:20` has read `CBOR` continuously since `18209449` (2025-09-11), verified by `git blame` this fire; it was never COSE. C113's commit body inherited and repeated that misread citation. C140 correctly caught the broken (a) — but then discarded the *whole* conclusion, including the independent and correct (b). **(b) alone establishes COSE**, regardless of what any sibling table says. That is the C144 correction.

### Provenance note (matters for routing)

The `CBOR`-in-Profile anomaly is **not C113-introduced and not handshake's.** `core-protocol:20` has said `CBOR` since 2025-09-11 (blame `18209449`), 9+ months before C113. C73 (`0179c470`) *created* handshake's W4-IOT-1 row and initially copied `registries`' `CBOR`; C113 (`57caa2e1`) corrected handshake to `COSE`. So the sequence is: the two sibling tables carried the category error from the start; handshake briefly inherited it (C73) then fixed itself (C113). **handshake is now the one doc that has it right.** Reverting it (the C140/C142 recommendation) would propagate the error back into the only correct site.

### edge-device-profile.md — checked, not a counter-example

`profiles/edge-device-profile.md:14-15` lists W4-IOT-1's "Primary Format: CBOR / CBOR Deterministic Encoding." That is the **serialization layer** (fully consistent with the COSE/CBOR profile, which *is* deterministic-CBOR-serialized); it defines **no** signature encoding distinct from COSE. Absence of the word "COSE" there ≠ a distinct raw-CBOR profile. Not a defect; not a counter-example.

---

## Disposition / Routing

| Item | Disposition this fire |
|------|----------------------|
| §A — C113 N1 + N2 fixes | **HELD** token-by-token; N1 additionally confirmed **CORRECT** (not the defect C140/C142 called it). 0 regression. |
| **DELTA-1 (re-adjudicated)** | **INVERTED. `handshake:24 = COSE` is CORRECT and stays.** The defect is `core-protocol.md:20` + `registries/initial-registries.md:7` = `CBOR`. This audit **SUPERSEDES the C140 (#454) / C142 (#459) adjudication direction** (which said handshake was the outlier). Owner-side evidence: handshake §6.0 vocabulary + the sibling tables' own internal BASE-1/IOT-1 inconsistency. |
| **Corrective fix** (recommended, NOT applied) | Change **`core-protocol.md:20`** and **`registries/initial-registries.md:7`** Profile `CBOR`→`COSE`. Routed as **one item into the operator-gated crypto-suite SSOT bundle C-M1 ≡ B-D1** — it touches files referenced by the merged #454/#459 and sits on the unresolved registry-SSOT surface. **Do NOT self-apply.** |
| Net-new internal (handshake) | **0.** handshake is clean and correct. |

**Why not self-apply the two-cell fix?** Three reasons, all binding: (1) it reverses the direction of two *merged* audit PRs — the corpus record must show a reasoned, dated reversal, not a silent contradicting edit; (2) it lands on the operator-gated C-M1≡B-D1 crypto-suite SSOT surface (registry canonical-form still UNANSWERED per B-D1); (3) audit-slot discipline: AUDIT surfaces + routes, REMEDIATION (operator-authorized) applies. The fix is trivial and unambiguous — but the *authority* to reverse merged conclusions on an operator-gated surface is not the auditor's.

---

## Operator memo item (for the standing crypto-suite SSOT bundle, C-M1 ≡ B-D1)

> **W4-IOT-1 Profile column — resolve `CBOR` → `COSE` at two sites.** The suite `Profile` column vocabulary is `{COSE, JOSE}` (handshake §6.0). W4-IOT-1 (Ed25519 → COSE/CBOR profile) must read `COSE`. `handshake.md:24` already does (correct). `core-protocol.md:20` and `registries/initial-registries.md:7` read `CBOR` (a serialization, not a profile name) — long-standing category error (since 2025-09-11 in core-protocol). **Recommended: set both to `COSE`.** This reverses the C140/C142 DELTA-1 direction (documented in C144 with owner-side evidence). Trivial one-token edit each; gated here only because it sits on the unresolved registry-SSOT surface and touches merged-PR files.

---

## Pattern note (C144)

The failure mode this fire corrects is **"majority-vote across sibling tables without checking the column's own vocabulary."** When N sites agree and 1 disagrees, the disciplined move is not a vote — it is to find where the column's *meaning* is defined (here handshake §6.0) and test each value against it. Two sites sharing a category error out-vote the one correct site every time under a naive count. The general guard: **a value is validated against its column's definition, not against a headcount of sibling cells** — especially when the "majority" cells can be shown internally inconsistent (BASE-1=COSE / IOT-1=CBOR for the same profile, in the same table). Corollary for delta re-audits: when a prior audit rejected a remediation because its *citation* was wrong, re-check whether the remediation's *conclusion* had an independent second leg — C112's §6.0 argument survived the death of its core-protocol citation, and that survival is the whole finding.
