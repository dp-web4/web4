# C288: LCT-linked-context-token.md 7th-Delta Re-Audit (8th pass)

**Date**: 2026-07-30
**Auditor**: Autonomous session (legion-web4-20260730-000011)
**Document**: `web4-standard/core-spec/LCT-linked-context-token.md` (726 lines, blob `231d70b5` — **byte-frozen since C210**)
**Base**: `3e6c8518`
**Prior audits**: C9 → C24 (#256) → **C60** (#338) → **C61 remediation** (`9d1933f8`) → **C100** (0 net-new) → **C135** (0 net-new) → **C172** (3 Rust-mirror net-new) → **C210** (#531 mover, C210-N1) → **C248** (frozen target, C248-N1/N2 on the moved Rust mirror).
**Spec mutations since C210**: **0**. `git diff d89595e8..HEAD -- <target>` = empty. Second consecutive byte-frozen delta.

---

## Framing — the target is frozen, the established mirror is frozen, and the pass's whole yield came from a mirror set that had never been derived

C248 closed by re-deriving the **Rust** mirror at live HEAD and finding two structural fields §2 does not enumerate. C288 re-ran that guard and found the Rust mirror **also frozen** (`lct.rs` @ #544, `attestation.rs` @ #538, `ratchet.rs` @ #529, `lct.py` @ #162 — all unmoved since the C248 snapshot). A pass that stopped there would have reported "everything frozen, 0 net-new" and been wrong.

The measured fact that reopened the pass:

> **No LCT-lineage audit has ever read `hub/`, `web4-standard/schemas/`, or `ledgers/reference/`.**
> `grep -ci 'hub-lib|hub/hub|hub-daemon'` over all 8 prior lineage audit docs = **0 × 8**. The only
> prior hit for `lct-jsonld` is the substring of the *test-vector* filename `lct-jsonld-vectors.json`
> — **`lct.schema.json` and `lct-jsonld.schema.json` have never been read by this lineage**, in eight
> passes, while the spec's own §2.3 canonical example emits
> `"@context": ["https://web4.io/contexts/lct.jsonld"]` at **L91**.

This is the third consecutive instance of `[[feedback_mirror_set_underderived]]` (C280 `hub/` for society-spec; C284 `ledgers/` for metabolic; C286 `hub/` for SAL) and the first where the never-read artifact sits **inside `web4-standard/` itself**.

**Counts**: §A — 0 spec motion; all carries HELD by construction, each re-verified at HEAD rather than asserted. §B — corpus-delta CLEAN against the spec prose; the re-derived mirror set yields **2 routed net-new findings** (one against the **standard's published schemas**, one against the **hub**), **1 standing carry confirmed still-broken** (C60-B1), **1 carry gaining new evidence** (C24-H1), and **3 refutations**. **Zero mutation.**

**The spec prose is CORRECT in both findings.** Neither routes a change to `LCT-linked-context-token.md`.

---

## §A. Verification (frozen target → HELD, each re-checked at HEAD)

### A.0 — Freeze confirmation
`git diff d89595e8..HEAD -- LCT-linked-context-token.md` → **empty**. Blob `231d70b5`, 726 lines. Last touch #531 (`d89595e8`, the C210 mover). No HTML-entity artifacts introduced.

### A.1 — C210-N1 HELD (§1.2 "key-derived" vs §3.3 signature-preimage)
Re-read at HEAD, not carried by assertion:
- §3.3 **L289**: `lct_id = "lct:web4:" + multibase32_encode(sha256(binding["binding_proof"]))` — signature-preimage.
- §1.2 **L49**: "identifiers are key-derived, proofs are signature-checked, quorums and assurance levels are recomputed from structure — never trusted from a claimed field."
- Ratified `web4-core/src/lct.rs:361-363` `derive_lct_id` = `"lct:web4:mb32:b" + base32(sha256(public_key))` — key-derived, **unchanged**.

The internal contradiction STANDS. Do NOT self-fix §3.3. **Newly relevant this pass**: §1.2 L49 is the exact clause both C288 findings turn on — see B.3 and B.4.

### A.2 — C172-N1/N2/N3 HELD
`lct.rs:361-363` intact; `lct.rs:366-373` adds the authoritative gloss (quoted in B.4). Routed off-spec, unchanged.

### A.3 — C248-N1 / C248-N2 HELD, anchors re-verified live
- **C248-N1** — `lct.rs:164 pub citizenships: Vec<BirthCertificateRef>` present; `lct.rs:155` still self-describes as "canon §2.3 `birth_certificate`, reshaped per dp 2026-07-16". §2.2 **L82** still singular. Carry STANDS, → C23-H1 bundle. **Gained corroboration this pass** (B.5): two further implementations also model it singular.
- **C248-N2** — `lct.rs:180 pub authority_ratchet: Option<RatchetRequirement>` present; §2.1 (L67-76) still 6 items, §2.2 (L78-86) still 4, neither naming it. Carry STANDS, cross-links C246-N1.
- **Do NOT re-discover #538/#544 as net-new.** Confirmed unmoved, not re-filed.

### A.4 — Python + vector carries HELD
`lct.py` frozen since `759eaefa` (#162, 2026-04-17); vectors frozen since `650518d9` (#83, 2026-03-25). Every C24/C60 Python + vector carry STANDS by construction. **C60-B1 re-verified live** — see B.6; it is not merely "still open", it is now *load-bearing* for B.3.

### A.5 — Sister cross-refs (§10.2/§10.3/§10.4) re-resolve
SAL, atp-adp, dictionary, entity-types all frozen at or before this snapshot (per C286/C282 freeze confirmations). Cross-refs resolve. CLEAN.

---

## §B. Corpus-Delta + Mirror-Set Re-Derivation

### B.0 — Corpus-delta (spec prose: CLEAN)
Window = 45 commits since the C248 audit commit `2e8f2ce4`. Only **3** touch `web4-standard/`:

| Commit | Reach on this spec |
|---|---|
| `01f410db` fix(ontology): `web4:Tensor` superclass + `web4:observationCount` (#581) | **METHOD CARRY v6 executed**: machine-diffed the schema edit against this spec's emitted examples. The spec's §2.3 `t3_tensor`/`v3_tensor` blocks carry no `observationCount` and assert no superclass; 0 reach. CLEAN. |
| `954ee391` proposal #580 (resilience to incomplete information) | Prospective authority; charges land on its precedent survey, not this file. See B.7. |
| `4665a430` proposal #579 (dictionary as context-mandatory role) | 0 LCT-structure reach. Declines. |

**No spec file this document cites moved.** Corpus surface clean against the prose.

### B.1 — Pre-registered admission criterion (written before the sweep; see the session log Step 5)
- **M1 — subject-matter reach.** Materially implements/consumes §2 structure, §3 identity-binding-`lct_id` derivation, §2.2/§4.2/§11.2 birth certificate, or §1.2 applied to LCT-borne evidence. Measured by the spec's **own constructs**, not the token `lct`.
- **M2 — mirror vs evidence.** Product-bearing code a relying party runs ⇒ **mirror** (may raise a defect). Reference/research/fixture/vendored ⇒ **evidence only** (may upgrade a standing carry; raises no defect).
- **M2c — in-standard normative sibling.** An artifact under `web4-standard/` that the standard publishes or the spec cites (schema, JSON-LD context, test vector, ontology). Divergence is a **standard-internal defect**, routed to the standard track, *regardless of whether a relying party "runs" it* — **not** downgradable to evidence by its path.
- **M3 — REACH, not verdict.** Could an implementer reading **only** this spec predict the artifact's behaviour? If **no**, admit — *regardless of whether the finding would indict the spec, the artifact, or neither.* (C284/C286 wording, verbatim: `[[feedback_admission_criterion_not_verdict]]`.)

**Bounding rule, pre-committed:** N = **3** artifact groups to full examination, order fixed before the sweep — (1) `hub/`, (2) schemas, (3) `test-vectors/lct/`. Class 6 gets a **scoped** read answering exactly two pre-committed questions. Everything else is **admitted-but-deferred with a §C ledger row** — a stated cap plus a ledger row is a deferral; a stated cap in prose alone is silent truncation (`[[feedback_prose_is_not_ledger]]`).

### B.2 — Gate results (all 8 candidate classes; declines recorded, not silent)

| # | Candidate | M1 | M2 | M3 | Result |
|---|---|---|---|---|---|
| 1 | `web4-core/src/{lct,attestation,ratchet}.rs` | ✓ | mirror | — | Established mirror; **frozen** since C248. No new surface. |
| 2 | `sdk/web4/lct.py` | ✓ | mirror | — | Established mirror; **frozen** since #162. |
| 3 | **`hub/`** (26 `.rs` with LCT tokens; 10 window commits; **0 × 8**) | ✓ | mirror | ✓ fails prediction | **ADMITTED — group 1.** → **N2** (B.4) |
| 4 | **`web4-standard/schemas/`** (`lct.schema.json`, `lct-jsonld.schema.json`, `contexts/lct.jsonld`; **0 × 8**; context spec-CITED at **L91**) | ✓ | **M2c** | ✓ | **ADMITTED — group 2.** → **N1** (B.3) |
| 5 | `web4-standard/test-vectors/lct/` | ✓ | M2c | ✓ | **ADMITTED — group 3.** → **already C60-B1**, no net-new (B.6) |
| 6 | `ledgers/reference/{go/lct/document.go, typescript/lct-document.ts}` (1305L; **0 × 8**) | ✓ | **evidence only** | ✓ | **SCOPED READ** — both pre-committed questions answered (B.5) |
| 7 | `core/lct_binding/` (10 files) | partial (§3-binding only; `verifier_lct_id` is an attestation-challenge field, `lct.lct_id` hits are in a `.md`) | — | — | **DECLINED at M1**; frozen since 2026-01/02. Deferred → §C. |
| 8 | `web4-trust-core/src/bindings/wasm.rs`; `web4-policy/` | `web4-policy` hits cite **SOCIETY_SPECIFICATION §4.2**, a different spec ⇒ clean decline; `wasm.rs` `role_lct_id`/`filling_entity_lct_id` are the R6 role API and duplicate the same `lct_id: Uuid` fact class 3 already yields | — | — | **DECLINED at M1.** Deferred → §C. |
| — | Residue checked, not left silent: `pair_message.rs`, `unlock_gate.rs`, `vault_tree.rs` | key-management, not LCT structure | — | — | **DECLINED at M1.** |

---

### B.3 — **C288-N1 (MEDIUM, standard-internal, ROUTED)** — the standard's published raw LCT schema contradicts the spec's required/optional split, contradicts its own JSON-LD sibling, and is unsatisfiable by every conforming artifact in the corpus

**M2c class.** `web4-standard/schemas/lct.schema.json` (7930 B) and `lct-jsonld.schema.json` (11432 B) both purport to describe an LCT. Machine-extracted, not eyeballed:

**Facet (a) — the required/optional split is inverted, and the two schemas disagree with each other.**

| Component | Spec §2.1/§2.2 | `lct.schema.json` | `lct-jsonld.schema.json` |
|---|---|---|---|
| `lct_id`,`subject`,`binding`,`mrh`,`policy` | **Required** (§2.1 L67-74) | required | required |
| `t3_tensor` | **Required** (§2.1 **L75**) | **NOT required** | required |
| `v3_tensor` | **Required** (§2.1 **L76**) | **NOT required** | required |
| `birth_certificate` | **Optional** (§2.2 **L82**) | **REQUIRED** | not required |
| `revocation` | **Optional** (§2.2 L85) | not required | **REQUIRED** |

`lct.schema.json` inverts the spec on **3 of 5** contested components; the two published schemas disagree on **4**. The `birth_certificate`-required inversion additionally contradicts ratified `lct.rs:475 is_regular() = citizenships.is_empty()`, which makes a citizenship-less LCT an explicitly valid state.

**Facet (b) — the raw schema is unsatisfiable by every conforming artifact.** It requires `birth_certificate.context`. Nothing in the corpus emits that key: the spec's §2.3 example emits `birth_context`; all 4 test vectors emit `birth_context`; `contexts/lct.jsonld` maps `birth_context` → `web4:birthContext`. Validated with `jsonschema` Draft7:

```
spec §2.3 canonical example vs lct.schema.json     → /birth_certificate: 'context' is a required property
interop-human-full.json      vs lct.schema.json    → /birth_certificate: 'context' is a required property
interop-minimal-interop.json vs lct.schema.json    → (same)
interop-revoked-agent.json   vs lct.schema.json    → (same)
valid-birth-certificate.json vs lct.schema.json    → 'issuing_society' + 'context' required   [= C60-B1]
spec §2.3 canonical example vs lct-jsonld.schema.json → 0 structural errors
```

**Root cause, and it is a partial remediation.** `650518d9` — *"C3: BirthCertificate field rename context → birth_context (#83)"*, 2026-03-25, whose own message states the purpose as "align with LCT spec §2.3" — updated `lct.py` + 3 test files + **5 test-vector JSON files**, and did **not** touch `lct.schema.json`. The schema is the sole surviving pre-rename artifact, and it lives in the standard. Same shape one field over: `9bcfe598` *"Cross-language LCT ID pattern fix: allow colons per spec"* fixed the colon class **for `lct_id` only**; `hardware_anchor`'s pattern `^eat:[A-Za-z0-9_-]+$` still forbids colons, so `interop-human-full.json`'s real (non-placeholder) `tpm2:sha256:abcdef1234` also fails.

**Facet (c) — reach: this is not a dead file.** It is registered in the SDK as `"lct-raw"` (`sdk/web4/validation.py:67`), and `ledgers/reference/typescript/lct-document.ts:9,226` names it as its source of truth ("Full LCT document model matching `lct.schema.json`"). **Why it survived 10 months**: `grep -rn 'lct-raw'` = 2 hits — the mapping itself, and `test_validation.py:101 assert "lct-raw" in schemas`, which asserts the schema is **listed**, never that anything **validates** against it. This is `[[feedback_does_the_impl_agree_with_itself]]`'s test-shape exactly (C286: the only test asserted non-overlap, never match).

**Placeholder noise explicitly NOT charged.** The raw validation also emits 12 errors from `...` ellipses and from the pipe-alternation strings (`"human|ai|society|…"`, `"genesis|rotation|fork|upgrade"`) in the spec's example. Those are documentation conventions, not defects, and are excluded. Likewise the `@context`/`@type` rejection under `additionalProperties: false` is **conceded** as a legitimate raw-vs-JSON-LD profile difference. Facets (a) and (b) survive all three exclusions.

**Is it NEW?** As a **FINDING**: yes — first read of these files in 8 passes. As a **FACT**: the required-list dates to `c66792fd` (2025-09-14, ~10.5 months); the `context` staleness dates to `650518d9` (2026-03-25, ~4 months).

**Refute (survives).** *(i) Is the raw schema normative?* It is published in `web4-standard/schemas/`, SDK-registered, and cited as a source of truth by an independent implementation — M2c admits it regardless. *(ii) Is the required-list divergence an intentional raw-vs-JSON-LD profile?* A profile cannot explain the T3/V3 direction: one published schema makes them mandatory and the other optional, for the same object. *(iii) Is facet (b) placeholder noise?* No — it reproduces against three interop vectors that contain **no** placeholders and otherwise validate.

**Severity/route.** **MEDIUM** (normative contradiction across co-equal published sources; not exploitable; fully reversible). **The spec prose is CORRECT — do not weaken §2.1/§2.2.** Routes to the **standard/schema track**: (1) complete the #83 rename in `lct.schema.json` (`context` → `birth_context`, add `genesis_block_hash`); (2) reconcile both schemas' `required` lists to §2.1/§2.2; (3) apply `9bcfe598`'s colon fix to `hardware_anchor`; (4) make `"lct-raw"` actually validate something. **Open DESIGN-Q for the operator: which of the two published schemas is normative?** Do NOT self-apply — normative artifact.

---

### B.4 — **C288-N2 (MEDIUM, hub-track, ROUTED)** — the portable A2 receipt names its signer with an identifier its own daemon's registry cannot be queried by

**M2 mirror** (product-bearing, running daemon). #591/#592/#595 (2026-07-29) added `AssuranceReceipt` — *"portable A2 evidence a relying party verifies without hestia"* — at `hub/hub-lib/src/constellation.rs:406`. Its doc comment cites this spec's principle **verbatim**: *"Trust in the hub identity itself is the relying party's to establish — inspectable evidence, not prescribed trust."* By design it crosses a trust boundary: verified by a party that runs neither hestia nor the hub.

**The contract it must satisfy** — `web4-core/src/lct.rs:366-371`, ratified, in its own words:

> "The canonical, key-derived `lct_id` for this LCT (canon §2.3). Computed from the binding public key on demand — never stored separately… **The local `id: Uuid` remains as an internal index only; registries key on THIS.**"

`Lct::new` sets `id: Uuid::new_v4()` (`lct.rs:526`) — a random v4 UUID, not derived from anything.

**The finding.** All three identifiers on the portable receipt are the **internal index**, carrying the canonical name:
- `constellation.rs:407 pub owner_lct_id: Uuid`
- `constellation.rs:416 pub hub_lct_id: Uuid`
- `constellation.rs:421 pub hub_signer_lct_id: Uuid` — documented as the field a relying party uses to **"resolve it to a published LCT."**

**The same binary disagrees with itself.** `hub/hub-daemon/src/rest.rs:6186-6193` — the LCT-registry ingest — computes `derive_lct_id(&payload.document.public_key)` and **rejects any publish whose claimed id does not re-derive**, with the comment *"The publisher's label is never trusted; the key is the identity."* That is §1.2 L49 implemented exactly. The resolution route `GET /v1/hubs/:hub_id/lcts/:lct_id` takes `Path<(Uuid, String)>` — **`String`** — and `get_lct` does `projected.registry.get(&lct_id)` on a String-keyed map (`rest.rs:6302-6316`). A v4 UUID is never a key in that map. `grep -rn '\.lct_id()' hub/` = **0**: nothing in the hub ever calls the canonical accessor.

So the receipt's one instruction for naming its signer is unexecutable against the registry the same daemon serves.

**The hub already hit this and documented it, one route above.** `rest.rs:1518-1522`, on the member-pubkey endpoint: *"replacing the doc.id registry scan that could never match (member uuid is `published_by`, never a doc.id)."* The two-namespace collision was diagnosed and worked around with a separate uuid-keyed side-channel — and the new portable receipt walks into it again, this time on a surface that leaves the hub.

**Is it NEW?** As a **FINDING**: yes; `hub/` is unread in 8 passes. As a **FACT**: `hub_signer_lct_id` was born `8b0b133d` (#592) on **2026-07-29 — one day old**; `owner_lct_id: Uuid` dates to #316, but was hub-internal until #591 made it portable, so the *reach* is also one day old.

**Refute.**
- **R1 (REFUTED — and it strengthens the finding).** *Resolution happens via `/v1/hubs/:hub_id/members/:member_uuid/pubkey`, which is uuid-keyed.* That endpoint reads `member_pubkeys`, the **admitted-member** pin map (`rest.rs:6280-6299`), and its own route comment says *"404 when the member is unpinned (**sovereign, not yet admitted**)."* The receipt's signer on a live hub **is** the sovereign — the doc distinguishes `hub_lct_id` (society) from `hub_signer_lct_id` (sovereign) precisely so the key holder can be named. The one uuid-keyed resolution path the hub offers **structurally excludes the identity the receipt names.**
- **R2 (PARTIALLY SUSTAINED — and it caps the severity).** *The key must arrive out of band anyway, so verification still works.* Correct: a relying party that already holds the hub's key can verify using `hub_signer_key_id` (8-byte `sha256(pubkey)` selector) alone. So this is **not** "verification is impossible" — it is "the LCT-resolution affordance the receipt advertises is unexecutable, so a party that does *not* already know the signer cannot bootstrap." That is exactly the party #591 was written for, but it is a reachability gap, not a forgery hole. **Severity capped at MEDIUM for this reason.**
- **R3 (REFUTED as a duplicate charge).** *This is C24-H1 (lct_id shape divergence) re-surfacing ⇒ reach-escalation, not net-new.* C24-H1 contests **which string shape** among candidates that are all `lct:web4:…` strings (2-seg vs 3-seg, hex vs mb32). A random v4 UUID is in none of them and differs in kind: it is not key-derived at all, so it cannot be recomputed from structure — the one hard invariant §1.2 L49 states. Filed net-new, with the honest note that it is **adjacent** to C24-H1 and should be adjudicated alongside it.

**Severity/route.** **MEDIUM** → **HUB track** (and the #579 discoverability authors, as a 5th instance of "name the thing the way the standard names it"). **The spec is CORRECT; no spec change is requested.** Cheapest possible moment to fix: `signing_bytes` is already `v2`, and its own comment records that **"no `v1` receipt was ever issued (the primitive had not yet reached a running daemon), so nothing is stranded"** — the same is true today for `v2`. Carrying the canonical `String` `lct_id` (or adding it alongside) is a byte-layout change that costs nothing now and becomes a breaking change the moment the first receipt is issued. Auditor MUST NOT self-apply.

**Not charged.** The rest of the primitive is a model §1.2 citizen and is recorded as such: the deliberate key-**selector**-not-key design (#592) closes the JWT-`jwk`-confusion hole, `roster_hash` sorts before hashing for cross-implementation determinism, and `signing_bytes` covers every field but the signature. The defect is narrow: its identifiers are the one part not recomputable from structure.

---

### B.5 — Class 6 scoped read (evidence only; both pre-committed questions answered)
Pre-committed before opening the files: *(i) how does it derive/format `lct_id`? (ii) singular or plural birth certificate?*

- **(i)** `ledgers/reference/typescript/lct-document.ts:487` emits `` lct_id: `lct:web4:${entityType}:${hash}` `` — the **SDK 3-segment shape**, i.e. a further independent instance of the C24-H1 divergence, from an implementation that names `lct.schema.json` as its source of truth.
- **(ii)** **SINGULAR**, and both emit the **pre-#83** field name: `ledgers/reference/go/lct/document.go:103` `Context BirthContext \`json:"context"\``; `lct-document.ts:114` `context: BirthContext`. Both frozen 2026-02-19/20, i.e. authored *before* the C3 rename.

**M2 holds: raises no spec defect.** Its value is reach for **N1** — the stale `lct.schema.json` is not an unread file, it is the file **two independent language implementations were built from**, and they inherited its stale field name. Recorded as **evidence upgrading C248-N1/C23-H1** (a third and fourth independent implementer both model citizenship singular) and **C24-H1** (a fourth instance of the 3-segment shape). Not filed as new findings.

### B.6 — Group 3: `test-vectors/lct/` — **already C60-B1**, no net-new
`valid-birth-certificate.json` declares `should_succeed: true` yet carries **2** `birth_witnesses` against the spec's ≥3 stated normatively five times (§4.2 **L312**, **L329**, §5 table **L340**, **L537**, §11.2 **L633/L670**) and enforced in ratified `attestation.rs:118-121` ("≥3, canon-required"); it omits `issuing_society`; it omits `t3_tensor`/`v3_tensor`.

**This is C60-B1 verbatim, open since 2026-06-15.** Machine-re-verified at HEAD (2 witnesses; `issuing_society` absent; the other 3 vectors carry 3 witnesses and `issuing_society`). Vector corpus frozen at `650518d9`. **Filed as CARRY CONFIRMED, not net-new** — the pre-registered cap ordering put this group third precisely so a known carry could not be re-sold as a discovery.

**One measured addition to the C60-B1 carry (not a new finding).** The same validation sweep shows `interop-revoked-agent.json` carries `t3_tensor` but **no `v3_tensor`**, against §2.1 **L76**. C60-B1 recorded the missing-tensor defect only for `valid-birth-certificate.json`; the vector-corpus track should treat it as covering **two** vectors. Recorded here because it was measured, not because it was sought.

### B.7 — Proposals #579/#580 (prospective authority)
- **#580** (resilience to incomplete/contradicting information): its precedent survey gains a datapoint from this pass. `lct.schema.json` requiring a key **no emitter produces** means every conforming document is *rejected*, not silently degraded — a **fail-closed-by-accident** case, distinct from C282-N1's assume-perfect and C284-N2's absence-yields-minimum. Routed to the survey as INFO; charges nothing against this file.
- **#579** (dictionary as context-mandatory role): 0 LCT-structure reach. **C288-N2 is a 5th instance** of #579's underlying "act kinds / role names / identifiers must be discoverable and consistently named" complaint. INFO to those authors.

---

## §C. Carry Ledger (for the next LCT delta ~C328)

**Net-new this pass**
- **C288-N1 (MEDIUM, OPEN, routed → standard/schema track).** `lct.schema.json` inverts §2.1/§2.2 on T3/V3 + birth_certificate; disagrees with `lct-jsonld.schema.json` on 4 components; requires the pre-#83 `birth_certificate.context` so **every conforming corpus artifact fails validation**; `hardware_anchor` pattern still forbids colons. Root cause = `650518d9` (#83) renamed 9 artifacts and missed the schema. Survived because `"lct-raw"` is registered but never validated against. **Spec CORRECT — do not weaken §2.1/§2.2.** Carries an operator DESIGN-Q: *which published schema is normative?* Do NOT self-apply.
- **C288-N2 (MEDIUM, OPEN, routed → HUB track + #579 authors).** `AssuranceReceipt.{owner,hub,hub_signer}_lct_id: Uuid` (`constellation.rs:407/416/421`) carry the internal index on a portable cross-boundary surface, while the same daemon's registry ingest enforces `derive_lct_id(pubkey)` (`rest.rs:6186`) and resolves on `String` (`rest.rs:6302`); `grep '.lct_id()' hub/` = 0. Signer-resolution instruction unexecutable; the uuid-keyed member endpoint excludes the sovereign. **Fix window is open NOW** — `signing_bytes` v2, no receipt yet issued. **Spec CORRECT.** Adjudicate alongside C24-H1. Do NOT self-apply.

**Carries HELD / confirmed**
- **C60-B1 CONFIRMED still 3-way broken** (2 witnesses, no `issuing_society`, no T3/V3) — and now **also** the only vector failing on `issuing_society` under N1's validation. **WIDENED by measurement**: `interop-revoked-agent.json` is missing `v3_tensor` (§2.1 L76), so the missing-tensor arm covers **2** vectors, not 1. Vector corpus frozen `650518d9`. → vector-corpus track.
- **C248-N1** STANDS, **corroborated**: 2 more implementations model citizenship singular (B.5). → C23-H1 bundle.
- **C248-N2** STANDS (`authority_ratchet` unenumerated in §2). → cross-links C246-N1.
- **C210-N1**, **C172-N1/N2/N3** STAND, anchors re-verified at HEAD.
- **C24-H1** STANDS, **gains a 4th instance** (`lct-document.ts:487`, 3-segment) — reach, not truth (`[[feedback_carry_gains_reach_not_truth]]`).
- All other C24/C60 design-Q + SDK + sister-doc carries STAND by freeze. None gate.

**Admitted-but-deferred (each MUST be re-run at C328 — this is the ledger row that makes the cap a deferral and not a truncation)**
- **Class 7 `core/lct_binding/`** — declined at M1 (§3-binding reach only; `verifier_lct_id` is an attestation-challenge field). **Deferred question**: does the TPM2/EK attestation path model §3.2 hardware binding consistently with `attestation.rs`? Frozen 2026-01/02 — re-check the freeze first.
- **Class 8 `web4-trust-core/src/bindings/wasm.rs`** — declined at M1 (R6 role API). **Deferred question**: does the published WASM surface expose `lct_id` as `Uuid` too? If yes it is a **second shipped face of C288-N2**, and composes with C284-N1 (same file, same "published WASM getter" class).
- **Class 8 `web4-policy/`** — declined at M1 (cites SOCIETY_SPECIFICATION §4.2). Re-check only if it grows LCT-structure code.
- **`lct-jsonld-vectors.json` (24 KB, 10 vectors)** — not opened this pass under the N=3 cap. **Deferred question**: do all 10 validate against `lct-jsonld.schema.json`, including its `revocation`-required clause?
- **`hub/` beyond `constellation.rs` + `identity.rs`** — 24 further `.rs` files carry LCT tokens, unexamined. **Deferred question**: does any other hub surface carry `*_lct_id: Uuid` across a trust boundary?

**Method notes**
- The `hub/` + `schemas/` + `ledgers/` blind spot was **per-lineage and invisible from inside the lineage** — every prior pass re-ran a mirror set derived once, at C24. Third consecutive pass where re-deriving from subject matter was the entire yield (`[[feedback_mirror_set_underderived]]`).
- Both findings are the **standard/implementation disagreeing with itself**, not with the spec — C286's lesson generalizing from "does the impl agree with itself" to "does the **standard** agree with itself" (`[[feedback_does_the_impl_agree_with_itself]]`).
- The pre-registered cap **paid for itself**: it forced the known carry (C60-B1) into third position, where it was correctly recognized as a carry rather than sold as a discovery.

---

## Verdict

**Target byte-frozen since C210 (2nd consecutive); established Rust + Python mirrors also frozen; spec prose regression-CLEAN and corpus-delta CLEAN.** The pass's entire yield came from re-deriving the mirror set from subject matter and reading three artifact classes the lineage had never opened in 8 passes.

**2 net-new MEDIUM findings, both routed, neither against the spec prose**: **C288-N1** — the standard's published raw LCT schema inverts §2.1/§2.2, contradicts its JSON-LD sibling, and rejects every conforming artifact in the corpus because a ratified rename updated 9 files and missed it; **C288-N2** — the one-day-old portable A2 receipt names its signer with a random v4 UUID while the same daemon's registry enforces and resolves the key-derived canonical id, leaving its own signer-resolution instruction unexecutable. **C60-B1 confirmed still broken** (carry, not discovery). **3 refutations recorded** (R1 refuted and strengthening; R2 partially sustained and capping severity to MEDIUM; R3 refuted as a duplicate charge). **Zero mutation** — both findings route to the standard and hub tracks; the auditor rewrites neither.

Rotation advances to **ISP (`inter-society-protocol.md`) 7th delta = C290**.
