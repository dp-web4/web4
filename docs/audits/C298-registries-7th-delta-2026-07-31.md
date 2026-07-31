# C298 — Registries `initial-registries.md` 7th-Delta Re-Audit

**Date**: 2026-07-31
**Auditor**: Legion autonomous web4 track (slot `060032`)
**Target**: `web4-standard/registries/initial-registries.md`
**Lineage**: C70 (cluster first-pass, #353) → C71 (remediation, #354) → C110 (2nd) → C142 (3rd) → C182 (4th) → C220 (5th) → C258 (6th) → **C298** (7th)
**Method**: §A prior-finding verification (byte-frozen hold on C71 fixes B-A1/B-A5/B-A6 + C56 claim-vs-canonical re-read of all 3 Suite-ID rows vs `core-protocol.md` §1 at live HEAD). §B corpus-delta since the C258 snapshot (2026-07-23) with snapshot-presence guard. **§B′ mirror set RE-DERIVED, not re-read** (method carry v8, born C296) — obligation (i) the four in-directory siblings the lineage dropped, obligation (ii) a bounded token-grep enumeration of what else *defines or mints* registry taxonomy. Audit-only — no spec edits (B-D1 flagship gates all registries remediation and is UNANSWERED).

**Policy-review conditions in force this pass** (7 binding conditions, session log `legion-web4-20260731-060032`): §B′ ordered and bounded; **anti-manufacture** — no finding against the frozen target's bytes without a canonical change in the interval or a dated inbound obligation; scope-contraction findings laid at the *scope*, not the spec; leads verified independently, never inherited; guarded carries stay closed; instrument discipline binding; 1 file.

---

## Headline

**The target is clean for the sixth consecutive delta — and the pass is not clean.** 4 net-new (**1 MED, 3 LOW**), **none of them inside the byte-frozen target**, all of them from the re-derived §B′ set. A fifth candidate — the one that read best — was **withdrawn by this pass's own post-write verification**; see *Refuted*.

`initial-registries.md` is byte-frozen since C71 `3f1d6fad` (2026-06-18 — **43 days**; blob `00a37a88`, 59 lines, **identical to the blob C258 verified**). §A held by construction and passed claim-vs-canonical against a canonical that itself did not move (`core-protocol.md` `3084e4d2`, 2026-06-05). §B is EMPTY: 3 `web4-standard/` commits in the interval, **0** new registry values.

**The finding is that the §B′ gate has been pointed at the wrong tree for six passes.** Three consecutive deltas (C182/C220/C258) published *"the registry taxonomy has no code-level mirror; no code-side validation; no drift surface"* — a negative measured **only over `web4-core/`**. `grep -c "implementation/sdk"` over all six lineage documents returns **0, 0, 0, 0, 0, 0**. The mirror was there the whole time: `web4-standard/implementation/sdk/web4/errors.py` (`39fb4119`, 2026-05-17, 493 lines) is a 30-code `ErrorCode` enum whose own docstring reads *"Canonical implementation per web4-standard/core-spec/errors.md … Defines 30 error codes across 7 categories."* Eleven SDK/test-vector artifacts carry registry tokens; the lineage read none of them.

Running the divergence analysis the gate was designed to produce and never reached: **overlap 24, SDK-only 6, registry-only 7.** Two of the registry-only codes are `W4_ERR_PROTO_FORMAT` and `W4_ERR_WITNESS_REQUIRED` — **exactly carry B-C1's two codes**, one of which the standard makes a **MUST** (`web4-handshake.md:164`). Two of the SDK-only codes exist in **no `.md` in `web4-standard/` at all**. Four more uppercase a namespace `errors.md` §1 explicitly documents as lowercase, with a test asserting on it.

**The pass's two best decisions were both refutations, and one of them killed its own second-strongest finding.** (a) The obvious flagship — *"18 `W4_ERR_*` codes are minted outside the registry"* — was **partially refuted by the SSOT itself**: `errors.md:9` (`aaa2bd86`, 2026-06-04) *sanctions* subsystem extension and names SAL §9, ACP §10, metering §6. Twelve of the eighteen are sanctioned, not rogue; what survived routes as a **reach-escalation on B-D1 claiming no new severity** (N2). (b) A drafted MED on the six ownerless `W4_ERR_AGY_*` codes was **WITHDRAWN** when the mandatory post-write instrument re-run contradicted its own zero-coverage cell: C106 and C138 had already adjudicated it twice, **on the merits**, and dismissed it correctly. It is recorded under *Refuted* with the refutation published in full.

---

## §A — C71 fix verification + claim-vs-canonical (C56) — SHORT, per policy condition

`3f1d6fad..HEAD` touches this file **0** times → blob identity `00a37a88`, C71 fixes hold **by construction**. Canonical `core-protocol.md` frozen at `3084e4d2` (2026-06-05), **did not move in the interval** → per anti-manufacture condition 2, no finding is laid against the target's bytes this pass.

| Row | `initial-registries.md` | `core-protocol.md` §1 (live HEAD) | Verdict |
|-----|------------------------|-----------------------------------|---------|
| **W4-BASE-1** | `X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 / HKDF (COSE)` (:5) | `X25519\|Ed25519\|ChaCha20-Poly1305\|SHA-256\|HKDF\|COSE` (:18) | ✅ **exact** |
| **W4-FIPS-1** | `P-256 ECDH / ECDSA-P256 / AES-128-GCM / SHA-256 / HKDF (JOSE)` (:6) | `P-256ECDH\|ECDSA-P256\|AES-128-GCM\|SHA-256\|HKDF\|JOSE` (:19) | ⚠️ KEM spelling only = **known B-C4 ≡ C68 B-7 carry, operator-gated. NOT re-opened** (C258 + C296 guards) |
| **W4-IOT-1** | `X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF (CBOR)` (:7) | `X25519\|Ed25519\|AES-CCM\|SHA-256\|HKDF\|CBOR` (:20) | ✅ **exact** (handshake:24 `COSE` remains the sole outlier = DELTA-1, handshake-owned) |

B-A1 / B-A5 / B-A6 held. Regression sweep: 0 (no HTML-entity artifacts; extension block `:10-12` intact; error catalog `:14-59` = 31 codes, unchanged).

**B-A6 is NOT re-opened** — C296 exonerated it and the exoneration is re-confirmed here: the token `HKDF` is exact against the canonical B-A6 cited. See N4 for what the exoneration leaves standing.

---

## §B — Corpus-delta since the C258 snapshot (2026-07-23) — EMPTY, and the instrument's blind spot published

**Interval**: 69 commits repo-wide, **3** touching `web4-standard/`:

| Commit | Date | Touches a registries-cited sibling? |
|--------|------|--------------------------------------|
| `4665a430` proposal: Dictionary becomes a context-mandatory society role (#579) | 2026-07-28 | No (`proposals/`) |
| `954ee391` proposal: resilience to incomplete/malformed/contradicting information (#580) | 2026-07-28 | No (`proposals/`) |
| `01f410db` fix(ontology): `web4:Tensor` superclass + `web4:observationCount` (#581) | 2026-07-30 | No (`ontology/`) |

**Cited siblings, all frozen and all predating the snapshot**: `core-spec/core-protocol.md` `3084e4d2` (2026-06-05) · `core-spec/errors.md` `6189432d` (2026-06-17) · `protocols/web4-handshake.md` `57caa2e1` (2026-06-29) · `core-spec/security-framework.md` `eedd36fc` (2026-06-28) · all four registry siblings `3f1d6fad` (2026-06-18).

**New registry values in the interval** —
`git log --since=2026-07-23 -p -- web4-standard/ | grep '^+' | grep -oE 'W4_ERR_[A-Z0-9_]+|w4_ext_[a-z0-9_]+@[0-9]+|W4-[A-Z]+-[0-9]+' | sort -u` → **empty** (re-run at HEAD `47b270c3`).

**Verdict: §B EMPTY for the registry surface — and that verdict has been true and uninformative for five passes.** Published here because it is the mechanism behind N1/N2: this grep's denominator is the **interval**, never the **corpus**. It is structurally incapable of seeing a divergence that predates the lineage. The registry's completeness against the corpus was measured exactly **once** — at C70 — and only in one direction (registry → `errors.md`, which produced B-C1). The reverse direction was never run in six passes. It costs two greps and a `comm`; §B′ runs it below.

---

## §B′ — Mirror set RE-DERIVED (method carry v8)

### Obligation (i) — the four in-directory siblings the lineage dropped [MANDATORY, FIRST]

C70's target line reads: *"`web4-standard/registries/` — `README.md`, `cipher-suites.md`, `error-codes.md`, `extensions.md`, `initial-registries.md`"* — a **five-file cluster**. Filename-mention counts across the lineage's own documents. Instrument published verbatim: `grep -o '<token>' <doc> | wc -l` per doc, tokens `initial-registries` / `cipher-suites` / `error-codes` / `extensions\.md` / `README`, re-run at HEAD `47b270c3` **after this section was drafted**:

| Pass | `initial-registries` | `cipher-suites` | `error-codes` | `extensions.md` | `README` |
|------|---------------------|-----------------|---------------|-----------------|----------|
| C70 (first) | 22 | 9 | 13 | 6 | 11 |
| C110 | 8 | 3 | 5 | 2 | 7 |
| C142 | 5 | **0** | 1 | 1 | 1 |
| C182 | 5 | 1 | 2 | **0** | 2 |
| C220 | 7 | 1 | 1 | **0** | 2 |
| C258 | 6 | 1 | 1 | **0** | 2 |
| **C298** | — | **read** | **read** | **read** | **read** |

**Correction on the record, and it matters for how the contraction is characterised.** A first draft of this table published `0` across the C142-C258 sibling columns; the post-write re-run above falsifies that. The four siblings do **not** drop to zero — they persist at 1-2 mentions per pass. Reading the surviving mentions shows what they are: a single row in the §B sibling-movement table (*"registries siblings (README/error-codes/cipher-suites/extensions) | `3f1d6fad` | No"*) plus, from C182 on, the `forum/nova` parallel-copy row. **They are freeze-checks, not reads.** So the honest statement is not *"four files vanished from the tracked set"* but the narrower and still-sufficient one: **from C142 onward the four siblings were tracked only as commit-hash liveness rows and their contents were never opened again** — 9/13/6/11 content mentions at C70 collapsing to 1/1/0/2 by C258. All five files are frozen at the same commit (`3f1d6fad`), so this is pure instrument, not corpus movement.

The distinction is not cosmetic: a freeze-check row is exactly the artifact that makes a contraction invisible, because it *looks* like coverage in the audit doc while asserting only that the blob hash did not move.

**All four dropped siblings read this pass.** Per policy condition 3, each candidate divergence was checked against C70's prose before any net-new claim:

| Observed in a dropped sibling | Already at C70? | Disposition |
|-------------------------------|-----------------|-------------|
| Numeric `0x000N` namespaces disjoint from the named/string forms, in all three registry files | **Yes** — B-D1 flagship (headline table, L15-21) | Snapshot-guard: **not net-new**. Reach measured in N2. |
| `cipher-suites.md` DH=X25519 on all 3 rows, no P-256 row, `0x0002 AES-256-GCM` has no counterpart suite, W4-IOT-1's AES-CCM has no codepoint | **Yes** — A-3 ("a disjoint set") | Not net-new. B-D1-subordinate. |
| `error-codes.md` class table reserves Security/Trust/Entity ranges, all empty; every code sits in the Protocol range | **Yes** — B-D2 [LOW] | Not net-new. |
| `extensions.md:35` "Extensions MUST NOT change core protocol semantics" vs entries `MRH_RDF`/`T3_V3` | **Yes** — B-D3 [MED] | Not net-new. |
| `extensions.md` `[Web4-MCP]`/`[Web4-Blockchain]`/`[Web4-PQC]` cite non-existent specs | **Yes** — B-C7 [LOW] | Not net-new. |
| `cipher-suites.md:17-19` KDF column = `HKDF-SHA256`/`HKDF-SHA384`/`HKDF-SHA256` vs target `:5-7` bare `HKDF` | **Partially** — B-A6 noted the *column*, not the *token* | → **N4** (evidence to C296-N2; no new charge) |
| `README.md:20-25` per-registry RFC 8126 policy table assigning `initial-registries.md` "N/A — not a registration target" | **No** — the table did not exist pre-C71 | → **N5** (remediation-introduced) |
| Corpus `W4_ERR_*` ⊅ registry: 18 codes | **No** — C70 measured only registry → `errors.md` | → **N2** (reach-escalation on B-D1) |

**Obligation (i) verdict: the contraction was real, and it cost the lineage N4 + N5.** Four of the eight rows above were already settled by C70 — which is the point of running the guard rather than reporting eight findings.

### Obligation (ii) — bounded outward enumeration: what else *defines or mints* registry taxonomy

Bounded token-grep with published thresholds (files with ≥2 distinct suite IDs, ≥2 distinct `w4_ext_*@N`, or ≥3 distinct `W4_ERR_[A-Z0-9_]+`), whole repo, excluding `/target/`, `node_modules`, and `docs/audits/` (audit docs quote taxonomy; they do not define it). Admission argued fresh per candidate — **nothing imported from C296**.

| Candidate | Measured | M1 (subject matter) | Ruling |
|-----------|----------|---------------------|--------|
| **`web4-standard/implementation/sdk/web4/errors.py`** | **30** distinct `W4_ERR_*`; `ErrorCode` enum; docstring self-declares canonicity vs `errors.md` | **PASS** — defines the error-code taxonomy as a typed set | **ADMITTED → GENUINE MIRROR. Divergence analysis run → N1.** |
| `web4-standard/implementation/sdk/web4/acp.py` | 8 ACP codes | PASS | **ADMITTED** — second face of the ACP extension (feeds N2) |
| `web4-standard/test-vectors/errors/error-taxonomy.json` | 5 codes (`4c076459`, 2026-03-17) | PASS — conformance fixture over the taxonomy | **ADMITTED** (concordant subset; 5/5 ∈ registry) |
| `web4-standard/implementation/sdk/web4/security.py`, `test_security.py`, `test_protocol.py`, `test_acp.py`, `test_errors.py`, `test_package_api.py`, `CHANGELOG.md`, `test-vectors/{protocol,security}/*.json` | 2 suite IDs each / assorted | PASS (suite side already counted by the security lineage at C180/C218/C256/C296) | **ADMITTED as set members**; suite-side divergence is C296's, not re-litigated |
| `web4-core/` (Rust `src/` + `python/`) | `W4_ERR_`=**0**, suite IDs=**0**, `w4_ext_`=**0** | **FAIL** — names no registry taxonomy | **EXCLUDED.** C182/C220/C258's negative was *correct for this tree* — it was simply not the tree the SDK is in. |
| `hub/` (excl. `target/`) | 0 / 0 / 0 | **FAIL** | **EXCLUDED** on subject matter (independent of C294's and C296's hub rulings) |
| `web4-policy/`, `web4-trust-core/` | 0 / 0 / 0 | **FAIL** | **EXCLUDED** |
| `ledgers/` | 1 hit: `act-chain/bridge/genesis_crypto.py:5` *"partial W4-BASE-1 compliance"* — a docstring | FAIL (cites one value in prose; defines nothing) | **EXCLUDED**, evidence-only |
| `web4-standard/protocols/web4-handshake.md` | 3 suite IDs, **5** `w4_ext_*@N` (the most of any file) | PASS | **ADMITTED** — already the DELTA-1/B-C6 owner; no new charge |
| `forum/nova/...` parallel copies | 2-3 suite IDs, 11 codes | n/a | **EXCLUDED** — frozen parallel spec (`1bac7d7f`, 2025-09-11); sync-vs-supersede lifecycle, not a line-diff → [[feedback_frozen_parallel_spec]] |
| `archive/reference-implementations/` | 26 codes in `web4_error_handler.py`, 8 in `agy_delegation.py`, … | n/a | **EXCLUDED** — archived sprawl, explicitly de-scoped by the primer |

**The re-derived set is 11 in-standard SDK/test-vector artifacts + 3 spec siblings, against a tracked set of 5 spec files and `web4-core/`.** The lineage's inherited set was not merely contracted (obligation i) — it was **pointed at the wrong tree** (obligation ii).

---

## Net-new findings

### C298-N1 (MED) — the genuine-mirror gate was mis-scoped for six passes; the mirror exists and diverges in both directions

**Routing: operator + SDK track. NOT auditor-applicable** (touches shipped code; the registry side is B-D1-gated).

**The instrument failure.** C182-N1, C220-N1 and C258-N1 each published, as an INFO finding, that *"the registry taxonomy has no code-level mirror … no code-side validation … no drift surface, because the crate never names them."* Every one of those greps was scoped to `web4-core`. Measured this pass, re-run at HEAD `47b270c3`:

```
grep -c "implementation/sdk" docs/audits/C{70,110,142,182,220,258}-*.md
  → 0  0  0  0  0  0
```

**The mirror.** `web4-standard/implementation/sdk/web4/errors.py` — `39fb4119` (2026-05-17), 493 lines. Module docstring: *"Canonical implementation per web4-standard/core-spec/errors.md. … Defines 30 error codes across 7 categories: Binding, Pairing, Witness, Authorization, Cryptographic, Protocol, Cross-Society (mcp-protocol.md §7.6). … Validated against: web4-standard/test-vectors/errors/."* It is a typed `ErrorCode`/`ErrorCategory` enum pair with per-code `ErrorMeta`. This is the strongest form of genuine mirror the C178/C180 gate defines, and it predates the lineage's first "no mirror exists" publication (C182, 2026-07-12) by **eight weeks**.

**The divergence** (`grep -ohE 'W4_ERR_[A-Z0-9_]+' … | sort -u` + `comm`, both sides re-run post-drafting): registry **31** codes · SDK **30** codes · **overlap 24** · SDK-only **6** · registry-only **7**.

| # | Divergence | Evidence | Why it matters |
|---|-----------|----------|----------------|
| **1** | `W4_ERR_PROTO_FORMAT` — in registry `:52`; **absent from the entire SDK tree** (`grep -rn "PROTO_FORMAT" web4-standard/implementation/sdk/` → 0) | `web4-handshake.md:164`: *"endpoints **MUST** abort with `W4_ERR_PROTO_FORMAT`"* | The shipped SDK cannot emit a code the standard makes a **MUST**. |
| **2** | `W4_ERR_WITNESS_REQUIRED` — in registry `:33`; absent from the SDK | `web4-metering.md:109` lists it | Same shape. |
| **1+2** | **These are exactly carry B-C1's two codes.** B-C1 (open since C70, owner `errors.md`) said the SSOT was missing them. It now has a **second, code-side face**: the mirror that names `errors.md` canonical is missing the same two. | | B-C1 gains a consumer; **reach-escalation, no new severity claimed.** |
| **3** | SDK mints 4 × `W4_ERR_CROSS_SOCIETY_{UNRECOGNIZED_LCT,EXCHANGE_INVALID,LAW_CONFLICT,WITNESS_REQUIRED}`; `errors.md` defines **0** `CROSS_SOCIETY` codes (`grep -c` → 0) | `errors.md:9`: *"MCP cross-society (`mcp-protocol.md` §7.6) currently uses **lowercase `web4_*` identifiers**"*; verified at `mcp-protocol.md:520-521` — `403 web4_cross_society_unrecognized_lct`, `409 web4_cross_society_exchange_invalid` | **Wire-format namespace divergence.** A peer implementing from mcp §7.6 emits `web4_cross_society_unrecognized_lct`; the Web4 SDK matches `W4_ERR_CROSS_SOCIETY_UNRECOGNIZED_LCT`. Non-interoperable — and `test_errors.py:311` asserts on the SDK spelling, locking it in. |
| **4** | `W4_ERR_PROPAGATION_SCOPE_UNSUPPORTED` and `W4_ERR_R7_REPUTATION_INVALID` — **0 hits across all `web4-standard/**/*.md`** | re-run at HEAD | Two codes minted by the SDK with **no specification anywhere**. |
| **5** | The 5 Metering codes (`GRANT_EXPIRED`, `RATE_LIMIT`, `SCOPE_DENIED`, `BAD_SEQUENCE`, `BAD_TIMESTAMP`) are in the registry `:55-59`, absent from the SDK | | The SDK implements `errors.md` §2 + mcp §7.6 and **no** other sanctioned extender (see N2). |

**Net-new argued both directions.** *Against:* the mirror has existed since 2026-05-17 — it predates C70 by a month, so as a **fact** it is not new, and per policy condition 3 it routes as a lineage/instrument regression rather than as fresh spec content. *For:* as a **finding** it is unambiguously net-new — three passes published the exact negation of it as a numbered INFO finding, and the divergence analysis it gates has never been run. **Disposition: net-new as a finding; the instrument regression is the mechanism, and C258-N1's text is hereby superseded — it is FALSE as written.**

### C298-N2 (LOW — reach-escalation on B-D1, **no new severity claimed**) — the declared registration mechanism can express none of the vocabulary the standard uses

**The strong form was refuted.** The natural flagship — *"18 `W4_ERR_*` codes are minted outside the registry"* — does not survive contact with the SSOT. `errors.md:9` (entered `aaa2bd86`, 2026-06-04, a C30 remediation) reads: *"Subsystem specifications **extend** this taxonomy with additional domain-specific codes and SHOULD reuse the codes defined here … Society/Authority Law (`web4-society-authority-law.md` §9), ACP (`acp-framework.md` §10), and metering (`web4-metering.md` §6) add codes following the `W4_ERR_*` convention."* **Twelve of the eighteen are sanctioned** (8 ACP + 3 SAL + `W4_ERR_FORMAT`/metering). The charge of "rogue minting" is **withdrawn**.

What survives, measured (`web4-standard/**/*.md`, regex `W4_ERR_[A-Z0-9_]+`, fragments dropped, re-run at HEAD):

- Corpus **49** distinct codes · target registry **31** · set difference **18**.
- `registries/README.md:20-25` declares **`error-codes.md`** the Expert-Review (RFC 8126) registration target for error codes. `error-codes.md` contains **11 numeric `0x00NN` codes and zero `W4_ERR_*`**. The declared registration gate cannot express **any** of the 49 codes the standard actually uses — nor any of the 30 the SDK ships.
- The target's own catalog carries **metering's** extension codes (`:55-59`) but **none** of SAL's or ACP's — it is a 2025-09-11 seed that was never reconciled to the 2026-06-04 extender model.

**This is B-D1's cost, measured — not a new defect.** B-D1 (flagship, UNANSWERED since C70) already holds that the directory ships two parallel systems and the README points at the orphan half. C298 supplies the magnitude: 49 codes in use, 0 registrable through the declared procedure. Per [[feedback_carry_gains_reach_not_truth]] this routes as reach, arguing severity both ways: *up*, because a normative RFC 8126 policy table now directs registrants into a dead namespace; *down*, because every artifact is Draft/pre-IANA and reversible, and B-D1 remains open with the file untouched. **Held at LOW.**

Note the overlaps, so the operator memo does not double-count: `W4_ERR_FORMAT` is carry **B-C3**; `W4_ERR_LEDGER_WRITE` (SAL §9 `:331`) vs `W4_ERR_ACP_LEDGER_WRITE` (ACP §10 `:537`) is standing carry **B-8**, and this is its registry-side WHY — **the collision was possible because no registration gate exists that either subsystem could have passed.** That is the same root C294-N1 named from the `errors.md` side.

### REFUTED — the ownerless `W4_ERR_AGY_*` family (drafted as a MED, withdrawn before commit)

**Recorded so the next pass does not re-discover it.** This was drafted as the pass's second MED and is **withdrawn**. It is published rather than deleted because the way it died is the useful part.

**The drafted claim.** `W4_ERR_AGY_{DELEGATION,EXPIRED,REPLAY,REVOKED,SCOPE,WITNESS}` appear in exactly one file under `web4-standard/` — `AGY_INTEGRATION_SUMMARY.md:150-155` (`7e1e2d37`, 2025-09-15, never touched, no `Status:` line, at the standard's root rather than `core-spec/`). There is no AGY specification (`ls web4-standard/core-spec/ | grep -ci 'agy\|agenc'` → **0**). `errors.md:9` names SAL, ACP, metering and mcp as sanctioned extenders and **omits AGY**. Yet AGY is normative elsewhere: `entity-types.md` §4.6 *"Agent Role (AGY)"* / §4.7 *"Client Role (AGY)"* / *"Agency Grant Structure (AGY)"*, `society-roles.md:248,254`, `acp-framework.md:5` and §4 *"ACP-AGY Integration"*. The draft asserted **zero C-series coverage**.

**The refutation — and it came from this pass's own mandatory post-write re-run.** The zero-coverage cell was **false**. `grep -rl "W4_ERR_AGY\|AGY_INTEGRATION_SUMMARY" docs/audits/` returns **4** files (one of which is this document). The other three had already settled it:

- `acp-framework-internal-consistency-2026-05-28.md:238-249` runs the same grep, reaches the same set, and routes the whole `W4_ERR_ACP_*` / `W4_ERR_AGY_*` question as a **DESIGN-Q in the "canonical error taxonomy completion" cluster** with C16-H1 and C17-M4.
- **C106 `:91` (2026-06-27) and C138 `:89` (2026-07-05) each adjudicated it explicitly and dismissed it twice — not on the snapshot guard alone but on the merits**: *"`errors.md` §1 lists **normative framework homes** (`acp-framework.md` §10, not `ACP_INTEGRATION_SUMMARY.md`); AGY has only a summary doc … so AGY's summary-only codes are correctly omitted, as are the parallel `ACP_INTEGRATION_SUMMARY.md` codes. At most a latent INFO; no route."*

**That reasoning is correct and this pass adopts it.** The extender list enumerates normative homes, not code sites; a summary doc is not a home; the omission is the SSOT behaving properly. The symmetry with `ACP_INTEGRATION_SUMMARY.md` — whose codes are *also* omitted while ACP's normative `acp-framework.md` §10 *is* listed — is decisive and was already published in June.

**What the draft added that C106/C138 did not consider, and its correct disposition.** Neither prior adjudication asked whether AGY *ought* to have a normative home given that `entity-types.md` grants it two roles and a grant structure and `acp-framework.md` declares a dependency on it. That is a real question — but it is **not a registries finding**, it is INFO at most, and it is already inside the DESIGN-Q the May acp audit routed. **Folded there; no new route, no new severity, no carry created.**

**Method note.** The draft's zero-coverage cell came from misreading an earlier tool result — a grep that *did* return three files, read as if it had returned none. Nothing in the draft's reasoning caught it; the post-write re-run did. Per [[feedback_publish_the_instrument]] this is the whole point of re-running every count *after* the finding text exists, and per [[feedback_refute_your_best_finding]] the refuter has to be pointed at the flagship, not the leftovers. It cost this pass a MED and the audit is more honest for it.

### C298-N4 (LOW — EVIDENCE appended to C296-N2; no new charge, B-A6 stays closed)

C296-N2 (one fire ago) framed the KDF-token split as *two audit lineages with two canonical tokens and mutual blindness* — security canonizing `HKDF-SHA256`, registries having installed bare `HKDF` at C70-B-A6 and certified "✅ matches" five times.

**Measured from the registries side, the mechanism is different and smaller: the split is intra-directory and intra-commit.**

- `initial-registries.md:5-7` — `HKDF` × 3.
- `cipher-suites.md:17-19` — `HKDF-SHA256` / `HKDF-SHA384` / `HKDF-SHA256`.
- **Both files are frozen in the same commit, `3f1d6fad`, in the same directory.** The rows describing the same algorithm set (ChaCha20-Poly1305 + X25519) carry different KDF tokens: `initial-registries.md:5` `HKDF` vs `cipher-suites.md:19` `HKDF-SHA256`.
- C70's B-A6 text explicitly observed that *"`core-protocol.md` §1 **and `cipher-suites.md`** both carry a KDF column"* — it saw the column and sourced the token from `core-protocol.md`. So the security lineage's token was **already inside the registries directory** when the registries lineage installed the other one.

**B-A6 is not re-opened**: the fix is exact against the canonical it cites, and C296's exoneration of `initial-registries.md` stands and is re-confirmed. What this corrects is C296-N2's *framing* — not "two lineages, mutual blindness" but "one directory, one commit, two spellings," which is B-D1-subordinate and moot if the numeric files are retired. Routed as evidence onto C296-N2; no new charge.

### C298-N5 (LOW) — C71's B-A4 fix shipped a normative table that pre-answers the DESIGN-Q the same audit held open

**Routing: operator, with B-D1.** Remediation-introduced (the C36 class).

- **Pre-C71** (`git show 3f1d6fad^:web4-standard/registries/README.md`), L14-20 was prose: *"### Expert Review / New registrations require expert review as per RFC 8126. / ### Specification Required / Registrations must reference a stable specification."* — **no per-file assignment.**
- **Post-C71**, L20-25 is a normative table: cipher-suites = Expert Review, error-codes = Expert Review, extensions = Specification Required, **`initial-registries.md` = "N/A — initial seed values, not a registration target."**
- C70 shipped that wording in the **AUTONOMOUS** bucket (B-A4) on the same day it shipped **B-D1** in the DESIGN-Q bucket — B-D1 being precisely the question of *which half of the directory is canonical*, with C70's own recommendation (Option A) being to declare the string/named form canonical, i.e. the opposite of what B-A4 encoded. C70 flagged the coupling for B-A5 (*"coordinate wording with B-D1"*) and not for B-A4.

Consequence: B-D1's remediation must now **revert a shipped normative table** rather than fill a blank, and five subsequent passes certified the C71 fixes as "held by construction" without noticing that one of them answers the open flagship. Severity argued both ways: *up* — a registrant following `README.md:20-25` registers into a namespace with **0** corpus consumers; *down* — Draft, pre-IANA, doc-only, trivially reversible, and B-D1 is still formally open. **Held at LOW**, but it belongs in the B-D1 memo because it changes what answering B-D1 costs.

---

## Standing carries — re-verified at live HEAD

- **B-D1 (FLAGSHIP, MED, operator)** — registry SSOT inversion. Still **UNANSWERED** (no trace in `SESSION_FOCUS.md` at `62ae9ba0d` or the forum). Gates all registries remediation → this pass stays audit-only. **Gains reach from N2 and cost from N5.**
- **B-C1 (MED, `errors.md`-owned)** — `W4_ERR_WITNESS_REQUIRED` + `W4_ERR_PROTO_FORMAT` absent from the declared SSOT. **Gains a second, code-side face (N1 rows 1-2): both are also absent from the shipped SDK, and one is a handshake MUST.**
- **B-C4 ≡ C68 B-7 (MED, operator)** — W4-FIPS-1 KEM spelling. Unchanged; **not re-opened** per the C258 and C296 guards. C296's corrected reach (6 occurrences / 5 files / 4 spellings) inherited verbatim; **not re-measured here, because re-running it scoped to its own enumeration is the C296-N3 failure.**
- **B-8 (MED, operator)** — `W4_ERR_LEDGER_WRITE` / `W4_ERR_ACP_LEDGER_WRITE` collision, held since C30. **Registry-side WHY supplied by N2.**
- **B-C2, B-C3, B-C5, B-C6, B-C7, B-D2, B-D3** — unchanged, all B-D1-subordinate or sibling-owned. B-D2/B-D3 re-verified against live bytes this pass (obligation i) and confirmed present, unchanged, **not re-opened**.
- **DELTA-1 (MED, handshake-owned)** — `registries:7` = `CBOR` corroborates `core-protocol:20` = `CBOR`; `web4-handshake.md:24` = `COSE` remains the sole outlier. Unchanged.
- **C258-N1 (INFO)** — **SUPERSEDED / FALSE as written** by N1. Do not re-publish "the registry taxonomy has no code-level mirror."

---

## Routing summary

| Bucket | Disposition |
|--------|-------------|
| §A C71 fixes + all 3 Suite-ID rows | Held by construction; BASE-1/IOT-1 **exact**; FIPS-1 = B-C4 only. Canonical did not move → anti-manufacture condition satisfied, **0 findings against the target's bytes**. |
| §B corpus-delta | **EMPTY** (3 `web4-standard/` commits, 0 new registry values) — and the instrument's structural blind spot published rather than presented as assurance. |
| §B′ obligation (i) — 4 dropped siblings | Contraction confirmed, and the **first draft's own numbers corrected on the record** (the siblings persist at 1-2 mentions as freeze-check rows, not 0; content mentions 9/13/6/11 at C70 → 1/1/0/2 at C258). All four read. **4 of 8 candidate divergences killed by the C70 snapshot-presence guard**; 2 survived (N4, N5). |
| §B′ obligation (ii) — outward | 11 in-standard SDK/test-vector artifacts admitted; `web4-core/`, `hub/`, `web4-policy/`, `web4-trust-core/`, `ledgers/` all **M1-FAIL on subject matter**; `forum/nova/` and `archive/` excluded by standing rule. |
| **C298-N1 (MED)** | **Mis-scoped gate + genuine SDK mirror + 6/7 two-way divergence, incl. a MUST the SDK cannot emit and a test-locked wire-namespace split → operator + SDK track. Supersedes C258-N1.** |
| **C298-N2 (LOW)** | Strong form REFUTED by `errors.md:9`; survivor routes as **reach-escalation on B-D1**, no new severity. Supplies B-8's registry-side WHY. |
| **REFUTED (drafted MED)** | **`W4_ERR_AGY_*` ownerless-family charge WITHDRAWN** — C106 `:91` + C138 `:89` adjudicated it twice on the merits and were right; the draft's zero-coverage cell was false and the post-write re-run caught it. Residual question folds into the already-routed "canonical error taxonomy completion" DESIGN-Q. **DO NOT RESURRECT.** |
| **C298-N4 (LOW)** | Evidence onto C296-N2 (mechanism corrected: intra-directory/intra-commit). **B-A6 stays closed.** |
| **C298-N5 (LOW)** | Remediation-introduced: B-A4 pre-answered B-D1 → fold into the B-D1 memo. |
| Net new | **4 — 1 MED, 3 LOW. Zero inside the byte-frozen target. Zero mutation this pass. One drafted MED withdrawn by the pass's own verification.** |
| C299 remediation slot | **Declared NO-OP.** Every finding is operator-, SDK-, or B-D1-gated. Do NOT manufacture a `registries/` edit. |

---

## Method carry — apply at every delta from C300 on

**v9 — a mirror gate is only as good as the tree it is pointed at.** The registries lineage ran a *correct* grep over `web4-core/` six times and published "no mirror exists" three times, while a 30-code typed mirror sat in `web4-standard/implementation/sdk/`. v8 (born C296) says re-derive the mirror set rather than re-read it; v9 adds the sharper half: **when a gate returns NEGATIVE, publish the paths it searched, and check that list against where the artifact class actually lives before publishing the negative as a finding.** A three-times-repeated INFO finding is not corroboration if all three ran the same mis-scoped grep.

Three corollaries, each earned by an error *this pass made and caught*:

1. **Baseline your own regex.** `W4_ERR_[A-Z_]+` silently truncates `W4_ERR_R7_REPUTATION_INVALID` to `W4_ERR_R`. Every count here was re-run with `[A-Z0-9_]+` after the defect surfaced. A character class is a hypothesis about the vocabulary.
2. **A number handed to you by a reviewer is not a measurement.** The policy reviewer supplied the sibling-mention table and this pass declared it "re-derived, not copied" while having copied it. The post-write re-run falsified four columns and changed the *characterisation* of the contraction (freeze-check rows, not absence). If a table is worth citing it is worth re-running, and the claim "re-derived" must be false-if-not-done.
3. **A `docs/audits/` backward grep is only as good as the reading of its output.** The withdrawn AGY MED rested on a grep that returned three files being read as returning none. Before charging *"no prior pass has considered this,"* re-run the backward grep in isolation and read every hit — [[feedback_empty_column_not_missing_cell]] applies to one's own tool results, not just to the corpus.

**Guards for the next registries delta (~C338):**
- **RE-DERIVE the mirror set again** — inheriting even this corrected 14-artifact list reproduces the mechanism.
- Run the **two-directional corpus↔registry set difference** (two greps + `comm`); the `--since` delta grep alone cannot see pre-lineage divergence and must never again be reported as completeness.
- Do NOT re-open: B-A6 (exonerated twice), `initial-registries.md:6` `P-256 ECDH` (≡ B-C4/B-7), B-D2, B-D3, B-C7, or the numeric-orphan fact (≡ B-D1).
- Do NOT re-run B-C4's or B-7's grep scoped to its own enumeration (C296-N3).
- If N1 is remediated, re-check `test_errors.py` — the SDK's cross-society spelling is test-locked.

---

## Review-gate self-audit

This audit creates no surface and drives no consequential act — it is a read-only analysis producing one Markdown record.

```
surface: C298 registries delta-audit doc   act: none (read-only audit; 0 spec/code edits)
S: low/reversible [construct: docs/audits/C298-registries-7th-delta-2026-07-31.md is additive-only]
R: n/a   W: n/a (no identity-bound act)
O: n/a   A: pass [construct: audit committed atomically with its evidence-basis, hash-chained via git]
V: n/a
verdict: PASS
```
