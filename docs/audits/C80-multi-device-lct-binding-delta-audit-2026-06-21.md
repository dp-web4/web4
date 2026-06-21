# `multi-device-lct-binding.md` — Second Delta Re-Audit (C80)

**Audited file**: `web4-standard/core-spec/multi-device-lct-binding.md` (1127 lines, current `main`)
**Audit date**: 2026-06-21
**Audit series**: C-series, C80 (second delta re-audit). Chain: **C19** (first-pass internal-consistency, 2026-05-28) → #246 → **C36** (first delta, 2026-06-07) → #281 → **C80** (this).
**Instrument**: multi-agent **refute-by-default WORKFLOW** — 3 §B finders (SDK/vector-mirror, internal-consistency, sibling-spec reciprocity) → 2 adversarial verifiers (refute-by-default, confirm only on incontrovertible line cites). §A done by direct token-by-token verification of #281's claims against the canonical SDK + vectors + the current spec, plus bidirectional carry re-verification against the *current* corpus. Per `[[feedback_audit_workflow_adversarial_verify]]`, `[[feedback_remediation_introduced_regression]]`, `[[feedback_auditor_blindspot_pattern]]`.
**Authority sources** (canonical precedence: SDK + shipped test vectors > spec text):
- **SDK** — `web4-standard/implementation/sdk/web4/binding.py` (619 lines)
- **Test vectors** — `web4-standard/test-vectors/binding/binding-vectors.json` (128 lines, 6 vector groups)
- **Sibling specs** — `t3-v3-tensors.md`, `LCT-linked-context-token.md`, `lct-capability-levels.md`, `atp-adp-cycle.md`, `errors.md`, `SOCIETY_SPECIFICATION.md`, `web4-society-authority-law.md`, `data-formats.md`, `entity-types.md`
- **Ontology** — `web4-standard/ontology/t3v3-ontology.ttl`

**Result**:
- **§A** — Of the 9 C36 autonomous findings + 3 C19 cleanups #281 remediated, **11/12 HELD**; **1 (C36-N6) introduced a NEW remediation regression** (the signature change swept §3.6 but missed the §3.2 call site → un-callable function). All 6 deferred carries (C36-N9/N11 + C19-M3/M4/M5/M7) re-verified **STILL-OPEN** against the *current* (post-C61/C67/C79) corpus; **C36-N9 HARDENED** (SOCIETY_SPEC now defers birth-certs to SAL) and **C19-M5 SHARPENED** (now couples §B-N1).
- **§B** — 3 finders → ~13 raw candidates → **8 distinct confirmed** (1 HIGH + 4 MEDIUM + 3 LOW) after dedup + adversarial verify; **3 deflated** (documented in §C).

---

## Executive Summary

Three headline conclusions.

1. **#281's remediation was correct but — once again — incomplete in exactly the way C36 warned about.** C36's own central lesson was *remediation-introduced regression*: when a remediation renames or re-signatures a symbol, it must sweep **every** call site. C36-N6 threaded a new `constellation` parameter into `cross_witness(...)`; #281 applied the new 3-parameter signature (§3.3 L500), updated the §3.6 recovery call site (L840 → 3 args), **but left the §3.2 enrollment call site at 2 args** (L490 `cross_witness(existing_device, new_device)`). A consumer implementing §3.2 faithfully calls a 3-parameter function with 2 arguments → `TypeError`. This is the un-remediated remainder of C36-N6 and the §A flagship — the *same class of defect the audit-of-the-remediation is supposed to catch, recurring across two remediation generations* (#246 missed §3.5 for H1; #281 missed §3.2 for N6).

2. **The deepest pre-existing latent defect this audit surfaces is structural T3 non-conformance (§B-N1, HIGH).** The root LCT's `t3_tensor` (§2.3 L218-230) and the §4.1 extension (L851-860) model T3 as a **flat dict of 8 ad-hoc dimension names** (`technical_competence`, `social_reliability`, …, `hardware_binding_strength`, `constellation_coherence`). The canonical T3 (`t3-v3-tensors.md §2`, ontology) has **exactly 3 root dimensions** (Talent/Training/Temperament) with every facet a sub-dimension via `web4:subDimensionOf`. None of the 8 names exist anywhere in `t3-v3-tensors.md` or the ontology as legitimate sub-dimensions — and `lct-capability-levels.md:37` explicitly tags this very `technical_competence`-style flat dict as the **deprecated "Old 6-flat-dimension schema."** This is multi-device-specific (grep confirms no other core-spec doc carries the flat form; `LCT-linked-context-token.md` uses the correct 3-root `composite_score` form). It is the wire-side manifestation of long-deferred C19-M5 (the 8 sub-dimensions absent from the ontology) — the two now **couple**.

