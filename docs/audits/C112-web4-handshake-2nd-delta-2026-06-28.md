# C112 — `protocols/web4-handshake.md` Second Delta Re-Audit (prior C28 → C72 → C73)

**Date**: 2026-06-28
**Auditor**: autonomous web4 session (legion, firing `180036`, LEAD voice)
**Target**: `web4-standard/protocols/web4-handshake.md` (269 lines; header `Last-Updated: 2026-06-18T18:00:00Z`)
**Series**: C112 — **second delta re-audit**. Lineage: **C28** first-pass (#264 audit / #265 fix `8b3bbac3`) → **C72** first delta audit (#360 `248a6c3e`) → **C73** remediation of 10 autonomous C72 findings (#362 `0179c470`) → **C112**. File **byte-frozen since C73** (Jun 18 22:03, 10 days). This is the AUDIT turn following the C110 registries 2nd-delta audit (#398); rotation advanced registries → handshake (fixed-order round-robin).

**Methodology** (standard delta-re-audit method):
- **§A** — verify the 10 C73 fixes (B1–B10) held token-by-token; regression sweep; **C56 claim-vs-canonical re-read EVEN on a byte-frozen target** (C108 lesson: a fix can land verbatim yet its cross-doc CLAIM be imprecise against canonical); bidirectional re-verification of every carried design-Q / cross-track item against the current (post-C106/C108/C109/C110) corpus.
- **§B** — net-new surface. All cross-ref dependencies PREDATE the C73 freeze → corpus-delta surface is empty; yield is on the C56 re-read + **snapshot-guarded** internal-consistency of the C73-introduced text (adversarial refute-by-default verify, 1 verifier agent — proportional to a frozen target).
- **§C** — disposition / routing (autonomous → C113 / design-Q → operator / cross-track).

**Authority anchors re-read this session** (re-read, not recalled):
- `web4-standard/protocols/web4-handshake.md` (full, L1–L269)
- `core-spec/core-protocol.md` §1 suite table L14–20 (3 suites; W4-IOT-1 Profile = **COSE**)
- `registries/initial-registries.md` suite rows L5–7 (W4-IOT-1 parenthetical = **CBOR**); error codes L52
- `core-spec/errors.md` §2.6 (W4_ERR_PROTO_* — PROTO_VERSION/PROTO_SEQUENCE present, **PROTO_FORMAT absent**)
- `core-spec/data-formats.md` §4.1 derivation (`salt = sha256(peer_identifier)` deterministic; `pairwise_key[:16]` truncation)
- `web4-standard/implementation/reference/web4_demo.py` L89–90 (`W4-SessionKeys:I->R` / `R->I`)
- C72 snapshot of the target (`git show 248a6c3e:…`) for the snapshot-presence guard

---

## Summary

**§A result**: **10/10 C73 fixes HELD** token-by-token; **0 regression**; B2 reference (`web4_demo.py` L89-90 directional labels) and B6 length-claim (data-formats `[:16]`) both verified against their canonical sources. Bidirectional carries D1/D2/D3/D4 + X1/X2/X3/X4 all re-confirmed **OPEN** (corpus frozen).

**§B result — 2 net-new findings (both LOW, autonomous), breaking the would-be 0-net-new wrap:**

- **N1 (LOW, autonomous — remediation-introduced at C73)** — §3 W4-IOT-1 "Profile" column = **CBOR**, but it should be **COSE**. (a) `core-protocol.md` §1 L20 says Profile = COSE; (b) handshake's OWN §6.0.1–6.0.3 + §12 define the profile vocabulary as **COSE** ("COSE/CBOR Profile", `w4_sig_cose@1`) and **JOSE** — "CBOR" is the serialization, *not* a profile name; the sibling rows (W4-BASE-1 → COSE, W4-FIPS-1 → JOSE) fix the column vocabulary as {COSE, JOSE}. W4-IOT-1 (Ed25519 + CBOR) signs HandshakeAuth as a §6.0.3 `COSE_Sign1` → its profile is COSE. **Snapshot-guard: the W4-IOT-1 row did not exist at C72 (`248a6c3e`); it was born at C73, so the CBOR-vs-COSE divergence is C73-introduced** — the C108-class "verbatim fix, imprecise claim": C73's commit body said B1 "mirrors core §1 / registry L7", but those two sources *disagree* on the Profile column (core = COSE, registry = CBOR) and C73 took registry's CBOR. The registry L7 carries the same imprecision (registry has no "Profile" column header — a weaker trailing parenthetical) → cross-track note, but for handshake.md the internal authority (§6.0) makes COSE correct independent of any SSOT decision.

- **N2 (LOW, autonomous — pre-existing cross-section contradiction, auditor-blindspot catch)** — §6.0.3 L143 "Sig structure: **Sign the canonical CBOR map of the payload** excluding any sig/envelope fields" contradicts §6.0.5 L156 / §6.1 L190-191 which state the HandshakeAuth signature **covers `Hash(TH || channel_binding)`** and is detached, "**not the raw payload bytes**." §6.0.2 L134 scopes §6.0.3 to *all* signed payloads including HandshakeAuth, so for HandshakeAuth the general §6.0.3 rule (sign payload map) and the specific §6.0.5/§6.1 rule (sign `Hash(TH‖cb)`) give two different signing inputs. **Snapshot-guard: BOTH ingredients existed at C72 (L139 "Sign the canonical CBOR map", L152 "MUST cover Hash(TH‖cb)") → NOT C73-introduced.** C28 and C72 both missed it (C72-B3 was envelope *shape*, C72-B5 was nonce/ts) — C73's added §6.1 L190-191 "(not the raw payload bytes)" only *sharpened* it. A careful implementer reconciles it ("specific §6.0.5 overrides general §6.0.3"), so LOW; the fix is a one-clause scope clarification.

**Routing**: **2 autonomous** (→ C113 handshake remediation) / **0 new design-Q** / carried design-Q + cross-track unchanged.

---

## §A. Prior-Finding Verification (C73 remediation of C72)

### §A.1 — The 10 autonomous C73 fixes — all HELD (token-by-token)

| C72 ID | Fix | Current site | Verdict |
|--------|-----|--------------|---------|
| B1 suites-1 (MED) | add W4-IOT-1 (MAY) row to §3 | §3 L24: `W4-IOT-1 (MAY) \| X25519 \| Ed25519 \| AES-CCM \| SHA-256 \| CBOR` | **HELD** (row present) — but Profile col = CBOR → **N1** |
| B2 sm-rekey-1 (MED) | §6.2 directional keys (info `I->R`/`R->I`) | §6.2 L203-204 `k_i2r…"W4-SessionKeys:I->R"`, `k_r2i…"R->I"`; L206-207 role→send/recv map | **HELD** — matches `web4_demo.py` L89-90 verbatim |
| B3 msgshape-2 (MED) | §6.1 HandshakeAuth → valid §6.0.3 COSE_Sign1 envelope | §6.1 L171-186: `protected{alg:-8,kid,content-type}`, payload "signed excluding envelope/sig", detached `sig` | **HELD** |
| B4 nonce-1 (MED) | §9 name the replay-tracked nonce + scope | §9 L235-238: tracks "**HandshakeAuth `nonce`** (§6.1)", unique within HPKE `context_key` | **HELD** |
| B5 nonce-2 (MED) | nonce/ts freshness integrity (sign or state AEAD) | §6.1 L195-197: nonce/ts "**not** in the signed input… integrity is provided by the AEAD envelope" | **HELD** (non-prejudging — states AEAD, does not fold into sig) |
| B6 w4idp-3 (MED) | §4.1 add HKDF-Expand output length `L` | §4.1 L38 `L=16`; L40-42 "matching the 16-byte truncation in data-formats §4.1" | **HELD** — data-formats §4.1 L95 `pairwise_key[:16]` confirmed |
| B7 msgshape-1 (LOW) | §6.0.1 `ext` → per-message | §6.0.1 L125: "via `media` and `ext` in ClientHello / `ext_ack` in ServerHello" | **HELD** |
| B8 msgshape-5 (LOW) | §6.1 disambiguate `cap.ext` | §6.1 L192-194: "`cap.ext` carries authenticated capability-grant extensions… distinct from the `ext`/`ext_ack`… negotiation channel" | **HELD** |
| B9 nonce-3 (LOW) | §9 replay-window retention ≥ ts band | §9 L239-241: "MUST retain entries for at least the `ts` acceptance band (≥300s)" | **HELD** |
| B10 sig-4 (LOW) | §6.0.5 fix `channel_binding` serialization | §6.0.5 L156: "`channel_binding = epk_I \|\| epk_R`… raw KEM-public-key bytes… no separator; signing input `= Hash(TH \|\| channel_binding)`" | **HELD** |

**Regression sweep**: the #362 (C73) diff was single-file (handshake.md only), no cross-spec surface. No HELD fix introduced a NEW defect *in a previously-clean region*. Per [[feedback_remediation_introduced_regression]], B1's new §3 row IS the locus of a remediation-introduced divergence (**N1**) — caught precisely because the discipline mandates checking whether the remediation's added content is itself consistent with canonical. **0 regression in the verification sense; 1 remediation-introduced defect (N1) in the C56 sense.**

**Remediation-completeness (C56 method, run even though byte-stable)**: re-read each C73 claim token-by-token against canonical. B2's "matches `web4_demo.py`" → verified (L89-90 `I->R`/`R->I`). B6's "matching the 16-byte truncation in data-formats §4.1" → verified (`pairwise_key[:16]`, both yield the first 16 bytes of the expand stream). **B1's claim "mirrors core §1 / registry L7" → FALSE for the Profile column** (core §1 L20 = COSE, registry L7 = CBOR; the two disagree, C73 took registry) → **N1**. This is the precise C108 pattern: a verbatim-applied fix whose cross-doc CLAIM is imprecise against canonical — only surfaced by the claim-vs-canonical re-read, not by "is the edit present."

### §A.2 — Bidirectional re-verification of carried design-Q / cross-track items

| C72 ID | C72 status | Current corpus | C112 verdict |
|--------|-----------|----------------|--------------|
| **D1** w4idp-1 (HIGH) | design-Q — `peer_salt` MUST be exchanged but no message carries it | ClientHello §5.1 L83-93 / ServerHello §5.2 L98-108 still have **no salt field** | **OPEN** (couples D2 + C-M3) |
| **D2** w4idp-2 (MED) | design-Q — random-exchanged salt vs deterministic | handshake §4.2 L47-49 random+exchanged; data-formats §4.1 L88 `salt = sha256(peer_id)` deterministic, no exchange | **OPEN** — contradiction re-confirmed verbatim |
| **D3** C-H1/C-M1/C-M3 | design-Q | core §2 still 4-msg-MAC; handshake still 3-msg-sig; nonce 96 (handshake)/32 (core)/48-bit (vector); `w4idp-<base32>` (handshake) vs `w4id:pair:` (data-formats) | **OPEN** — all three re-confirmed; corpus frozen |
| **D4** errors-status-3 (INFO) | design-Q — §10 `AUTHZ_DENIED@401` rides errors B-1 | §10 L251 still `401` + `W4_ERR_AUTHZ_DENIED`; errors.md unchanged (C106 was 0-net-new) | **OPEN** — rides errors B-1 (recommend 403) |
| **X1** vectors (MED) | cross-track — regenerate handshakeauth_{cose,jose} | vectors still `2025-09-11` (`d5b79aad`), never regenerated | **OPEN** — vector maintainer |
| **X2** sig-2 (LOW) | cross-track — JOSE vector payload `alg` EdDSA→ES256 | vector unchanged | **OPEN** |
| **X3** sig-5 (LOW) | cross-track — JOSE vector `typ=JWT` | vector unchanged | **OPEN** |
| **X4** errors PROTO_FORMAT (MED) | cross-track — add to errors.md §2.6 (= C70 B-C1) | errors.md §2.6 L86-91 lists PROTO_VERSION/PROTO_SEQUENCE; **PROTO_FORMAT still absent** | **OPEN** — errors.md owner |
| **P-256 spelling** (C-M2 remnant) | cross-track / SSOT | handshake §3 L23 `P-256EC`; core §1 `P-256ECDH`; registry `P-256 ECDH` | **OPEN** — folds into operator-gated FIPS-KEM SSOT carry (C-M1 ≡ C70-B-D1; widened to 5 sites by C108/C110). Do NOT self-apply. |

No carry RESOLVED downstream this cycle (corpus frozen). No carry HARDENED beyond its C72 statement. D2's salt contradiction and X4's PROTO_FORMAT gap re-verified verbatim against the live sibling docs.

---

## §B. Net-New Findings (snapshot-guarded, adversarially verified)

Corpus-delta surface is **empty**: every handshake cross-ref dependency predates the C73 freeze (core-protocol Jun 5, registries Jun 18 10:03 < handshake 22:03, errors Jun 17, data-formats Jun 5, handshakeauth vectors 2025-09-11). So §B yield is entirely on the **C56 claim-vs-canonical re-read** + snapshot-guarded internal consistency. One adversarial verifier (refute-by-default) examined all 10 C73-fix spans; both findings below survived refutation.

### Autonomous-actionable (→ C113 remediation on handshake.md)

**N1 (LOW) — §3 W4-IOT-1 Profile column: CBOR → COSE** *[remediation-introduced at C73; C108-class]*
§3 L24's W4-IOT-1 row carries Profile = **CBOR**. The correct value is **COSE**:
- handshake's own §6.0.1 L126 (`w4_sig_cose@1` = "COSE/CBOR profile"), §6.0.2 L132 ("COSE/CBOR"), §6.0.3 L136 ("COSE/CBOR Profile"), §12 L265 ("COSE/CBOR (MTI)") establish the profile name as **COSE**; there is no "CBOR" profile. The sibling rows (L22 → COSE, L23 → JOSE) fix the column vocabulary as {COSE, JOSE}; "CBOR" is the serialization paired *with* COSE, not a profile.
- `core-protocol.md` §1 L20 independently says W4-IOT-1 Profile = **COSE**.
- Adversarial refutation tested ("handshake matches registry L7's CBOR, so core is the outlier"): **does not refute** — the defect is provable *internally* against handshake's own §6.0 normative prose, independent of any sibling; the registry agreement only shows the error is shared (and registry's parenthetical is a weaker authority with no "Profile" column header).
- **Snapshot-guard**: absent at C72 (`248a6c3e` had no W4-IOT-1 row) → born at C73 → remediation-introduced.
- **Fix (C113)**: §3 L24 Profile `CBOR` → `COSE`. **Cross-track note**: registry L7 carries the same `(CBOR)` → route to registries owner (couples loosely to the SSOT carry, but the profile-name correction is independent of the P-256 SSOT decision).

