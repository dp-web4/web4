# C31 — `security-framework.md` First-Pass Internal-Consistency + Cross-Spec Audit

**Audit ID**: C31
**Target**: `web4-standard/core-spec/security-framework.md` (97 lines) — the Web4 Security Framework (cryptographic suites, key management, authentication/authorization)
**Date**: 2026-06-04
**Auditor**: autonomous web4 session (legion, slot `120000`), v2 protocol
**Type**: First-pass internal-consistency audit + cross-spec consistency audit
**Prior coverage**: none — `security-framework.md` is genuinely un-audited. It is the **oldest core-spec normative file** (last substantive git mod 2025-09-11) and the most foundational of the three remaining un-audited files (the two `r6-*.md` files are deferred as a later pair). Several known carries land here: the **W4-IOT-1 orphan** (`carry-cross-track`) and the **P-256 spelling** (`=C27-L2`) — both re-confirmed against SDK + conformance-vector authority below rather than re-litigated.
**Method note**: executed as a multi-agent audit — five parallel lens-finders (internal consistency / cross-spec core-protocol+ISP / cross-spec lct+token / cross-spec handshake §6 / SDK+test-vector triangulation), each followed by an adversarial verifier instructed to *refute by default*. 24 candidate findings → **24 survived verification, 0 fully refuted**, but the adversarial pass **corrected 8 overstated severities/dispositions** and surfaced a third registry copy the finders missed. Every surviving finding was re-verified by hand against the live files.

---

## Scope & Methodology

`security-framework.md` declares itself (line 3) as the document that *"defines the security framework for the Web4 standard … cryptographic primitives, key management, authentication and authorization."* Its crypto-suite definitions (W4-BASE-1, W4-FIPS-1) are cited or mirrored by `core-protocol.md`, `lct-capability-levels.md`, `LCT-linked-context-token.md`, `web4-handshake.md §6`, and `registries/initial-registries.md`, and are pinned by the SDK (`implementation/sdk/web4/security.py`) and conformance vectors (`test-vectors/security/security-primitives.json`). The audit proceeds in the standard three passes:

1. **Internal-consistency pass** (§A) — does the document agree with itself (§1.1 suite table vs. §1.2 algorithm specs vs. §1.3 canonicalization; normative-keyword discipline; abstract-vs-body)?
2. **Cross-spec pass** (§B) — does it agree with the specs, registries, SDK, and vectors that surround it?
3. **Primitive-clustered pass** (`auditor-blindspot-pattern`, §C) — re-read through the *crypto-suite-registry SSOT* and *key-rotation-identity* lenses, hunting cross-section / cross-spec contradictions a section-by-section read misses.

**Severity**: **HIGH** = correctness/normative contradiction, esp. a spec statement contradicting a conformance vector/SDK; **MEDIUM** = cross-spec divergence needing reconciliation; **LOW** = hygiene/wording/naming; **INFO** = forward-awareness or positive confirmation, no action.

**Routing**: **AUTONOMOUS** (a future remediation turn can fix it inside `security-framework.md` without a design decision); **DESIGN-Q** (requires an operator-level canonicity decision; recorded, *not resolved here* per binding condition 1); **CROSS-TRACK** (fix/verify lands in another file — not edited this turn).

**Binding conditions honored**: BC#12 (vector-count recount at audit-write time — `security-primitives.json` carries **12 vectors `sec-001..sec-012`**, of which **6 bind to `security-framework.md`** [sec-001/002/007/008/009/011] and 6 to `data-formats.md` [sec-003/004/005/006/010/012] — see B-L4). BC#13 (header date-staleness is INFO unless coupled to a normative date-dependency — here the header has *no version and no date at all*; recorded INFO, see C-I6). Anti-padding: the 3rd pass surfaced a **genuine** cross-section contradiction (no canonical crypto-suite registry — C-M1); the six INFO items are honest positive confirmations / negative results, explicitly labelled, not filler.

---

## Findings Summary

