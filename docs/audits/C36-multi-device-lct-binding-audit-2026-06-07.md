# `multi-device-lct-binding.md` — Delta Re-Audit (C36)

**Audited file**: `web4-standard/core-spec/multi-device-lct-binding.md` (1036 lines, current `main`)
**Audit date**: 2026-06-07
**Audit series**: C-series, C36 (delta re-audit; first-pass was C19 internal-consistency 2026-05-28 + remediation PR #246 / commit `7a8e3d3f`)
**Instrument**: multi-agent **refute-by-default WORKFLOW** — 6 finders (2 §A status + 4 §B new-finding lenses) → adversarial verify (2 independent skeptics per candidate, unanimous-survive). 44 agents total. Per `[[feedback_audit_workflow_adversarial_verify]]`.
**Authority sources** (canonical precedence: SDK + shipped test vectors > spec text):
- **SDK** — `web4-standard/implementation/sdk/web4/binding.py` (618 lines)
- **Test vectors** — `web4-standard/test-vectors/binding/binding-vectors.json` (128 lines, 5 groups)
- **Sibling specs** — `LCT-linked-context-token.md`, `t3-v3-tensors.md`, `atp-adp-cycle.md`, `errors.md`, `SOCIETY_SPECIFICATION.md`, `web4-society-authority-law.md`, `data-formats.md`
- **Ontology** — `web4-standard/ontology/{t3v3-ontology.ttl, web4-core-ontology.ttl, t3v3.jsonld}`

**Result**: §A — **6/6 C19-remediated findings HELD**; **7/7 C19-deferred items STILL-OPEN**. §B — 19 raw new candidates → **11 distinct confirmed** (1 HIGH + 5 MEDIUM + 4 LOW + 1 INFO) after dedup + adversarial verify; 2 deflated (documented in §C).

---

## Executive Summary

This is the first delta re-audit of `multi-device-lct-binding.md` since its C19 first-pass and the #246 remediation. Two headline conclusions:

1. **The #246 remediation was correct but incomplete.** All six wire-actionable C19 findings (H1, H2, H3, M1, M2, M6) are present in the current spec, correctly applied, and still match the canonical SDK + test vectors — a clean 6/6 HELD. None of the seven deferred items (M3, M4, M5, M7, L1–L3) has been resolved by drift elsewhere; all remain open.

2. **The #246 edits introduced four NEW defects** — the dominant pattern of this audit. A partial remediation that *renames* a field and *reframes* method calls into module-level functions must sweep **every** section and **define** every newly-introduced symbol. #246 did neither completely:
   - **N1** — the H1 rename `device_lct` → `device_lct_id` missed §3.5 entirely; `remove_device` still dereferences `.lct_id` (and L655 mixes both forms in one expression). This is the un-remediated remainder of C19-H1.
   - **N3** — the M2 clamp edit calls `constellation_trust_ceiling(...)` in §3.4 but never defines that function anywhere in the spec; §4.2 supplies only a table that cannot resolve the shipped 4-type ceiling vector.
   - **N6** — the H1 reframe replaced `device.record_cross_witness(...)` with a module-level `record_cross_witness(constellation, ...)` that is undefined, and references a `constellation` local that is not in `cross_witness(device_a, device_b)`'s scope. One undefined symbol was traded for two.
   - **N5** (partial) — the H3 formula rewrite left `a_fresh` sourced from a static `device.device_trust.attestation_freshness` with no default, where the SDK derives it dynamically (defaulting to 1.0).

   **Lesson (new, delta-audit-specific): remediation-introduced regression.** When a remediation renames/reframes symbols, the audit-followup MUST re-verify (a) the rename swept all sections, and (b) every newly-introduced module-level function is defined. Recorded for memory.

Beyond the remediation residue, the deepest pre-existing latent defect surfaced is **N2**: §3.4 computes `base_trust` as a `device.trust_weight`-**weighted** average, while the SDK and the shipped `constellation_trust_multi_device` vector use a **uniform** mean. The `trust_weight` field (§2.3) has no SDK counterpart. The divergence is currently *masked* in both shipped vectors because the example constellations clamp to their ceiling — a textbook case of a vector passing under two different algorithms.

**Refute-by-default discipline paid off.** Of 19 raw candidates, the 4 §B lenses independently surfaced the weighted-average issue three times (B1/B7/B13 — collapsed to N2) and the undefined-helper issue three times (B3/B8/B11 — collapsed to N4/N6); title-string dedup missed these, manual synthesis caught them. Two candidates were correctly deflated: one mis-framed N2's underlying issue with a wrong proposed fix; one was a refinement of already-deferred M3.

---

## Severity Ladder

- **HIGH** — Wire-actionable defect verifiable against SDK or test vectors; an implementation conforming to the spec text would produce broken code or fail a shipped vector.
- **MEDIUM** — Internal semantic inconsistency, undocumented spec→SDK algorithmic drift, or cross-document reciprocity gap.
- **LOW** — Informational gap, dangling reference, naming divergence, or unsubstantiated detail — does not by itself break the wire.
- **INFO** — Fidelity note; no correctness impact.

---

## §A — Delta Status of C19 Findings

### A.1 — Remediated wire findings (6/6 HELD)

| C19 | Topic | Status | Evidence (current spec) |
|-----|-------|--------|--------------------------|
| **H1** | `device_lct` → `device_lct_id` (string) | **HELD** | §2.3 L176/185/194, §2.4 L243/279, §3.3 L517–532, §3.6 L744/758 all use `device_lct_id`; `\.device_lct\.` grep = 0. Matches SDK `DeviceRecord.device_lct_id` (`binding.py:179`). *(Caveat: §3.5 is the exception — see N1.)* |
| **H2** | `witness_freshness` name + false half-life docstring | **HELD** | §3.4 L575 `witness_freshness(days_since_last_witness(device))`; §4.3 L819 `def witness_freshness(days_since_witness)`, L838 `days_since_last_witness` helper. `compute_witness_freshness`/`apply_witness_decay`/"Half-life: 30 days" greps = 0. Matches SDK `binding.py:214` + `WITNESS_DECAY_TABLE`. |
| **H3** | 3-factor per-device formula; drop `composite` | **HELD** | §3.4 L574–577 `anchor_weight * w_fresh * a_fresh`; §2.4 device_trust (L286–290) has no `composite`. Matches SDK `binding.py:465–472`. |
| **M1** | recovery quorum ceiling division | **HELD** | §5.2 L906 `max(2, (device_count + 1) // 2)  # ceil(n/2) = majority`; `device_count // 2` grep = 0. Matches SDK `binding.py:244` + vector `recovery_quorum_calculation` (n=5→3, n=6→3, n=10→5). |
| **M2** | TPM2 row + anchor-composition ceiling clamp | **HELD** | §4.2 L802 `Single TPM2 \| 0.75`; §3.4 L595–596 `ceiling = constellation_trust_ceiling(...)` / `min(ceiling, raw_trust)`. Matches SDK `binding.py:107–115, 527–528` + vector `constellation_trust_single_device`→0.75. *(Caveat: ceiling fn undefined in spec — see N3.)* |
| **M6** | `status` field + lifecycle-state prose | **HELD** | §2.3 L182/191/200 + §2.4 L292 `"status"`; §2.4 L296–300 active\|suspended\|revoked prose. Matches SDK `DeviceStatus` (`binding.py:81–86`). |

**Remediation quality: clean.** Every edit landed and still matches canonical authority. The two caveats (N1, N3) are *new* defects in adjacent code, not regressions of the remediated lines themselves.

### A.2 — Deferred items (7/7 STILL-OPEN)

| C19 | Topic | Status | Note |
|-----|-------|--------|------|
| **M3** | 3 exception classes absent from `errors.md` W4_ERR taxonomy | **STILL-OPEN** | `errors.md` adds nothing for QUORUM/RECOVERY/ANCHOR. Sharpening note from verify pass: device-removal & recovery quorum could reuse the existing canonical `W4_ERR_WITNESS_QUORUM` (`errors.md:66`, 409) per `errors.md §9` "SHOULD reuse"; only `NoHardwareAnchorError` is a true gap. Fold into **carry-C30 error-canonicity**. |
| **M4** | `LCT-linked-context-token.md` does not acknowledge §7.1 extension | **STILL-OPEN** | LCT-core has no `device_constellation`/`cross_device_witnesses`/`root_attestation` section. (Now joined by N9 — the §7.2 Society side.) |
| **M5** | 8 T3 sub-dimensions absent from `t3v3-ontology.ttl` | **STILL-OPEN** | Ontology defines only 3 root dims + open `web4:subDimensionOf`; no named sub-dimension instances. `t3-v3-tensors.md` references `constellation_coherence` only in a §10.4 "Simulation-Only / not canonical" disclaimer. Cross-corpus design-Q. |
| **M7** | §7.3 ATP costs not aligned with `atp-adp-cycle.md` | **STILL-OPEN** | §7.3 costs (enroll 10 / witness 1 / removal 5 / recovery 20) have no counterpart in `atp-adp-cycle.md`. Cross-spec design-Q. |
| **L1** | `"mutual": true` redundant under §3.3 | **STILL-OPEN** | §2.4 cross_device_witnesses still carries `"mutual": true`. Spec-cleanup. |
| **L2** | §2.4 schema omits `revocation` object used by §3.5 | **STILL-OPEN** | §3.5 L685–686 read `device_to_remove.revocation.reason`/`.ts`; §2.4 schema defines no `revocation` object. Spec-cleanup. |
| **L3** | §5.3 "24h review window" unsubstantiated | **STILL-OPEN** | No derivation/citation. Spec-cleanup. |

No deferred item was resolved by drift in any sibling spec or the ontology since 2026-05-29.

---

## §B — New Confirmed Findings (11)

> Numbering N#. "Introduced by #246" flags a remediation-induced regression. Classification: `wire-actionable` / `cross-spec` / `spec-cleanup` / `design-Q`. Adversarially verified (unanimous-survive, 2 skeptics).

### N1 — [HIGH] §3.5 `remove_device` dereferences `.lct_id`; canonical field is `device_lct_id` (un-remediated remainder of C19-H1) · *introduced-by-#246 (incomplete sweep)* · wire-actionable

§3.5 is the **only** section still using the pre-#246 `.lct_id` access:
- L655 `if d.device_lct_id != device_to_remove.lct_id` — **mixes both forms in one expression**
- L665 `"device_to_remove": device_to_remove.lct_id`
- L683 `root_lct.device_constellation.remove_device(device_to_remove.lct_id)`

The device-record field is `device_lct_id` everywhere else (§2.3 L176, §2.4 L243, §3.6 L758) and on the SDK `DeviceRecord` (`binding.py:179`); there is no `.lct_id` attribute. A consumer implementing §3.5 faithfully gets an `AttributeError`. #246-H1 renamed §2.3/§2.4/§3.3/§3.6 but missed §3.5. **Resolution**: `device_to_remove.lct_id` → `device_to_remove.device_lct_id` (3 sites). Autonomous-actionable.

### N2 — [MEDIUM] §3.4 `base_trust` is a `trust_weight`-weighted average; SDK + vector use a uniform mean · wire-actionable

§3.4 L578 `device_trusts.append((device, device_trust, device.trust_weight))`; L581–583 `weighted_sum = sum(t*w …)/weight_total` — each device weighted by `device.trust_weight` (§2.3 examples 0.4/0.35/0.25). The SDK uses an **unweighted** mean: `binding.py:512` `total_weight += 1.0` per device; `DeviceRecord` has **no** `trust_weight` field. Vector `constellation_trust_multi_device` reason: `avg(0.95,0.98,0.93)=0.9533` — an explicit simple mean. Currently *masked* because both example constellations clamp to ceiling (weighted ≈0.9555 vs uniform 0.9533, both ≥0.95). **Resolution**: drop the `trust_weight` weighting (uniform mean) and drop/annotate the orphan `trust_weight` field. Autonomous-actionable (touches §2.3 example — apply carefully). *Note: the `trust_weight` field values are NOT separately canonical — see §C deflation #1; the defect is the weighting algorithm, not the example numbers.*

### N3 — [MEDIUM] §3.4 `constellation_trust_ceiling()` is called but never defined; §4.2 table cannot resolve the 4-type ceiling vector · *introduced-by-#246-M2* · wire-actionable

§3.4 L595 `ceiling = constellation_trust_ceiling(root_lct.device_constellation)` and §4.2 L808 reference the function normatively, but no `def constellation_trust_ceiling(...)` exists in the spec (unlike the sibling §3.4 helpers `compute_coherence_bonus` L607 and `compute_cross_witness_density` L624, which are defined inline). The §4.2 table alone cannot reproduce vector `trust_ceiling_by_config` case `[phone, fido2, tpm2, software] → 0.98`: the SDK (`binding.py:395–442`) subtracts `software` before counting hardware anchors and skips the exact-3 `phone_fido2_tpm` row (0.95) when a 4th type is present — rules that exist **only** in the SDK. A spec-only implementer could plausibly return 0.95. **Resolution**: inline the ceiling-derivation algorithm (mirroring `binding.py:395`) or add the software-exclusion + named-vs-generic precedence rules to §4.2, and cross-reference the definition from §3.4. Autonomous-actionable.

### N4 — [MEDIUM] §3.4 cross-witness density uses undefined `is_recent()` + a `/2` formula that diverges from the SDK unique-mutual-pair set · wire-actionable

§3.4 L633–639: `actual_witnesses = sum(len([w … if is_recent(w)]) …) / 2`, then `min(1.0, actual_witnesses/possible_pairs)`. `is_recent` is undefined. The SDK (`binding.py:371–392`) builds a deduped set of in-constellation mutual pairs (`pair = tuple(sorted([d.device_lct_id, w_id]))` with `w_id in device_ids` guard) and applies **no** recency filter. For a full mesh both give 1.0, but for partial/one-directional/duplicated witnessing they diverge: the spec's `/2` over-counts and lacks the set-membership guard. **Resolution**: either define `is_recent` (and its window) or remove it to match the SDK, and adopt the unique-pair-set computation. Autonomous-actionable.

### N5 — [MEDIUM] §3.4 `attestation_freshness` read statically with no default; SDK derives it dynamically (defaults 1.0) · *partially introduced-by-#246-H3* · wire-actionable

§3.4 L576 `a_fresh = device.device_trust.attestation_freshness` reads a stored scalar with no documented default. The SDK (`binding.py:468–470`) sets `a_fresh = 1.0` then overrides from `device.latest_attestation.freshness_factor` if present; `DeviceRecord` has no `device_trust` field. Vectors `constellation_trust_single_device`/`_multi_device` supply no `attestation_freshness` yet assume `a_fresh = 1.0`. The spec is undefined for those inputs. **Resolution**: state that `attestation_freshness` defaults to 1.0 when no attestation proof is present (and ideally source it from the attestation envelope). Autonomous-actionable.

### N6 — [LOW] §3.3 `record_cross_witness(constellation, …)` is undefined and `constellation` is out of scope · *introduced-by-#246-H1* · spec-cleanup

§3.3 L538 `record_cross_witness(constellation, device_a.device_lct_id, device_b.device_lct_id, utc_now())`. No `def record_cross_witness(...)` exists in the spec, and `constellation` is not a parameter of `cross_witness(device_a, device_b)` (L504). The #246 reframe from the method form traded one undefined symbol (`device.record_cross_witness`) for two. The SDK defines `record_cross_witness(constellation, device_a_id, device_b_id, timestamp)` (`binding.py:534`). **Resolution**: add the function definition (or a "see SDK" annotation) and thread `constellation` into the `cross_witness` signature. Autonomous-actionable.

### N7 — [LOW] §3.4 constant named `ANCHOR_WEIGHTS`; canonical SDK constant is `ANCHOR_TRUST_WEIGHT` · wire-actionable

§3.4 L574/L600 use `ANCHOR_WEIGHTS`; the SDK exports `ANCHOR_TRUST_WEIGHT` (`binding.py:91`, `__all__` L35–63). Values match (0.95/0.98/0.93/0.40); only the identifier diverges. #246 aligned other identifiers to the SDK but left this one. **Resolution**: rename `ANCHOR_WEIGHTS` → `ANCHOR_TRUST_WEIGHT`. Autonomous-actionable.

### N8 — [LOW] §3.5 quorum check counts unfiltered `authorizing_devices`, contradicting its own docstring and the SDK · spec-cleanup

§3.5 docstring L651 "Quorum of **remaining** devices"; body L657 `if len(authorizing_devices) < … recovery_quorum` counts the raw argument and **discards** the `remaining` set computed at L654–655. The SDK intersects: `binding.py:338–340` `authorizing_active = active_ids & set(authorizing_devices)`. Docstring-vs-body contradiction + SDK divergence. **Resolution**: count `len(set(authorizing_devices) ∩ remaining)`. Autonomous-actionable.

### N9 — [MEDIUM] §7.2 imposes four Society `MUST` obligations the cited `SOCIETY_SPECIFICATION.md` does not acknowledge, and cites the wrong birth-certificate authority · cross-spec / design-Q

§7.2 (L1003–1009) requires Societies to "Support multi-device birth certificate issuance / Verify hardware attestations / Maintain device constellation state / Enforce recovery quorum", and §3.1/§3.6 call `society.issue_multi_device_birth_certificate(...)` / `society.process_recovery(...)`. A grep of `SOCIETY_SPECIFICATION.md` for any device/constellation/recovery/birth-cert term returns **zero** matches. Separately, the canonical `Web4BirthCertificate` lives in `web4-society-authority-law.md §2.2` (per `entity-types.md:161`), not `SOCIETY_SPECIFICATION.md`, so the issuance obligation cites the wrong owner. Parallel to deferred M4 but on the §7.2 Society integration claim. **Couples carry-C23-H1** (canonical BirthCertificate shape). Cross-spec design-Q — not self-resolvable here.

### N10 — [INFO] §3.4 returns unrounded trust; SDK returns `round(min(…), 4)` · spec-cleanup

§3.4 L596 `min(ceiling, raw_trust)`; SDK `binding.py:528` `round(min(trust, ceiling), 4)`. Not observable in the (exact-ceiling) shipped vectors. **Resolution**: add `round(…, 4)` for fidelity. Autonomous-actionable but cosmetic.

### N11 — [LOW] Identifier scheme: spec uses entity-type-segmented LCT IDs not emitted by the LCT-core canonical generator · design-Q (carry-C33)

§2.3/§2.4 use `lct:web4:root:…`, `lct:web4:device:phone:…`, `…:fido2:…`, `…:laptop:…`. The LCT-core canonical generator (`LCT-linked-context-token.md:260`) emits `lct:web4:<mb32>` with no entity-type segment. Consistent with LCT-core's segmented *examples* but not its normative generator. `data-formats.md §1.3` declares the `lct:web4:` surface form an open scheme decision. Records the multi-device-specific new segments (`root:`, `device:phone:`…) as additional instances feeding **carry-C33 B-H1**. NOT self-resolvable. *(The `did:web4:device:` subject usage at §2.4 L244 is consistent with `data-formats.md §1.2` and is NOT flagged.)*

---

## §C — Deflated Candidates (2, documented for honesty)

| Raw | Claim | Why deflated |
|-----|-------|--------------|
| §2.3 `trust_weight` values (0.4/0.35/0.25) "should equal anchor weights 0.95/0.98/0.93" | refuted 1/2 | The proposed **fix is wrong**: SDK `DeviceRecord` has no `trust_weight` field, and `HardwareAnchor.trust_weight` (a type-derived property) is a *different* quantity than the spec's per-device averaging weight. The genuine adjacent defect (weighted-vs-uniform average) is captured as **N2**; the example *values* are not separately canonical. Correctly not counted as a distinct finding. |
| Reuse `W4_ERR_WITNESS_QUORUM` instead of `InsufficientQuorumError`/etc. | refuted 1/2 | A *refinement/resolution* of already-deferred **M3**, routed to **carry-C30 error-canonicity**, not an independent new contradiction. Folded into §A.2 M3 note (two of three exceptions can reuse the existing 409 code; only `NoHardwareAnchorError` is a true gap). |

---

## Implementation-track flag (per BC#6 — flag type only, no prescribed diffs)

| Finding | Type | Track |
|---------|------|-------|
| N1, N6, N7, N10 | wire-actionable, localized | **Autonomous** (next remediation turn) |
| N2, N3, N4, N5, N8 | wire-actionable, algorithm/schema alignment to SDK+vectors | **Autonomous** (apply carefully; N2 touches §2.3 example) |
| N9 | cross-spec reciprocity + wrong-authority citation | **Design-Q** (couples carry-C23-H1; parallels M4) |
| N11 | identifier-scheme | **Design-Q** (carry-C33 B-H1) |
| C19 M3/M4/M5/M7 | cross-corpus / cross-spec | **Deferred** (carry-C30 / LCT-recip / ontology / ATP) |
| C19 L1/L2/L3 | spec-cleanup | **Autonomous** (small) |

---

## Cross-audit signals

- **Remediation-introduced regression** (NEW pattern). #246 resolved 6/6 wire findings correctly but introduced N1 (incomplete rename), N3 (undefined ceiling fn), N6 (undefined module-level fn + out-of-scope local), and N5-partial. Delta re-audits MUST verify that renames swept all sections and that every reframed module-level function is defined. This is the C-series counterpart to the audit-side `[[feedback_auditor_blindspot_pattern]]`: remediation has its own blindspot — the *adjacent* code the edit reaches into.
- **Test-vectors-as-authority** (continued). N2, N3, N5 all turn on the shipped `binding-vectors.json`; N2/N3 expose vectors that *pass under the wrong algorithm* because of ceiling-clamp masking — a reminder that vector-passing ≠ algorithm-correct.
- **Canonical-errors-taxonomy cluster** extends: M3 still open, now with a concrete reuse path (`W4_ERR_WITNESS_QUORUM`) for 2 of 3 → carry-C30.
- **Subordinate-ontology cluster**: M5 still open (4-audit convergence unchanged).

---

## Authority Summary

- **SDK** (`binding.py`) is canonical for formula/shape/name (N1, N2, N3, N4, N5, N6, N7, N8, N10).
- **Test vectors** (`binding-vectors.json`) are co-equal canonical for algorithmic conformance (N2, N3, N5).
- **`errors.md`** is canonical for W4_ERR codes (M3 + reuse note).
- **`web4-society-authority-law.md §2.2`** is canonical for `Web4BirthCertificate` (N9).
- **`data-formats.md` + LCT-core** own the `lct:web4:` surface form (N11 → carry-C33).

---

*"Identity is coherence across witnesses. A remediation is coherent only if its edits reach every section the renamed symbol lives in."*