**N2 (LOW) — §6.0.3 "Sig structure" contradicts §6.0.5/§6.1 on the HandshakeAuth signing input** *[pre-existing cross-section contradiction; C28+C72 blindspot]*
§6.0.3 L143 "Sig structure: **Sign the canonical CBOR map of the payload** excluding any `sig`/envelope fields" vs §6.0.5 L156 + §6.1 L190-191 "the signature covers `Hash(TH || channel_binding)`… (**not the raw payload bytes**)". §6.0.2 L134 scopes §6.0.3 to all signed payloads *including HandshakeAuth*, so for HandshakeAuth the two clauses prescribe two different signing inputs (payload map vs `Hash(TH‖cb)`).
- A careful implementer reconciles it via "specific (§6.0.5) overrides general (§6.0.3)" → severity **LOW**, but the §6.0.3 line as written is literally false for HandshakeAuth.
- **Snapshot-guard**: both ingredients present verbatim at C72 (`248a6c3e` L139 "Sign the canonical CBOR map", L152 "MUST cover Hash(TH‖cb)") → **NOT C73-introduced**; an auditor-blindspot catch (C72-B3 addressed envelope *shape*, C72-B5 addressed nonce/ts — neither flagged the signing-input conflict). C73's L190-191 "(not the raw payload bytes)" *sharpened* it. See [[feedback_auditor_blindspot_pattern]].
- **Fix (C113)**: scope §6.0.3's "Sig structure" line — e.g. "Sign the canonical CBOR map of the payload excluding any `sig`/envelope fields (**for HandshakeAuth, the signing input is `Hash(TH ‖ channel_binding)` per §6.0.5, which governs the signed content; §6.0.3 governs the `COSE_Sign1` envelope/canonicalization**)." Or state §6.0.3's content-signing rule applies to non-handshake signed payloads (LCT binding, Metering) while §6.0.5 governs HandshakeAuth.

