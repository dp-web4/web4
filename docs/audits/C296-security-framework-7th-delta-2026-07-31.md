# C296 — `security-framework.md` Seventh Delta Re-Audit (8th pass)

**Audit ID**: C296
**Target**: `web4-standard/core-spec/security-framework.md` (97 lines) — Web4 Security Framework (crypto suites, key management, authentication/authorization)
**Date**: 2026-07-31
**Auditor**: autonomous web4 session (legion, slot `web4-20260731-020400`), v2 protocol, LEAD voice
**Type**: **Seventh delta re-audit** (8th pass overall). Lineage: **C31** (first pass, 2026-06-04, #268 → remediation #271) → **C68** (1st delta) → **C69** remediation (#350) → **C108** (2nd delta) → **C109** remediation (#396 `eedd36fc`) → **C140** (3rd, 0 net-new) → **C180** (4th, 0 net-new) → **C218** (5th, 0 net-new) → **C256** (6th, 0 net-new) → **C296**.
**Prior audit docs**: `C31-…`, `C68-…`, `C108-…`, `C109-…remediation…`, `C140-…3rd-delta…`, `C180-…4th-delta…`, `C218-…5th-delta…`, `C256-security-framework-6th-delta-2026-07-23.md`.

---

## Headline

**The 4-delta clean streak ends. 4 net-new findings — 2 MEDIUM, 1 LOW, 1 INFO — and not one of them is inside the byte-frozen target.** All four come from the **inward** half of the mirror set: `web4-standard/` artifacts that *independently define* security primitives and that the tracked-sibling table never listed. The target's own §A/§C are clean for the 5th consecutive delta.

The interval's headline number is the one the method carry predicted: **the outward mover everyone would have audited (`hub/`, 28 commits) yields no charge, and the yield is in four `.md` files that have not changed since 2025-09-11 and that six of the eight prior passes never opened.**

- **C296-N1 (MEDIUM)** — `profiles/blockchain-bridge-profile.md` declares suite `W4-BASE-1` and data format **JSON/JCS**; §1.1 pins W4-BASE-1's `Encoding` to **COSE (MUST)**, vector `sec-001` asserts `"encoding": "COSE"`, and `test_security.py:90` asserts it as a live test. 3 of the 4 profiles align exactly; this is the sole outlier. §1.3 *wants* to permit it ("JOSE/JSON … SHOULD for bridge scenarios") and the suite vocabulary has no way to say it.
- **C296-N2 (MEDIUM)** — the **KDF token** carries the identical exact-string conformance contract as the KEM token that made C31's B-H1 a HIGH finding (`test_security.py:64`/`:75`), and **two audit lineages have ratified two different canonical values**: the security lineage's spec + vector + SDK say `HKDF-SHA256`; the registries lineage's **B-A6 fix deliberately installed bare `HKDF`** and five consecutive registries deltas (C110/C142/C182/C220/C258) published "✅ **matches**" against `core-protocol.md`. Neither lineage ever checked the other's authority. This widens standing carry **B-7 from a case (KEM) to a dimension (suite fields)**.
- **C296-N3 (LOW, instrument)** — two standing carries' *instruments* have decayed while their verdicts survived: **B-7**'s "live re-grep" is scoped to the carry's own enumeration and so can only ever confirm it (C31 counted 5 files; C256 "re-confirmed" 4); **B-8**'s cited path does not exist and has not existed in any of the 4 audit docs that cite it.
- **C296-N4 (INFO → C-M1/B-D1)** — §1.3's `MUST` is quantified over "**All** Web4 signed payloads" with **no scoping predicate**, and the repo contains a live counterexample: `hub/hub-lib/src/envelope.rs` mints a **third** canonicalization (bespoke canonical JSON, neither deterministic-CBOR nor RFC 8785 JCS) as the authority primitive for every consequential hub request. `hub/` is **M3-DECLINED** (evidence, not defendant) — argued fresh below, not imported from C294.

---

## Scope, Method, and Published Instruments

### Frozen-wrap structure

`git diff eedd36fc HEAD -- web4-standard/core-spec/security-framework.md` is **empty**. The file is byte-identical to its C109 remediation and has been for **33 days**; live blob `2880e643f4d7b9899dca38d97dee3358b0f38237`, **byte-identical to the blob C218 and C256 each verified**. So §A is verification-by-construction plus a live carry re-check, §B is the corpus-delta surface, §B′ is the re-derived mirror set, §C is one fresh-internal refute-by-default pass.

### Publishing the instrument (counting rule stated before any count)

**Rule for every per-directory count in this document**: `git rev-list --count 72e6b89a..HEAD -- <dir>` — **commits touching the directory**, not files changed. (The C296 scope proposal initially published a *file*-count bucketed by two path segments; the policy reviewer's counts disagreed with all three of mine because the rule was different and unpublished. Both rules were valid; only one was stated. That bucketing is also precisely what let two named crates vanish into a "misc" bucket — see §B′.1.) Snapshot = **`72e6b89a`** (the C256 merge, 2026-07-23). No file-count and commit-count appear in the same table anywhere below.

| Directory | Commits since `72e6b89a` |
|---|---|
| `hub/` | **28** |
| `docs/` | 23 |
| `whitepaper/` | 9 |
| `web4-standard/` | **3** |
| `web4-trust-core/` | 2 |
| `web4-policy/` | 1 |
| **`web4-core/`** | **0** |
| *total (all paths)* | **66** |

**`web4-core/` at zero movement is load-bearing and is stated, not assumed**: it mechanically preserves every C180/C218/C256 §B′ verdict (`crypto.rs`, `pair_channel.rs`, `attestation.rs`, `ratchet.rs`, `vault/crypto.rs`), and it means C256's forward guard — *"do NOT re-run the security gate on `role_extension.rs` unless it gains a §1/§2/§3 primitive or its own signing preimage"* — is satisfied by construction rather than by inspection. The guard was re-tested, not presumed: `role_extension.rs` has not moved, so it gained neither.

### Method carries applied (v2–v7), and where each one landed

- **v7 — re-derive the mirror set from SUBJECT MATTER, in BOTH directions, pre-registering M1/M2/M3 in writing before the sweep.** This is the carry the pass exists to execute and it is where all 4 findings came from. Pre-registration is in §B′.0.
- **v5 — widen a silence charge from the CASE to the DIMENSION, and grep `docs/audits/` BACKWARD for a pass that already settled the class.** Both halves fired on N2: widening KEM→all-suite-fields produced the KDF question, and the backward grep found the registries lineage had already *ratified the opposite answer* five times. Without the backward grep this would have shipped as a spelling nit against `initial-registries.md`; with it, the finding is a two-lineage collision and `initial-registries.md` is not charged at all.
- **v4 — baseline your own instrument.** §A.3's carry re-greps were run corpus-wide rather than against the carry's enumeration; that is what produced N3.
- **v2 — grep the BEHAVIOUR, not the vocabulary.** `hub/` encodes **0** suite-ID tokens (`W4-BASE-1|W4-FIPS-1|W4-IOT-1` = 0 across all of `hub/`, excluding `target/`). A vocabulary grep would have returned a clean zero and closed the gate. The behaviour grep (X25519 13 / Ed25519 26 / ChaCha20 4 / HKDF 2) is what passed M1.
- **v3 — check the enforcement mechanism the spec names.** §1.3 names COSE/CBOR and JOSE/JSON as its two canonicalizations; grepping the *consumers* of that mechanism is what surfaced the third one (N4).

### Bounds held (recorded so the next pass inherits them)

1. **The `hub/` sweep is a contradiction/corroboration check against §1/§2/§3 only — explicitly NOT a vulnerability hunt.** 28 commits of hub is enough surface to swallow a session, and a hub security review is a different task under a different skill. Nothing below asserts anything about hub's security posture.
2. **`protocols/` split (D0).** D0 gates *remediation and finding-routing* against the `protocols/` cluster, **not reading it as evidence**. `protocols/web4-handshake.md` and `protocols/web4-lct.md` are read below and cited as evidence; **no finding is laid against a `protocols/` file**, and everything surfaced there is recorded under the existing B-7 / B-10 / D0 carries.
3. **Severity**: HIGH = correctness/normative contradiction; MEDIUM = cross-spec divergence; LOW = hygiene/precision/instrument; INFO = positive confirmation or forward-awareness.
   **Routing**: AUTONOMOUS (fixable inside the target) / DESIGN-Q (operator canonicity) / CROSS-TRACK (lands elsewhere). **Nothing below is self-applied.**

### Structure note (C120/C121 doc-specific MUST check)

`security-framework.md` still has **no normative-summary / §12-style section**, so the "normative summary restates entity MUSTs unconditionally" defect class **does not apply**. Re-confirmed from C140/C180/C218/C256.

---

## §A — Prior-Finding Verification, Regression, Completeness, Carry

### A.1 — 6 C69 fixes + 1 C109 fix: **HELD by byte-freeze**

Live blob `2880e643` is byte-identical to the blob C218 *and* C256 verified. C140/C180/C218/C256 each verified all seven token-by-token; blob-identity mechanically preserves that verdict, and no re-derivation is owed.

| ID | Fix | Verdict at C296 |
|---|---|---|
| **B-1** (C69) | §1.3 COSE `crv = 6` / `alg = -8` (EdDSA) | **HELD** (blob-identical) |
| **B-4** (C69) | §1.1 column `Profile` → `Encoding` | **HELD** |
| **B-5** (C69) | §1.1 add `KDF` column (`HKDF-SHA256`) | **HELD** — *and see N2: this fix is the reason the security lineage's canonical KDF token is `HKDF-SHA256`* |
| **B-6** (C69) | §1.2 COSE `RFC 8152` → `RFC 9052/9053` | **HELD** |
| **B-9 interim** (C69) | §2.3 stop asserting in-place identifier mutation | **HELD** |
| **B-2** (C69) | §3.1 handshake deference | **HELD → widened by C109-N1** |
| **N1** (C109) | §3.1 split §6.0.5 / §9 / §6.1 cite | **HELD — precise** |

**Regression sweep**: blob-identity → cross-file regression surface nil.

### A.2 — C56 remediation-completeness re-read: **clean (held by construction)**

Blob-identity preserves C218/C256's completeness verdict. No residual one-sided-claim defect.

### A.3 — Bidirectional carry re-verification, **run corpus-wide rather than against each carry's own enumeration**

This is the v4 change from prior passes, and it is what produced N3. Instruments are published inline.

| Carry | Routing | Status at C296 (live, corpus-wide) |
|---|---|---|
| **B-3** §3.2 "authz based on VCs" vs SAL/R6 | DESIGN-Q | **OPEN, unchanged** — §3.2 verbatim (frozen). C256's `role_extension.rs` forward-note stands; `web4-core/` at 0 commits adds nothing new. |
| **B-7** FIPS-KEM spelling drift | CROSS-TRACK | **OPEN — and its published enumeration is WRONG. See N3.** Instrument: `grep -rn "P-256ECDH\|P-256 ECDH\|P-256EC\b\|ECDH-P256" web4-standard/ --include=*.md` at HEAD → **6 occurrences across 5 files**, not the "5 sites" C256 published. Widened to a dimension by N2. |
| **B-8** SDK docstring quotes deleted A-L2 phrase | CROSS-TRACK | **OPEN; verdict survives, instrument does not. See N3.** The cited path `implementation/sdk/web4/security.py` **does not exist**; the real file is `web4-standard/implementation/sdk/web4/security.py`, last touched `759eaefa` (2026-04-17) — genuinely frozen, so "unmoved" was true, but it was read off an empty `git log` for a nonexistent path. |
| **B-9 / B-M2** rotation mutate-vs-stable-DID | DESIGN-Q | **interim HELD** (§2.3 frozen); semantics decision stands. |
| **B-10** `cose:ES256` mislabel | CROSS-TRACK | **OPEN; reach under-published.** Instrument: `grep -rn "cose:ES256" web4-standard/ --include=*.md` → **9 occurrences across 4 files** (`lct-capability-levels.md` 5, `multi-device-lct-binding.md` 2, `LCT-linked-context-token.md` 1, **`protocols/web4-lct.md:241` 1**), not the "8 across 3 LCT files" C256 published. `cose:EdDSA` = **0** corpus-wide (target token still absent). The 4th file is in `protocols/` → **evidence only, no finding laid against it** (D0). Snapshot-presence: `web4-lct.md` last touched `27b85624` (2026-02-17) — present and unchanged at every prior pass, so this is **reach the record lost, not new content**. |
| **C-M1 ≡ C70-B-D1** crypto-suite/encoding SSOT | DESIGN-Q | **OPEN — and materially strengthened this fire.** N1, N2, and N4 all land in this bundle. |
| **B-H2 / B-11** W4-IOT-1 + AES-CCM | DESIGN-Q / CROSS-TRACK | **OPEN, unchanged.** C140 DELTA-1 re-confirmed live: `web4-handshake.md:23` gives W4-IOT-1 Profile=**COSE**, `core-protocol.md:20` and `initial-registries.md:8` give **CBOR**. Unchanged; not re-adjudicated. |
| **B-L6 / B-L7** vector ownership; `device` W4ID method | CROSS-TRACK | OPEN, unchanged. `security-primitives.json` last touched `3df1a758` (2026-03-18) — frozen; its `spec` field still names both `security-framework.md` and `data-formats.md`. |

**No carry resolved into a defect. Two carries (B-7, B-10) are under-published relative to their live reach; that is N3 and the B-10 row above, and per [[feedback_carry_gains_reach_not_truth]] it routes as a reach correction, never as net-new truth.**

---

## §B — Corpus-Delta Pass (movers since the C256 snapshot `72e6b89a`)

`web4-standard/` moved **3 commits**, touching exactly 3 files:

| Mover | Bearing on security-framework |
|---|---|
| `ontology/t3v3-ontology.ttl` | **None.** T3/V3 tensor ontology; 0 crypto-suite / key-management / auth tokens. Owned by the t3-v3 lineage (C270). |
| `proposals/resilience-to-incomplete-information.md` (#580) | **None normative** — authority PROSPECTIVE, charges land on its precedent survey. No security counter/violation/positive observed this fire; nothing added to the survey. |
| `proposals/dictionary-as-context-mandatory-role.md` (#579) | **None** — dictionary/context role; no security primitive. |

Tracked siblings from C256's table, re-checked at HEAD: `protocols/web4-handshake.md`, `core-spec/core-protocol.md`, `registries/initial-registries.md`, `core-spec/LCT-linked-context-token.md`, `core-spec/multi-device-lct-binding.md`, `core-spec/lct-capability-levels.md`, `web4-standard/implementation/sdk/web4/security.py` (**corrected path**) — **0 of 7 moved**.

**§B yields 0 findings.** For the second consecutive delta the corpus-delta surface is empty. **This is exactly the configuration the frozen-wrap trap lives in**, and it is why the pass's entire yield had to come from §B′ re-deriving the mirror set rather than from re-walking the inherited one.

---

## §B′ — Mirror Set Re-Derived from Subject Matter, Both Directions

### B′.0 — Pre-registered gate (written BEFORE the sweep, per v7)

- **M1 — subject-matter presence.** Does the candidate encode a §1 suite primitive, a §2 key-management rule, or a §3 authentication/authorization mechanism? Tested by **behaviour** tokens, not vocabulary (v2).
- **M2 — genuineness.** Is it a genuine mirror of **this** spec, or of a *different* spec (C218/C256 "third kind"), a name-collision (C178), or a downstream **consumer** of §1 primitives?
- **M3 — admission (REACH, not verdict).** Does the target's normative text *reach* this artifact? Per [[feedback_admission_criterion_not_verdict]], M3 asks about the scope of the spec's own quantifier — it must **not** ask "would admitting this indict the spec," which pre-judges the conclusion and is self-sealing.

**Outward candidate set** (what implements the subject matter): `hub/`, `web4-trust-core/`, `web4-policy/`, plus the freeze-held prior set. **Inward candidate set** (what *else specifies* it): every `web4-standard/` artifact that independently names a suite ID.

### B′.1 — Why the outward set was nearly wrong (recording the near-miss)

The scope proposal derived the outward set from **dominant mover** and pre-named only `hub/`; `web4-trust-core/` and `web4-policy/` were inside a "misc" bucket produced by the unpublished file-count rule. A crate named **trust-core** — with `src/`, `tests/`, `benches/`, its own `PATENTS.md` — is nearer this spec's subject matter than hub is by name alone, and like hub had never been gated for security in 7 passes. It is named and ruled below. **Deriving the set correctly and finding nothing is the point; omitting a candidate because its mover count is low is the C294 error reproduced.**

### B′.2 — `web4-trust-core/`: **M1-FAIL — on subject matter, not on dormancy**

Instrument (`grep -rIn --include=*.rs --include=*.toml --include=*.py <tok> web4-trust-core | grep -v /target/`): `W4-BASE-1|W4-FIPS-1|W4-IOT-1` **0** · `X25519` **0** · `ChaCha20|chacha` **0** · `HKDF|hkdf` **0** · `COSE|cose|ciborium|cbor` **0** · `Ed25519|ed25519` **0**. The only near-tokens are `rotat` (3) and `verif` (3): `src/bindings/wasm.rs:503 pub fn rotate(&mut self, new_entity_lct_id: &str, rotated_by: &str)` is **entity-LCT re-binding of a trust tensor** — no keypair, no key material — and the `verif` hits are prose in `ROLLOUT_PLAN.md`. §2.3 key rotation is cryptographic key rotation; this is not it.

**The reason matters more than the verdict, and the two failure reasons look identical in a table.** `22d5a8f6` (dp ruling, 2026-07-24) appends a "Successor research track" section to `web4-trust-core/README.md`: a derivation-as-law successor for "this crate's **update/decay arithmetic**", gated on "a DerivationSpec reproducing this crate's normative **t3v3 vectors**", closing *"Until then, this crate is the enforced semantics."* That makes the crate the **live enforced surface**, not a superseded one. It therefore fails M1 **because t3v3 update/decay arithmetic is not a §1/§2/§3 primitive** — never because it is awaiting a successor.

**Instrument limitation, recorded because an unreadable surface is not an empty one.** That same ruling names an **off-repo** live derivation surface (`dp-web4/web4-trust-core`, a *repo* distinct from this crate, nothing published to crates.io). Every C-series pass in this repo — not just security's — runs an instrument that structurally cannot see it. Treating it as absent would be the same shape as the silence-charge error the v5 carry exists to prevent. **Flagged forward to the t3-v3 lineage (C270's successor), which owns the subject matter.**

### B′.3 — `web4-policy/`: **M1-FAIL**

Same instrument: **0** on every suite/KEM/AEAD/KDF/COSE/signature token; `verif` = 1, `rotat` = 0. Its single commit in the window (`1fa86e09`) is a `Cargo.lock` refresh pinning `web4-core 0.2.0 → 0.4.0`, machine-generated. Not a security mirror.

### B′.4 — `hub/`: **M1-PASS · M2-CONSUMER (mixed) · M3-DECLINED (evidence, not defendant)**

**M1 — PASS.** Instrument (same form, `grep -v /target/`): `X25519` **13** · `Ed25519|ed25519` **26** · `ChaCha20|chacha` **4** · `HKDF|hkdf` **2** · **`COSE|cose|ciborium|cbor` 0** · `W4-BASE-1|W4-FIPS-1|W4-IOT-1` **0**. Hub implements the W4-BASE-1 KEM/KDF/AEAD triple *by behaviour* while naming **no** suite (`hub/hub-daemon/src/main.rs:186` — "derive the ECDH session key, then ChaCha20-Poly1305"; `hub/hub-lib/src/pair_message.rs:15-16` — "ChaCha20-Poly1305 over an HKDF-derived session key"). **A vocabulary grep returns 0 and closes the gate; the behaviour grep is what opened it.**

**M2 — mixed, and the distinction is the C218/C256 test.** Hub's *transport* crypto is **delegated**: `hub/hub-lib/src/signer.rs:151` states the hub's X25519 ECDH key is "same `web4_core::pair_channel`", and both `hub-lib` and `hub-daemon` declare `web4-core.workspace = true`. Those primitives are already counted at their real definition site (`pair_channel.rs`, the C180 genuine mirror) and are **not** a new site — the `role_extension.rs` ruling, applied consistently. **But `hub/hub-lib/src/envelope.rs` defines its own signing preimage**: `signing_bytes()` → `canonical_signing_bytes()` = `challenge_nonce ++ serialize_canonical(payload)`, with `serialize_canonical` a hand-rolled canonical-JSON serializer (`envelope.rs:174-220`). That is the `attestation.rs` shape (own preimage), not the `role_extension.rs` shape (calls someone else's) — so on the lineage's own distinguishing test it **is** a distinct site. See N4.

**M3 — DECLINED. Argued fresh for security; C294's errors-lens decline is cited as precedent-of-method only, never imported as a verdict.**
Instrument: hub cites exactly **one** `web4-standard/core-spec` document across all of `hub/` — `hub-law-schema.md` (`hub/docs/HUB-LAW.md:18`, `hub/hub-daemon/src/main.rs:370`, `hub/hub-lib/tests/fixtures/hub-law/README.md:53`) — plus one proposal (`proposals/lct-mcp-as-smart-contract.md`). `security-framework.md`: **0 citations**. Suite IDs: **0**.
Under C158 self-scoping, an artifact that *names the specs it implements* is bound to those and not to others by silence; hub names hub-law-schema and does not name security-framework. **Hub is therefore EVIDENCE, not defendant** — nothing below is a charge against hub, and hub's conformance is not assessed.
**Why the decline does not dissolve N4:** N4 is a finding about **`security-framework.md` §1.3's own quantifier**, which needs no defendant. §1.3 says "**All** Web4 signed payloads MUST implement COSE/CBOR" with no scoping predicate. Either that quantifier reaches an in-repo component that depends on the standard's own crate — in which case the MUST has a live counterexample — or it does not, in which case **§1.3's scope is undefined**. Both branches are findings about the spec. The M3 decline chooses neither; it only refuses to name hub the defendant.

### B′.5 — Inward derivation: what *else* in `web4-standard/` independently defines a suite

This is the half no prior pass ran as a derivation. Instrument: `grep -rln "W4-BASE-1\|W4-FIPS-1\|W4-IOT-1" web4-standard/ --include=*.md --include=*.json --include=*.ttl` → **15 files**.

| File | Independent suite definition? | Read by a prior security pass? |
|---|---|---|
| `core-spec/security-framework.md` | the target | — |
| `core-spec/core-protocol.md` | **yes** — full 3-suite table | yes (B-7, B-H2) |
| `protocols/web4-handshake.md` | **yes** — full 3-suite table | yes (B-7, DELTA-1) |
| `registries/initial-registries.md` | **yes** — list form | yes (B-7) |
| `test-vectors/security/security-primitives.json` | **yes** — `sec-001`/`sec-002` field-by-field, **authority** | C31, C68 only |
| `profiles/cloud-service-profile.md` | **yes** — W4-FIPS-1, 6 fields | C31, C68 only (as a "further partial copy") |
| `profiles/edge-device-profile.md` | **yes** — W4-IOT-1, 6 fields | C31, C68 only |
| **`profiles/peer-to-peer-profile.md`** | **yes** — W4-BASE-1, 6 fields | **NEVER — 0 mentions in any audit doc** † |
| **`profiles/blockchain-bridge-profile.md`** | **yes** — W4-BASE-1, 6 fields | **NEVER — 0 mentions in any audit doc** † |

† **Instrument scope, stated because the post-write re-run caught it.** `grep -rl "<profile>" docs/audits/` returns **1** at HEAD — *this document*. The published zero is the pre-write baseline, `grep -rl … docs/audits/ | grep -v C296`, which is the only measurement that answers the question asked ("did a **prior** pass read it?"). Recorded rather than silently corrected: a self-counting grep is the same silent-failing-hypothesis class as N3(a), caught here only because the count was re-run **after** the finding was written ([[feedback_publish_the_instrument]]).
| `QUICK_REFERENCE.md` | partial (BASE-1 prose) | never |
| `INTEGRATION_STATUS.md`, `implementation/sdk/CHANGELOG.md`, `testing/test-vectors/handshakeauth_{cose,jose}.json`, `test-vectors/protocol/core-protocol.json` | referential only | — |

**Nine artifacts independently define a Web4 crypto suite. C256's tracked-sibling table listed seven siblings and none of the four profiles.** The set did not merely fail to grow — it **shrank**: C31 §C-M1 explicitly counted `profiles/cloud-service-profile.md:19` and `profiles/edge-device-profile.md §3` as copies, and they fell out of the tracked table by C108 and stayed out for six consecutive passes. Two profiles were never named at all.

---

## Findings

### C296-N1 — MEDIUM — `blockchain-bridge-profile.md` declares W4-BASE-1 and then sets an encoding W4-BASE-1 forbids

**Routing**: CROSS-TRACK (lands in `profiles/`) — **adjudicate WITH C-M1/B-D1**. **NOT auditor-applicable**: the fix forks on an operator canonicity decision (see below). Do not self-apply.

`profiles/blockchain-bridge-profile.md` §3 declares **`Suite ID: W4-BASE-1`**; its §2 declares **Primary Format: JSON, Canonicalization: JSON Canonicalization Scheme (JCS)**.

`security-framework.md` §1.1 pins W4-BASE-1's `Encoding` column to **COSE**, Status **MUST**. §1.2 restates it: "**Encoding**: COSE (RFC 9052/9053)". §1.3 makes deterministic CBOR per CTAP2 the canonicalization for the MTI path and RFC 8785 JCS the canonicalization for the JOSE path.

Three independent authorities agree the profile is the side out of alignment:
- vector `sec-001` (`security-primitives.json`) asserts `"encoding": "COSE"` for W4-BASE-1;
- `test_security.py:65`/`:76` assert `suite.encoding.value == v["expected"]["encoding"]` — **exact string equality**;
- `test_security.py:90` asserts `SUITE_BASE.encoding == EncodingProfile.COSE` with the docstring *"BASE suite uses COSE encoding (MUST per spec)"*.

**Refutation attempts (refute-by-default):**
- *R1 — "§2 Data Format is the application payload format, not the signature envelope encoding."* **Refuted by the pattern, not by argument.** §2 pairs a format with a **canonicalization scheme**, which is exactly the signing-canonicalization pairing §1.3 defines (JCS for JOSE, CBOR-deterministic for COSE). And the other three profiles align **exactly**: `cloud-service` = W4-FIPS-1 (Encoding JOSE) + JSON/JCS ✔; `edge-device` = W4-IOT-1 (CBOR) + CBOR/CBOR-deterministic ✔; `peer-to-peer` = W4-BASE-1 (COSE) + CBOR/CBOR-deterministic ✔. If §2 were not the signing-encoding surface, 3-of-4 exact alignment would be coincidence.
- *R2 — "blockchain anchoring genuinely needs JSON."* **Refuted as a defence, and it strengthens the finding.** That motivates the *choice*, not the *suite-ID mismatch*. §1.3 already anticipates it — "JOSE/JSON (ES256) is **SHOULD for bridge scenarios**" — the standard **wants** to permit exactly this profile and has no vocabulary to express it: the profile cannot say "W4-BASE-1 with the bridge JOSE allowance," because `Encoding` is a per-suite cell with no override mechanism. So the sharper statement is: **§1.3 grants a bridge allowance that the suite vocabulary cannot express, and the one profile that needs it expresses it by contradicting the suite it names.**
- *R3 — snapshot-presence (C98).* `blockchain-bridge-profile.md` last touched `18209449` (2025-09-11) — frozen through every C-series pass. **This is not new content.** It is net-new *as a finding* because the dimension (profile §2 encoding vs. its declared suite's `Encoding` cell) has never been run: `blockchain-bridge-profile` = **0 mentions across `docs/audits/` excluding this document** (see the † note in §B′.5 on why the exclusion is the honest scope), and no audit doc anywhere charges the profile-encoding dimension. Provenance stated plainly; the finding is first-charge, not first-existence.

**The fork the operator owns** (which is why this is not auditor-applicable): either (a) the profile should name `W4-FIPS-1`, or (b) §1.3's bridge allowance needs an expressible override in the suite vocabulary, or (c) the `Encoding` cell is not binding on profiles — which `test_security.py:90` currently contradicts.

### C296-N2 — MEDIUM — the KDF token: two audit lineages have ratified two different canonical values

**Routing**: CROSS-TRACK / DESIGN-Q — **into the C-M1/B-D1 bundle. Widens standing carry B-7 from a case to a dimension.** Do not self-apply, do not renumber or normalize, and **`initial-registries.md` is NOT charged**.

C31's **B-H1** was a HIGH finding built on one argument: `test_security.py` asserts **exact string equality** on a suite field, the vector is authority, so a spec spelling that differs is a live conformance break. B-7 is that finding's standing carry — and it was scoped to the **KEM** field only. Widening from the case to the dimension (v5), the **KDF field carries the identical contract**: `test_security.py:64` and `:75` assert `suite.kdf == v["expected"]["kdf"]`.

Live token by site:

| Site | KDF token | Instrument |
|---|---|---|
| `security-framework.md` §1.1 (both rows), §1.2 (both suites) | **`HKDF-SHA256`** | `sed -n '16,17p;31p;39p'` |
| `security-primitives.json` `sec-001`/`sec-002` — **authority** | **`HKDF-SHA256`** | `"kdf": "HKDF-SHA256"` |
| SDK `security.py` `SUITE_BASE`/`SUITE_FIPS` — **authority** | **`HKDF-SHA256`** | `kdf="HKDF-SHA256"` |
| `core-protocol.md` §1 (all 3 suites) | `HKDF` | `sed -n '16,21p'` |
| `registries/initial-registries.md` (all 3 suites) | `HKDF` | `sed -n '3,8p'` |
| `profiles/` — all **4** files | `HKDF` | `grep -A9 "Cryptographic Suite"` |
| `protocols/web4-handshake.md` §3 | **no KDF column at all** (5 fields) | `sed -n '20,25p'` — *evidence only, D0* |

**8 sites spell it bare `HKDF`; 3 authorities spell it `HKDF-SHA256`; 1 cannot express it.**

**What the backward audit-grep (v5) changed about this finding.** `grep -rn "bare .HKDF\|KDF token\|KDF spelling" docs/audits/` shows the registries lineage did not *overlook* the bare token — it **installed** it. C70's **B-A6** reads: *"Add the `HKDF` KDF token to `initial-registries.md` Suite IDs… it is currently the only suite definition without a KDF, while `core-protocol.md` §1 and `cipher-suites.md` both carry a KDF column."* It was applied at C71 and re-verified **five consecutive times** — C110, C142, C182, C220, C258 — each publishing the same cell: *"✅ **matches** core-protocol §1 (BASE-1 KDF=HKDF L18, FIPS-1 KDF=HKDF L19)."*

So this is not a typo nobody noticed. **The registries lineage validates its KDF token against `core-protocol.md`; the security lineage validates its against the vector + SDK. Each is internally correct and each is blind to the other's authority.** Five "✅ matches" verdicts were published on a token the security conformance vector rejects by exact-string comparison, and C69's **B-5** — which *added* the `HKDF-SHA256` KDF column to §1.1 — is the very fix that opened the gap.

That is the same shape as C294-N1: **not an absence, but two mutually non-interoperable answers minted by different mechanisms**, and it is precisely the question **C-M1/B-D1** exists to settle (which artifact is the suite-registry SSOT). It supplies a second concrete instance for that flagship, alongside B-7's KEM case.

*`initial-registries.md` is explicitly not charged*: B-A6 was correctly applied against its declared reference, and re-opening it would be re-litigating a consumed guard. The defect is the **absence of a cross-lineage canonical token**, which no single file owns.

### C296-N3 — LOW — two carry instruments have decayed while their verdicts survived

**Routing**: AUTONOMOUS-adjacent (record-keeping inside the audit lineage; no spec file changes). Recorded so the next pass inherits corrected instruments.

**(a) B-7's re-grep is self-scoped and can only confirm itself.** C256's B-7 row reads *"live grep **re-confirms** all divergent"* and then lists exactly the four files the carry already named. A corpus-wide grep at HEAD returns **6 occurrences across 5 files** — the fifth being `profiles/cloud-service-profile.md:19` `P-256ECDH`, which **C31 itself counted** (its C-M1 note: *"Further partial copies: `profiles/cloud-service-profile.md:19` = `P-256ECDH`; `profiles/edge-device-profile.md §3` = the full IOT-1 row… Five files, four distinct W4-FIPS-1 KEM spellings"*). The site is frozen since 2025-09-11, so **nothing moved — the record lost it.** A re-grep scoped to a carry's own enumeration is a hypothesis that cannot fail ([[feedback_enumeration_and_grep_hypotheses]]); it was published as a live corpus measurement for four consecutive passes.
**Corrected B-7 reach: 6 occurrences / 5 files / 4 distinct spellings** (`P-256ECDH` ×2 — `core-protocol.md:19`, `cloud-service-profile.md:19`; `P-256EC` — `web4-handshake.md:23`, *evidence only, D0*; `P-256 ECDH` — `initial-registries.md:6`; `ECDH-P256` ×2 — target L17/L35). Canonical target `ECDH-P256` unchanged.

**(b) B-8's cited path does not exist.** Four audit docs — **C31, C180, C218, C256** — cite the carry site as `implementation/sdk/web4/security.py`. There is no `implementation/` directory at repo root; the file is `web4-standard/implementation/sdk/web4/security.py`. `git log -- implementation/sdk/web4/security.py` returns **empty output for a nonexistent path**, and C256 read that empty result as *"unmoved… 0 commits since C218."* The **verdict happens to be true** (real last touch `759eaefa`, 2026-04-17 — frozen well before C218), but it was produced by a silent-failing instrument that would have reported "unmoved" no matter what the file did ([[feedback_prior_finding_path_provenance]]).

**Neither (a) nor (b) changes any prior verdict.** Both are recorded because the same two instruments are scheduled to run again at C336.

### C296-N4 — INFO — §1.3's `MUST` has no scoping predicate, and the repo holds a live counterexample

**Routing**: DESIGN-Q → **the C-M1/B-D1 bundle**. Not a charge against `hub/` (M3-DECLINED, §B′.4). Not self-applicable.

§1.3: *"**All Web4 signed payloads MUST** implement COSE/CBOR (Ed25519/EdDSA) as mandatory-to-implement (MTI). JOSE/JSON (ES256) is SHOULD for bridge scenarios."* It offers exactly **two** canonicalizations: deterministic CBOR per CTAP2, or JCS canonical JSON (RFC 8785).

`hub/hub-lib/src/envelope.rs` — described in its own module doc as *"the V2 authority primitive for hub HTTP API… Every consequential request must prove **who** is asking and **that** the request hasn't been replayed"* — implements a **third**: `signing_bytes()` (`:174`) → `canonical_signing_bytes()` (`:179`) = `challenge_nonce ++ serialize_canonical(payload)`, where `serialize_canonical` (`:191-220`) is a hand-rolled canonical-JSON serializer. Its own comment (`:103-107`) notes `serde_json` is "canonical-by-default" but that an explicit canonicalizer is used "so the hub doesn't depend on" that. It cites neither CTAP2 nor RFC 8785. `COSE|cose|ciborium|cbor` = **0** across all of `hub/`.

**Why this is a new kind of datapoint, and why it is INFO rather than MEDIUM.** C180-N1 and C218-N1 record web4-core *omitting* COSE — an **absence**, read as "the SDK lags, the spec is correct." This is a **divergence**: an in-repo component that depends on the standard's own crate (`web4-core.workspace = true`) actively **mints a third canonicalization** for its authority primitive. It is a distinct site under the lineage's own test (own preimage, like `attestation.rs`; unlike `role_extension.rs`, which only calls one). But it is filed **INFO, not MEDIUM**, because M3 declined to bind hub, so the finding rests entirely on the spec-side quantifier: §1.3's "All Web4 signed payloads" carries **no scoping predicate** — no conformance-claim condition, no profile condition, no entity-class condition. Either it reaches this component (live counterexample) or it does not (undefined scope). **The auditor does not get to pick; the operator does, and it is the same SSOT question C-M1/B-D1 already holds.**

---

## §C — Fresh-Internal Refute-by-Default Pass

**0 net-new internal contradictions.** Blob-identity preserves C140/C180/C218/C256's clean §C; candidates re-confirmed at their frozen call sites:

- §1.1 table ⟷ §1.2 prose: KEM/Sig/AEAD/Hash/KDF/Encoding token-match for both suites (`ECDSA-P256` table vs `ECDSA with P-256` prose = the long-standing benign wording variant carried from C140 — **not** a finding, and deliberately *not* swept into N2: N2 is about a token under an exact-string conformance assertion, this one is not).
- §1.3 MTI COSE (`crv = 6` / `alg = -8`) ⟷ §1.1 W4-BASE-1 `Encoding = COSE` ⟷ §1.2 COSE RFC 9052/9053: internally consistent. The §1.3 defect found this fire (N4) is a **scope** defect, not an internal contradiction.
- §2.3 rotation prose ⟷ `LCT-linked-context-token.md` §7.3 (frozen): resolves.
- §3.1 ⟷ handshake §6.0.5 / §9 / §6.1 (frozen): all three cites resolve.
- No standalone W4-IOT-1 statement in this file — the DELTA-1 divergence remains corpus-side.

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| **C296-N1** | **MEDIUM** | `blockchain-bridge-profile.md` declares `W4-BASE-1` but sets JSON/JCS; §1.1 pins that suite's `Encoding` to COSE (MUST), and vector `sec-001` + `test_security.py:90` assert it. 3 of 4 profiles align exactly. §1.3 grants a bridge JOSE allowance the suite vocabulary cannot express. | CROSS-TRACK, **adjudicate with C-M1/B-D1**; NOT auditor-applicable |
| **C296-N2** | **MEDIUM** | KDF token: same exact-string conformance contract as the KEM (`test_security.py:64`/`:75`). Security lineage ratifies `HKDF-SHA256` (spec + vector + SDK); registries lineage **installed** bare `HKDF` at C70-B-A6 and published "✅ matches" 5× (C110/C142/C182/C220/C258). Two lineages, two canonical tokens, mutual blindness. Widens B-7 case→dimension. | CROSS-TRACK / DESIGN-Q → C-M1/B-D1; `initial-registries.md` **not** charged |
| **C296-N3** | LOW | Instrument decay: B-7's re-grep is scoped to its own enumeration (real reach 6/5, published 5/4); B-8's cited path does not exist in 4 audit docs, so its "unmoved" verdict came from an empty `git log` on a nonexistent path (verdict true, instrument silent-failing). | Audit-lineage record-keeping; no spec change |
| **C296-N4** | INFO | §1.3's "**All** Web4 signed payloads MUST … COSE/CBOR" has no scoping predicate; `hub/hub-lib/src/envelope.rs` mints a third canonicalization (bespoke canonical JSON, neither CTAP2-CBOR nor RFC 8785 JCS) as its authority primitive, with `cose|cbor` = 0 across hub. Divergence, not absence — unlike C180-N1/C218-N1. | DESIGN-Q → C-M1/B-D1; hub M3-DECLINED (evidence, not defendant) |

**Totals: 0 HIGH, 2 MEDIUM, 1 LOW, 1 INFO — 4 net-new. Zero mutation: no spec, SDK, vector, profile, or hub file was modified this turn.**

- **§A**: 6 C69 + 1 C109 fixes HELD by byte-freeze (blob `2880e643`, identical to C218's and C256's verified blob), 0 regressed; C56 completeness clean. 8 carries STAND, none resolved into a defect; **two (B-7, B-10) had their published reach corrected** — 6/5 and 9/4 respectively.
- **§B**: **EMPTY for the 2nd consecutive delta** — 0 of 7 tracked siblings moved; the 3 `web4-standard/` movers are all off-subject.
- **§B′**: outward set re-derived and *corrected* (2 named crates had been bucketed into "misc") — `web4-trust-core/` M1-FAIL **on subject matter**, `web4-policy/` M1-FAIL, `hub/` **M1-PASS / M2-mixed / M3-DECLINED**. Inward set derived for the first time: **9 artifacts independently define a suite; the tracked table listed 7 siblings and none of the 4 profiles; 2 profiles had never been named in any audit doc, corpus-wide.**
- **§C**: 0 net-new internal contradictions — the target itself is clean for the **5th consecutive delta**.

---

## Key Adjudication

1. **The mirror set had been shrinking, and nobody was measuring the set itself.** C31 counted the profile copies; by C108 they were gone from the tracked table and they stayed gone for six passes. Every pass after that re-ran an *inherited* list and correctly reported it clean. The v7 carry says re-derive from subject matter — the operative word is **re-derive**, and the failure mode it guards is not "the set failed to grow" but "the set silently contracted while each pass reported a faithful zero over what remained." **Both C296 MEDIUMs live in files the set used to contain.**

2. **A backward grep turned a spelling nit into a governance finding.** N2 began as "8 sites say `HKDF`, the spec says `HKDF-SHA256`" — a hygiene item worth a LOW at best, landing as a charge against `initial-registries.md`. `grep docs/audits/` **backward** (v5) found C70-B-A6 had *deliberately installed* the bare token and that five subsequent registries deltas published "✅ matches" on it. The real finding is that **two audit lineages ratified two different canonical tokens against two different authorities and neither ever read the other**, which is a C-M1/B-D1 instance, not a typo — and it exonerates the file the naive version would have charged. The backward grep did not kill the finding; it relocated and strengthened it.

3. **Declining M3 is not declining the finding.** Hub failed the admission test cleanly (1 core-spec citation, and it is not this spec; 0 suite tokens), so hub is evidence. The temptation is then to drop the envelope observation — but N4 never needed hub to be bound: it is a defect in **§1.3's own quantifier**, which has no scoping predicate, and it holds on both branches of the reach question. M3 asks about reach, not about whether admitting would indict ([[feedback_admission_criterion_not_verdict]]); answering "no defendant" and "no finding" as if they were the same question is how a self-sealing gate hides a spec defect behind a jurisdictional ruling.

4. **The pass that would have looked identical.** With `web4-core/` at 0 commits, §B empty for the second delta running, and the target byte-frozen for 33 days, the inherited method produces a clean 5th consecutive no-op — defensible, cheap, and wrong. The only thing separating this pass from that one is that the mirror set was re-derived instead of re-read. That is now the third consecutive lineage (C280 → C292 → C294 → C296) where the defect was **the inherited mirror set itself**, and the pattern is no longer incidental: **on a frozen target, the set is the audit.**

---

## Next-Turn Carry

- **C297 `security-framework.md` remediation slot = NO-OP.** All 4 findings are CROSS-TRACK / DESIGN-Q and land **outside** the target; 0 AUTONOMOUS findings inside the file. **Do NOT manufacture an edit to `security-framework.md`.** Rotation advances.
- **N1 + N2 + N4 bundle into the standing C-M1 ≡ B-D1 operator memo and must be adjudicated together** — all three are instances of the one unanswered question (which artifact is the crypto-suite/encoding SSOT, and what is binding on whom). N2 additionally supplies the *why* for the two-lineage split that C70-B-A6 and C69-B-5 jointly created. **Do not self-apply any of them.**
- **Corrected carry reach, to be inherited verbatim (do NOT re-derive as net-new):** **B-7** = 6 occurrences / 5 files / 4 spellings (adds `profiles/cloud-service-profile.md:19`); **B-10** = 9 occurrences / 4 files (adds `protocols/web4-lct.md:241`, evidence-only under D0); **B-8** real path = `web4-standard/implementation/sdk/web4/security.py` (last touch `759eaefa`, 2026-04-17).
- **Tracked-sibling table for the next security delta (C336) — replace the 7-sibling list with the 9-artifact inward set** from §B′.5, i.e. add `profiles/{blockchain-bridge,cloud-service,edge-device,peer-to-peer}-profile.md` and keep `test-vectors/security/security-primitives.json` in the table rather than in prose. **The list must be re-derived, not re-read** — that is the finding of this pass, and re-reading this corrected list would reproduce it.
- **`hub/` guard for the next security delta**: M3-DECLINED on C158 self-scoping (1 core-spec citation, `hub-law-schema.md`; 0 suite tokens). **Do not re-run the hub security gate unless hub gains a `security-framework.md` citation, a suite-ID token, or a conformance claim.** If it does, M2's split verdict applies: transport crypto is delegated to `web4_core::pair_channel` (already counted at C180), only `envelope.rs`'s own preimage is a distinct site.
- **`web4-trust-core/` guard**: M1-FAIL on subject matter (0 crypto primitives; `rotate()` is trust-tensor re-binding, not §2.3 key rotation). Re-gate only if it gains a §1/§2/§3 primitive. **Separately flagged forward to the t3-v3 lineage**: dp's `22d5a8f6` ruling names an **off-repo** live derivation surface that no in-repo C-series instrument can see — an instrument limitation every lineage inherits, recorded here because an unreadable surface is not an empty one.
- **`role_extension.rs` non-re-mining guard (C256) carried forward, re-tested not presumed**: `web4-core/` moved 0 commits this interval, so it gained neither a §1/§2/§3 primitive nor its own signing preimage. Guard stands unconsumed.
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: **DESIGN-Q** — C-M1 ≡ B-D1 SSOT (now carrying C180-N1, C218-N1, C140-DELTA-1, **and C296-N1/N2/N4**); B-3 authz basis (VCs vs SAL/R6); B-9/B-M2 rotation semantics; B-H2/B-11 W4-IOT-1 + AES-CCM. **CROSS-TRACK** — B-7 (corrected reach); B-8 (corrected path); B-10 (corrected reach); B-L6/B-L7. **Do not self-apply any.**
- **D0 (`protocols/` cluster) still operator-gated.** This pass **read** `web4-handshake.md` and `web4-lct.md` as evidence under the reviewer-approved split and laid **no finding** against either. That split should be the standing posture: D0 gates routing and remediation, not reading.
- **Rotation advances.** Next slot = C298 per the fixed order; next `security-framework.md` delta ≈ **C336**.

---

*Audit produced under Autonomous Session Protocol v2 — slot `web4-20260731-020400`, LEAD voice. Read-only: no spec, SDK, vector, profile, or implementation file was modified this turn. Remediation (C297) is the next alternation turn and is a declared NO-OP (0 AUTONOMOUS findings inside the target).*
