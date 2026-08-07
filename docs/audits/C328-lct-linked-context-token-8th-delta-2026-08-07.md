# C328: LCT-linked-context-token.md 8th-Delta Re-Audit (10th pass)

**Date**: 2026-08-07
**Auditor**: Autonomous session (legion-web4-20260807-000000)
**Document**: `web4-standard/core-spec/LCT-linked-context-token.md` (726 lines, blob `231d70b5` — **byte-frozen since C210**)
**Base**: `b21da071`
**Lineage (10 documents)**: **C9** (`docs/audits/lct-internal-consistency-2026-05-22.md`, pre-convention filename, self-identifying `# C9 Audit:` on line 1) → C24 (#256) → C60 (#338) → **C61 remediation** (`9d1933f8`) → C100 → C135 → C172 → C210 (#531 mover) → C248 → **C288** (#596) → **C328**.
**Spec mutations since C210**: **0**. `git diff d89595e8..HEAD -- <target>` = empty. **Third consecutive byte-frozen delta.**
**Window**: 61 commits since the C288 merge `121b8a48`.

---

## Framing — the pass's whole yield came from discharging the previous pass's own deferral list, and the ledger row that made that deferral possible had lost every name it covered

C288 capped its mirror expansion at N=3 and wrote five admitted-but-deferred artifacts into its §C ledger, with the instruction *"RE-RUN THESE AT C328 — this row is what makes the N=3 cap a deferral, not truncation."* All five are discharged here (§D), each with a row, including the ones that came back NEGATIVE.

The spine (§B) is the v19/v23/v24 row-set reconstruction, applied to this lineage for the first time in ten passes. It found the **catch-all mechanism** — a ledger row that keeps a **true** disposition while losing every id it covers. That finding is **LOW and it deflates** (§B.4, published as such). What makes it worth a row anyway is that its **payload arrived in the same pass**: the deferral discharge in §D.4 produced new evidence bearing on exactly two carries — `C24-M4` and `C24-M6` — whose names the catch-all had removed. The evidence had no row to attach to.

**Counts**: §A 0 spec motion. §B — 23-row ledger reconstructed; 20 rows memberless at C288; **1 LOW net-new (C328-N1)**. §C — 2 carry re-classifications (v16), 0 net-new. §D — 5/5 deferrals discharged: 1 confirmed YES (reach-escalation of C288-N2), 1 NEGATIVE gate, 1 M2 evidence-only, 1 executed clean, 1 measured. §E — corpus-delta **CLEAN against the spec prose, 4th consecutive**. **Zero mutation.**

**The spec prose is CORRECT in every finding below.** Nothing routes a change to `LCT-linked-context-token.md`.

---

## §A. Freeze + carry verification at live HEAD

### A.0 — Freeze confirmation
`git diff d89595e8..HEAD -- LCT-linked-context-token.md` → **empty**. Blob `231d70b5`, 726 lines. Last touch `d89595e8` (#531, 2026-07-16).

### A.1 — Established mirrors, motion measured (not assumed)

`git log --oneline 121b8a48..HEAD -- <path> | wc -l`:

| Mirror | Commits in window | Verdict |
|---|---|---|
| `web4-core/src/lct.rs` | 0 | frozen |
| `web4-core/src/attestation.rs` | 0 | frozen |
| `web4-core/src/ratchet.rs` | 0 | frozen |
| `implementation/sdk/web4/lct.py` | 0 | frozen |
| `web4-standard/schemas/lct.schema.json` | 0 | frozen (`9bcfe598`, 2026-02-22) |
| `web4-standard/schemas/lct-jsonld.schema.json` | 0 | frozen (`af621844`, 2026-04-10) |
| `web4-standard/test-vectors/lct/` | 0 | frozen (`af621844` / `650518d9`) |
| `ledgers/reference/` | 0 | frozen |
| **`hub/`** | **29** | **moved — see §D.5** |
| `web4-trust-core/` | 2 | `.gitignore` + `Cargo.lock` only; **`src/bindings/wasm.rs` = 0 (COLD)** |

**Correction carried from this session's own policy review.** The scope proposal justified deferral (ii) with *"that tree MOVED in the window."* It did not: the two `web4-trust-core/` commits touch `.gitignore` and `Cargo.lock`, and `git log 121b8a48..HEAD -- web4-trust-core/src/bindings/wasm.rs` is **empty**. The deferral is still owed, and is discharged in §D.2 — but as a freeze-check plus one read, not a live-motion investigation. An inflated premise must not license a deep dive.

**Window instrument, both forms published (they disagree and both are right):**

```
git log  --format='' --name-only 121b8a48..HEAD | ...   # per-commit TOUCHES
git diff --name-only            121b8a48..HEAD | ...    # unique PATHS
```
`hub` 71/36 · `docs` 26/26 · `whitepaper` 10/6 · `web4-standard` 4/4 · `web4-trust-core` 2/2 · `web4-core` 1/1 · `.github` 1/1 · `forum` 1/1. The whitepaper gap is 6 unique paths of which the three `build/` artifacts were touched twice.

### A.2 — Carries verified by re-reading

- **C210-N1 HELD.** §1.2 L49 ("identifiers are key-derived … never trusted from a claimed field") vs §3.3 L289 (`lct_id` from `sha256(binding_proof)`). Both unchanged. Do NOT self-fix §3.3.
- **C172-N1/N2/N3 HELD.** `lct.rs` frozen; `derive_lct_id` = `"lct:web4:mb32:b" + base32(sha256(public_key))` unchanged.
- **C248-N1 / C248-N2 HELD.** `lct.rs` frozen ⇒ `citizenships: Vec<BirthCertificateRef>` and `authority_ratchet: Option<RatchetRequirement>` both present; §2.1/§2.2 still 6/4 items, neither naming the ratchet; §2.2 L82 still singular.
- **C24-M4 / C24-M6 re-verified at HEAD, and both HOLD at the spec level** — §2.3 L211-212 emits `"revocation": {"status": "active"` as an example only, with no enumeration anywhere in 726 lines; `superseded` appears at L509 (§7.3, "Mark as `superseded`" — a status action) **and** at L519 (§7.4 reason list). **But see §C: the standard's own published schema settles both, and no LCT pass has ever read it on this field.**
- **C60-B1 HELD** (vector corpus frozen). **C288-N1 / C288-N2 HELD**, both widened — §C, §D.

---

## §B. SPINE — v19 / v23 / v24 carry ROW-SET reconstruction

### B.1 — The ledger's row set, reconstructed from the origin

C9's 8 findings (H1 H2 M1–M4 L1 L2) were all remediated by PR #225 and C24 re-verified 8/8 — **disposition recorded, no loss.** C24 added 12; C60 added 21; C60 §C + the C61 remediation (#338, 9 autonomous) dispositioned A1/A2/B3/B4/B16/B18/B19 and split B5/B14 into an applied half and a carried half. **Every C9 and C60 disposition is recorded.** The reconstruction therefore starts at the first ledger that publishes the surviving set in full.

**C100 §C (`:102-106`) and C135 §C (`:104-108`) each enumerate the same 23 rows individually:**

| Class | Rows |
|---|---|
| DESIGN-Q (10) | `C24-H1` `C24-M4` `C24-M6` `C24-L3` `C60-B2` `C60-B5-uniqueness` `C60-B12` `C60-B14-req` `C60-B15` `C60-B17` |
| SDK cross-track (5) | `C24-M2` `C24-M3` `C60-B6` `C60-B7` `C60-B8` |
| Vector corpus (1) | `C60-B1` |
| Sister-doc (4) | `C60-B9` `C60-B10` `C60-B11` `C60-B13` |
| Firewall / DEMOTED (3) | `C23-H1` `C24-D1` `C24-D2` |

### B.2 — Membership matrix (v24: `grep -F` each id **individually**)

Instrument, published: `grep -oE "(C60-)?\bBn\b" <doc> | wc -l` per id per doc, word-anchored so `B1` cannot absorb `B10`–`B19`. Run over the six delta docs.

| id | C100 | C135 | C172 | C210 | C248 | **C288** |
|---|---|---|---|---|---|---|
| C24-H1 | 2 | 4 | 5 | 1 | 1 | **8** |
| C60-B1 | 2 | 2 | 3 | 2 | 2 | **11** |
| C23-H1 | 4 | 3 | 2 | 0 | 9 | **3** |
| C24-M2 | 2 | 2 | 2 | 1 | 1 | **0** |
| C24-M3 | 1 | 1 | 0 | 0 | 0 | **0** |
| C24-M4 | 2 | 2 | 1 | 0 | 0 | **0** |
| C24-M6 | 2 | 2 | 0 | 0 | 0 | **0** |
| C24-L3 | 2 | 2 | 1 | 1 | 1 | **0** |
| C60-B2 | 2 | 2 | 2 | 1 | 1 | **0** |
| C60-B5 | 2 | 4 | 3 | 2 | 1 | **0** |
| C60-B6 | 2 | 2 | 2 | 1 | 1 | **0** |
| C60-B7 | 2 | 2 | 2 | 1 | 1 | **0** |
| C60-B8 | 2 | 2 | 2 | 1 | 1 | **0** |
| C60-B9 | 12 | 5 | 3 | 1 | 1 | **0** |
| C60-B10 | 7 | 6 | 3 | 1 | 0 | **0** |
| C60-B11 | 2 | 3 | 2 | 1 | 0 | **0** |
| C60-B12 | 6 | 3 | 3 | 1 | 1 | **0** |
| C60-B13 | 2 | 3 | 2 | 1 | 1 | **0** |
| C60-B14 | 5 | 6 | 3 | 2 | 1 | **0** |
| C60-B15 | 2 | 2 | 2 | 1 | 1 | **0** |
| C60-B17 | 2 | 2 | 2 | 1 | 1 | **0** |
| C24-D1 | 1 | 1 | **0** | 0 | 0 | **0** |
| C24-D2 | 1 | 1 | **0** | 0 | 0 | **0** |

**23 rows in, 3 named at C288.** Row count published: **23 → 3**.

### B.3 — The mechanism, located in the documents

Not attrition (C320's cause), not table→prose (C322's), not a collapsed table (C324's). **A catch-all row, C326's third mechanism, introduced in two stages:**

- **C172 `:105`** — still a full enumeration: *"Standing carries (all STAND …): DESIGN-Q C24-H1[widened]/M4/M6/L3, C60-B2/B5/B12/B14-req/B15/B17; SDK C24-M2/M3, C60-B6/B7/B8; vector C60-B1; sister-doc C60-B9/B10/B11/B13; firewall C23-H1."* (My first matrix under-counted C172 badly, because the compound form `C60-B2/B5/B6/…` prefixes only the first member. **A named matcher is not a reproducible one** — the C326 rider, hit on this pass's own instrument. The bare-id matcher above is the corrected one, and it is what the table publishes.)
- **C210 `:94` / C248 `:105`** — §C becomes `**All C24/C60 design-Q + C60-B1 vector carries STAND** by Python/vector freeze. None gate.` **The ledger loses membership; §A.3 (`C210:41`, `C248:41`) still enumerates**, so the names survive in prose but not in the row. That is [[feedback_prose_is_not_ledger]] running in reverse — the ledger delegating to the prose.
- **C288** — §A.4 `:55` reads *"Every C24/C60 Python + vector carry STANDS by construction"* and §C `:207` reads *"All other C24/C60 design-Q + SDK + sister-doc carries STAND by freeze."* **Neither enumerates, and no other line in the document does.** Membership reaches zero.

**v19 is satisfied** (a disposition exists). **v23 is blind** (the row count never fell — the row is still there). The only check that fires is **v24: membership.**

### B.4 — Deflation, published (the honest half)

The disposition is not merely present, it is **TRUE**, and this pass verified it independently rather than accepting it:

- `implementation/sdk/web4/lct.py`, `test-vectors/lct/` — 0 commits in window ⇒ `C24-M2/M3`, `C60-B1/B6/B7/B8` stand.
- **The sister-doc carries do NOT rest on the Python/vector freeze**, which is the one place the catch-all's *warrant* could have failed to cover its members. Measured separately: `t3-v3-tensors.md` 0, `lct-capability-levels.md` 0, `protocols/web4-lct.md` 0, `capability.py` 0, `t3v3-ontology.ttl` 0 commits in window ⇒ `C60-B9/B10/B11/B13` stand too. **The catch-all is warranted for all 20 members.**
- **20 of the 23 are backstopped** in this track's standing carry ledger (`carries.md:70`), which names every C24/C60 id individually. Same instrument that made C322-N1 a LOW.
- **`C24-D2` was correctly demoted** at C24 (§1.2 English prose "AI" vs §2.3 wire enum `ai` — different registers, SDK matches §2.3, §1.2 explicitly delegates to `entity-types.md`). **No defect; its loss costs nothing.**
- **`C24-D1`'s forwarding pointer HOLDS — my best hypothesis was REFUTED.** D1 (`web4-core-ontology.ttl:219` `rdfs:range web4:Web4BirthCertificate`, undefined) was folded at C24 into `C16-M8`, which is **live**: re-verified at `C286:86` and `C326:348`. I proposed that the fold was *directionally wrong* — that C16-M8's remedy (create `sal-ontology.ttl`) would not discharge a range in the `web4:` namespace. **The evidence killed it:** `forum/nova/web4-sal-bundle/sal-ontology.ttl:1` declares `@prefix web4: <https://web4.io/ontology#>` and `:13` declares `web4:Web4BirthCertificate a rdfs:Class`. Promoting that file into `web4-standard/ontology/` **would** discharge D1. The fold is correct and the pointer is intact.

⇒ **C328-N1 is LOW.** A real, named, reproducible loss of membership on 20 rows, fully backstopped elsewhere, with a true disposition. It is worth a row and not worth more.

### B.5 — Why it is worth a row anyway: the payload arrived in the same pass

§D.4 executed an artifact this lineage had never opened and produced two facts that bear directly on **`C24-M4`** and **`C24-M6`** — two of the ids the catch-all removed. Under a named ledger the evidence attaches to a row. Under `"All other C24/C60 design-Q … STAND"` there is no row to attach it to, and the finding that a 68-day-old design question has been silently settled by the standard's own schema is the kind of thing that gets written into a §B narrative and lost at the next delta. **The cost of a memberless row is not that the carry becomes false. It is that the carry becomes unaddressable.** Routed as §C below, not as new inventory.

### B.6 — Instrument error found in this section's own work, published

The dangling-reference scan behind §B.4 first ran **file-scoped** and reported **three** dangling classes in `web4-core-ontology.ttl` — `web4:T3Tensor`, `web4:V3Tensor`, `web4:Web4BirthCertificate`. Re-run **namespace-wide** across all four canonical `.ttl` files (the correct scope, since `t3v3-ontology.ttl:1` declares the *same* `https://web4.io/ontology#` prefix), the count is **one**:

```
files: hub-law.ttl role-extension.ttl t3v3-ontology.ttl web4-core-ontology.ttl
defined IRIs: 119   referenced in rdfs:range/domain/subClassOf: 35
DANGLING: https://web4.io/ontology#Web4BirthCertificate  (web4-core-ontology.ttl)
```

Two of three were an artefact of the scope, not the corpus (v13.6: N identically-shaped disagreements is a signature — here two of the three shared the benign cause). Recorded because the wrong number is the one that would have read as a discovery. Corollary observation, INFO, no row: `web4-core-ontology.ttl` and `t3v3-ontology.ttl` carry **no `owl:Ontology` declaration and no `owl:imports`** (only `hub-law.ttl:16` and `role-extension.ttl:29` do), so the split-file graph is bound by shared-namespace convention alone.

---

## §C. Carry re-classification (v16) — the standard's own schema settles C24-M4 and C24-M6

**Not net-new inventory.** Both carries remain open; what changes is their **class**, which is what v16 exists to distinguish: *omits* ≠ *forbids* ≠ *requires*.

`web4-standard/schemas/lct.schema.json` (blob `e46d5a09`, frozen `9bcfe598` 2026-02-22) publishes:

- `revocation.status` — enum **`["active", "revoked"]`**
- `revocation.reason` — enum **`["compromise", "superseded", "expired"]`**

| Carry | Filed as (C24, 2026-05-31) | Measured at HEAD |
|---|---|---|
| **C24-M4** | *"Spec doesn't enumerate `revocation.status` values; SDK `RevocationStatus.SUSPENDED` is spec-unspecified but behaviourally exercised by a published vector."* | True of the **prose** (0 enumerations in 726 lines). **False of the standard.** `lct.schema.json` publishes a **closed 2-value enum**, and the SDK-generated vector emits `suspended`, which the schema **rejects** — `revocation/status: 'suspended' is not one of ['active','revoked']` (§D.4). The carry's premise moves from *unspecified* to *specified and violated*. |
| **C24-M6** | *"`superseded` is a STATUS in §7.3, a REASON in §7.4, and absent from SDK."* | The schema **adjudicates in favour of §7.4**: `superseded` is in the **reason** enum and absent from the **status** enum. Consequence the design question did not anticipate: §7.3 **L509** *"Mark as `superseded`"* describes a state the standard's own schema makes **unrepresentable**. |

**Route**: operator DESIGN-Q bundle, folded into **C288-N1**'s open question *"which published schema is normative?"* — because that question now decides two older carries, not just C288-N1's own field set. **The spec is CORRECT and no spec change is requested here**; if `lct.schema.json` is normative the remedy is to align §7.3, and if it is not, the schema's enums are unbacked. Auditor MUST NOT self-apply. **Both carries are restored to the ledger by name in §F.**

---

## §D. Discharge of C288's five pre-registered deferrals

C288 §C: *"ADMITTED-BUT-DEFERRED — RE-RUN THESE AT C328 — this row is what makes the N=3 cap a deferral, not truncation."* **5/5 discharged, one row each, including the NEGATIVEs.**

### D.1 — `core/lct_binding/` → **M2, evidence-only. No defect. Upgrades C288-N1.**

*C288's question: does the TPM2/EK path model §3.2 consistently with `attestation.rs`?*

**Admission test first.** `git grep -lF 'lct_binding' -- ':!core/lct_binding'` = **52 files**, by directory: `tests/sessions` 18 · `archive/reference-implementations` 6 · `simulations` 5 · `docs/history/design_decisions` 5 · `docs/audits` 5 · `sessions/active` 2 · `docs/strategy` 2 · one each in `web4-standard/implementation/sdk/tests`, `web4-standard/core-spec`, `sessions/outputs`, `.hardbound/bundles`, `docs/what/specifications`, `docs/history`, `docs/compliance`, `demos`, `core`. **The two `web4-standard/` hits are substring collisions, not citations** — `LCT-linked-context-token.md:266` is the spec's own `def create_lct_binding(...)` pseudocode and `test_package_api.py:376/592` are test method names ([[feedback_loose_matcher_certifies_absence]]: a substring hit is not a citation). **Zero product-bearing referrers ⇒ M2 (evidence only, may upgrade a carry, raises no defect).** Frozen since `d9ab940e`, 2026-02-20.

**The §3.2 question answers itself.** §3.2 is ten lines and its whole hardware clause is step 2, *"Create binding with hardware anchor (if available)"*. There is no modelling commitment to be inconsistent with. **NEGATIVE — no §3.2 divergence exists to find.**

**What it does yield** (evidence, routed to C288-N1): `software_provider.py:176/322` emits `hardware_anchor: None`; `trustzone_provider.py:383` emits `result["key_handle"]`; `provider.py:124` models `attestation_type ∈ {"eat", "tpm2_quote", "arm_psa"}`. **None of these can satisfy `lct.schema.json`'s `^eat:[A-Za-z0-9_-]+$`** — a third independent implementer whose anchors the published schema rejects.

### D.2 — `web4-trust-core/src/bindings/wasm.rs` → **YES. Confirmed 2nd (and 3rd) shipped face of C288-N2. Reach-escalation, not net-new.**

*C288's question, verbatim: "does the published WASM surface ALSO expose `lct_id` as `Uuid`? if yes = 2nd shipped face of C288-N2."*

**Yes**, and the underlying type is worse than the binding:

```rust
// web4-core/src/role.rs:132-140
pub struct RoleAssignment {
    pub role: SocietyRole,
    /// The role's own LCT — authority binds here
    pub role_lct_id: Uuid,
    /// The entity currently filling this role
    pub filling_entity_lct_id: Uuid,
```

```rust
// web4-trust-core/src/bindings/wasm.rs:884-885
fn parse_uuid(s: &str) -> Result<uuid::Uuid, JsValue> {
    uuid::Uuid::parse_str(s).map_err(|e| JsValue::from_str(&format!("Invalid UUID '{}': {}", s, e)))
}
```

`wasm.rs` carries **93 `#[wasm_bindgen]` attribute sites** (crate v0.2.0; the token occurs 94 times, the 94th being the `use wasm_bindgen::prelude::*` import — see §G.7) and routes `role_lct_id`, `filling_entity_lct_id`, `entity_lct_id`, `founder_lct_id` through `parse_uuid` on the way in (`:494-495`, `:513`, `:520`, `:559`, `:568`) and `.to_string()` on the way out (`:527-534`).

Three measured consequences:

1. **`web4-core` disagrees with itself.** `lct.rs:366-371` states the UUID is *"internal index only; registries key on THIS"* (the derived `lct:web4:mb32:b…` string). `role.rs:137` types *"The role's own LCT"* as that same internal index. One crate, two incompatible answers to "what is an LCT id" — [[feedback_does_the_impl_agree_with_itself]].
2. **The published JS boundary hard-rejects a canonical id.** `Uuid::parse_str("lct:web4:mb32:b72asy…")` fails, so a caller holding the id `derive_lct_id` produces cannot construct a `WasmRoleAssignment` at all. C288-N2's hub case was a silent type mismatch; this is a parse refusal at the boundary.
3. **C288-N2's "the fix is free" argument does not extend here.** That argument rested on `signing_bytes` being pre-issuance (see D.5). `role.rs:137/140` are **public fields on a public struct in a published crate** — changing the type is a breaking API change. The remedy's cost differs by face, and the carry recorded only the cheap one.

**Route: reach-escalation of C288-N2** ([[feedback_carry_gains_reach_not_truth]] — a carry acquiring new consumer surfaces is never net-new), with the cost note above as the escalation. **Spec CORRECT.** Composes with C284-N1 (same file, same published-WASM-getter class). Do NOT self-apply.

### D.3 — `web4-policy/` → **NEGATIVE gate.**

*C288's condition, verbatim: "declined at M1. Re-check only if it grows LCT-structure code."* Discharged as written, not widened.

- Paths searched: **all of `web4-policy/`**, `--include=*.rs --include=*.py --include=*.toml`.
- Motion: `git log --oneline 121b8a48..HEAD -- web4-policy` = **0 commits** (last touch `1fa86e09`, 2026-07-27, before the window).
- Tokens: `grep -rlnE 'lct_id|birth_certificate|BirthCertificate|t3_tensor|authority_ratchet'` = **0 files**.

**Condition not met. Remains declined at M1.** (v9: a gate is only as good as the tree it points at — the tree and the matcher are both published above.)

### D.4 — `lct-jsonld-vectors.json` → **EXECUTED. 10/10 against the JSON-LD schema; 0/10 against the raw schema.**

*C288's question: do all 10 pass `lct-jsonld.schema.json`, including its `revocation`-required clause?* Ten vectors, never opened in ten passes. **Executed, not reasoned about.**

**Instrument** (scratch path outside the repo, not committed):
```
python3 /tmp/c328/validate.py     # jsonschema 4.26.0
  vectors: web4-standard/test-vectors/lct/lct-jsonld-vectors.json   blob 04e0f4b3  (af621844, 2026-04-10)
  schema A: web4-standard/schemas/lct-jsonld.schema.json            blob 64dd77d6  (af621844, 2026-04-10)
  schema B: web4-standard/schemas/lct.schema.json                   blob e46d5a09  (9bcfe598, 2026-02-22)
```
**v21 check**: the run emitted **20** `PASS`/`FAIL` lines against a table of 2 schemas × 10 vectors = **20 rows**. No line dropped between stdout and this table.
**v17 re-run at a different scope**: re-validated under `Draft202012Validator` (both files declare `$schema: draft/2020-12`; C288 used Draft7). **Both drafts return identical counts** — 10/10 and 0/10. Instrument stable.

**Result A — `lct-jsonld.schema.json`: 10/10 PASS**, `revocation`-required clause included. **CLEAN.**
**Result B — `lct.schema.json`: 0/10 PASS.**

**The pre-committed routing fires exactly as written** (recorded in this session's policy review *before* the run, so a carry could not be sold as a discovery): *a 0/10 against the raw schema is C288-N1 reach, not net-new; only a failure against `lct-jsonld.schema.json` would be candidate net-new.* The JSON-LD schema passed. **No net-new finding from this artifact.**

Failure-arm census against `lct.schema.json` (count = number of the 10 vectors exhibiting the arm):

| n | path | arm |
|---|---|---|
| **10** | `<root>` | `Additional properties are not allowed ('@context', '@type' were unexpected)` |
| 9 | `birth_certificate` | `'context' is a required property` — C288-N1's known pre-#83-rename arm |
| 8 | `revocation/ts` | `None is not of type 'string'` |
| 8 | `revocation/reason` | `None is not of type 'string'` |
| 8 | `revocation/reason` | `None is not one of ['compromise','superseded','expired']` |
| 2+1 | `mrh/bound/[01]` | `'type'` / `'ts'` required |
| 2+1 | `mrh/witnessing/[01]` | `'role'` / `'last_attestation'` required |
| **1** | `revocation/status` | **`'suspended' is not one of ['active','revoked']`** → **§C, C24-M4** |
| 1 | `revocation/reason` | `'investigation' is not one of [...]` |
| 1 | `binding/hardware_anchor` | `'tpm2:sha256:abcdef1234' does not match '^eat:[A-Za-z0-9_-]+$'` |
| 1 | `<root>` | `'birth_certificate' is a required property` |

**Two additions to C288-N1's reach (measured, not sought):**

- **NEW ARM — `additionalProperties: false` forbids `@context` and `@type` on 10/10.** These are the exact two fields the spec's **own remediation added**: C24-L4 → applied at C61 → verified HELD by C60 §A.0 at **§2.3 L62/L63**. The published schema rejects a field the standard put there on purpose. C288-N1 recorded the T3/V3, `birth_certificate` and `hardware_anchor` arms; it did not record this one.
- **The colon arm now indicts the spec's own canonical example, not just an implementer's vector.** §2.3 **L99** emits `"hardware_anchor": "eat:mb64:hw:..."`; the pattern's character class `[A-Za-z0-9_-]` excludes `:`, so **`eat:mb64:hw:...` FAILS**. Verified directly: `re.match(r'^eat:[A-Za-z0-9_-]+$', 'eat:mb64:hw:...')` → `None`; `'eat:abc_def-123'` → match. `9bcfe598` fixed the `lct_id` pattern and left this one.

### D.5 — `hub/` `.rs` sweep → **measured; the boundary set is C288-N2's; anchors all stale; the free-fix window was used twice and not taken.**

*C288's question: any other `*_lct_id: Uuid` crossing a trust boundary?*

**Instrument**: `git grep -nE '[a-z_]*lct_id\s*:\s*Uuid' -- 'hub/**/*.rs' ':!hub/target'` → **160 lines** (168 when widened to `(Option<|Vec<)?Uuid`). Files: `rest.rs`, `main.rs`, `mcp.rs`, `admin.rs`, `constellation.rs`, `envelope.rs`, `events.rs`, `ledger.rs`, `session.rs`, `signer.rs`, `state.rs`, `charter.rs`, `hub.rs`, `init.rs`, `proposal.rs`.

**Honest reading — this is NOT a 160-site widening of C288-N2.** The hub is *internally consistent*: it is a Uuid-keyed subsystem throughout, and an internal index used internally is what `lct.rs:366-371` says a Uuid is for. C288-N2's charge is specifically about a Uuid-typed id on a surface a **relying party must resolve against the canonical registry**. That set has not grown beyond the receipt fields C288 already found. **No net-new from the sweep.** Recorded so the next pass does not re-derive it: 160 is the population, not the finding.

**Two things the sweep did surface, both about C288-N2's own premises:**

**(a) v22 — every C288-N2 anchor is stale after 29 hub commits.** Re-resolved **by content**:

| C288 anchor | At HEAD | Drift |
|---|---|---|
| `constellation.rs:407` `owner_lct_id` | **`:543`** | +136 |
| `constellation.rs:416` `hub_lct_id` | **`:555`** | +139 |
| `constellation.rs:421` `hub_signer_lct_id` | **`:560`** | +139 |
| `rest.rs:6186` `derive_lct_id` ingest | **`:6855`** | +669 |

Spec anchors moved 0 in the same window. **The clock an anchor is on belongs to the tree, not the carry** — and the cheap test (`git log <lastpass>..HEAD -- <file> | wc -l`, non-zero ⇒ re-resolve) would have flagged all four.

**(b) C288-N2's "the fix is free" window was used twice, and neither bump took it.** C288 argued: *"Cheapest possible moment to fix: `signing_bytes` is already `v2`, and no `v1` receipt was ever issued … the same is true today for `v2`."* In this window `AssuranceReceipt` was version-bumped **twice** — `694584e6` (#598, `signing_bytes` **v2→v3**) and `33f9b03a` (#601, constellation attestation receiver-first v2). At HEAD, `constellation.rs:619` declares `pub fn signing_bytes` and `:621` extends with `b"web4:assurance-receipt:v3:"` (also rebuilt at `:1461` by the reconstructability test), while `:601-618` records that **no `v2` receipt was ever issued either, "and that is measured, not assumed"** (the running image checked against `/proc/<pid>/exe`, `query_hub` as positive control).

**So the window is still open** — C288-N2's cheapness argument holds at v3. What is new is that **two byte-layout changes passed through the exact struct while the carry was open and neither carried the fix.** A carry routed to another track, holding a stale anchor and no row in that track's ledger, does not get consumed by that track's own work on the same lines. **Escalation to C288-N2, not net-new.**

---

## §E. Corpus delta — CLEAN against the spec prose (4th consecutive)

Merged with §D.5 per the policy review (one `hub/`-weighted traversal, two questions). Of the 61 window commits: 29 in `hub/` (surveyed above — governance/plane-split/atomic-write/test hardening; none touches LCT structure or the spec's subject matter), 26 in `docs/` (audit docs, incl. C314/C318/C320/C322/C324/C326), 10 whitepaper touches (Publisher lane), 4 in `web4-standard/`, 1 in `web4-core/`. **No commit in the window claims authority over LCT subject matter** (v2: grepped for the behaviour — `lct_id` derivation, `birth_certificate` shape, `authority_ratchet`, T3/V3 embedding — not the vocabulary). **0 net-new against the spec. Zero mutation.**

---

## §F. Carry Ledger for the next LCT delta (~C368)

**Row count: 26** (23 reconstructed + C328-N1 + C288-N1 + C288-N2; C172/C210/C248 rows listed separately below). **Every id named individually — that is the point of C328-N1 and this ledger must not be the next pass's exhibit.**

### F.1 — Net-new this pass

| id | sev | status | summary |
|---|---|---|---|
| **C328-N1** | **LOW** | OPEN → method/record | The lineage's 23-row carry ledger reached **3 named ids at C288** via a catch-all row (`"All other C24/C60 … STAND by freeze"`) whose disposition is **true and warranted** (independently re-verified, §B.4) and which names **zero** of its 20 members. Mechanism = C326's third (catch-all), staged: C172 enumerates → C210/C248 move the names from §C into §A.3 → C288 drops them entirely. **Backstopped** in `carries.md:70`; **`C24-D2` correctly demoted, `C24-D1`'s fold pointer verified intact.** Corrective act = this ledger. **5th lineage reconstructed; 5th row loss; 51 ids across C320(4) C322(9) C324(5) C326(13) C328(20).** |

### F.2 — Restored to the ledger by name (all 20; re-verified TRUE at HEAD)

**DESIGN-Q (operator)** — `C24-H1` (lct_id form; 4 instances) · **`C24-M4`** (revocation.status — **re-classified §C**: prose omits, `lct.schema.json` **forbids** `suspended`) · **`C24-M6`** (superseded status-vs-reason — **re-classified §C**: the schema **adjudicates for §7.4** and makes §7.3 L509 unrepresentable) · `C24-L3` (valuation bound) · `C60-B2` (`mrh.paired[].context` unmodeled) · `C60-B5-uniqueness` (active-count invariant + disambiguation) · `C60-B12` (entity_type closed-15 vs extended types) · `C60-B14-req` (anti-collusion requirement) · `C60-B15` (selective-disclosure layer) · `C60-B17` (per-attestation revocation mechanism).

**SDK cross-track** (`lct.py` frozen `759eaefa`, 2026-04-17) — `C24-M2` (`LCT.create()` no `mrh.witnessing`) · `C24-M3` (no `attestations` from witnesses) · `C60-B6` (V3 clamp ↔ L3) · `C60-B7` (bootstrap factory) · `C60-B8` (genesis quorum guard).

**Vector corpus** (frozen `650518d9`/`af621844`) — `C60-B1` (`valid-birth-certificate.json` 3-way broken; **2 vectors** on the missing-tensor arm per C288).

**Sister-doc** (all four sister files 0 commits in window, measured §B.4) — `C60-B9` (per-role tensor cardinality vs t3-v3 §6.3) · `C60-B10` (`dimensions`-wrapper vs flat) · `C60-B11` (`birth_timestamp` gating) · `C60-B13` (`web4-lct.md` 7-role/15-type staleness).

**Firewall / DEMOTED** — `C23-H1` (birth-cert 3-way shape, cite-only) · `C24-D1` (ontology `:219` dangling `web4:Web4BirthCertificate`; **folded into live `C16-M8`, pointer VERIFIED**, and confirmed the **only** dangling IRI namespace-wide, 1 of 35 refs) · `C24-D2` (**correctly demoted, no defect — do not resurrect**).

### F.3 — Standing findings, HELD and widened

- **C288-N1 (MEDIUM, standard/schema track)** — HELD, **two arms added** (§D.4): (a) `additionalProperties:false` forbids `@context`/`@type` on **10/10** JSON-LD vectors, the exact fields C24-L4→C61 **added** to §2.3 L62/L63; (b) the `^eat:[A-Za-z0-9_-]+$` colon prohibition now indicts **the spec's own §2.3 L99 example** `eat:mb64:hw:...`, not only an implementer's vector. Third independent implementer producing non-`eat:` anchors (§D.1). Its open DESIGN-Q *"which published schema is normative?"* now **decides C24-M4 and C24-M6 as well** (§C). **Spec CORRECT — do not weaken §2.1/§2.2.** Do NOT self-apply.
- **C288-N2 (MEDIUM, HUB track)** — HELD, **reach-escalated** (§D.2, §D.5): 2nd face `web4-trust-core/src/bindings/wasm.rs` (94 `#[wasm_bindgen]` exports; `parse_uuid` **hard-rejects** a canonical id at the published JS boundary), 3rd face `web4-core/src/role.rs:137/140` (public fields, published crate ⇒ **the free-fix argument does not extend**). All four C288 anchors re-resolved by content. `signing_bytes` **v2→v3** in-window with the fix untaken; window still open (measured at HEAD). Adjudicate alongside `C24-H1`.
- **C210-N1** HELD · **C172-N1/N2/N3** HELD · **C248-N1** HELD (→ C23-H1 bundle) · **C248-N2** HELD (→ cross-links C246-N1).

### F.4 — Swept clean this pass; check only whether they CHANGED, do not re-derive

`lct-jsonld.schema.json` + `lct-jsonld-vectors.json` (**10/10 PASS**, both drafts) · `web4-policy/` (**NEGATIVE gate**, condition unmet — paths and matcher published in §D.3) · `core/lct_binding/` (**M2 evidence-only**, 0 product referrers; §3.2 has no modelling commitment to violate) · the `hub/` `*_lct_id: Uuid` population (**160 sites, internally consistent, not a widening** — do not rebuild this as a finding).

---

## §G. Post-write re-runs at a different scope (v17) — and what they caught

Every count above was re-run after the section was written, at a different scope than it was drafted with.

1. **CAUGHT — the §B membership matcher.** The first matrix used `grep -oF "C60-B7"` and returned **0 for C172**, which would have published "C172 dropped 11 ids." C172 `:105` names all of them in the compound form `C60-B2/B5/B6/B7/B8/…`, where only the first member carries the prefix. The corrected bare-id matcher (`(C60-)?\bBn\b`) moves C172 from *the drop point* to *the last full enumeration*, which relocates the entire mechanism from one pass to two. **The published table is the corrected instrument.** ([[feedback_named_matcher_not_reproducible]], hit on its own first outing.)
2. **CAUGHT — the ontology dangling scan** (§B.6): file-scoped 3 → namespace-wide **1**. Published rather than silently corrected.
3. **CAUGHT — the deferral (ii) motion premise** (§A.1): `web4-trust-core/` 2 commits ≠ `wasm.rs` moved. Caught by this session's policy review, not by me; recorded as such.
4. **CAUGHT — `core/lct_binding/`'s two `web4-standard/` referrers** are substring collisions (`create_lct_binding`, `test_lct_binding`), not citations. A loose matcher would have promoted an M2 artifact to M2c on a false in-standard reference.
5. **Re-run, held**: the D.4 validation under `Draft202012Validator` (declared) vs `Draft7Validator` (C288's) — identical, 10/10 and 0/10. The v21 line-count check (20 emitted / 20 rows) held.
6. **Re-run, held**: the window instruments (§A.1) — both forms published rather than one conceded. The `hub/` population re-measured with `grep -rnE … hub --include=*.rs | grep -v /target/` (a different tool and root from the `git grep … ':!hub/target'` that produced it) — **160 both ways**. C288's memberless zeros re-checked with plain `grep -c` at document scope — `C24-M4`/`C24-M6`/`C60-B9`/`C60-B13` = **0**, agreeing with the word-anchored matcher.
7. **CAUGHT, post-write — two of my own cells in §D.** (a) "94 `#[wasm_bindgen]` export sites" counted **token occurrences**; the attribute-line count is **93**, the 94th being the `use` import — and an attribute line is not the same thing as an export site (some are `(constructor)`/`(getter)` inside an already-exported `impl`). Corrected to the measurable quantity. (b) "`constellation.rs:619` signs `…v3:`" named the `pub fn signing_bytes` line, not the domain tag, which is at **`:621`** (and `:1461`). Both are small; both are exactly the class of cell this section exists to catch, and neither was fixed silently.

**Not re-derived, per the standing guards**: C326's `sal-governance.json` sweep (checked only for change: unmoved) · the per-suite-directory consumer census (**known-bad instrument, not rebuilt**) · C318's suite-coverage flagship (**stays refuted**) · #531/#538/#544 (**consumed, not re-discovered**).

---

## §H. Lessons

1. **A pre-registered deferral row is the highest-yield instrument this rotation has.** Four of this pass's five substantive results came from a list the *previous* pass wrote down because it knew it was capping itself. C288's sentence — *"this row is what makes the N=3 cap a deferral, not truncation"* — is what made §D possible; without it the five artifacts would have been re-derived from scratch or not at all. **A cap that names what it dropped is not truncation. This is the second consecutive pass to be paid by publishing its own limits** (C324 was the first, for the instrument; this is the first for the *scope*).
2. **v24's real cost is not falsity, it is unaddressability.** C328-N1 is LOW: the disposition was true, warranted, and backstopped, and this pass verified all three rather than assuming the loss was damaging. But the *payload* landed in the same pass — §D.4's schema execution produced facts that belong to `C24-M4` and `C24-M6`, and the ledger had no rows to receive them. **The question to ask of a memberless row is not "are its members still true" but "where does new evidence about them go."**
3. **The oldest artifact in the corpus can settle the newest question.** `lct.schema.json` has been frozen since 2026-02-22 and unread by this lineage for ten passes. It silently decides a design question filed 2026-05-31 — and decides it *against* a normative sentence of the spec (§7.3 L509 "Mark as `superseded`"). [[feedback_ontology_is_a_spec_peer]] generalises: a published schema is a *peer*, and a peer can adjudicate.
4. **A carry's remedy has a per-face cost, and the ledger records only the face it was found on.** C288-N2 was correctly written as "free to fix now." That is true of `signing_bytes` and false of `role.rs`. When a carry gains reach, re-price the remedy — otherwise the cheap framing outlives the cheap case.
5. **Refuting your own best hypothesis is cheaper than defending it.** The "the D1 fold points somewhere that cannot discharge it" line was the most interesting thing in §B until one grep of `forum/nova/web4-sal-bundle/sal-ontology.ttl` killed it. Two minutes; it would have been a false MEDIUM.

---

**Verdict: 8th delta SERVED. Target byte-frozen (3rd consecutive), corpus-delta CLEAN against the spec prose (4th consecutive), ZERO mutation, 0 net-new against the spec.** One LOW net-new (`C328-N1`, ledger-membership), two carries re-classified by measurement (`C24-M4`, `C24-M6`), two standing MEDIUMs widened (`C288-N1` two arms, `C288-N2` two shipped faces + stale anchors + an untaken free-fix window), 20 carry rows restored by name, **5/5 pre-registered deferrals discharged with a row each including the NEGATIVEs**, and **6 cells corrected before shipping — 5 of them mine, caught by the post-write re-run (one of which would have relocated the whole §B mechanism to the wrong pass), 1 by the policy review** — all published rather than quietly fixed. Rotation advances to **ISP (`inter-society-protocol.md`) = C330**.

---

## Review-gate block

```
surface: C328 audit pass (docs/audits/, read-only over the standard)   act: publish an audit record; route findings to operator/HUB/schema tracks
S: low/reversible [construct: no mutation of any spec, schema, vector, or code artifact; sole write is a new file under docs/audits/]
R: n/a [construct: no reachability-gated act]   W: n/a [construct: no consequential act performed on behalf of an identity]
O: pass [construct: §A freeze verification precedes every claim; §D admission tests precede every read]   A: pass [construct: this document + the PR commit record the act, its evidence, and the instruments, together]
V: n/a [construct: no irreversible act; every finding is routed, none self-applied — the guardrail forbids the auditor rewriting §2/§3.3/§7.3]
verdict: PASS
```