### Refuted / not net-new (recorded so they are not re-raised)
- All 10 C73-fix spans except the §3 row are internally consistent (verifier swept §4.1, §6.0.1, §6.0.5, §6.1 reshape, §6.2, §9, cap.ext → no additional defect).
- B6's data-formats §4.1 cross-ref length-claim → verified, not a defect.
- No corpus-delta findings (all deps frozen).

---

## §C. Disposition / Routing

| ID | Sev | Class | Route |
|----|-----|-------|-------|
| **N1** Profile CBOR→COSE | LOW | **autonomous** | §3 L24 Profile `CBOR`→`COSE` (→ C113); cross-track note to registries (L7 same) |
| **N2** §6.0.3 signing-input | LOW | **autonomous** | scope §6.0.3 L143 vs §6.0.5 for HandshakeAuth (→ C113) |
| D1 w4idp-1 | HIGH | design-Q | peer_salt carrier (couples D2 + C-M3) — operator |
| D2 w4idp-2 | MED | design-Q | random-exchanged vs `H(peer_id)` salt — operator |
| D3 C-H1/C-M1/C-M3 | HIGH/MED | design-Q | carried bundle — operator (NEVER auto-action) |
| D4 errors-status-3 | INFO | design-Q | §10 AUTHZ_DENIED@401 rides errors B-1 |
| X1 vectors | MED | cross-track | regenerate handshakeauth_{cose,jose} — vector maintainer |
| X2 sig-2 | LOW | cross-track | JOSE vector payload alg EdDSA→ES256 |
| X3 sig-5 | LOW | cross-track | JOSE vector typ=JWT |
| X4 PROTO_FORMAT | MED | cross-track | add to errors.md §2.6 (= C70 B-C1) — errors owner |
| P-256 spelling | — | cross-track/SSOT | `P-256EC` 3-way — operator-gated (C-M1 ≡ C70-B-D1, 5 sites). Do NOT self-apply. |