3. **A second cluster (§B-N3/N4/N5) traces to one unreconciled root cause: the device record has two divergent shapes.** §2.3's constellation-entry shape ({`device_lct_id`, `anchor_type`, `enrolled_at`, `last_witnessed`, `status`}) and §2.4's standalone Device-LCT shape ({…, `cross_device_witnesses` *objects*, `device_trust` block}) were never reconciled with each other or with the SDK `DeviceRecord` / shipped vectors. The §3.4 trust algorithm is fed §2.3 constellation entries (L566) yet reads `cross_device_witnesses` and `latest_attestation` off them (N5) — fields that live only on §2.4. The §2.4 `device_trust` block is read by no algorithm and has no SDK counterpart (N4, orphan). And the §2.4 `cross_device_witnesses` *object* shape (`w["device_lct_id"]`, §3.4 L703) contradicts the SDK + shipped vector, which use a bare-string `cross_witnesses` list (N3, wire-actionable — a spec-faithful §3.4 **crashes on the `constellation_trust_multi_device` vector**).

**Refute-by-default paid off.** Of ~13 raw candidates, the verifiers refuted 3 (a `composite_score`-key claim that collapsed into N1; a §4.2 table-completeness claim the spec itself pre-empts at L884-888; a `(n+1)//2` "numeric error" that recomputes correctly — only the *word* "majority" is loose). The cross-witness shape issue surfaced independently from two lenses (SDK-mirror B1 + internal-consistency F4) and collapsed to N3/N5.

---

## Severity Ladder

- **HIGH** — Wire-actionable defect verifiable against SDK or test vectors (an implementation conforming to the spec text produces broken code or fails a shipped vector), OR a structural conformance violation against a canonical sibling spec.
- **MEDIUM** — Internal semantic inconsistency, undocumented spec→SDK algorithmic/shape drift, or cross-document reciprocity gap.
- **LOW** — Naming divergence, dangling/orphan field, latent enum mismatch, or wording imprecision — does not by itself break the wire.
- **INFO** — Fidelity note; no correctness impact.

---

## §A — Delta Status of C36 + C19 Findings

### A.1 — #281-remediated findings (11/12 HELD; 1 introduced a new regression)