| ID | Sev | Routing | One-line |
|----|-----|---------|----------|
| **B-H1** | HIGH | AUTONOMOUS | W4-FIPS-1 KEM spelling (`P-256` / `ECDH with P-256`) contradicts conformance vector `sec-002` + SDK canonical token **`ECDH-P256`** |
| **B-H2** | HIGH | DESIGN-Q | `core-protocol.md` carries a third suite **W4-IOT-1** + malformed `P-256ECDH` token, absent from SDK/vectors/`security-framework.md` (W4-IOT-1 orphan carry) |
| **C-M1** | MED | DESIGN-Q | **No file is the canonical crypto-suite registry** — ≥3 divergent copies (`security-framework §1.1`, `core-protocol §1`, `registries/initial-registries.md`) |
| **B-M2** | MED | DESIGN-Q | §2.3 "update the Web4 Identifier to use the new public key" contradicts LCT §7.3 stable-subject-DID rotation model (correctness trap for `did:web4:key`) |
| **B-M3** | MED | AUTONOMOUS | §2 rotation under-specifies vs. LCT §7.3 lifecycle and gives **no cross-reference** to it |
| **A-L1** | LOW | AUTONOMOUS | §1.3 labels JOSE/JSON **`OPTIONAL/SHOULD`** — conflated RFC 2119 keywords; SHOULD everywhere else |
| **A-L2** | LOW | AUTONOMOUS | §1.1 "MUST NOT be **negotiated** as MTI" misuses MTI as a runtime-negotiable property |
| **A-L3** | LOW | AUTONOMOUS | Abstract promises "a comprehensive analysis of security considerations" the body never delivers |
| **A-L4** | LOW | AUTONOMOUS | §1.1 table FIPS KEM `P-256` (a curve) vs §1.2 prose `ECDH with P-256` (the mechanism) — internal half of B-H1 |
| **B-L5** | LOW | CROSS-TRACK | LCT example `binding_proof` labels `cose:ES256:...` pair a COSE envelope with the non-MTI ES256 alg (should be `cose:EdDSA`) |
| **B-L6** | LOW | CROSS-TRACK | `security-primitives.json` declares two specs and mixes crypto-suite vectors with W4ID/VC vectors |
| **B-L7** | LOW | CROSS-TRACK | `data-formats.md` names 3 W4ID methods (key/web/**device**) but SDK `KNOWN_METHODS` + vectors cover only key+web |
| **C-I1** | INFO | — | W4-BASE-1 (MTI suite) triangulates **token-for-token** across spec / SDK / vector — triangulation method confirmed working |
| **C-I2** | INFO | — | Key algorithms (Ed25519 / P-256) referenced consistently across `security-framework`, LCT, lct-cap-levels |
| **C-I3** | INFO | — | Key generation/storage tiers (§2.1/§2.2) agree with the LCT entity-generated-key + hardware-anchor model |
| **C-I4** | INFO | — | §1.3 cross-refs to handshake §6.0.3/§6.0.4 **resolve correctly and content-match**; MTI=COSE/SHOULD=JOSE split is identical in both |
| **C-I5** | INFO | — | `inter-society-protocol.md` defines no suites — correct deference pattern (negative result); the model the duplicated files should follow |
| **C-I6** | INFO | — | Header carries no version field and no date (corpus-wide hygiene; ~14/25 core-spec files lack a header — `security-framework.md` is *not* an outlier) |

8 actionable (2H / 2M-design + 1M-auto / 4L) split **5 AUTONOMOUS / 3 DESIGN-Q / 3 CROSS-TRACK**, plus 6 INFO.

---

## §A — Internal-Consistency Findings

### A-L1 (LOW, AUTONOMOUS) — JOSE/JSON status conflates `OPTIONAL` and `SHOULD`

§1.3 line 44 reads: *"JOSE/JSON (ES256) is **OPTIONAL/SHOULD** for bridge scenarios."* `OPTIONAL` (= `MAY`, truly elective) and `SHOULD` (a recommendation) are distinct RFC 2119 conformance levels; the dual label is internally ambiguous. The canonical value is unambiguously `SHOULD` in **five** other places — the same file's §1.1 suite table (line 17, `JOSE | SHOULD`), the §1.3 subsection heading itself (line 52, `#### JOSE/JSON (SHOULD)`), and the cross-referenced handshake §6.0.2 (line 129), §3 table (line 23), and §12 summary (line 235). Line 44 is the lone anomaly.

- **Routing**: AUTONOMOUS. Drop `OPTIONAL/` so line 44 reads `JOSE/JSON (ES256) is SHOULD for bridge scenarios.`
- *Severity note*: two finders rated MEDIUM; the adversarial pass moderated to LOW — it is a pure intra-file wording inconsistency, not a cross-spec divergence, and a careful reader can resolve it from the five concordant statements.

### A-L2 (LOW, AUTONOMOUS) — "MUST NOT be negotiated as MTI" misuses MTI as a negotiable property

§1.1 line 22: *"Other suites MAY be offered but MUST NOT be negotiated as MTI."* MTI (mandatory-to-implement) is a **static designation the spec assigns** — line 20 already fixes W4-BASE-1 as the sole MUST suite and line 26 labels it *"(Mandatory to Implement)"*. Runtime negotiation selects which suite peers *use*, not which is MTI, so applying the negotiation verb to a non-negotiable property is self-incoherent. The spec's own correct usage at line 44 (*"implement COSE/CBOR … as mandatory-to-implement (MTI)"*) confirms MTI is meant as a fixed property.

- **Routing**: AUTONOMOUS. Reword, e.g. *"Other suites MAY be offered but MUST NOT be required in place of the mandatory W4-BASE-1 baseline."* No behavioral change (W4-BASE-1 is mandatory regardless).

### A-L3 (LOW, AUTONOMOUS) — Abstract promises a "comprehensive analysis of security considerations" the body omits

The opening abstract (line 3) claims the document covers *"… key management, authentication and authorization, and a comprehensive analysis of security considerations."* The body contains only §1 Cryptographic Suites, §2 Key Management, §3 Authentication and Authorization. There is **no Security Considerations / threat-analysis section** anywhere in the file (the only `risk` mention is incidental, inside §2.3 Key Rotation). The abstract's scope claim is internally unmet.

- **Routing**: AUTONOMOUS. Either trim the abstract to match actual content, or add a Security Considerations section. *(Note: the deferred `r6-security-analysis.md` already supplies an R6-scoped threat model; a future operator decision may choose to home a security-considerations section here vs. there — but trimming the over-claim is autonomous either way.)*

### A-L4 (LOW, AUTONOMOUS) — §1.1 table vs §1.2 prose disagree on the W4-FIPS-1 KEM

Within the same document, the §1.1 suite table (line 17) lists the W4-FIPS-1 KEM as bare **`P-256`** (a *curve*, not a key-agreement mechanism), while §1.2 (line 35) calls it **`ECDH with P-256`** (the actual KEM). The W4-BASE-1 KEM cell correctly names a mechanism (`X25519`), so the FIPS row naming a bare curve is the anomaly. This is the **internal-consistency half of B-H1** and is fixed by the same edit (converge on the vector/SDK token `ECDH-P256`, with `(ECDH with P-256, FIPS 186-4)` as the §1.2 expansion).

- **Routing**: AUTONOMOUS. Resolve together with B-H1.

---

## §B — Cross-Spec Findings

### B-H1 (HIGH, AUTONOMOUS) — W4-FIPS-1 KEM spelling contradicts the conformance vector and SDK ⭐ flagship

`sec-002` is a suite-**definition** conformance vector that pins the exact KEM identifier string an implementation must return for W4-FIPS-1:

| Source | W4-FIPS-1 KEM token |
|---|---|
| `security-primitives.json` sec-002 (line 28) — **authority** | **`ECDH-P256`** |
| SDK `security.py:117` (`SUITE_FIPS`) — **authority** | **`ECDH-P256`** |
| `security-framework.md` §1.1 table (line 17) | `P-256` |
| `security-framework.md` §1.2 prose (line 35) | `ECDH with P-256` |

The token `ECDH-P256` appears **nowhere** in core-spec. `test_security.py:71` asserts **exact string equality** (`suite.kem == v["expected"]["kem"]`), so this is a literal-identifier contract, not a loose match. Per **test-vectors-as-authority**, the spec prose is the side out of alignment: an implementer reading §1.1/§1.2 would emit `"P-256"` and fail `sec-002`.

Decisive control for HIGH (not LOW shorthand): **every other cell** in §1.1 matches the vector token exactly — W4-BASE-1 KEM `X25519`, FIPS Sig `ECDSA-P256`, AEAD, Hash — proving the column functions as the **identifier registry**, not human prose. The FIPS KEM cell is the lone deviation.

- **Routing**: AUTONOMOUS. Change the §1.1 KEM cell (and §1.2 token) to `ECDH-P256`, keeping `(ECDH with P-256, FIPS 186-4)` as a parenthetical. SDK + vector already agree on the canonical value, so no operator decision is needed — the spec simply trails.
- *Severity note*: this is the C-series flagship pattern — a spec statement fails its own conformance vector (cf. C18-H3). Upheld HIGH after attempted refutation.

### B-H2 (HIGH, DESIGN-Q) — `core-protocol.md` carries an orphan third suite W4-IOT-1 + a malformed FIPS KEM token

`core-protocol.md` §1 (lines 18–20) lists **three** suites: W4-BASE-1 (MUST), W4-FIPS-1 (SHOULD), and **W4-IOT-1 (MAY)** (`X25519 / Ed25519 / AES-CCM / SHA-256 / HKDF / CBOR`). `security-framework.md`, the SDK `CryptoSuiteId` enum (`security.py:63-64`), the `SUITES` dict (`125-128`), and the conformance vectors (only `sec-001`/`sec-002`) all define **only two** suites. W4-IOT-1 is therefore an **orphan** with no SDK type, no conformance vector, and no `security-framework.md` entry — *though* it **is** independently and fully specified in `profiles/edge-device-profile.md §3` (same six fields), so it is a real, used suite, not a phantom. Separately, `core-protocol.md:19` spells the FIPS KEM **`P-256ECDH`** — a third, malformed (missing-separator) variant matching neither `security-framework.md` nor the canonical vector token `ECDH-P256`.

- **Routing**: DESIGN-Q (forks on operator canonicity). Either (a) **add** W4-IOT-1 to the SDK + vectors + `security-framework.md` (recognizing the edge-device profile uses it), or (b) **remove** it from `core-protocol.md` if MAY-tier suites are intentionally out of the conformance-tested set. The `P-256ECDH` typo in `core-protocol.md` is fixed downstream of the C-M1 canonical-token decision (CROSS-TRACK to that file). Re-confirms the `W4-IOT-1 orphan` and `P-256 spelling (=C27-L2)` carries against SDK+vector authority.

### B-M2 (MEDIUM, DESIGN-Q) — §2.3 key-rotation "update the identifier" contradicts the LCT §7.3 rotation model

§2.3 (line 78): *"The key rotation process involves generating a new key pair and **updating the entity's Web4 Identifier to use the new public key**."* This contradicts the authoritative rotation model in `LCT-linked-context-token.md §7.3` (lines 470–481), which **keeps the identifier stable** (*"Same subject DID"*) and instead creates a **new LCT** (new `lct_id` derived from the new `binding_proof` per §3.3) whose `lineage` points to the parent, with a 24–48h overlap window, before retiring the parent as *"superseded"* (§7.4 line 490).

The contradiction is a genuine **correctness trap** for the `did:web4:key` method: `data-formats.md §1.2` (line 29) says that method's `method-specific-id` **is** a public key (*"self-certifying"*), so changing the key necessarily **mints a new identifier** — it cannot "update" an existing one in place, and the old W4ID (and every relationship/credential referencing it) is orphaned. Notably the LCT subject example (line 65) is literally `did:web4:key:z6Mk…`, the exact case where "Same subject DID" is unachievable on key change. §2.3 acknowledges none of this.

- **Routing**: DESIGN-Q. The canonical rotation semantics (mutate-identifier vs. stable-subject-DID/new-LCT) and the `key`-method-subject behavior are an operator decision; the LCT spec is the more developed model and is the likely winner, but `security-framework.md` is the document titled "Key Management … Rotation" and is what implementers read first.
- *Severity note*: one finder rated HIGH; moderated to MEDIUM — it is a contradiction between two normative **prose** sections (plus an example), not a contradiction of a conformance vector/SDK.

### B-M3 (MEDIUM, AUTONOMOUS) — §2 rotation under-specifies and gives no cross-reference to LCT §7.3

Distinct from the semantic clash in B-M2: §2.3 describes rotation in a single generic sentence and **never references** the LCT spec's concrete rotation lifecycle (new LCT + new binding; `lineage` parent with `reason: "rotation"` from the enum `genesis|rotation|fork|upgrade`; the 24–48h dual-validity overlap; relationship migration; retire parent as `superseded`). The whole file contains zero mentions of `lineage`/`superseded`/`overlap`/LCT. Because §2 is the document titled "Key Management," readers treat it as authoritative even though it under-specifies relative to LCT §7.3.

- **Routing**: AUTONOMOUS — and the *autonomous-actionable companion* to the B-M2 DESIGN-Q. The file **already uses this exact deference pattern** at §1.3 (lines 50/55: *"See web4-handshake.md Section 6.0.3"*), so adding *"See `LCT-linked-context-token.md §7.3` for the normative rotation lifecycle"* is a routine in-file edit needing no design decision. Applying B-M3 reduces the B-M2 contradiction surface even before the DESIGN-Q resolves.

### B-L5 (LOW, CROSS-TRACK) — LCT example `binding_proof` labels use the non-MTI ES256 algorithm

§1.3 makes COSE/CBOR with **Ed25519/EdDSA** the MTI signature profile (line 48: *"Ed25519 with `crv: Ed25519` and `alg: EdDSA`"*); JOSE/ES256 is only SHOULD. Yet the LCT examples label signatures **`cose:ES256:...`** — a COSE envelope tag paired with the ES256 (ECDSA-P256) algorithm, the non-MTI one — at `lct-capability-levels.md` lines 114/267/363/463/525 (line 114 is the Level 1 *software-key* binding, which §2.3 there says is "Ed25519 or P-256") and `LCT-linked-context-token.md:169`. The MTI-consistent label would be `cose:EdDSA:...` (cf. the correct `cose:Sig_structure` at `LCT-linked-context-token.md:72`).

- **Routing**: CROSS-TRACK. The defective labels live in `lct-capability-levels.md` and `LCT-linked-context-token.md`, not in `security-framework.md`. Example placeholder strings only (all `…`), no normative text or vector contradicted — hence LOW.

### B-L6 (LOW, CROSS-TRACK) — `security-primitives.json` mixes two specs' vectors under one "security" name

The vector file's `spec` field (line 4) names **both** `security-framework.md` *and* `data-formats.md`, and its 12 vectors span two ownership domains: `sec-001/002/007/008/009/011` exercise crypto-suite + key-policy material owned by `security-framework.md`, while `sec-003/004/005/006` (W4ID/DID parse), `sec-010` (pairwise W4ID derivation), and `sec-012` (Verifiable Credential JSON-LD) exercise types defined in `data-formats.md` (§1 ABNF, §2 VC, §4 pairwise derivation). A `security-framework.md` conformance run would legitimately consume only **6 of the 12** vectors. Ownership is *already* unambiguous (each spec owns its types) — this is purely a file-organization concern, not a contradiction.

- **Routing**: CROSS-TRACK. Optional: split the data-formats vectors into their own file, or annotate per-vector which spec each binds to. Lands entirely in the test-vectors artifact.

### B-L7 (LOW, CROSS-TRACK) — `data-formats.md` names 3 W4ID methods but SDK + vectors cover only 2

`data-formats.md §1.2` (lines 29–31) defines three methods — `key`, `web`, and **`device`** (anchored to `multi-device-lct-binding.md`). The SDK `KNOWN_METHODS` frozenset (`security.py:168`) is `{"key","web"}` only, and the vectors test only `key` (sec-003) and `web` (sec-004); `is_known_method` returns `False` for a valid `did:web4:device:…`. This is **spec-conformant** (data-formats.md:27 says the method list is non-exhaustive/extensible and unrecognized methods MUST be treated as *unsupported*, not *malformed*; the W4ID regex still parses `device`), so it is staleness/incompleteness, not a violation.

- **Routing**: CROSS-TRACK. The canonical method list is owned by `data-formats.md`; remediation (add a `device` vector and/or extend `KNOWN_METHODS` once the device method stabilizes) lands in the SDK + test-vectors track.

---

## §C — Primitive-Clustered Pass (`auditor-blindspot-pattern`)

Re-reading through the *crypto-suite-registry SSOT* and *key-rotation-identity* lenses surfaced one genuine root-cause contradiction (C-M1) that the section-by-section read sees only as scattered symptoms, plus the confirmations/observations that bound the audit's coverage.

### C-M1 (MEDIUM, DESIGN-Q) — No file is the canonical crypto-suite registry; ≥3 divergent copies exist

This is the **root cause** of B-H1, B-H2, A-L4, and the FIPS-KEM spelling spread. The cryptographic-suite table is defined **from scratch in at least three places, none pointing at another as authoritative**:

| Location | Suites listed | FIPS KEM spelling | Columns |
|---|---|---|---|
| `security-framework.md §1.1` | BASE-1, FIPS-1 | `P-256` | …+`Status` |
| `core-protocol.md §1` | BASE-1, FIPS-1, **IOT-1** | `P-256ECDH` | …+`KDF`, status in Suite-ID cell |
| `registries/initial-registries.md` (`## Suite IDs`) | BASE-1, FIPS-1 | `P-256 ECDH` | list form |

(Further partial copies: `profiles/cloud-service-profile.md:19` = `P-256ECDH`; `profiles/edge-device-profile.md §3` = the full IOT-1 row; `web4-handshake.md §3` = `P-256EC`.) Five files, **four** distinct W4-FIPS-1 KEM spellings, and an inconsistent suite count.

- **Routing**: DESIGN-Q. The operator must designate the canonical registry. A dedicated `registries/initial-registries.md` is the IETF-conventional SSOT for suite-ID registries (arguably more natural than `security-framework.md`), in which case both core-spec files (and the profiles) should *reference* it rather than re-list partial copies. Whatever is chosen, the canonical W4-FIPS-1 KEM token should be `ECDH-P256` (per B-H1's SDK+vector authority) and the W4-IOT-1 inclusion question (B-H2) resolves here.
- *Method note*: the finders initially framed this as a two-way `security-framework`-vs-`core-protocol` choice; the adversarial pass caught the **third** copy in `registries/initial-registries.md`, making it a ≥3-way SSOT decision. Recorded honestly.

### Positive confirmations & negative results (INFO — coverage, no action)

- **C-I1** — **W4-BASE-1 (the MTI suite) triangulates token-for-token** across `security-framework.md` (§1.1/§1.2), SDK `SUITE_BASE` (`security.py:105-113`), and vector `sec-001`: `X25519 / Ed25519 / ChaCha20-Poly1305 / SHA-256 / HKDF-SHA256 / COSE`. The suite that most needs to be exact *is* exact; this isolates the W4-FIPS-1 KEM as the **sole** substantive prose/vector divergence and confirms the triangulation method works.
- **C-I2** — Key algorithms agree: `security-framework` (Ed25519 MUST / ECDSA-P256 SHOULD) ↔ `LCT-linked-context-token.md:224` ("Ed25519 or P-256") ↔ `lct-capability-levels.md:96,480`. Ed25519-primary / P-256-secondary throughout.
- **C-I3** — Key generation/storage (§2.1 "entities MUST generate their own key pairs"; §2.2 HSM > Secure Enclave/TEE > Encrypted) agree with the LCT entity-generated-key model (`LCT §3.1/§3.2`, society never sees the private key) and the hardware-anchor tier (`lct-capability-levels.md §2.7` Level 5 `key_storage: "tpm"`).
- **C-I4** — §1.3's cross-references **resolve correctly**: `web4-handshake.md` (at `protocols/web4-handshake.md`) §6.0.3 "COSE/CBOR Profile (MUST)" (line 132) and §6.0.4 "JOSE/JSON Profile (SHOULD)" (line 143) exist and content-match (COSE alg=-8 EdDSA, crv=6 Ed25519; JOSE JCS RFC 8785, alg ES256). The MTI=COSE / SHOULD=JOSE split is stated identically in both documents. *(Minor: the bare `web4-handshake.md` reference omits the `protocols/` subdir — `security-framework.md` is in `core-spec/`; a path-precision nicety, not a defect.)*
- **C-I5** — `inter-society-protocol.md` defines **no** crypto suites (uses crypto only operationally, e.g. "generate an Ed25519 keypair"). It is the **correct deference pattern** — neither a registry nor a divergent copy — and the model the duplicated files (C-M1) should follow once an SSOT is designated.
- **C-I6** — The header (lines 1–3) is a title + one-paragraph abstract with **no version field and no date**. Per BC#13 this is INFO. It is *not* an outlier: surveying core-spec headers, ~14 of ~25 files carry no version/date header and the rest use at least four competing formats. Header-format canonicity is a corpus-wide hygiene question, not a `security-framework.md`-specific gap.

---

## Disposition Ledger (for the next remediation turn)

**AUTONOMOUS (5)** — fixable inside `security-framework.md` alone, no design decision:
- **B-H1 + A-L4** (one edit): W4-FIPS-1 KEM → `ECDH-P256` in §1.1 table and §1.2 token (keep `(ECDH with P-256, FIPS 186-4)` parenthetical). *Pre-finalization BC#5 corpus sweep mandatory* — confirm the token choice against `security-primitives.json`/`security.py` before writing.
- **A-L1**: drop `OPTIONAL/` from §1.3 line 44.
- **A-L2**: reword §1.1 "MUST NOT be negotiated as MTI".
- **A-L3**: trim the abstract's "comprehensive analysis of security considerations" claim (or add the section).
- **B-M3**: add a `See LCT-linked-context-token.md §7.3` deference in §2.3 (companion to the B-M2 DESIGN-Q).

**DESIGN-Q (3)** — operator canonicity, *recorded not resolved*:
- **C-M1**: canonical crypto-suite registry (≥3-way: `registries/initial-registries.md` vs `security-framework.md §1.1` vs `core-protocol.md §1`) — the root cause.
- **B-H2**: W4-IOT-1 inclusion (add to SDK/vectors/`security-framework.md` vs remove from `core-protocol.md`) — couples to C-M1.
- **B-M2**: canonical key-rotation semantics (mutate-identifier vs stable-subject-DID/new-LCT) + `did:web4:key`-subject behavior — couples to LCT §7.3.

**CROSS-TRACK (3)** — fix lands in another artifact:
- **B-L5**: `cose:ES256:...` → `cose:EdDSA:...` example labels in `lct-capability-levels.md` + `LCT-linked-context-token.md`.
- **B-L6**: split/annotate `security-primitives.json` by owning spec.
- **B-L7**: add a `device`-method vector / extend SDK `KNOWN_METHODS` once the method stabilizes (owned by `data-formats.md` + SDK).
- *(downstream of C-M1)*: normalize the `P-256ECDH` / `P-256EC` / `P-256 ECDH` tokens in `core-protocol.md`, `cloud-service-profile.md`, `registries/initial-registries.md`, `web4-handshake.md §3` to the canonical `ECDH-P256` once the SSOT is chosen.

---

*Audit produced under Autonomous Session Protocol v2 — exit #150, slot `120000`, LEAD voice. Read-only: no spec, SDK, or test-vector files were modified this turn. Remediation is the next alternation turn.*
