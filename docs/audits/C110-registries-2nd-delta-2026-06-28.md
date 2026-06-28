# C110 — Registries Cluster 2nd-Delta Re-Audit

**Date**: 2026-06-28
**Auditor**: Legion autonomous web4 track (slot `000036`)
**Target**: `web4-standard/registries/` — `README.md`, `cipher-suites.md`, `error-codes.md`, `extensions.md`, `initial-registries.md`
**Lineage**: C70 (first audit, #353) → C71 (remediation, #354) → **C110**
**Method**: §A prior-finding verification (token-by-token hold) + #-regression sweep + **C56 claim-vs-canonical re-read** of each C71 fix against current canonical (run EVEN though the target is byte-frozen — per the C108 lesson where a byte-stable target still yielded a net-new). §B corpus-delta scan (diff sibling movement since 2026-06-18; re-verify cited anchors live; re-confirm/re-route standing carries with the C90/C98 snapshot-presence guard). Audit-only — no spec edits.

---

## Headline

**0 net-new.** The cluster is byte-frozen since the C71 remediation (`3f1d6fad`, 2026-06-18 — 10 days). All **6/6** C71 autonomous fixes (B-A1..B-A6) held token-by-token AND passed the claim-vs-canonical re-read against current canonical. No regression. Unlike C108 (which broke an 8-wrap 0-net-new streak with a LOW finding), the registries claim-vs-canonical re-read came back **clean** — reported honestly, not manufactured. The cluster's remediation (a hypothetical C111) remains **gated on the operator** answering the flagship **B-D1 SSOT inversion** design-Q, which is still unanswered (no trace in SESSION_FOCUS or forum). This makes the registries cluster the first since security to surface a structural operator-gate as the sole blocker to further progress.

---

## §A — C71 fix verification (B-A1..B-A6) + claim-vs-canonical re-read

Canonical sources re-read this turn: `core-protocol.md` §1 suite table (frozen since C33, 2026-06-05), `errors.md` (frozen since C67, 2026-06-17), `web4-handshake.md` §5 (Capability & Suite Negotiation).

| C71 fix | What it applied | Held token-by-token? | Claim-vs-canonical (C56) |
|---------|-----------------|----------------------|--------------------------|
| **B-A1** | `initial-registries.md` L7: `W4-IOT-1 : X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF (CBOR)` | ✅ | ✅ **matches** core-protocol §1 L20 (`W4-IOT-1 (MAY) \| X25519 \| Ed25519 \| AES-CCM \| SHA-256 \| HKDF \| CBOR`). The C71 remediation correctly merged B-A6's HKDF into the IOT-1 row too (the C70 audit text omitted it; canonical carries it). |
| **B-A2** | three `[Web4 Standard Section X.Y]` placeholders → real targets: cipher-suites→`core-protocol.md` §1; error-codes→`errors.md`; extensions→`web4-handshake.md` §5 | ✅ | ✅ all 3 targets **live files**. §5 = "Capability & Suite Negotiation"; §5.1 ClientHello L89 carries `"ext": ["w4_sig_cose@1", … "w4_ext_93f07f2a@0"]` — extensions ARE offered there, so the corrected anchor is semantically right (the C70 audit's "§10" was Error Handling — the C71 correction to §5 was sound). |
| **B-A3** | README contact `iana-web4@example.org` → `TBD-before-IANA-submission` | ✅ (README L32) | ✅ pre-IANA honesty marker, consistent with whole-tree draft status |
| **B-A4** | README registration prose → per-registry RFC 8126 policy table (cipher/error=Expert Review, extensions=Specification Required, initial=N/A) | ✅ (README L20-25) | ✅ each registry FILE's own "Registration Procedure" line **matches** the README table (cipher-suites L8 / error-codes L8 = Expert Review; extensions L8 = Specification Required) — internally consistent |
| **B-A5** | uniform `Status / Last-Updated` on all 5 files; numeric files marked "Draft / experimental — pre-IANA template" | ✅ (all 5 carry the line) | ✅ neutral on B-D1's canonical-form decision, as intended |
| **B-A6** | add `HKDF` KDF token to BASE-1/FIPS-1 | ✅ (initial-registries L5-6) | ✅ **matches** core-protocol §1 (BASE-1 KDF=HKDF L18, FIPS-1 KDF=HKDF L19) |

**Regression sweep**: 0. All B-A2 reference targets resolve to live files; `errors.md` still carries 37 `W4_ERR_*` occurrences (error-codes.md's ref target intact); handshake §5 anchor live.

**Suite-mapping cross-check** (initial-registries Suite IDs vs core-protocol §1): BASE-1 ✅ exact, IOT-1 ✅ exact. FIPS-1: KEM = `P-256 ECDH` (initial, with space) vs `P-256ECDH` (core-protocol, no space) vs `ECDH-P256` (security-framework §1.2 canonical) — **the only remaining drift, = the known B-C4/B-7 carry, operator-gated** (see §B).

---

## §B — Corpus-delta + standing-carry re-route (0 net-new)

No sibling movement since 2026-06-18 introduced new registry drift. `core-protocol.md` (C33, 2026-06-05) and `errors.md` (C67, 2026-06-17) both PREDATE the registry snapshot, so no inbound drift. `security-framework.md` C108/C109 (2026-06-28) edited §3.1 (citation split) — no suite-table change, no registries impact. All standing carries re-confirmed OPEN, unchanged owners:

### Operator design-Qs (gate a future C111 registries remediation)
- **B-D1 (FLAGSHIP) — Registry SSOT inversion** [MED]: directory still ships two parallel, mutually-disjoint registry systems; README still links the three numeric orphan files (0 corpus consumers) as "the registries" and demotes `initial-registries.md` (the corpus-cited form) to "Initial registry values." **Still UNANSWERED** (no trace in SESSION_FOCUS / forum). This single decision gates B-D2, B-A5-wording, and the EXT disposition. **A C111 registries remediation is a no-op until the operator answers B-D1.**
- **B-D2 — `error-codes.md` numeric class scheme self-contradictory** [LOW]: empty Security/Trust/Entity classes; INSUFFICIENT_TRUST/MRH_VIOLATION mis-binned in Protocol range; `0x0000`=SUCCESS here but "reserved" elsewhere. Subordinate to B-D1; moot if file retired. Unchanged.
- **B-D3 — `extensions.md` forbids what it registers** [MED]: L35 "Extensions MUST NOT change core protocol semantics" still co-exists with registered core primitives `MRH_RDF` (0x0001) + `T3_V3` (0x0005). Unchanged.

### Cross-track (sibling-owned — do NOT apply here)
- **B-C1 — `W4_ERR_WITNESS_REQUIRED` (→errors §2.3) + `W4_ERR_PROTO_FORMAT` (→errors §2.6) absent from errors.md** [MED]: **STILL OPEN**. Both are live MUST/do-emit codes (`web4-metering.md:109`, `web4-handshake.md:160` MUST-abort). errors.md byte-frozen since C67 (pre-dates C70); the errors.md 2nd-delta (C106, #394, 2026-06-27) did NOT apply them. **Snapshot-presence guard applied**: both codes ARE present in `initial-registries.md` and were present at the C70 audit-time blob (`88cb2c5d`) → NOT net-new in registries; the open defect is their absence from the declared SSOT (`errors.md`), owner = errors.md. *Sharpening*: `initial-registries.md` is now demonstrably MORE complete than the SSOT file on these two codes — reinforces B-D1's framing that it is the more authentic registry-of-record.
- **B-C4 ≡ C68 B-7 — `W4-FIPS-1` KEM spelling drift across ≥5 sites** [MED]: `P-256 ECDH` (initial-registries) / `P-256ECDH` (core-protocol §1) / `ECDH-P256` (security-framework §1.2, recommended canonical) / others. **STILL OPEN, operator-gated**; C108 re-confirmed it WIDENED to 5 sites with `ECDH-P256` as the canonical short token. Folds into the security-framework suite-registry carry (C68 C-M1).
- **B-C2** (canonicalize `W4_ERR_RATE_LIMIT`→`W4_ERR_AUTHZ_RATE`), **B-C3** (3 competing "format" error names), **B-C5** (harmonize suite-table columns), **B-C6** (register live `w4_sig_cose@1`/`w4_sig_jose@1`), **B-C7** (extensions cite non-existent specs) — all unchanged, sibling/operator-gated, fold into the standing errors-layer + security-framework bundles.

---

## Routing summary

| Bucket | Disposition this turn |
|--------|----------------------|
| §A C71 fixes (B-A1..B-A6) | 6/6 HELD + claim-vs-canonical CLEAN; 0 regression. No action. |
| Operator design-Qs (B-D1/B-D2/B-D3) | Re-confirmed OPEN. **B-D1 gates C111 registries remediation** — surface in the standing operator decision memo. Do NOT self-apply. |
| Cross-track (B-C1..B-C7) | Re-confirmed OPEN, sibling-owned. B-C1 most actionable (errors.md owns); B-C4≡B-7 widened to 5 sites (security owns). Route inbound, do NOT apply here. |
| Net new | **0** (honest clean result — not manufactured under C108 precedent). |

**Pattern note (for the next pass)**: registries is now the rotation's standout *operator-gated* cluster — every autonomous fix is applied and held, but ALL three remaining buckets (the SSOT inversion + the design-Qs + the cross-track normalizations) require either an operator decision (B-D1) or a sibling's own delta cycle. The cluster cannot advance further autonomously. Next rotation step after this audit = **handshake cluster 2nd-delta** (last C72/C73). A C111 registries remediation should only be scheduled once the operator answers B-D1.