| C36/C19 | Topic | Status | Evidence (current spec) |
|---------|-------|--------|--------------------------|
| **N1** | §3.5 `.lct_id` → `.device_lct_id` | **HELD** | §3.5 L730/741/759 all `device_to_remove.device_lct_id`; only residual `.lct_id` is `root_lct.lct_id` (L382, correct — the root LCT *does* have `lct_id`). Matches SDK `DeviceRecord.device_lct_id`. |
| **N2** | weighted → uniform mean; drop `trust_weight` | **HELD** | §3.4 L593 `base_trust = sum(device_trusts)/len(device_trusts)`; `trust_weight` grep = 0. Matches SDK `total_weight += 1.0` (binding.py:512) + `constellation_trust_multi_device` vector. |
| **N3** | define `constellation_trust_ceiling()` inline | **HELD** | §3.4 L617-665 defines it with software-exclusion (L632) + named-before-generic precedence; hand-reproduces all 6 `trust_ceiling_by_config` vector cases (software→0.40, phone→0.75, fido2→0.80, phone+fido2→0.90, 3-named→0.95, 3-named+software→0.98). Mirrors SDK L395-442. |
| **N4** | density → unique-mutual-pair set; remove `is_recent` | **HELD** | §3.4 L701-708 `witness_pairs` set + `w_id in device_ids` guard, no recency filter; `is_recent` grep = 0. Matches SDK L385-392. *(Caveat: the entry SHAPE it iterates is wrong — see §B-N3, a distinct issue C36-N4 did not address.)* |
| **N5** | `a_fresh` defaults 1.0 from `latest_attestation` | **HELD** | §3.4 L583-585 `a_fresh = 1.0; if device.latest_attestation is not None: a_fresh = device.latest_attestation.freshness_factor`. Byte-for-byte mirrors SDK L468-470. *(Caveat: `latest_attestation` has no §2.4 schema home — see §B-N4/N5.)* |
| **N6** | thread `constellation` into `cross_witness()` | **REGRESSED** | Signature updated (§3.3 L500 `cross_witness(constellation, device_a, device_b)`) and §3.6 call site updated (L840, 3 args), **but §3.2 L490 `cross_witness(existing_device, new_device)` left at 2 args** → un-callable. See **§A flagship** below. |
| **N7** | `ANCHOR_WEIGHTS` → `ANCHOR_TRUST_WEIGHT` | **HELD** | §3.4 L577/L610 `ANCHOR_TRUST_WEIGHT`; `ANCHOR_WEIGHTS` grep = 0. Matches SDK `__all__` + binding.py:91. |
| **N8** | quorum intersects remaining-active | **HELD** | §3.5 L727-733 `authorizing_active = remaining_active & set(authorizing_devices)`; check uses the filtered set. Matches SDK L338-340. *(Adjacent nit: the signature-collection loop L747 still iterates raw `authorizing_devices` — see §B-N7.)* |
| **N10** | `round(…, 4)` | **HELD** | §3.4 L606 `round(min(ceiling, raw_trust), 4)`. Matches SDK L528. |
| **L1** | drop redundant `"mutual": true` | **HELD** | `"mutual"` JSON grep = 0 (only prose "mutual" at L688). |
| **L2** | flat `revoked_at`/`revocation_reason` | **HELD** | §2.4 L296 + §3.5 L760-762 use flat fields; no nested `revocation.reason/.ts`. Matches SDK `DeviceRecord` L185-186. |
| **L3** | 24h review window → RECOMMENDED | **HELD** | §5.3 L1003-1004 "RECOMMENDED default: 24h; deployments MAY tune…". |

**Remediation quality: 11/12 clean, 1 incomplete-sweep regression.** Every edit that landed still matches canonical authority. The single failure is N6's call-site sweep.

#### §A flagship — C36-N6 remediation regression: §3.2 `cross_witness` call left at the old arity

C36-N6 (LOW) found `cross_witness(device_a, device_b)` referenced an out-of-scope `constellation`. #281's fix **changed the function arity** from 2 to 3 parameters (`cross_witness(constellation, device_a, device_b)`, §3.3 L500) and updated the §3.6 recovery call site to match (L840, 3 args). It **did not update the §3.2 additional-enrollment call site** (L490), which still passes 2 arguments:

```python
# §3.2 L490 — 2 args against a now-3-parameter signature
cross_witness(existing_device, new_device)
```

A consumer implementing §3.2 faithfully binds `constellation=existing_device, device_a=new_device, device_b=<missing>` → `TypeError: missing required argument`. Pre-#281 this call was correct (2 args / 2 params); #281's arity change *introduced* the breakage. **Severity: HIGH** (wire-actionable, un-callable enrollment path). **Resolution**: `cross_witness(root_lct.device_constellation, existing_device, new_device)` (mirroring §3.6 L840). Autonomous-actionable.

> This is the second consecutive generation of the *same* C36-named pattern: #246 renamed `device_lct`→`device_lct_id` but missed §3.5 (→ C36-N1 HIGH); #281 re-signatured `cross_witness` but missed §3.2 (→ this). Recorded for `[[feedback_remediation_introduced_regression]]`: an arity/signature change is a rename of the *call contract* — the completeness sweep must grep **every call site**, not only the definition and the one obvious caller.

### A.2 — Deferred carries (6/6 STILL-OPEN; 1 hardened, 1 sharpened) — bidirectionally re-verified against the *current* corpus

