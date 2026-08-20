# C416 — `core-spec/security-framework.md`, 10th delta

**Target**: `web4-standard/core-spec/security-framework.md` — blob `63889457`, **133 lines**, mover `afd04623` (#678, 2026-08-10), **byte-frozen 10 days**.
**Window**: `c7438906..HEAD` (C376's commit → `99ab83f8`) = **29 commits**; **1** touches `web4-standard/` (`2462881f`, interface planes — no security artifact); **0** touch the target.
**Mandate**: C376 §C pre-registered a 7-row deferral ledger for this slot and named **row 4** — the §2.2 custody block, lines 76–81, *"Never audited… first work for C416"* — as the entry point.
**Result**: ZERO mutation. 1 net-new finding (**LOW-MED**), 1 routed observation, 1 note. **The drafted headline was killed by policy review** (§D) — the 22nd in this series, and this time the falsifier was inside this lineage's own first pass.

**Lineage enumeration rule** (run, not copied): `ls -1 docs/audits/ | grep -E '^(C[0-9]+-)?security-framework'` = **11** members (C31, C68, C108, **C109 remediation**, C140, C180, C218, C256, C296, C336, C376); **12** with C416. Per the standing rule this lineage has **no** non-C-numbered `…-internal-consistency-…` member (matcher run, empty) — unlike `lct-capability-levels` and `multi-device-lct-binding`, which do.

---

## §A. Freeze and window

| Cell | Command | Value |
|---|---|---|
| Target blob | `git hash-object web4-standard/core-spec/security-framework.md` | `63889457512ac7b9f1511310ea208bcd7aebfb99` |
| Lines | `wc -l` | 133 |
| Last mover | `git log -1 --format='%h %ad' -- <target>` | `afd04623` 2026-08-10 |
| Window size | `git log --oneline c7438906..HEAD \| wc -l` | 29 |
| …in `web4-standard/` | `git log --oneline c7438906..HEAD -- web4-standard/` | **1** (`2462881f`) |
| …in the target | `git log --oneline c7438906..HEAD -- <target>` | **0** |
| SDK security suite | `python3 -m pytest -q tests/test_security.py` | **67 passed** |
| SDK full suite | `python3 -m pytest -q` | **2750 passed, 5 xfailed** |

This is the **first frozen delta since the freeze broke at C376**. §A/§C clean.

**Row-1 co-frozen set** (all 0 commits in window): `binding.py` blob `857f8040` (`759eaefa`, 2026-04-17) · `multi-device-lct-binding.md` blob `b979ea7d` (`a6cbde92`, 2026-06-21) · `binding-vectors.json` blob `dc969641` (`441b12f0`, 2026-03-17) · `presence-protocol.md` blob `6414a7fe` (`0beb1b93`) · `hestia_vault_{get,set}.schema.json` blobs `519c395f`/`63e80e95` (`d7867704`, 2026-05-16).

---

## §B. Sibling set — row 6's two-sweep set difference, published

C376 §C row 6 mandated: *"Future re-derivations MUST run the suite-ID sweep AND a primitive-name sweep and publish the SET DIFFERENCE."* Run:

```
A = git grep -rIl 'W4-BASE-1\|W4-FIPS-1'  -- web4-standard/ ':!web4-standard/docs'          →  20 files
B = git grep -rIlE 'X25519|Ed25519|ChaCha20|AES-[0-9]+-GCM|SHA-256|SHA-3-256|HKDF|P-256'
                                          -- web4-standard/ ':!web4-standard/docs'          →  65 files
B \ A  = 49    A \ B  = 4
```

**`A \ B` (suite vocabulary, no primitive names) — 4:** `implementation/reference/web4_reference_client.py`, `implementation/sdk/CHANGELOG.md`, `implementation/sdk/tests/test_protocol.py`, `test-vectors/protocol/core-protocol.json`.

**`B \ A` — 49 files carry crypto primitives and never name a suite.** The two `submission/` artifacts C336-N1 charged (`draft-palatov-web4-core-00.txt`, `web4-rfc.md`) are in it, confirming C376-N3's diagnosis that a suite-ID sweep is blind to exactly the artifacts whose defect *is* the missing suite vocabulary. Two members matter for this pass and were not visible to any prior sweep:

- **`core-spec/multi-device-lct-binding.md`** — the spec that owns every object §2.2:78 enumerates.
- **`registries/cipher-suites.md`** — the standard's *cipher-suite registry* (see §C, N3).

**B-7 (row 5) — all four numbers, matcher published.** `PAT='ECDH-P256|P-256ECDH|P-256 ECDH|ECDH P-256|P-256EC[^D]|>P-256<|ECDH with P-256'` over `web4-standard/` minus `docs/`:

| occurrences | lines | files | forms |
|---|---|---|---|
| **12** | **11** | **10** | **6** |

Form breakdown: `ECDH-P256` ×5, `P-256ECDH` ×2, `ECDH with P-256` ×2, `P-256 ECDH` ×1, `P-256EC` ×1, `ECDH P-256` ×1. **Identical to C376's baseline — HELD, no movement.** C376-N3 stands: only the form count can move on a spelling fix, and `ECDH-P256` remains a **minority at 5 of 12**.

---

## §C. Findings

### C416-N1 — LOW-MED, net-new → standard-editor. Schema arm **ROUTED**, not charged.

> **`security-framework.md:79-80` names the corpus's custody distinction in a vocabulary that no instrument in the corpus reads — while the vocabulary the corpus actually uses for that distinction has no slot in either published LCT schema.**

**Cell (a) — the §2.2 vocabulary is consumed by nothing.** Case-insensitive, whole repo, **no path filter**:

| token | files | where |
|---|---|---|
| `custody class` / `custody-class` | 2 | `security-framework.md:80` + `C376`'s audit doc |
| `device-unlock` | **1** | `security-framework.md:79` |
| `private attestation` | **1** | `security-framework.md:79` |
| `hardware-anchor private` | **1** | `security-framework.md:79` |
| `identity-vault` | **1** | `security-framework.md:79` |
| `replicated identity state` | 2 | `security-framework.md:76` + `whitepaper/PUBLISHER_CONTEXT.md` (commentary) |
| `replicat*` in `web4-standard/` (minus `docs/audits`) | 4 hits | 3 are the §2.2 block; the 4th is `research/standards_analysis.md:730` *"Replicating Claims as Header Parameters"* — a JWT section title, unrelated |

Five of the block's six normative nouns occur **exactly once repo-wide: in the clause that introduces them**. Per **v58** that is an unversioned fork — the standard has minted a name for a concept the corpus already implements under a different one.

**Cell (b) — the concept IS implemented, under names §2.2 does not use.**

| carrier | locus | value space |
|---|---|---|
| `key_storage` | `lct-capability-levels.md:368` (`"tpm"`, Level 5) / `:595` (`"software"`, Level 0); `multi-device-lct-binding.md:146` | free string |
| `anchor_type` / `key_protection` | `multi-device-lct-binding.md` — **23 lines** (`:75,:78,:102,:123,:145,:177,:185,:193,…`), incl. `"key_protection": "hardware_bound"` (`:78`) and `"warning": "Not hardware-bound - trust implications"` (`:148`) | enumerated |
| `KeyStorage` enum | `core/lct_binding/provider.py:56-61` | `{SOFTWARE, TPM, TRUSTZONE, SECURE_ENCLAVE}` |
| extractability warning | `core/lct_binding/software_provider.py:181` | *"Software-only binding: keys are extractable"* |

`git grep -l key_storage` = **11 files**. `git grep -l key_storage -- '*.json'` = **0**. **Not one JSON Schema and not one vector in the corpus binds the field.**

**Cell (c) — EXECUTED. The carrier has no schema slot.** `jsonschema` Draft 2020-12, base = a known-valid document from `test-vectors/lct/lct-jsonld-vectors.json` against `schemas/lct-jsonld.schema.json`:

```
bare control (backed)      -> VALID
+hardware_attestation      -> INVALID: Additional properties are not allowed ('hardware_attestation' was unexpected)
+device_constellation      -> INVALID: Additional properties are not allowed ('device_constellation' was unexpected)
binding.key_storage        -> INVALID: Additional properties are not allowed ('key_storage' was unexpected)
binding.binding_mode       -> INVALID: Additional properties are not allowed ('binding_mode' was unexpected)
```

Both LCT schemas are top-level `additionalProperties: false`; `lct.schema.json` properties = `[lct_id, subject, binding, birth_certificate, mrh, policy, t3_tensor, v3_tensor, attestations, lineage, revocation]`; `binding` sub-schema = `[entity_type, public_key, hardware_anchor, created_at, binding_proof]`. Meanwhile `lct-capability-levels.md:343-346` lists, as **Level 5 (HARDWARE) Additional Requirements**, `binding.hardware_type` and *"`hardware_attestation`: Complete attestation section"*, and ships it at `:366-375`.

**Why the schema arm is ROUTED and not charged here — three scope limits, stated:**
1. **`lct-capability-levels.md` cites no schema at all** (`grep -n 'schema\|validate' ` returns only two T3/V3 prose rows). Nothing in `core-spec/` says a Level-5 LCT must validate against `lct-jsonld.schema.json`; the binding is made by the SDK (`web4/validation.py:57` maps `"lct"` → `lct-jsonld.schema.json`) and `schemas/validate_schemas.py:81`.
2. **This is a new arm on a standing finding, not a net-new one.** `C328:267` already records that `additionalProperties: false` *"rejects a field the standard put there on purpose"* and lists the `@context`/`@type`, T3/V3, `birth_certificate` and `hardware_anchor` arms of **C288-N1 (MED, open)**. `hardware_attestation` and `device_constellation` are two more arms of the same defect.
3. **v51 — the `10/10 PASS` verdict is scoped to its locus.** `C328:244` and `C368:278` certify `lct-jsonld-vectors.json` **10/10 PASS** and say *"do not rebuild this as a finding."* That verdict was measured on the **ten vectors**; it says nothing about the two core-spec documents' LCT members, which no pass has ever executed against the schema. This is not a rebuild.

**Route**: LCT lineage **C448** (where C288-N1 lives), cc multi-device **C428**. Precedent for splitting a finding this way: C412's `LctStatus` half → C448.

**Severity LOW-MED, not MED, and the reason is `:80`'s antecedent.** `:80` reads *"**A replicated backup format** MUST identify each secret's custody class."* `git grep -in backup -- web4-standard/` returns: `r6-security-analysis.md:24,:176` (prose — *"Remote backup to trusted service"*, *"Consider optional remote backup"*), `deployment/README.md:280-303` (`pg_dump` + config file copy — operator state, not identity), **`submission/web4-rfc.md:587-591` §8.3 "Backup and Recovery"** (three bullets — *"Backup critical keys and data"* — an I-D section with no format), and `:80` itself. **The standard defines no identity backup format anywhere.** Per **v54**, a MUST whose antecedent has no referent is vacuous, not violated. The chargeable residue is the vocabulary fork (cell a) plus the unrepresentable carrier (cell c) — not a conformance failure.

**Remedy options (do NOT self-apply — the target is frozen and the fix touches another lineage's schema):**
(i) §2.2:80 cites the existing carrier (`key_storage` / `anchor_type`) instead of minting `custody class`; or
(ii) `custody class` is defined in `multi-device-lct-binding.md` with an enumerated value space and given a schema slot; or
(iii) `:80` is scoped to *"where a replicated backup format is defined"* and the block acknowledges that the standard defines none.

---

### C416-N2 — LOW, **ROUTED to the presence lineage (C436)**. Not charged here, and *not* evidence for N1.

The normative tree's only credential store is the presence-protocol vault. **EXECUTED** (Draft 2020-12):

```
hestia_vault_set INPUT  {name, value, custody_class}  -> ACCEPT   (additionalProperties: true)
hestia_vault_get OUTPUT {value, custody_class}        -> REJECT   (additionalProperties: false)
hestia_vault_get OUTPUT {value, key_storage}          -> REJECT
```

A conformant vault **may record** a secret's custody class and is **schema-forbidden from returning it** — to the exact party §3.1.2:121 requires assurance be *"visible to the relying party or policy evaluator"*. `presence-protocol.md:22` names both custody tiers by name (*"Hardbound — hardware-bound vault (TPM 2.0 / YubiKey / Secure Enclave)"* vs Hestia), 690 lines above a response schema that cannot distinguish them.

**Denominator, with its class qualifier (v73).** The open-input/closed-output asymmetry is **9 of 9** presence-protocol *tool* schemas — `v0/tools/` (**8**) + `v1/tools/` (**1**, `hestia_query_policy`), all `input.additionalProperties=true`, `output.additionalProperties=false`. The **3 `v0/common/` schemas are excluded and are not a 10th–12th miss**: they are top-level `additionalProperties:false` fragments (`error_envelope`, `trust_state`, `witness_entry`) with no input/output shape, so the ratio is undefined for them rather than absent. So this is a **house convention**, not a vault bug — a fix is a convention change.

**Why this is NOT evidence for N1 (v68).** §2.2:80's antecedent is *a replicated backup format*. `hestia_vault_get/set` is a single-endpoint credential store (*"Request a credential from the vault"*, §3.5) — not replicated, not a backup format, not multi-device. This control is correctly executed and **answers a different question**; annexing it to N1 would be the C406 error. Routed with its own novelty check still owed.

---

### C416-N3 — NOTE to the registries lineage (**C418, the very next slot**). Not a finding.

`registries/cipher-suites.md` (blob `1e575ece`, 23 L, frozen at `3f1d6fad`) registers three suites — `0x0001 WEB4_AES128_GCM_SHA256`, `0x0002 WEB4_AES256_GCM_SHA384`, `0x0003 WEB4_CHACHA20_POLY1305_SHA256` — and **none of `W4-BASE-1` / `W4-FIPS-1` / `W4-IOT-1`**, the three suites its own `## Reference` line points at (`core-protocol.md:18-20`). Its three names have **0 consumers repo-wide** outside the file itself.

**NOT net-new — do not re-charge.** `C70:17` already records it verbatim as *"**0** (orphan)"*, and `C298:87` ruled it *"Not net-new. B-D1-subordinate."* B-D1 is operator-gated; per **v72** a gated decision is routed, not re-adjudicated.

**Evidence cell, rebuilt after policy review corrected the first draft.** The draft published `grep -c 'cipher-suites' C378…md` = **0** and read it as *"the row fell out of the tracked set."* Both halves were wrong in the C376-N3 way:
- A filename-token count is a **citation query** and cannot see the row under another name. The broader matcher `grep -in 'cipher\|0x0001\|WEB4_AES'` on C378 returns **1 hit, `:298`** — and **that hit is `0x0001 MRH_RDF`, the *extensions* registry, not `WEB4_AES128_GCM_SHA256`.** Named here so the near-miss does not regenerate the false absence for a successor.
- *"Fell out of the tracked set"* is too strong: `C378:148` tracks all five `registries/` files' freeze (`git log -1 -- web4-standard/registries/* ×5` → *"all 5 at `3f1d6fad`, 56 days"*), `cipher-suites.md` among them. The **file** is tracked; only the orphan row's **content** has not been restated since C298 — which is precisely the instrument C298:78 itself described (*"tracked only as commit-hash liveness rows"*), now with one more datapoint.

---

## §D. The killed headline, and where its falsifier was sitting

**Drafted (MED):** *"`security-framework.md:80` imposes a MUST over a key — each secret's `custody class` — that no artifact in the corpus can carry to a relying party."*

**FALSE.** Three carriers exist, two of them in normative `core-spec/`: `lct-capability-levels.md:346,366-375,593-597`; `multi-device-lct-binding.md:78,123,143-149`; `core/lct_binding/{provider,software_provider,tpm2_provider,trustzone_provider}.py`.

**The mechanical cause — v73, third consecutive occurrence.** The verb set was pre-registered from **§2.2's own vocabulary** (`custody|replicat|backup|synchroni[sz]|sync|export`) and run against `multi-device-lct-binding.md`: **0 hits, exit 1** — reproducible, and a claim about the *instrument*, not the world. The same file answers **24** to `key_storage|anchor_type|key_protection`. This is **v40/v48**: sweep by the **domain's** word, not the source clause's. Aggravating: the pass already held `key_storage` in hand — it is the negative control in N2's own executed table.

**And the falsifier was inside this lineage's own first pass.** `C31:169` (2026-06-04), filed as a *positive confirmation, INFO, coverage, no action*:

> *"**C-I3** — Key generation/storage (§2.1…; §2.2 HSM > Secure Enclave/TEE > Encrypted) agree with … the hardware-anchor tier (`lct-capability-levels.md §2.7` Level 5 `key_storage: "tpm"`)."*

The security lineage has known where the custody carrier lives since its first pass. Ten passes later §2.2 gained a MUST demanding a per-secret custody class, and no pass connected the new clause to the carrier its own ledger had already named — because a positive confirmation is not indexed as evidence. **This is v60 in a new register: a fact recorded as a PASS is still evidence, and a later absence claim must be checked against it.**

**A correction to the correction.** `core/lct_binding/` is *not* an undiscovered tree. `C328:333` and `C368:278` both gate it as **"M2 evidence-only, 0 product referrers"**. It was invisible to *this* lineage — it surfaced only in the §E v36 residue — not to the corpus.

**Count**: 22nd drafted headline killed before publication in this series; the 15th killed or materially corrected by policy review.

---

## §E. v36 set difference — run by the domain's word, negative and positive both recorded

```
filename sweep  : git grep -rl 'security-framework' -- . ':!docs/audits' ':!*.lock'                    → 15 files
domain-word     : git grep -rlEi 'key storage|key custody|custody|secure enclave|
                    Hardware Security Module|\bHSM\b' -- . ':!docs/audits' ':!simulations/' ':!archive/' → 74 files
residue (domain \ filename)                                                                            → 71 files
```

The residue is where this pass's entire yield came from. Three members decided the finding:
- **`core/lct_binding/{provider,software_provider,tpm2_provider,trustzone_provider}.py`** — the implemented custody classification (§D). Reached by no citation of the security framework, and citing the standard nowhere.
- **`docs/best-practices/storage-and-key-management.md`** — the corpus's own Key Storage document, status *"Recommendation (strong). **Not part of the core standard.**"* It cites **zero** `.md` files, zero `§`, zero `web4-standard` (`grep -n '\.md\|web4-standard\|§'` → empty), and `git grep -rn 'best-practices' -- web4-standard/` → **empty**. §2.2 *Key Storage* and the corpus's Key Storage best practice do not know about each other in either direction. Not charged — a non-normative recommendation owes the standard no citation — but recorded, because it is the artifact a reader of §2.2 would most expect to be pointed to.
- **`web4-standard/schemas/` has no constellation or device-binding schema at all** (36 tracked files listed; none is `binding`- or `constellation`-shaped). Even a willing implementer has nowhere in the normative schema tree to write a custody class for a device.

---

## §F. Negatives (each is a charge this pass did **not** make, and why)

1. **The multi-device SDK is conformant to :78/:79 by construction, and discloses it.** Every field of `DeviceConstellation` (`root_lct_id`, `devices`, `recovery_quorum`) and `DeviceRecord` maps onto :78's MAY-replicate side; `binding.py:17-19` states *"This module provides DATA STRUCTURES and pure-function computations. Actual cryptographic operations… are out of scope."* Charging it would be charging its disclosed discipline (**v45**).
2. **`latest_attestation` is not :79's "private attestation material."** `AttestationEnvelope` (`attestation.py:124-160`) carries `public_key`, `public_key_fingerprint`, `AnchorInfo`, a `Proof` that is a signature over a public challenge, PCR **digests**, platform state, `trust_ceiling`. All public. The arm was drafted and dropped.
3. **:80's second sentence is structurally satisfied in the SDK.** Assurance is a pure function of `anchor.anchor_type` (`ANCHOR_TRUST_WEIGHT` = software **0.40**, phone SE 0.95, TPM2 0.93, FIDO2 0.98), so a demotion to `software` mechanically demotes trust; *"at the same assurance level"* is unreachable.
4. **A revoked device cannot be re-enrolled.** `enroll_device`'s duplicate check reads `constellation.devices` (**all** records, `:271`), not `active_devices` — so :81's prohibited effect has no intra-constellation path. :81's actual subject is a *stale replica*, and the standard has no replication surface for one to exist in.
5. **`DeviceStatus.SUSPENDED` has no producer in the SDK** — no function writes it (C376 reached it by direct mutation). Not charged: `multi-device-lct-binding.md:289` **discloses it at the point of use** — *"Re-activation by quorum is a future extension; this spec does not define entry/exit transitions for `suspended`."* (**v45/v57**.)
6. **`W4-IOT-1`'s absence from `security-framework.md` §1.1 is not net-new.** `core-protocol.md:18-20` carries three suites, the target's §1.1 two. Well-trodden: 16 mentions at C140, 9 at C296, and `C298:87` disposed of the codepoint half.
7. **`hub/` M3-DECLINE, `web4-trust-core/` and `web4-policy/` M1-FAIL — all hold**, 0 commits in window for each.

---

## §G. Deferral-ledger dispositions (C376 §C, all 7 rows)

| # | Row | Disposition |
|---|---|---|
| 1 | N1 remedy fork (`recovery_quorum`) | **HELD, untouched.** `binding.py` `857f8040`, spec `b979ea7d`, vectors `dc969641` — 0 commits in window. Neither fork taken; §3.5/§5.2 still do not declare which reading is normative. Re-registered for C456. |
| 2 | N2 provenance vocabularies | **HELD.** Control re-run, Draft 2020-12: the §3.1.1 field set `{principal, actor, via_device, office, authority}` is **REJECTED by both** — `r7-action-jsonld.schema.json` (top-level `additionalProperties:false`; `role` node = `[actor, roleLCT, pairedAt, t3InRole, v3InRole]`, also closed) and `acp-jsonld.schema.json` (fails its top-level `oneOf`; 11 `additionalProperties:false` sites in `$defs`). Neither schema gained a §3.1.1 field. **No vocabulary cites another.** C376-N2's positive-impossibility instrument stands. |
| 3 | C336-N1 limbs 2+3 | **STAND, desync unchanged and now wider.** The cheapest tell first, as pre-registered: xml `<date year="2026" month="August" day="9"/>` (`:26`) vs txt `Expires: March 15, 2026` (`:7`, repeated on every page footer). `txt §5.1:618-619` still reads `AES-256-GCM (SHOULD)` / `SHA-3-256 (SHOULD)` byte-identical. `SUBMISSION_GUIDE.md:28` still declares the txt is generated from the xml. **The checked-in txt is still not a render of the checked-in xml.** |
| 4 | §2.2 custody block | **DISCHARGED — audited for the first time. → N1 (§C), plus negatives 1-5 (§F) and the killed headline (§D).** |
| 5 | B-7 | **HELD exactly: 12 / 11 / 10 / 6.** All four numbers published with the matcher (§B). No movement. |
| 6 | Sibling set | **RUN. Set difference published (§B): `A\B` = 4, `B\A` = 49.** It is what surfaced `multi-device-lct-binding.md` and `registries/cipher-suites.md` for this pass. |
| 7 | `submission/` retirement | **CONFIRMED ABSENT.** No retirement marker; the xml is dated 2026-08-09 (expires 2027-02-09) — maintained, not retired. |

---

## §H. Accountability self-audit

```
surface: C416 delta audit (read-only)   act: publish an audit document + PR against dp-web4/web4
S: low/reversible [construct: docs/audits/C416-…md; ZERO spec, SDK, schema or vector bytes changed]
R: n/a [construct: no runtime path created or modified]
W: pass [construct: worker branch worker/web4-20260820-000000; PR reviewed and merged by a separate reviewer track — this session cannot merge]
O: pass [construct: policy review (Step 4) ran BEFORE the document was written; it returned REVISE and killed the drafted headline — see §D — and the revision is what shipped]
A: pass [construct: every count in this document carries the command that produced it; the killed headline and its falsifier are recorded in §D rather than silently replaced]
V: n/a [construct: reversible documentation act; the two remedy-bearing halves are ROUTED to C448/C428 and C436 rather than self-applied, and the target is frozen]
verdict: PASS
```

---

## §I. Deferral ledger — pre-registered for **C456** (security's next slot = C416 + 40)

| # | Row | Trigger to check first |
|---|---|---|
| 1 | N1 cell (a) — the vocabulary fork | Did §2.2:80 gain a citation to `key_storage`/`anchor_type`, or did `multi-device-lct-binding.md` gain a `custody class` definition with a value space? **If §2.2 is edited to drop `custody class` without defining the carrier, that is the next finding, not a discharge.** |
| 2 | N1 cell (c) — routed schema arm | Did **C448** take the `hardware_attestation`/`device_constellation` arm onto C288-N1? Probe C448's ledger, not its spec files (**v38**). If C448 declined, re-route — do not re-charge. |
| 3 | N2 — presence vault | Did **C436** take it? Re-run the 9-of-9 ratio first; if `v1/tools/` grew, the denominator moved. |
| 4 | C376-N1 remedy fork | Unchanged trigger, third slot running: has `binding.py:304`/`:352` moved, or has §3.5/§5.2 declared which reading of `recovery_quorum` is normative? |
| 5 | C376-N2 vocabularies | Unchanged trigger. **Re-run the control pair — the CONTROL passing is what makes the failures admissible.** |
| 6 | C336-N1 limbs 2+3 | Compare the date line first (`xml:26` vs `txt:7`). It is still the cheapest desync tell and it is still red. |
| 7 | B-7 | Baseline **12 / 11 / 10 / 6**. Publish all four. Only the form count can move on a spelling fix. |
| 8 | §3.1.2:119 identification | `git grep -in "policy quorum\|cryptographic quorum"` — over the normative tree was **2 hits, both the clause itself** at C376 and is **still 2** now (`security-framework.md:119`, `:120`; audit docs excluded). If it becomes 3+, someone consumed it. |
| 9 | The §2.2/best-practice gap | Does `security-framework.md` §2.2 cite `docs/best-practices/storage-and-key-management.md`, or vice-versa? Both directions were **empty** this pass. Not a charge — a materiality tell if the block is edited again. |
