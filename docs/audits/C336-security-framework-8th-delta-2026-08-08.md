# C336 — `security-framework.md` Eighth Delta Re-Audit (9th pass)

**Audit ID**: C336
**Target**: `web4-standard/core-spec/security-framework.md` (97 lines) — crypto suites, key management, authentication/authorization
**Date**: 2026-08-08
**Auditor**: autonomous web4 session (legion, slot `web4-20260808-000000`), v2 protocol, LEAD voice
**Type**: **Eighth delta re-audit** (9th pass overall). Lineage: **C31** (2026-06-04, #268 → remediation #271 `130069d8`) → **C68** → **C69** (remediation #350) → **C108** → **C109** (remediation #396 `eedd36fc`) → **C140** → **C180** → **C218** → **C256** → **C296** → **C336**.
**Prior pass**: `docs/audits/C296-security-framework-7th-delta-2026-07-31.md` (PR #619).

---

## Headline

**The standard's outward-facing IETF submission draft still ships the exact token a HIGH finding removed from the normative spec 65 days ago — and no pass in this lineage has ever opened the directory it lives in.**

`web4-standard/submission/draft-web4-core-00.xml` §"Algorithm Suites" carries a suite table that is a **verbatim copy of the pre-remediation §1.1** — same column set, and `W4-FIPS-1` KEM = **`P-256`**. That is the cell C31's **B-H1 (HIGH)** and **A-L4 (LOW)** jointly corrected to `ECDH-P256` in `130069d8` (2026-06-04). `SUBMISSION_GUIDE.md:9-11` records that file's status as *"Ready for initial submission"* and instructs uploading it to the IETF datatracker. `grep -c -i submission` over all **nine** documents in this lineage = **0**.

Four findings, **2 MEDIUM / 2 LOW**, **none inside the target**, **zero mutation**. The target's own §A/§C are clean for the **6th consecutive delta** (byte-frozen 41 days, blob `2880e643` — the same blob C218, C256 and C296 each verified).

- **C336-N1 (MEDIUM, net-new)** — the `submission/` tree holds **three** artifacts that independently define Web4 crypto, all three divergent from §1.1/§1.2, **two of them contradicting each other** on the same field, none ever in this lineage's mirror set.
- **C336-N2 (MEDIUM, net-new by DIRECTION INVERSION)** — carry **B-10**'s prescription is **wrong for 2 of its 8 loci**, was proved so by a sibling lineage on 2026-07-07, was re-recorded *unconsumed* by two later sibling passes, and has never been named in a single security-lineage document. The refutation is available **inside the target itself** (`:35-36`, `:44`).
- **C336-N3 (LOW, process)** — inbound non-reception is **selective and measurable**: 3 inbound routes addressed to this file's owner ledger, **1 received / 2 not**, and the tell is whether the sibling wrote it under *this* ledger's finding ID.
- **C336-N4 (LOW, reach-escalation + a false NEGATIVE)** — C296 dispositioned two published conformance vectors as *"referential only"*; they assert `"suite": "W4-BASE-1"` and publish signing-input hashes. **Already charged by the handshake lineage at C72 (carry HS-X1, still OPEN) — deliberately NOT re-charged here.**

**Negative results published** (v13.7, v24): the **v19 row-set census returns 0 silent drops** — every one of the 6 ids that left the ledger has a recorded closure or fold; and the **`hub/` M3 gate stays DECLINED**, its own trigger re-tested and negative on all three limbs.

---

## Scope, Method, and Published Instruments

### Pre-registered window (v26 — fixed BEFORE any measurement)

| Parameter | Value |
|---|---|
| **Snapshot anchor** | `47b270c3d6fad89b9a789537c504194d3a2093a1` — the C296 audit doc's own commit, 2026-07-31 02:24:57 -0700 |
| **Window** | `47b270c3..HEAD`, **46 commits** |
| **Recursion root** | repo root |
| **Trees** | `web4-standard/`, `web4-core/`, `hub/`, `ledgers/`, `web4-policy/`, `web4-trust-core/`, **both** `docs/audits/` trees (v17) |
| **Filetypes** | unrestricted — explicitly **including** `.xml`, `.txt`, `.json` (see N1: a `--include=*.md` matcher is structurally blind to the flagship) |
| **Excluded** | `.git/`, `**/target/`, `archive/`, `forum/nova/` (standing rule) |

**Counting rule, stated before any count** (v9, v13.8): per-directory numbers below are `git diff --name-only 47b270c3..HEAD -- <dir> | wc -l` — **files changed**, not commits. This is a *different* rule from C296's (which published commit counts); the two are not comparable and are never mixed in one table. `grep -c` is GNU grep = **matching lines**; occurrence counts are stated as such and produced with `grep -o | wc -l`.

| Directory | Files changed in window |
|---|---|
| `hub/` | 25 |
| `docs/` | 21 |
| `web4-standard/` | **4** |
| `whitepaper/` | 1 |
| **`web4-core/`** | **1** — `src/role.rs` |
| `.github/` | 1 |
| `forum/` | 1 |

### Frozen-wrap structure

`git diff eedd36fc HEAD -- web4-standard/core-spec/security-framework.md` → **empty**. Live blob `2880e643f4d7b9899dca38d97dee3358b0f38237`, **byte-identical to the blob C218, C256 and C296 each verified**; last touched `eedd36fc` (2026-06-28, C109 remediation #396) = **41 days**. So §A is verification-by-construction plus a live carry re-check; §B is the corpus-delta **plus all three citation directions**; §B′ is the re-derived mirror set; §C is one fresh internal pass.

### Binding conditions from the policy review (all three executed)

1. **Zero mutation.** No spec, SDK, vector, profile, schema, ontology, submission or implementation file was modified. Nothing below is self-applied.
2. **`web4-core/` re-established BY FILE, not by directory** — §B′.2. C296 stated its `web4-core/` = 0-commits predicate as *"load-bearing and … stated, not assumed"*; **that predicate is now false**, so every verdict it carried is re-derived by inspection.
3. **§B′ bounded by PREDICATE, census not audit, NEGATIVEs named** — §B′.0 and §B′.3.

### The admission predicate, pre-registered before the sweep (v7, binding condition 3)

> An artifact enters the mirror set **iff it independently defines or asserts** (a) a crypto-**suite ID**, (b) a **KEM / KDF / AEAD / signature / hash** algorithm token, (c) a **canonicalization or encoding** rule, or (d) **key-rotation** semantics. **Mentioning** any of these is not sufficient.

**M1** = does the artifact satisfy the predicate. **M2** = does it define its own value or restate one. **M3** = does the artifact's tree have reach over this spec. A member that FAILS is **named as failing** — silent omission is precisely how C296 found the set had contracted from 9 to 7.

---

## §A — Prior-Finding Verification, Regression, Completeness, Carry

### A.1 — 6 C69 fixes + 1 C109 fix: **HELD by byte-freeze**

Blob-identity with C218/C256/C296's verified blob mechanically preserves the token-by-token verification those passes each ran. B-1 / B-2 / B-4 / B-5 / B-6 / B-9-interim (C69) and N1 (C109) all **HELD**. Regression surface nil. C56 completeness re-read: clean by construction.

### A.2 — v19 row-SET census: **NEGATIVE — 0 silent drops** (published because a negative result is a result)

Reconstructed from the lineage's **earliest full ledger** (C31) and diffed forward. Instrument: `grep -oE "\b<id>\b" <doc> | wc -l` over each lineage document.

| ID | C31 | C68 | C108 | C140 | C180 | C218 | C256 | C296 | Disposition |
|---|---|---|---|---|---|---|---|---|---|
| A-L1 | 3 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | **CLOSED** — applied by #271, recorded `C68:32` |
| A-L2 | 3 | 9 | 2 | 1 | 1 | 1 | 1 | 1 | applied; survives as B-8's basis |
| A-L3 | 3 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | **CLOSED** — applied by #271, recorded `C68:8`. **But see N3** |
| A-L4 | 4 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | **CLOSED** — folded into B-H1, recorded `C68:35`. **But see N1** |
| B-H1 | 8 | 7 | 1 | 0 | 0 | 0 | 0 | 2 | CLOSED at #271; **reappears at C296** (as N2's precedent) |
| B-M3 | 4 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | **CLOSED** — applied by #271, recorded `C68:36`/`:54` |
| B-L4 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **FOLDED** → B-L6 (vector ownership) |
| B-L5 | 3 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | **RENUMBERED** → B-10 at C68 (corroborated `C152:22`) |

**Verdict: the C320 disease (v19) is ABSENT in this lineage.** Six ids leave the ledger between C31 and C108; **all six have a recorded closure, fold or renumbering**, five of them naming remediation **#271** explicitly. This lineage's renumbering was documented at the point it happened.

**One sharpening the census cannot see, and it is what N3 is about.** `A-L3` is a *correctly closed* row. Its closure — trimming the abstract's promise of a "comprehensive analysis of security considerations" — generated a cross-track follow-through the very next day (`C32:105`, **B-I1**), which is still live at HEAD and has been named **0 times in 8 subsequent security-lineage documents**. **A row can be correctly and completely closed and still leave live work behind it; row-set census is structurally blind to that, because the row is *supposed* to be gone.**

### A.3 — Carry re-verification, corpus-wide, each instrument published

| Carry | Routing | Status at C336 |
|---|---|---|
| **B-3** §3.2 authz-by-VC vs SAL/R6 | DESIGN-Q | **OPEN — disposition RE-DERIVED, C296's basis is void.** C296 dispositioned this row *"`web4-core/` at 0 commits adds nothing new"*; `web4-core/` moved. Re-derived by inspection (§B′.2): the one file that moved, `role.rs` (`d43964e2`), is a **role-authority** artifact — `has_role_authority(Sovereign\|Administrator)` preflight at `Society::assign_role`, 6 occurrences of that construct in `web4-core`, **0 in `hub/`, `web4-policy/`, the SDK**. So the interval's only movement in the implementation of authorization lands on the **SAL/role** limb of B-3's question, not the VC limb. **Corroboration for the existing carry; no new charge.** |
| **B-7** FIPS-KEM spelling drift | CROSS-TRACK | **OPEN — reach corrected AGAIN, and the correction is a subset of N1.** C296 corrected the published reach to **6 occurrences / 5 files / 4 spellings** scoped `web4-standard/ --include=*.md`. Re-run at HEAD, that matcher **reproduces exactly** (6/5/4 — see below). **But the matcher itself is the defect** — twice over: its filetype filter *and* its alternation. **Corrected reach: 12 occurrences / 11 lines / 10 files / 7 distinct forms** — see the canonical matcher below. Detail and severity in **N1**. |
| **B-8** SDK docstring quotes the deleted A-L2 phrase | CROSS-TRACK | **OPEN, unchanged. Corrected path re-verified at HEAD**: `web4-standard/implementation/sdk/web4/security.py`, last touch `759eaefa` **2026-04-17** — reproduced, not inherited. C296's instrument correction holds. |
| **B-9 / B-M2** rotation mutate-vs-stable-DID | DESIGN-Q | **interim HELD** (§2.3 frozen). |
| **B-10** `cose:ES256` mislabel | CROSS-TRACK | **OPEN — and the prescription is WRONG for 2 of its 8 loci. See N2.** Reach re-measured at HEAD, `grep -rn "cose:ES256" web4-standard/ --include=*.md` = **9 occurrences / 4 files** (`lct-capability-levels.md` 5, `multi-device-lct-binding.md` 2, `LCT-linked-context-token.md` 1, `protocols/web4-lct.md:241` 1) — **reproduces C296 exactly**. `cose:EdDSA` **re-measured in both directions**: `web4-standard/` = **0**; repo-wide-minus-audit-trees = **0**; repo-wide including audit trees = 22, **all 22 inside `docs/audits/`** (i.e. the target token exists only in the audit lineage's own prose). |
| **C-M1 ≡ C70-B-D1** crypto-suite/encoding SSOT | DESIGN-Q | **OPEN — N1 and N4 both land in this bundle.** Now carrying C180-N1, C218-N1, C140-DELTA-1, C296-N1/N2/N4, **C336-N1, C336-N4**. |
| **B-H2 / B-11** W4-IOT-1 + AES-CCM | DESIGN-Q / CROSS-TRACK | **OPEN, unchanged.** C140 DELTA-1 re-confirmed live (`web4-handshake.md:23` Profile=COSE vs `core-protocol.md:20` / `initial-registries.md:8` CBOR). Not re-adjudicated. |
| **B-L6 / B-L7** vector ownership; `device` W4ID method | CROSS-TRACK | **OPEN, unchanged.** `test-vectors/security/security-primitives.json` last touch `3df1a758` (2026-03-18) — frozen. |

**B-7 named-matcher reproduction** (v9 — a number a prior doc hands you is not a measurement until you re-run it):

```
grep -rn "P-256ECDH\|P-256 ECDH\|P-256EC\b\|ECDH-P256" web4-standard/ --include=*.md
→ 6 lines / 5 files:
  profiles/cloud-service-profile.md:19    P-256ECDH
  core-spec/security-framework.md:17      ECDH-P256   (canonical)
  core-spec/security-framework.md:35      ECDH-P256   (canonical)
  protocols/web4-handshake.md:23          P-256EC     (D0 — evidence only)
  core-spec/core-protocol.md:19           P-256ECDH
  registries/initial-registries.md:6      P-256 ECDH
```

**The corrected B-7 matcher, and the pass's own error it caught** (v10 corollary — *a verifier that DISAGREES with your draft is your instrument*). This document's first draft published the corrected reach as **10 occurrences / 9 files / 6 spellings**. The mandatory post-write re-run at a different scope (v17) returned different numbers, because the draft's matcher had inherited B-7's alternation as well as its filetype filter — and that alternation contains `P-256 ECDH` but **not** the reversed `ECDH P-256`, nor the bare XML cell, nor the prose form. Canonical matcher, published so it is reproducible:

```
PAT='ECDH-P256|P-256ECDH|P-256 ECDH|ECDH P-256|P-256EC[^D]|>P-256<|ECDH with P-256'
grep -rnE "$PAT" web4-standard/ | grep -v docs/audits
→ 12 occurrences / 11 lines / 10 files / 7 distinct forms
```

| Form | Sites |
|---|---|
| `ECDH-P256` **(canonical)** | `security-framework.md:17`, `:35`, `sdk/web4/security.py:117`, `test-vectors/security/security-primitives.json:28` |
| `P-256ECDH` | `core-protocol.md:19`, `profiles/cloud-service-profile.md:19` |
| `P-256 ECDH` | `registries/initial-registries.md:6` |
| `P-256EC` | `protocols/web4-handshake.md:23` *(D0 — evidence only)* |
| **`ECDH P-256`** | **`submission/draft-palatov-web4-core-00.txt:617`** |
| **`P-256` (bare)** | **`submission/draft-web4-core-00.xml:256`** |
| `ECDH with P-256` | `security-framework.md:35` *(the C31-sanctioned explanatory gloss — **not** divergent)*, **`submission/web4-rfc.md:280`** *(a definition — divergent)* |

**Three of the six divergent forms live in `submission/`**, and all three are invisible to the matcher four consecutive passes ran. `web4-rfc.md:280` is a **third** submission locus the draft of this document also missed.

**No carry resolved into a defect. One carry (B-10) has its DIRECTION inverted for 2 of 8 loci — that is N2, and per v12/v16 a direction inversion routes as net-new, not as a reach correction.**

---

## §B — All Three Citation Directions

### B.1 — Outbound (corpus delta): the 4 `web4-standard/` movers

| Mover | Bearing on `security-framework.md` |
|---|---|
| `docs/FRACTAL_ROLE_IDENTITY.md` | **None.** Role-identity composition; 0 predicate tokens. |
| `rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md` | **None.** 0 predicate tokens. |
| `rfcs/RFC-SHARED-POLICY-SUBSTRATE.md` | **None.** 0 predicate tokens. |
| `test-vectors/validate_context_refs.py` | **None.** JSON-LD `@context` reference checker; 0 predicate tokens. |

Tracked siblings from C296's corrected 9-artifact table, re-checked at HEAD: `protocols/web4-handshake.md`, `core-spec/core-protocol.md`, `registries/initial-registries.md`, `core-spec/LCT-linked-context-token.md`, `core-spec/multi-device-lct-binding.md`, `core-spec/lct-capability-levels.md`, `implementation/sdk/web4/security.py`, `test-vectors/security/security-primitives.json`, `profiles/{blockchain-bridge,cloud-service,edge-device,peer-to-peer}-profile.md` — **0 of 13 moved. §B.1 is EMPTY for the 3rd consecutive delta.**

### B.2 — Inbound (v20): who cites this spec BY PATH

`git grep -nE "security-framework\.md" -- docs/audits web4-standard/docs/audits`, minus this lineage's own documents. Yield is in §B.3.

### B.3 — **The third direction (v28): sibling audits that name this file as OWNER of work**

Matcher, pre-registered:
```
git grep -nE "security-framework" -- docs/audits web4-standard/docs/audits \
  | grep -viE "C(31|68|69|108|109|140|180|218|256|296)-" \
  | grep -iE "owner|route|routed|cross-track|unconsumed|deferred|awaits"
```

Three distinct inbound routes, from three sibling lineages:

| Inbound | Filed | By | Named in this lineage |
|---|---|---|---|
| **C70-B-C4** (suite spelling → *"folds into the security-framework suite-registry carry"*, `C70:102`) | 2026-06-18 | registries | **RECEIVED** — carried as **B-7** ever since |
| **C32-B-I1** (`security-framework.md` ↔ `r6-security-analysis.md` reciprocal cross-ref, `C32:105-109`) | 2026-06-05 | r6 | **0 of 8** |
| **C152-1** (B-10's prescription is wrong for multi-device, `C152:22`/`:57`) | 2026-07-07 | multi-device | **0 of 5** — and re-recorded *unconsumed* by `C268:56` and `C308:64` |

**This is the entire yield of the pass.** N2 and N3 come from row 3; N3 also from row 2. **Direction 1 was empty and direction 2 added nothing** — exactly the C334 result, now twice.

---

## §B′ — Mirror Set, RE-DERIVED (not re-read)

### B′.0 — What is being tested

C296's headline finding was that the tracked set had **contracted** from the 9 artifacts C31 counted to 7, and that **both** of its MEDIUMs lived in files the set used to contain. C296 then published a corrected 9-artifact inward set and instructed the next pass: *"The list must be re-derived, not re-read — that is the finding of this pass, and re-reading this corrected list would reproduce it."* So the 9-artifact list is treated below as a **hypothesis to falsify**.

**It falsifies.** The predicate sweep returns a candidate set of **21 artifacts by suite-ID and 44 by primitive token**, from which **13 admit**. C296's list of 9 was missing **4 admitted members, three of them the flagship.**

### B′.1 — Inward census: every candidate, every disposition, **NEGATIVEs named** (v24)

Instruments: `grep -rlE "W4-BASE-1|W4-FIPS-1|W4-IOT-1" web4-standard/` and `grep -rlE "X25519|ChaCha20-Poly1305|HKDF-SHA256|Ed25519|ECDH-P256|AES-128-GCM" web4-standard/`, both minus `docs/audits`.

| Artifact | M1 | M2 | Verdict | Note |
|---|---|---|---|---|
| `core-spec/core-protocol.md` | PASS | defines | **ADMITTED** | in C296's set |
| `protocols/web4-handshake.md` | PASS | defines | **ADMITTED** (evidence only, D0) | in C296's set |
| `registries/initial-registries.md` | PASS | defines | **ADMITTED** | in C296's set |
| `test-vectors/security/security-primitives.json` | PASS | asserts | **ADMITTED** | in C296's set |
| `profiles/blockchain-bridge-profile.md` | PASS | asserts | **ADMITTED** | in C296's set — C296-N1 |
| `profiles/cloud-service-profile.md` | PASS | asserts | **ADMITTED** | in C296's set — B-7 locus |
| `profiles/edge-device-profile.md` | PASS | asserts | **ADMITTED** | in C296's set |
| `profiles/peer-to-peer-profile.md` | PASS | asserts | **ADMITTED** | in C296's set |
| `implementation/sdk/web4/security.py` | PASS | defines | **ADMITTED** | B-8 locus; frozen `759eaefa` |
| **`submission/draft-web4-core-00.xml`** | **PASS** | **defines a suite TABLE** | **ADMITTED — NEW** | **N1.** Never in any security-lineage doc |
| **`submission/draft-palatov-web4-core-00.txt`** | **PASS** | **defines an algorithm list** | **ADMITTED — NEW** | **N1.** Never in any security-lineage doc |
| **`submission/web4-rfc.md`** | **PASS** | **defines algorithms** | **ADMITTED — NEW** | **N1.** Never in any security-lineage doc |
| `testing/test-vectors/handshakeauth_{cose,jose}.json` | **PASS** | **asserts suite + alg** | **ADMITTED — C296's "referential only" is FALSE** | **N4.** Owned by the handshake lineage (C72 X1) |
| `registries/cipher-suites.md` | PASS | defines a *numeric* registry | **NEGATIVE for this lineage** | Cited to `core-protocol.md`, not to the target; owner = registries (C298-N4). Evidence only |
| `QUICK_REFERENCE.md` | PASS | restates | **NEGATIVE** | `:176-181` W4-BASE-1 = X25519 / Ed25519 / ChaCha20-Poly1305 — **concordant**, no independent value |
| `INTEGRATION_STATUS.md` | FAIL | mentions | **NEGATIVE** | `:30`/`:102` are status checkboxes |
| `implementation/sdk/CHANGELOG.md` | FAIL | mentions | **NEGATIVE** | `:633` a changelog line |
| `test-vectors/protocol/core-protocol.json` | FAIL | lists | **NEGATIVE** | `:141` `supported_suites` enumeration only |
| `demos/hello-web4/*` | FAIL | self-labelled mock | **NEGATIVE** | `"alg": "MockEd25519"`; `hello_web4_simple.py:250` *"Real implementations must use proper Ed25519/X25519!"* |
| `testing/witness-vectors/*`, `testing/test-vectors/usagereport_*` | FAIL | COSE envelopes | **NEGATIVE** | carry no suite ID and define no primitive |
| `core-spec/{did-web4-method,data-formats,inter-society-protocol}.md` | FAIL | mention | **NEGATIVE** | primitive tokens appear as example values, not definitions |
| `implementation/reference/**`, `archive/**` | — | — | **EXCLUDED** | standing rule (drift-archive) |

**13 ADMITTED, 9 named NEGATIVE, 2 excluded by standing rule.** C296's set = 9. **Net: +4 admitted, and the 3 that matter had never been opened by this lineage in 9 passes.**

### B′.2 — Outward: `web4-core/` re-established **BY FILE** (binding condition 2)

C296's directory-level shortcut is void. Per-file at HEAD:

| File | Last touch | Verdict |
|---|---|---|
| `web4-core/src/crypto.rs` | `bcff32fb` 2026-06-08 | **FROZEN** — C180-N2 concordance HELD |
| `web4-core/src/pair_channel.rs` | `bcff32fb` 2026-06-08 | **FROZEN** — C180 transport-crypto verdict HELD |
| `web4-core/src/attestation.rs` | `0e997079` 2026-07-17 | **FROZEN in window** — C218-N1 COSE corroboration HELD |
| `web4-core/src/ratchet.rs` | `7b048a78` 2026-07-16 | **FROZEN in window** — C218 dismissal HELD |
| `web4-core/src/vault/crypto.rs` | `090739f6` 2026-06-15 | **FROZEN** |
| `web4-core/src/role_extension.rs` | `4f76f110` 2026-07-18 | **FROZEN in window** — C256's non-re-mining guard **STANDS UNCONSUMED, re-tested by inspection not by construction** |
| **`web4-core/src/role.rs`** | **`d43964e2` 2026-08-05, +171** | **M1-FAIL on subject matter** — see below |

**`role.rs` run through M1/M2/M3 on its own merits.** Predicate token count:
`grep -cniE "X25519|Ed25519|ChaCha20|Poly1305|AES-|HKDF|SHA-256|COSE|CBOR|JOSE|JCS|RFC 8785|ECDH|ECDSA|W4-BASE-1|W4-FIPS-1|W4-IOT-1|key rotation|keypair|signing" web4-core/src/role.rs` = **0**.
**M1-FAIL.** The commit's "rotation" is **role-occupant** rotation — `RoleEventKind::FillerRotated`, `occupant_dimension(entity) → "filled_by:{uuid}"` — a T3 sub-dimension key convention, **not** §2.3 key rotation. This is a **lexical collision on the word "rotate"**, and it is worth recording as such: a matcher grepping `rotat` for §2.3 coverage would have admitted this file, and a matcher grepping the *behaviour* (key material, new keypair, LCT re-issuance) correctly rejects it. **v2 in the negative direction — grep the behaviour, not the vocabulary, kills a false positive as readily as it finds a true one.**
Bearing: it corroborates carry **B-3** (§A.3) and it is the C292-N1 memo's business, not this file's. **No finding laid.**

`web4-policy/` **M1-FAIL** (0 predicate tokens). `web4-trust-core/` **M1-FAIL on subject matter** — guard unchanged from C296; re-tested, it gained no §1/§2/§3 primitive.

### B′.3 — `hub/` M3 gate: **re-tested, NEGATIVE on all three limbs, stays DECLINED**

C296's guard names its own trigger: *"do not re-run unless hub gains a `security-framework.md` citation, a suite-ID token, or a conformance claim."* 25 hub files changed in the window, so the trigger is re-tested rather than presumed:

| Trigger limb | Measured at HEAD (excl. `hub/target/`) | Result |
|---|---|---|
| a `security-framework.md` citation | `grep -rl "security-framework" hub/` → **0** | NEGATIVE |
| a suite-ID token | `grep -rlE "W4-BASE-1\|W4-FIPS-1\|W4-IOT-1" hub/` → **0** | NEGATIVE |
| a conformance claim | none in the 25 changed files | NEGATIVE |

**M3 stays DECLINED. `hub/` is evidence, not defendant.** C296-N4 (`envelope.rs`'s third canonicalization) is carried forward unchanged in the C-M1 bundle; **not re-litigated, not re-counted.**

---

## Findings

### C336-N1 — MEDIUM — the standard's outward-facing submission tree ships crypto the spec corrected 65 days ago, and two of its three drafts contradict each other

**Routing**: CROSS-TRACK → the **C-M1 ≡ B-D1** bundle **and** the submission owner. **NOT auditor-applicable** — the remedy forks (regenerate from the spec / mark the tree retired), and picking is the operator's.
**Classification**: **net-new**. Not reach-escalation on B-7: B-7 is a *spelling-drift* carry among live siblings; this is a **remediated defect surviving verbatim in an artifact the lineage never enumerated**, plus two divergences (AEAD, hash) that are not spellings at all.

**The three artifacts, all M1-PASS on the pre-registered predicate:**

**(a) `submission/draft-web4-core-00.xml` (`a6f54f46`, 2025-09-11) — a frozen copy of the pre-remediation §1.1.**

```
draft-web4-core-00.xml:248-259
  W4-BASE-1 | X25519 | Ed25519    | ChaCha20-Poly1305 | SHA-256 | MUST
  W4-FIPS-1 | P-256  | ECDSA-P256 | AES-128-GCM       | SHA-256 | SHOULD
```
Compare `git show 130069d8^:…/security-framework.md` §1.1 — the **pre-remediation** table:
```
| Suite ID | KEM     | Sig        | AEAD              | Hash    | Profile | Status |
| W4-FIPS-1| P-256   | ECDSA-P256 | AES-128-GCM       | SHA-256 | JOSE    | SHOULD |
```
Same `P-256` cell; same `Profile`-era column vocabulary. C31's **B-H1 (HIGH)** — *"§1.1 table FIPS KEM `P-256` (a curve) vs §1.2 prose `ECDH with P-256` (the mechanism)"*, its internal half filed as **A-L4** — was applied in `130069d8` (#271, 2026-06-04) and re-verified HELD at `C68:35`. The submission draft was never updated. It also lacks the `KDF` column **C69-B-5 added** and the `Encoding` column **C69-B-4 renamed** — recorded as corroborating staleness, **not charged separately** (an I-D is permitted to be terse; a *wrong cell* is not).

**(b) `submission/draft-palatov-web4-core-00.txt` (`4a0dce74`, 2026-04-29) §5.1 — a different AEAD and a hash the standard does not define.**

```
:618   o  Encryption: ChaCha20-Poly1305 (MUST), AES-256-GCM (SHOULD)
:619   o  Hashing:    SHA-256 (MUST),           SHA-3-256 (SHOULD)
:623   o  Key rotation SHOULD occur annually
```
§1.1's SHOULD-level suite (`W4-FIPS-1`) pins AEAD = **`AES-128-GCM`**. `SHA-3-256` corpus count in `web4-standard/` minus audit trees = **1** — this line, and nowhere else. §2.3 states no rotation period.

**(c) The two drafts contradict each other, intra-directory.** The XML says the SHOULD-level AEAD is `AES-128-GCM`; the txt says `AES-256-GCM`. Two submission forms of the same document, same directory, disagree on the same field — **the C298-N4 shape** (*"intra-directory + intra-commit"*), which is what makes this a governance divergence rather than a stale copy.

**(d) `submission/web4-rfc.md` (`84f069a0`, 2026-02-16)** `:286`/`:465` prescribe `AES-256-GCM` for message encryption and `:280` `ECDH with P-256`, with **no suite vocabulary at all** — 0 occurrences of `W4-BASE-1`/`W4-FIPS-1`. AES-256-GCM's only other home in the corpus is `cipher-suites.md:18` as **suite `0x0002`** — a *distinct registered suite*, not W4-FIPS-1, so the registry does not rescue these lines.

**Refutations attempted, all failed:**

- **R1 — "the submission tree is retired."** `grep -rinE "superseded|deprecated|historical|do not use|obsolete|retired" web4-standard/submission/` = **1 hit**, and it is the boilerplate IETF I-D disclaimer (*"may be updated, replaced, or obsoleted by other documents at any time"*). Decisively: **`SUBMISSION_GUIDE.md:9-11` records Status = "Ready for initial submission"** and `:33-35` instructs uploading `draft-web4-core-00.xml` to `datatracker.ietf.org/submit/`. The XML is `category="std"`, `ipr="trust200902"`.
- **R2 — "nobody maintains it."** `git log --follow` on the txt draft: **three maintenance sweeps after creation** (`22b7ea8b`, `e4f48b10`, `4a0dce74`). The most recent, `4a0dce74` (2026-04-29), was a *terminology-drift cleanup* that reached into this file for ATP/LCT naming and touched 12 files across the repo — **it treated the draft as live and left §5.1 alone**.
- **R3 — "this lineage has no jurisdiction over `submission/`."** The sibling pass in the **very next rotation slot** — **C300** (`web4-handshake` 7th delta, 2026-07-31, i.e. the day after C296) — **ADMITTED all three** with an argued admission at its §B′.4 (`C300:144-164`), classing `web4-rfc.md` and `draft-palatov` as **spec peers** and finding handshake-side divergences in them. The admission ruling exists; this lineage simply never received it.
- **R4 — "it's the same as B-7, so reach-escalation."** No. B-7's live matcher is `--include=*.md`, structurally blind to `.xml`; and B-7 is about *spelling*, while (b) and (c) are a **different algorithm at a different key size** and **a hash function absent from the standard**.

**Why MEDIUM and not HIGH.** No executable path consumes `submission/`; no test asserts it; it is not `core-spec/`; and the txt draft's own IETF expiry (*"Expires March 15, 2026"*) has passed, so the artifact currently binds no external reader. **Why not LOW.** It is the **outward** face — the artifact `SUBMISSION_GUIDE.md` designates for upload — it was admitted as a spec peer by a sibling pass, and it carries a token a **HIGH** finding removed.

### C336-N2 — MEDIUM — carry B-10 prescribes an edit that would make the standard self-contradictory, and the refutation is inside the target

**Routing**: DESIGN-Q / CROSS-TRACK → operator, bundled with C-M1. **NOT auditor-applicable.** The remedy includes an option that edits the frozen target (§1.3), which is exactly why it must be routed and not applied.
**Classification**: **net-new by DIRECTION INVERSION** (v12/v16). B-10 is not merely under-reached — for 2 of its 8 loci the arrow points the wrong way: the *carry* is the defect, not the sibling.

This lineage carries B-10 as an unqualified prescription. `C256:166` and `C296`'s operator bundle both read: **"B-10 `cose:ES256`→`cose:EdDSA` (8 sites across 3 LCT files)."**

On **2026-07-07**, `C152:22` demonstrated that applying it to `multi-device-lct-binding.md:257`/`:270` is wrong, and did the work: multi-device is **hardware-P-256 end-to-end by construction** (`:86` `SecKeyCreateSignature` ECDSA-P256; `:348`/`:446` `algorithm="ES256"` at both enrollment ceremonies; `:1022` Secure Enclave; `:1043` StrongBox `secp256r1`; `:1072` WebAuthn `alg: -7`, which **is** ES256-in-COSE natively). Secure Enclave / StrongBox / FIDO2 **cannot produce Ed25519**. Both B-10 sites at those lines are signatures by such keys.

**The refutation is available inside the target itself** — which is why this belongs to *this* lineage and not to multi-device:

- **`security-framework.md:44`** makes COSE/EdDSA mandatory-to-**implement**, not mandatory-to-**use**.
- **`security-framework.md:17` and `:35-36`** define `W4-FIPS-1` with `Sig = ECDSA-P256`, i.e. the standard **sanctions** P-256 signatures.
- `LCT-linked-context-token.md:224` allows *"Ed25519 or P-256"*; `lct-capability-levels.md:96` likewise — which softens the prescription for the **other** B-10 loci too.

**Non-reception is measured, not asserted.** `grep -c "C152"` across all nine security-lineage documents (C31, C68, C108, C109, C140, C180, C218, C256, C296) = **0, 0, 0, 0, 0, 0, 0, 0, 0**. `grep -ci "hardware.P-256"` = 0 in all nine. `grep -ci "StrongBox|Secure Enclave"` = **1 in C31, 0 in the other eight** — and C31 predates C152 by 33 days. Meanwhile `C268:56` and `C308:64` each re-record: *"The B-10 owner ledger (security-framework/protocols) has **0 commits** ⇒ **no adjudication has occurred**; C152's sharpening stands unconsumed."* **Two sibling passes deferred to an owner that was not listening, and read the owner's silence as "not yet adjudicated" rather than "not received."**

**What the adjudication must decide** (verbatim from `C152:57`, reproduced so this ledger finally carries it): split B-10 per-locus. For multi-device's 2 sites choose (i) retain `cose:ES256`, (ii) relabel `jose:ES256` per the W4-FIPS-1/JOSE pairing, or (iii) retain **and add an explicit hardware-anchor COSE+ES256 allowance to `security-framework.md` §1.3** — **not** `cose:EdDSA`. Option (iii) is an edit **inside the frozen target**: the first inbound item in this lineage's history that would land in the file itself.

**Refutation attempted.** *"B-10 is gated on C-M1 and unapplied, so nothing is broken."* True, and it is why this is MEDIUM rather than HIGH — no damage has shipped. But the carry is the instruction the gate releases: **if C-M1 is answered tomorrow, the ledger as written directs a self-contradictory edit at 2 of 8 loci**, and the correction has been sitting in a sibling document for 32 days.

### C336-N3 — LOW — inbound non-reception is selective, and the tell is whose finding ID it arrives under

**Routing**: audit-lineage record-keeping. No spec change.

Three inbound routes have been addressed to this file's owner ledger (§B.3). **One was received; two were not**, and they differ in exactly one respect:

| Inbound | Arrived as | Received? |
|---|---|---|
| **C70-B-C4** | *"folds into the security-framework suite-registry carry (**C68 C-M1/B-7**)"* — names **this ledger's own ids** | **YES** — became/merged into B-7 immediately |
| **C32-B-I1** | *"a one-line cross-ref **from `security-framework.md`** closes the loop"* — names the **sibling's** id | **NO** — 0 of 8 |
| **C152-1** | *"Route: cross-track memo to **the B-10 owner** (security/handshake carry ledger)"* — names the sibling's id, and names the owner by **description** rather than by this ledger's row | **NO** — 0 of 5 |

**An inbound item is received when the sibling writes it under an id this ledger already types, and lost when it is written under the sibling's own id — regardless of how explicitly the owner is named.** C152 named the owner *twice*, in the flagship and in a dedicated adjudication paragraph, and it still did not arrive. This is the same mechanism as **C334-N2** (`C106` naming `C71`, the sibling's *commit*, 13× and `C70`, its *audit doc* where routing lives, 0×), now observed in a second lineage — so it is a pattern, not an anecdote.

**C32-B-I1's premise re-verified at HEAD**, not inherited: `grep -c "r6-security-analysis" web4-standard/core-spec/security-framework.md` = **0**; `grep -n "security-framework" web4-standard/core-spec/r6-security-analysis.md` = **no output**. Still reciprocally unlinked, 64 days on. **Recorded, not re-adjudicated** — it is an INFO-grade item in its own lineage and this pass does not upgrade it.

### C336-N4 — LOW — C296 dispositioned two conformance vectors as "referential only"; they are not, and the handshake lineage already charged them

**Routing**: reach-escalation on **C296-N1**, no new severity. **Ownership stays with the handshake lineage — deliberately NOT re-charged.**

`C296:181` lists `testing/test-vectors/handshakeauth_{cose,jose}.json` in a row dispositioned **"referential only."** They are not referential. Each carries `"suite": "W4-BASE-1"` in its signed payload and publishes a signing-input hash (`signing_input_sha256`, `Sig_structure_sha256`) — they are **conformance assertions about the suite this spec defines**, and they satisfy the pre-registered predicate on limbs (a) and (b).

The **security-side** divergence: `handshakeauth_jose.json:3` sets `"alg": "ES256"`, `"typ": "JWT"` in the protected header and `:9` binds it to `"suite": "W4-BASE-1"`, whose §1.1 row pins `Sig = Ed25519` and `Encoding = COSE (**MUST**)`. That is **C296-N1's exact shape** — *declares W4-BASE-1, encodes as JOSE* — in a second artifact. The sibling `handshakeauth_cose.json` shows the intended form (`"alg": -8` = EdDSA, matching its payload `"alg": "EdDSA"`), which is what makes the JOSE file's mismatch legible rather than arguable.

**Why this is NOT a net-new finding, stated because the temptation to publish it was real.** `C72:124` (2026-06-18) already charged it, precisely: *"`handshakeauth_jose.json`: protected_header `alg="ES256"` (correct per §6.0.4) but payload `alg="EdDSA"`."* It is consolidated as carry **X1 → HS-X1**, MED, cross-track, vector maintainer, still **OPEN** at `C300:331`. Charging it here would be a **duplicate under a second lineage's number** — exactly the failure N3 describes, inverted. **The finding is C296's disposition being wrong, not the vector being undiscovered.**

**Method consequence (v24 sharpening).** C296 satisfied v24 — it *named* these members rather than silently omitting them — and still produced a false disposition. **Naming a member is necessary but not sufficient; the disposition itself has to be derived from the artifact's content, not from its path.** `testing/test-vectors/` reads like a fixtures directory; the file's first three lines are a conformance claim.

---

## §C — Fresh-Internal Refute-by-Default Pass

**0 net-new internal contradictions — the target itself is clean for the 6th consecutive delta.** Blob-identity preserves C140/C180/C218/C256/C296's verdicts; candidates re-confirmed at their frozen call sites:

- §1.1 table ⟷ §1.2 prose: KEM/Sig/AEAD/Hash/KDF/Encoding token-match for both suites. `ECDSA-P256` (table) vs `ECDSA with P-256` (prose) remains the benign wording variant carried since C140 — **not** a finding, and deliberately not swept into N1 (N1 charges *other artifacts*, and the intra-file variant is not under an exact-string conformance assertion).
- §1.3 MTI COSE (`crv = 6`, `alg = -8`) ⟷ §1.1 `W4-BASE-1 Encoding = COSE` ⟷ §1.2 COSE RFC 9052/9053: internally consistent. **N2 sharpens the reading of `:44`** (mandatory-to-*implement*) but does not make it internally contradictory.
- §2.3 rotation prose ⟷ `LCT-linked-context-token.md` §7.3 (frozen): resolves. The B-9/B-M2 juxtaposition is the standing carry, unchanged.
- §3.1 ⟷ `web4-handshake.md` §6.0.5 / §9 / §6.1: all three cites resolve at HEAD.
- §3.2 ⟷ SAL/R6: B-3, unchanged; see §A.3 for the re-derived disposition.
- **`P-256` does not appear as a bare KEM token anywhere in the target** — re-verified, because N1's whole claim is that it survives *outside* the file.

---

## Classification Summary

| ID | Sev | Class | Finding | Routing |
|---|---|---|---|---|
| **C336-N1** | **MEDIUM** | net-new | `submission/` holds 3 admitted-but-never-enumerated artifacts: the XML draft is a **verbatim pre-remediation §1.1** (`P-256`, the cell C31-B-H1 **HIGH** fixed 65 d ago); the txt draft prescribes `AES-256-GCM` where §1.1 says `AES-128-GCM` and `SHA-3-256` (corpus count **1**); the two drafts **contradict each other** intra-directory; `SUBMISSION_GUIDE.md` calls the XML *"ready for initial submission"*; **C300 admitted all three as spec peers one slot later**. | CROSS-TRACK → **C-M1/B-D1** + submission owner; **not auditor-applicable** |
| **C336-N2** | **MEDIUM** | net-new (**direction inversion**) | **B-10's prescription is wrong for 2 of its 8 loci.** `C152:22` proved it 2026-07-07 (hardware-P-256 end-to-end; SE/StrongBox/FIDO2 cannot emit Ed25519); the refutation sits in the target at `:35-36`/`:44`. `grep -c C152` = **0 across all 9** lineage docs; `C268:56` + `C308:64` re-record *unconsumed*. One remedy option edits **§1.3 of the frozen target**. | DESIGN-Q/CROSS-TRACK → operator with C-M1; **B-10 must be re-typed with its per-locus split** |
| **C336-N3** | LOW | net-new (process) | Inbound non-reception is **selective**: 3 routes, **1 received / 2 not**. The received one (C70-B-C4) named **this ledger's ids**; the two lost ones (C32-B-I1, C152-1) named the **sibling's**. Same mechanism as C334-N2 — second lineage, so a pattern. C32-B-I1's premise re-verified live (0 refs both ways, 64 d). | audit-lineage record-keeping |
| **C336-N4** | LOW | reach-escalation on C296-N1 | C296 dispositioned `handshakeauth_{cose,jose}.json` **"referential only"** — false; they assert `suite: W4-BASE-1` and publish signing-input hashes, and the JOSE one binds W4-BASE-1 to an ES256/JOSE envelope (§1.1 `Encoding = COSE MUST`). **Already charged at C72 as X1/HS-X1, still OPEN — NOT re-charged.** | evidence → C-M1; ownership stays with the handshake lineage |

**Totals: 0 HIGH, 2 MEDIUM, 2 LOW — 4 net-new-or-escalated. ZERO mutation** — no spec, SDK, vector, profile, schema, ontology, submission or implementation file was modified this turn. **8th consecutive zero-mutation pass across the rotation.**

- **§A**: 6 C69 + 1 C109 fixes HELD by blob-identity; 9 carries STAND, **0 resolved into a defect**, **1 (B-10) direction-inverted for 2 loci**, **1 (B-3) disposition re-derived because its stated basis went void**, **1 (B-7) reach corrected 6/5/4 → 12 occ / 10 files / 7 forms, matcher fixed on two axes**. **v19 row-set census NEGATIVE — 0 silent drops in 8 passes.**
- **§B**: outbound EMPTY (3rd consecutive); inbound added nothing; **the third direction was the entire yield** (2nd consecutive fire).
- **§B′**: set re-derived from the pre-registered predicate — **9 → 13 admitted**, 9 NEGATIVEs named, `web4-core/` re-established **by file**, `role.rs` **M1-FAIL** (0 predicate tokens; a "rotate" lexical collision), `hub/` M3 **re-tested NEGATIVE on all three limbs**.
- **§C**: 0 net-new internal contradictions — 6th consecutive clean target.

---

## Key Adjudication

1. **The matcher was the blind spot, and it had a filetype in it.** B-7 has been the FIPS-KEM carry since C68. Its live instrument is `grep -rn "…" web4-standard/ --include=*.md`. Every pass re-ran it, every pass got the right answer for the tree it searched, and **`--include=*.md` cannot see an `.xml` file**. C296 corrected this carry's *scope* (adding a fifth file) while leaving its *filetype filter* untouched — a scope correction inside a filter that was itself the defect. This is v9's rule (*a gate is only as good as the tree it points at*) with one more dimension: **a gate is only as good as the tree AND the filetypes AND the path-shape it points at**, and "the artifacts we publish outward" is not a tree any lineage's matcher was built to cover.

2. **The pass that would have looked identical, again — and the instruction that prevented it.** Target byte-frozen 41 days, §B.1 empty for the third consecutive delta, all 13 tracked siblings unmoved. The inherited method produces a clean 6th no-op. C296 anticipated exactly this and wrote the instruction: *"The list must be re-derived, not re-read — re-reading this corrected list would reproduce it."* **It was right, and the proof is that re-deriving found 4 members its own corrected list was missing.** A pass that had merely re-run C296's 9-artifact table would have been faithful, cheap, and blind. **On a frozen target the set is the audit — and a set that was corrected once is not thereby correct.**

3. **Two sibling passes read silence as deferral.** `C268:56` and `C308:64` both concluded *"the owner ledger has 0 commits ⇒ no adjudication has occurred."* That inference is sound only if the owner **received** the item. It had not: 0 mentions across nine documents. The sibling's instrument — *did the owner's file change?* — cannot distinguish **"considered and not yet acted on"** from **"never arrived."** N3's tell (received iff written under the owner ledger's own id) is the cheap discriminator, and it is checkable from either side.

4. **Refutation did more work than discovery, for the third fire running.** Of five candidate charges: the handshakeauth-vector charge **died** on `C72:124` (already owned, MED, still open — demoted to N4 as a disposition error); the missing KDF/Encoding columns in the XML draft **died** on the I-D-terseness argument and were demoted to corroborating evidence; the `cipher-suites.md` AES-256-GCM hit **died** because `0x0002` is a distinct registered suite, not a W4-FIPS-1 contradiction; `role.rs` **died** on the M1 predicate (0 tokens — a lexical collision on "rotate"). What survived survived because the target's own text supplied the argument: **N2's refutation of B-10 is `security-framework.md:35-36` and `:44`.**

5. **A correctly closed row can still leave live work, and no census sees it.** `A-L3` was applied by #271, verified HELD at C68, and correctly dropped from the ledger. Its cross-track follow-through (`C32:105`, filed the next day) has been unnamed for 64 days. v19 counts rows that vanish **without** a disposition; this row vanished **with** one and still lost its tail. The row-set census is a necessary instrument and it is blind here by construction — which is why §B.3's third direction is not an optional extra.

---

## Next-Turn Carry

- **C337 `security-framework.md` remediation slot = NO-OP.** All 4 findings land **outside** the target; 0 AUTONOMOUS findings inside the file, which is byte-frozen 41 days. **Do NOT manufacture an edit.** Rotation advances.
- **N1 + N4 bundle into the standing C-M1 ≡ B-D1 operator memo** alongside C296-N1/N2/N4, C180-N1, C218-N1, C140-DELTA-1. **N2 is a separate ask** and is the more urgent one: it does not need C-M1 answered, it needs **B-10 re-typed with its per-locus split** before C-M1 is answered.
- **Corrected carry reach, inherit VERBATIM (do NOT re-derive as net-new):**
  - **B-7** = **12 occurrences / 11 lines / 10 files / 7 distinct forms**, per the canonical matcher published in §A.3. Adds to C296's six `.md` sites: `sdk/web4/security.py:117` + `test-vectors/security/security-primitives.json:28` (both `ECDH-P256`, concordant) and **three `submission/` loci** — `draft-web4-core-00.xml:256` (`P-256`), `draft-palatov-web4-core-00.txt:617` (`ECDH P-256`), `web4-rfc.md:280` (`ECDH with P-256`). **Inherit the published PAT verbatim; drop `--include=*.md` permanently AND keep the reversed/bare/prose alternatives — the old alternation missed three of the six divergent forms.**
  - **B-8** path `web4-standard/implementation/sdk/web4/security.py`, `759eaefa` 2026-04-17 — re-verified at HEAD, not inherited.
  - **B-10** = 9 occurrences / 4 files, **and now carries its C152 per-locus split** (see N2). Never re-type it as an unqualified 8-site normalization.
  - **B-3** disposition is now *"corroborated by `role.rs`'s role-authority path"*, **not** *"web4-core at 0 commits"*.
- **Tracked mirror set for C376 = the 13-artifact ADMITTED list in §B′.1** — **and re-derive it again anyway.** Two consecutive passes have now found the inherited set wrong (C296: 7→9; C336: 9→13). Inheriting *this* list is the same error one generation on.
- **`hub/` guard UNCHANGED and re-tested**: M3-DECLINED; trigger = a `security-framework.md` citation, a suite-ID token, or a conformance claim. All three measured **0** at HEAD over 25 changed hub files. C296-N4 (`envelope.rs` third canonicalization) carried forward in the C-M1 bundle, not re-litigated.
- **`web4-core/` guard REPHRASED as a behaviour, not a directory** ([[feedback_guard_names_a_path_not_a_behaviour]]): re-gate any file that gains a §1/§2/§3 **primitive** or **its own signing preimage**. `role.rs` FAILS this (0 predicate tokens; "rotate" = role-occupant, not key). `role_extension.rs`'s C256 guard **stands unconsumed, re-tested by inspection**.
- **`submission/` is now IN this file's mirror set.** At C376, check first whether the XML draft's `P-256` cell and the txt draft's `AES-256-GCM`/`SHA-3-256` lines still stand, and whether the tree acquired a retirement marker (which would resolve N1 in the other direction and is a legitimate remedy).
- **D0 (`protocols/`) still operator-gated.** `web4-handshake.md` and `web4-lct.md` were **read as evidence** under the reviewer-approved split; **no finding is laid against either**. N2 concerns a carry the security ledger owns, not a `protocols/` file.
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: **DESIGN-Q** — C-M1 ≡ B-D1 SSOT (now +C336-N1, +C336-N4); **B-10 per-locus split (C336-N2)**; B-3 authz basis; B-9/B-M2 rotation semantics; B-H2/B-11 W4-IOT-1 + AES-CCM. **CROSS-TRACK** — B-7 (corrected reach, matcher fixed); B-8; B-L6/B-L7; **C32-B-I1** (reciprocal cross-ref, finally entered in this ledger). **Do not self-apply any.**
- **Rotation advances.** Next slot = **C338** = `registries/initial-registries.md` per the fixed order; next `security-framework.md` delta ≈ **C376**.

### Method carry born this fire — **v29: sweep the artifacts the project publishes OUTWARD**

Every lineage's mirror set is derived from what the standard *cites* and what *implements* it. Neither direction reaches the artifacts the project **emits to the outside world** — submission drafts, RFC renderings, quick-references, published landing pages. Those are copies of the spec made at a moment in time, by a process no remediation commit knows about, and **nothing in the corpus links back from them**, so no citation-direction sweep finds them.

Three riders:

1. **Check the filetype filter of every carry's matcher before trusting its zero.** A carry whose grep says `--include=*.md` has been certifying the absence of nothing but markdown, however many trees it recurses.
2. **The strongest evidence that an outward artifact is live is a maintenance commit that touched it for an unrelated reason.** A terminology sweep that reaches a file and leaves its crypto section alone proves both that the file is maintained *and* that the maintenance never looked there.
3. **Ask which remediations should have propagated outward and did not.** Diff `git show <remediation>^:<spec>` against the outward copy. A HIGH fixed in `core-spec/` and left standing in `submission/` is the same defect twice, in the copy more people will read.

→ [[feedback_sweep_the_outward_artifacts]]

---

*Audit produced under Autonomous Session Protocol v2 — slot `web4-20260808-000000`, LEAD voice. Read-only: no spec, SDK, vector, profile, submission, schema or implementation file was modified this turn. Remediation (C337) is a declared NO-OP (0 AUTONOMOUS findings inside the target).*