| Carry | Topic | Status (re-verified 2026-06-21) | Note |
|-------|-------|----------|------|
| **C36-N9** | §7.2 four Society MUSTs unacknowledged + wrong birth-cert authority | **STILL-OPEN — HARDENED** | `SOCIETY_SPECIFICATION.md` (current) still has **zero** device/constellation/recovery/multi-device-birth-cert content; it now **explicitly defers** Birth Certificates to `web4-society-authority-law.md §3.4` as a SAL record class. So §3.1's `society.issue_multi_device_birth_certificate(...)` + §8 reference to SOCIETY_SPEC cite the **wrong owner** more clearly than at C36 — the canonical authority is SAL. Couples carry-C23-H1. **Operator/cross-track.** |
| **C36-N11** | entity-type-segmented LCT IDs (`lct:web4:root:`, `…:device:phone:`) | **STILL-OPEN** | §2.3/§2.4 unchanged; LCT-core canonical generator still emits `lct:web4:<mb32>` with no entity segment. Feeds **carry-C33 B-H1**. **Design-Q.** |
| **C19-M3** | 3 exception classes absent from `errors.md` W4_ERR taxonomy | **STILL-OPEN** | `errors.md` post-C66/C67 still has only `W4_ERR_WITNESS_QUORUM` (L66, §3.2). The reuse path (device-removal + recovery quorum → `W4_ERR_WITNESS_QUORUM`, 409) is intact; **only `NoHardwareAnchorError` is a true gap**. The spec still raises bare Python classes (`InsufficientQuorumError`/`InsufficientRecoveryQuorum`/`NoHardwareAnchorError`) with no errors.md mapping note. Fold into **carry-C30 error-canonicity.** |
| **C19-M4** | LCT-core does not acknowledge the §7.1 extension | **STILL-OPEN** | `LCT-linked-context-token.md` post-C60/C61 still has **zero** `device_constellation`/`cross_device_witnesses`/`root_attestation` content. Not resolved downstream. **Cross-spec (LCT-recip).** |
| **C19-M5** | 8 T3 sub-dimensions absent from `t3v3-ontology.ttl` | **STILL-OPEN — SHARPENED** | Ontology still declares only 3 T3 roots + open `web4:subDimensionOf`; none of the 8 multi-device dims are declared. Now **couples §B-N1**: the wire example (§2.3) and the ontology gap are the same defect viewed from two ends. **Cross-corpus design-Q.** |
| **C19-M7** | §7.3 ATP costs not aligned with `atp-adp-cycle.md` | **STILL-OPEN** | `atp-adp-cycle.md` post-C78/C79 has **no** device/enroll/constellation cost counterpart. §7.3's costs (enroll 10 / witness 1 / removal 5 / recovery 20) remain free-floating. **Cross-spec design-Q.** |

No deferred carry was resolved by drift in any sibling spec or the ontology since C36 — confirmed by direct grep against the post-remediation versions of errors.md (C67), LCT-core (C61), atp-adp (C79), and SOCIETY_SPEC.

---

## §B — New Confirmed Findings (8)

> Numbering N#. Classification: `wire-actionable` / `cross-spec` / `design-Q` / `spec-cleanup`. Adversarially verified (refute-by-default; confirm only on incontrovertible cites). Per BC#6, each carries a one-line Resolution but **no prescribed diff**.

### N1 — [HIGH] §2.3/§4.1 `t3_tensor` is a flat 8-dimension dict; violates the canonical 3-root T3 structure (the deprecated "old flat schema") · cross-spec / design-Q · couples C19-M5

§2.3 L218-230 and §4.1 L851-860 define `t3_tensor.dimensions` as a flat dict of 8 keys (`technical_competence`, `social_reliability`, `temporal_consistency`, `witness_count`, `lineage_depth`, `context_alignment`, `hardware_binding_strength`, `constellation_coherence`) + a sibling `composite_score`. `t3-v3-tensors.md` (canonical) mandates T3 as **exactly 3 root dimensions** — Talent/Training/Temperament — with every refinement a sub-dimension via `web4:subDimensionOf` (`t3-v3-tensors.md:135`; ontology `t3v3-ontology.ttl` declares only the 3 roots). **None** of the 8 names appear anywhere in `t3-v3-tensors.md` or the ontology as legitimate sub-dimensions, and `lct-capability-levels.md:37` explicitly labels this `technical_competence`-style dict the deprecated **"Old 6-flat-dimension schema."** Multi-device-specific: grep confirms no other core-spec doc carries the flat form (`LCT-linked-context-token.md:388` uses the correct 3-root `composite_score = 0.4·talent + 0.3·training + 0.3·temperament`). §4.4 (L931-959) reframes `constellation_coherence` conceptually as "a dimension within T3" but never maps it under a root, so it does not rescue the structure. This is the wire-side manifestation of long-deferred C19-M5. **Resolution**: restructure §2.3/§4.1 to the 3-root form — express the multi-device facets (`hardware_binding_strength`, `constellation_coherence`) as `web4:subDimensionOf` refinements of the appropriate root(s), and register them in the ontology (closes M5). **Design-Q** — cross-spec coordination (t3-v3 + ontology); not unilaterally applicable to multi-device alone.