**No spec/SDK/vector edits made this turn** (audit turn). The **2 autonomous** items (N1, N2) are internal to handshake.md and queued for the next REMEDIATION turn (**C113**). The carried design-Q (D1–D4) bundle with C27-H1/H2 + C24-H1; the cross-track items (X1–X4) route to the vector maintainer and the errors.md owner; the P-256 spelling stays operator-gated.

**Next turn = REMEDIATION (C113)**: apply N1 (§3 Profile CBOR→COSE) + N2 (scope §6.0.3 signing-input) to `web4-standard/protocols/web4-handshake.md`. After C113, handshake.md will have completed two full delta cycles (C28→#265→C72→C73→C112→C113).

---

## Lessons

- **The C108 method paid off a second time**: running the C56 claim-vs-canonical re-read on a byte-frozen target — where all 10 fixes "held" — surfaced **N1**, a remediation-introduced divergence invisible to "is the edit present." A fix can land verbatim and still carry an imprecise cross-doc claim (here: C73 said B1 "mirrors core §1 / registry L7" but those two sources disagree on the Profile column).
- **The cross-section sweep paid off too**: **N2** is a pre-existing contradiction that *two* prior audits (C28, C72) missed because each finding was scoped to one concern (envelope shape; nonce). The auditor-blindspot pattern — contradictions *between* sections survive section-by-section passes — recurs. A C73 clarification edit ("not the raw payload bytes") made a latent conflict glaring.
- **Frozen ≠ clean.** This is the 11th frozen-target wrap in the C92–C112 streak, but it yielded **2 net-new** (vs C108's 1 and nine 0-net-new wraps). The yield came entirely from the two re-read disciplines, not from corpus delta (which was empty). Report honestly: 0 when clean (C110), N when found (C108, C112) — the method is the re-read, not a quota.