### N2 — [MEDIUM] §2.3 `t3_tensor` carries no entity-role binding; violates the t3-v3 role-context invariant · cross-spec / design-Q

§2.3 L218 attaches `t3_tensor` directly to the root LCT object with no `entity`/`role` qualifier (same in §4.1). `t3-v3-tensors.md:14` is emphatic: tensors "are **not absolute properties** — they exist **only within role contexts** … RDF triples in the MRH explicitly bind tensors to entity-role pairs"; the canonical structure keys tensors by role (`role_tensors`), and the ontology binds trust to an entity-role pair. The constellation-identity tensor supplies no role context. **Resolution**: bind the root LCT's T3 to an explicit entity-role pair (even a default `Self`/`Citizen` role), or state which role-context aggregate it represents. **Design-Q** (couples N1 — same edit site).

### N3 — [MEDIUM] §3.4 cross-witness representation (name + shape) diverges from the SDK + shipped vector; a spec-faithful impl crashes on `constellation_trust_multi_device` · wire-actionable

§3.4 `compute_cross_witness_density` (L702-705) iterates `for w in d.cross_device_witnesses:` then `w_id = w["device_lct_id"]` — a list of **objects** keyed `device_lct_id`, consistent with §2.4 L274-280. The SDK (`binding.py:387-388`) iterates `for w_id in d.cross_witnesses:` over bare **strings**, and the field is named `cross_witnesses`, not `cross_device_witnesses`. The shipped vector `constellation_trust_multi_device` supplies `"cross_witnesses": ["dev1","dev2"]` (strings, binding-vectors.json:108). A spec-faithful §3.4 evaluates `"dev1"["device_lct_id"]` → `TypeError` on the canonical vector. Both **name** and **shape** diverge; the vector is the tiebreak and sides with the SDK. **Resolution**: in §3.4 iterate `for w_id in d.cross_witnesses` over plain LCT-ID strings, and reconcile the field name `cross_device_witnesses` (§2.4/§3.4) → `cross_witnesses` (or vice-versa, picking one corpus-wide). Autonomous-actionable (touches §2.4 example + §3.4 — apply carefully; couples N5).

### N4 — [MEDIUM] §2.4 `device_trust` block is orphaned — read by no algorithm, with no SDK counterpart · spec-cleanup / wire-shape

§2.4 L282-286 gives each device a `device_trust` object (`anchor_strength`/`attestation_freshness`/`cross_witness_score`). The §3.4 algorithm sources anchor strength from `ANCHOR_TRUST_WEIGHT[device.anchor_type]` (L577) and attestation freshness from `device.latest_attestation.freshness_factor` (L584-585) — **not** from `device_trust`; nothing in the spec reads the block (the §3.4 comment L573-574 even points at it only descriptively). SDK `DeviceRecord` (binding.py:180-189) has no `device_trust` field. It is a dead wire block — likely a leftover the C36-N2/N5 freshness remediation never reconciled. **Resolution**: drop `device_trust` from the §2.4 example (the canonical inputs are `anchor_type` + an optional attestation envelope), or, if it is meant to be a cached read-model, annotate it as non-authoritative. Autonomous-actionable.

### N5 — [MEDIUM] §2.3 constellation-entry shape and §2.4 standalone Device-LCT shape are unreconciled; §3.4 reads §2.4-only fields off §2.3 entries · wire-shape (root cause of N3/N4)

The trust algorithms bind `devices = root_lct.device_constellation.devices` (§3.4 L566) — the §2.3 constellation-entry shape, which carries only {`device_lct_id`, `anchor_type`, `enrolled_at`, `last_witnessed`, `status`} (L174-198). Yet §3.4 reads `d.cross_device_witnesses` (L703) and `device.latest_attestation` (L584) off those same objects — fields present **only** on the §2.4 standalone Device LCT (L274-289), never on the §2.3 entries. The doc never states how a constellation entry resolves to its full device LCT. **Resolution**: define one device-record shape (or an explicit projection) that carries every field the §3.4/§4.3 algorithms read, aligned to the SDK `DeviceRecord` (which is the single flat shape the SDK actually computes over). N3 (wire-actionable, vector-crash) and N4 (orphan block) are the two concrete instances of this root cause; route together. Autonomous-actionable.

### N6 — [LOW] §2.4 `revocation_reason` admits `recovery_revoked`, which the SDK `remove_device` guard rejects · wire-actionable (latent) · spec/SDK split

§2.4 L296 defines the `revocation_reason` enum with **5** values including `recovery_revoked`, and §3.6 `recover_identity` L836 sets `revocation_reason = "recovery_revoked"`. The SDK `remove_device` (binding.py:322-324) defines `valid_reasons = {"lost","sold","compromised","upgrade"}` (**4**) and raises `ValueError` on anything else. A spec-blessed value is rejected by the canonical removal guard. Latent (mitigated): §3.6 sets the field directly, not via `remove_device`, and the SDK has no `recover_identity`, so no shipped path currently reaches the guard with `recovery_revoked`. **Resolution**: add `recovery_revoked` to the SDK `valid_reasons` (it is a legitimate revocation reason), **or** scope it in §2.4 as "set only by the recovery path (§3.6)" so the §3.5/SDK 4-value removal guard is correct by construction. Autonomous (spec note) + SDK-track (enum).

### N7 — [LOW] §3.5 signature-collection loop iterates raw `authorizing_devices`, not the quorum-filtered `authorizing_active` · spec-cleanup

§3.5 correctly checks quorum over `authorizing_active = remaining_active & set(authorizing_devices)` (L731, the C36-N8 fix), but the subsequent signature-collection loop iterates the **raw** argument: L747 `for device in authorizing_devices:`. It thus collects removal signatures from devices that may not be in the remaining-active set (e.g. the device being removed, or already-revoked devices). Inconsistent with the quorum semantics the same function just enforced. **Resolution**: iterate `for device in authorizing_active` (or document that signature collection is intentionally broader than the quorum count). Autonomous-actionable.

### N8 — [LOW] §5.2 docstring/comment call `(device_count + 1) // 2` a "true majority"; for even n it yields exactly half · spec-cleanup

§5.2 L983 docstring says the quorum "is a true majority: ceil(device_count / 2)" and L994's comment says `# ceil(n/2) = majority`. The formula `(n+1)//2` equals `ceil(n/2)`, but for **even** n that is exactly n/2 (a tie), not a strict majority (>n/2): e.g. n=6 → 3, which is half of 6, not a majority. The three shipped vector values (n=5→3, n=6→3, n=10→5) all recompute correctly — the numbers are right; only the word "majority"/"true majority" is imprecise. **Resolution**: reword to "≥ half (ceil n/2)" or change the formula to `(n//2)+1` if a strict majority is actually intended (would change the n=6 and n=10 vectors — likely NOT desired, so prefer the wording fix). Autonomous-actionable (wording).

---

## §C — Deflated Candidates (3, documented for honesty)

| Raw | Claim | Why deflated |
|-----|-------|--------------|
| `composite_score` key+value (§2.3 L229) "contradicts the canonical T3 composite" | refuted | `composite_score` **is** the canonical key for the §10.2 weighted sum (`LCT-linked-context-token.md:388`). The real defect is that the flat 8-dim structure has no Talent/Training/Temperament roots to compute it from — a *consequence* of N1, not an independent key contradiction. Folded into N1. |
| §4.2 ceiling table is non-exhaustive vs the §3.4 code branches (2-hw=0.90, 1-hw=0.80, multi-software=0.40) | refuted | §4.2 L884-888 + L890-900 **explicitly** declare the `constellation_trust_ceiling` *function* (not the table) authoritative and state the precedence rules. The table is intentionally illustrative. No defect. |
| §5.2 `(n+1)//2` is a "numeric error" (HIGH) | deflated to N8 (LOW) | All three vector values recompute correctly under `(n+1)//2`. Only the natural-language word "majority" is imprecise for even n. Not a numeric/wire defect — reduced to a LOW wording cleanup (N8). |

---

## Implementation-track flag (per BC#6 — flag type only, no prescribed diffs)

| Finding | Type | Track |
|---------|------|-------|
| §A flagship (§3.2 `cross_witness` arity) | wire-actionable, localized | **Autonomous** (next remediation turn, C81) |
| N3, N4, N5 | wire-shape / SDK+vector alignment (one root cause) | **Autonomous** (apply together; N3/N5 touch §2.4 example — apply carefully) |
| N6 | enum-vs-guard | **Autonomous** (spec note) + **SDK-track** (add `recovery_revoked` to `valid_reasons`) |
| N7, N8 | spec-cleanup | **Autonomous** (small) |
| N1, N2 | T3 structural conformance + role-binding (cross-spec; couples C19-M5) | **Design-Q** (coordinate t3-v3 + ontology; closes M5) |
| C36-N9 | Society reciprocity + wrong birth-cert authority (now SAL) | **Operator/cross-track** (couples carry-C23-H1) |
| C36-N11 | identifier scheme | **Design-Q** (carry-C33 B-H1) |
| C19-M3 | error taxonomy (`NoHardwareAnchorError` true gap; quorum reuse path intact) | **Deferred** (carry-C30) |
| C19-M4 | LCT-core reciprocity | **Deferred** (LCT-recip) |
| C19-M5 | ontology sub-dimensions (couples N1) | **Deferred / Design-Q** (resolve with N1) |
| C19-M7 | ATP cost reciprocity | **Deferred** (cross-spec) |

---

## Cross-audit signals

- **Remediation-introduced regression — second generation, same pattern.** #246 (H1 rename) missed §3.5 → C36-N1; #281 (N6 re-signature) missed §3.2 → §A flagship. An **arity/signature change is a rename of the call contract**; the completeness sweep must grep every call site, not just the definition + the one obvious caller. → `[[feedback_remediation_introduced_regression]]`.
- **Token-by-token remediation verification earns its keep (again).** All 11 surviving #281 edits genuinely HELD against the SDK + vectors; but the *same* method that confirmed them is what caught the §3.2 call-site miss and the N3 shape divergence that the C36-N4 fix (which the diff "applied correctly") silently left wrong. Verifying the *claim* (does the algorithm match the canonical inputs?) beats verifying the *edit* (did the line land?). → C56/C64 method.
- **Bidirectional carry re-verification surfaced two state changes** that a "still-open?" checkbox would have missed: C36-N9 **hardened** (SOCIETY_SPEC now defers to SAL, sharpening the wrong-authority citation) and C19-M5 **sharpened** (now couples §B-N1's wire example). Neither resolved; both moved. → C62/C64 method.
- **Test-vectors-as-authority (continued).** N3 is caught only because the shipped vector feeds bare strings; the spec's object-shaped iteration would crash. A vector that *passes* (the algorithm is right) can still expose a *shape* the spec text gets wrong.
- **Subordinate-ontology cluster** (C19-M5) now has a concrete wire counterpart (N1) — the strongest pull yet toward resolving the 8-dimensions-in-the-ontology question, because the flat form is both (a) absent from the ontology and (b) the corpus-deprecated "old flat schema."

---

## Authority Summary

- **SDK** (`binding.py`) is canonical for formula/shape/name (N3, N4, N5, N6; §A flagship).
- **Test vectors** (`binding-vectors.json`) are co-equal canonical for algorithmic conformance and the cross-witness wire shape (N3).
- **`t3-v3-tensors.md` + `t3v3-ontology.ttl`** are canonical for T3 structure (N1, N2; C19-M5).
- **`web4-society-authority-law.md §2.2/§3.4`** is canonical for `Web4BirthCertificate` (C36-N9).
- **`errors.md`** is canonical for W4_ERR codes (C19-M3 + reuse note).
- **`data-formats.md` + LCT-core** own the `lct:web4:` surface form (C36-N11 → carry-C33).

---

*"A remediation is coherent only if its edits reach every section the renamed symbol — and every call site of the re-signatured function — lives in."*
