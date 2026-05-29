# `multi-device-lct-binding.md` — Internal-Consistency Audit (C19)

**Audited file**: `web4-standard/core-spec/multi-device-lct-binding.md` (1007 lines, last modified 2026-05-13)
**Audit date**: 2026-05-28
**Audit series**: C-series internal-consistency sweep, C19 (continues C12-C18)
**Authority sources**:
- **SDK canonical** — `web4-standard/implementation/sdk/web4/binding.py` (619 lines)
- **Sibling specs** — `LCT-linked-context-token.md`, `t3-v3-tensors.md`, `atp-adp-cycle.md`, `errors.md`
- **Shipped test vectors** — `web4-standard/test-vectors/binding/binding-vectors.json` (128 lines, 5 vector groups: witness_freshness_decay, recovery_quorum_calculation, coherence_bonus_by_diversity, trust_ceiling_by_config, constellation_trust_*)
- **Ontology** — `web4-standard/ontology/{web4-core-ontology.ttl,t3v3-ontology.ttl,t3v3.jsonld,r7-action.jsonld}`

**Finding count**: 13 (3 HIGH + 7 MEDIUM + 3 LOW) + 4 DEMOTED

---

## Executive Summary

This is the first internal-consistency audit on `multi-device-lct-binding.md`. The spec is the longest un-audited core-spec file and predates the C-series sweep on the broader corpus. Findings split cleanly into two groups: **wire-actionable internal defects** (H1, H2, H3, M1, M2, M6 — six findings localized to the spec text and verifiable against shipped SDK + test vectors) and **cross-document gaps** (M3, M4, M5, M7 — four findings where this spec asserts integration with another spec that the other spec does not acknowledge).

Notable cross-audit clusters this audit extends:

- **Canonical-errors-taxonomy cluster** (M3): C16-H1 + C17-M4 + C18-M2 + C19-M3 = **4-audit convergence**. Each audit independently finds spec-level exception names without W4_ERR mapping in `errors.md`.
- **Subordinate-ontology cluster** (M5): C16-M8 + C17-M1 + C18-M6 + C19-M5 = **4-audit convergence**. Each audit finds spec-cited semantic terms (predicates, dimensions, classes) absent from `web4-core-ontology.ttl` / `t3v3-ontology.ttl`.

A new pattern reinforced here: **shipped test vectors as first-class audit authority** (established C18-H3 against `acp-jsonld-validation.json`, now reused at C19-M1 and C19-M2 against `binding-vectors.json`). Test vectors disagree with spec normative content in two distinct ways:

1. **M1** — Spec §5.2 says `device_count // 2` (floor); SDK and test vectors agree on `(n+1)//2` (ceiling = true majority). Test vector for n=5 explicitly expects 3, which is what SDK returns. Spec returns 2.
2. **M2** — Spec §3.4 final formula caps trust at `min(1.0, ...)`; SDK and test vectors agree the cap is the **anchor-composition-derived ceiling** from §4.2. Test vector `constellation_trust_single_device` states reason: "0.95 base capped at 0.75 single_phone_se ceiling".

In both cases the shipped wire contract is the SDK + test vector position; the spec is wrong.

---

## Severity Ladder

- **HIGH** — Wire-actionable defect verifiable against SDK or test vectors; an implementation conforming to the spec text would fail the shipped test vector.
- **MEDIUM** — Internal semantic inconsistency, undocumented spec→SDK drift, or cross-document gap with a named cluster.
- **LOW** — Informational gap, schema redundancy, or unsubstantiated parameter — does not affect wire correctness.

---

## HIGH (3)

### H1 — `device_lct` shape inconsistency: schema (string) vs pseudocode (object with `.lct_id` and methods)

**Spec sites**:

`§2.3 Root LCT Structure` defines `device_constellation.devices[].device_lct` as a **string identifier**:

> L176: `        "device_lct": "lct:web4:device:phone:...",`
> L185: `        "device_lct": "lct:web4:device:fido2:...",`
> L194: `        "device_lct": "lct:web4:device:laptop:...",`

`§2.4 Device LCT Structure` likewise treats it as a string at L279:

> L279: `      "device_lct": "lct:web4:device:laptop:...",`

But §3.3 / §3.5 / §3.6 pseudocode treat `device_lct` as an **object with `.lct_id` attribute** (and in §3.3, with methods):

> L510: `        device_lct=device_a.device_lct`
> L514: `        device_lct=device_b.device_lct`
> L524: `        "device_a": device_a.device_lct.lct_id,`
> L525: `        "device_b": device_b.device_lct.lct_id,`
> L531: `    device_a.device_lct.record_cross_witness(device_b.device_lct.lct_id)`
> L532: `    device_b.device_lct.record_cross_witness(device_a.device_lct.lct_id)`
> L641: `                 if d.device_lct.lct_id != device_to_remove.lct_id]`
> L728: `            "device_lct": device.device_lct.lct_id,`
> L744: `        if device.device_lct.lct_id not in [d.device_lct.lct_id for d in recovery_devices]:`

**BC#5 sweep result** (full-file grep for `device_lct`): 5 string-form schema sites (L176, L185, L194, L279, L728); 7 line positions with `.lct_id` access carrying 11 syntactic accesses (L524, L525, L531, L532, L641, L728, L744 — L531/L532 each have 2 accesses, L744 has 2); 4 sites treating `device_lct` as object reference for parameter/method (L510, L514, L518, L519) plus method calls at L531/L532.

**SDK canonical** — `web4-standard/implementation/sdk/web4/binding.py:179`:

> `    device_lct_id: str`

(SDK uses a flat field named `device_lct_id` of type `str`, never an `LCT` object. Throughout the SDK, when device identity is needed, the string ID is used directly — there is no `.lct_id` attribute access on a `device_lct` object.)

**Why HIGH**: A spec consumer reading §2.3/§2.4 will produce a schema where `device_lct` is a string. A spec consumer reading §3.3/§3.5/§3.6 will produce code that accesses `.lct_id` and `.record_cross_witness` methods. These cannot both be correct. The SDK has resolved the question by renaming the schema field to `device_lct_id` (no ambiguity), but the spec still carries both interpretations.

**Recommended resolution direction** (informational — remediation is a separate PR): align spec to SDK by renaming schema field `device_lct` → `device_lct_id` (matching `lct_id` convention used elsewhere in §2.3 — e.g. `lct_id` at L163, L213, L262) and replacing `device.device_lct.lct_id` → `device.device_lct_id` throughout pseudocode (∼7 line edits in §3.3, §3.5, §3.6).

**Cross-audit signal**: Field-shape vs pseudocode-shape mismatch is similar to C13-T3-v3 H1 (weights swapped) but more pervasive (here it spans 3 sections, not 1 line).

---

### H2 — Caller/callee name mismatch: `compute_witness_freshness` (§3.4) vs `apply_witness_decay` (§4.3)

**Spec sites**:

`§3.4 Trust Computation Across Devices`, inside `compute_constellation_trust`:

> L564: `        freshness = compute_witness_freshness(device)`

But there is no function named `compute_witness_freshness` defined anywhere in this spec. The only spec-defined function with witness-related decay semantics is in `§4.3 Trust Decay`:

> L798: `def apply_witness_decay(device):`
> L799: `    """`
> L800: `    Trust decays if device hasn't been witnessed.`
> L801: `    `
> L802: `    Half-life: 30 days without witnessing`
> L803: `    """`
> L804: `    days_since_witness = (utc_now() - device.last_witnessed).days`
> ... (table-based decay function returning factor in [0.3, 1.0])

**SDK canonical** — `web4-standard/implementation/sdk/web4/binding.py:214`:

> `def witness_freshness(days_since_witness: int) -> float:`

(SDK exports `witness_freshness`, not `compute_witness_freshness` and not `apply_witness_decay`.)

**Why HIGH**: A spec consumer implementing the §3.4 algorithm faithfully will write a call to a function that the spec never defines. The closest match (§4.3 `apply_witness_decay`) has a different name and takes a `device` parameter rather than `days_since_witness`. The shipped SDK uses a third name (`witness_freshness`). This is a 3-way name collision within the same spec + SDK that no spec consumer can resolve without out-of-spec context.

**Bonus observation** (does not change severity): the §4.3 L802 docstring claim "Half-life: 30 days without witnessing" is mathematically false against its own function body. At 30 days the function returns 0.9, not 0.5. At 180 days it returns 0.5, so the actual half-life (if any) is ~180 days. The SDK at `binding.py:218` carries the same misleading "Per spec §4.3" docstring reference but the actual table values are identical. Flagged as supplemental evidence but counted under H2 — not a separate finding (M-category would be over-counting).

**Recommended resolution direction**: rename §3.4 L564 call to `witness_freshness(days_since_last_witness(device))` (matching SDK convention) and rename §4.3 L798 definition to `witness_freshness(days_since_witness)` with the days parameter (matching SDK signature). The "Half-life: 30 days" docstring claim should be removed or replaced with "see decay table".

---

### H3 — §3.4 trust formula structural conflict with §2.4 schema and SDK

**Spec sites**:

`§2.4 Device LCT Structure` defines a `device_trust` object with four fields:

> L286: `  "device_trust": {`
> L287: `    "anchor_strength": 0.95,`
> L288: `    "attestation_freshness": 0.98,`
> L289: `    "cross_witness_score": 0.88,`
> L290: `    "composite": 0.93`
> L291: `  }`

The example values (0.95, 0.98, 0.88, 0.93) imply `composite` is an aggregate of the three preceding fields — under any plausible aggregation rule (arithmetic mean = 0.937 ≈ 0.93; product = 0.95 × 0.98 × 0.88 = 0.819 ≠ 0.93; so mean-like, not product-like). Critically, `composite` includes `anchor_strength` (0.95).

`§3.4 Trust Computation Across Devices` formula at L562-565:

> L562: `    for device in active:`
> L563: `        anchor_weight = ANCHOR_WEIGHTS[device.anchor_type]`
> L564: `        freshness = compute_witness_freshness(device)`
> L565: `        device_trust = anchor_weight * freshness * device.device_trust.composite`

This multiplies `anchor_weight` (which is 0.95 for `phone_secure_element` per L587 `ANCHOR_WEIGHTS`) by `device.device_trust.composite` (which already includes `anchor_strength` per §2.4). The same anchor-strength factor is applied twice.

**SDK canonical** — `web4-standard/implementation/sdk/web4/binding.py:445-472`:

> L465: `    base = device.anchor.trust_weight`
> L466: `    w_fresh = witness_freshness(days_since_witness)`
> L467: ` `
> L468: `    a_fresh = 1.0`
> L469: `    if device.latest_attestation is not None:`
> L470: `        a_fresh = device.latest_attestation.freshness_factor`
> L471: ` `
> L472: `    return base * w_fresh * a_fresh`

SDK formula = **anchor_weight × witness_freshness × attestation_freshness**. No `composite` term. No double-count.

**Why HIGH**: Either §2.4 schema or §3.4 formula must change for the spec to be internally consistent. Under the schema's natural reading, the formula triple-counts anchor strength (anchor_weight × composite-which-includes-anchor_strength). Under the formula's natural reading, `composite` is something other than an aggregate of the schema's three components — but the schema example values prove it is mean-like. The SDK has resolved this by dropping `composite` from the data model entirely and using a 3-factor formula (anchor × witness-freshness × attestation-freshness).

**Bonus observation** (per BC#4 evidence): the spec's §3.4 also references `cross_witness_score` indirectly via `device.device_trust.composite` — but at the constellation level §3.4 separately computes `witness_density = compute_cross_witness_density(active)` (L577) and multiplies by `(1 + witness_density × 0.1)` (L581). So cross-witness density gets counted **twice** as well — once inside `composite` per the schema, once at the constellation aggregate.

**Recommended resolution direction**: drop the `device_trust.composite` field from §2.4 (SDK does not model it), and rewrite §3.4 L565 to match SDK: `device_trust = anchor_weight * witness_freshness * attestation_freshness`.

---

## MEDIUM (7)

### M1 — `default_recovery_quorum` floor-div bug vs majority claim

**Spec site** — `§5.2 Recovery Quorum Selection` at L866-877:

> L866: `def default_recovery_quorum(device_count):`
> L867: `    """`
> L868: `    Minimum devices needed for recovery.`
> L869: ` `
> L870: `    Balances security vs. recoverability.`
> L871: `    """`
> L872: `    if device_count <= 2:`
> L873: `        return device_count  # All devices required`
> L874: `    elif device_count <= 4:`
> L875: `        return 2`
> L876: `    else:`
> L877: `        return max(2, device_count // 2)  # Majority`

For `device_count = 5`, `5 // 2 = 2`, so the function returns `max(2, 2) = 2`. The inline comment claims "Majority", but **2 of 5 is not a majority** (majority of 5 is 3).

**SDK canonical** — `web4-standard/implementation/sdk/web4/binding.py:232-244`:

> L232: `def default_recovery_quorum(device_count: int) -> int:`
> ... 
> L244: `    return max(2, (device_count + 1) // 2)  # ceil(n/2) = majority`

SDK uses `(n+1)//2` = ceiling division = true majority. For n=5: `(5+1)//2 = 3`.

**Shipped test vector** — `web4-standard/test-vectors/binding/binding-vectors.json:23-34`:

> ```json
> {"input_device_count": 5, "expected_quorum": 3},
> {"input_device_count": 6, "expected_quorum": 3},
> {"input_device_count": 10, "expected_quorum": 5}
> ```

Test vector for n=5 expects 3, n=10 expects 5 — both consistent with SDK ceiling formula and inconsistent with spec floor formula. The spec algorithm fails its own shipped test vector for n ∈ {5, 7, 9, …}.

**Why MEDIUM not HIGH**: The wire-actionable consequence is that an implementation following the spec text fails the shipped test vector — but the test vector authority pattern (precedent C18-H3) was treated as MEDIUM-equivalent there. Pattern continues here. (One could argue HIGH given the conformance test failure; classified MEDIUM for ladder consistency with the formula's other characteristics — small input range affected, recovery is sometimes lenient.)

**BC#3 corpus-grep**: `grep -rn "default_recovery_quorum\|recovery_quorum" web4-standard/` confirms the function definition exists at exactly two sites: spec §5.2 L866 and SDK binding.py:232. No other definitions to disambiguate.

**Cross-audit signal**: This is the second C-series spec where shipped test vectors disagree with spec algorithm (after C18-H3 against `acp-jsonld-validation.json`). Strengthens "test vectors as first-class authority" rule.

---

### M2 — §4.2 trust ceiling table + §3.4 trust formula structurally decoupled

**Spec sites**:

`§4.2 Trust Ceiling by Configuration` at L783-791:

> | Configuration | Max Trust |
> |---------------|-----------|
> | Single software key | 0.40 |
> | Single phone SE | 0.75 |
> | Single FIDO2 | 0.80 |
> | Phone + FIDO2 | 0.90 |
> | Phone + FIDO2 + TPM | 0.95 |
> | 3+ diverse hardware anchors | 0.98 |

**Three structural problems with this table + the §3.4 formula that should use it**:

**(a) Missing "Single TPM2" row.** The table covers single-phone-SE, single-FIDO2, single-software — but skips single-TPM2.

SDK has it — `binding.py:107-115`:

> L107: `CONSTELLATION_TRUST_CEILING: Dict[str, float] = {`
> L108: `    "single_software": 0.40,`
> L109: `    "single_phone_se": 0.75,`
> L110: `    "single_fido2": 0.80,`
> L111: `    "single_tpm2": 0.75,`
> L112: `    "phone_fido2": 0.90,`
> L113: `    "phone_fido2_tpm": 0.95,`
> L114: `    "3_plus_diverse": 0.98,`
> L115: `}`

SDK row for `single_tpm2` is 0.75; spec table has no row.

**(b) §3.4 formula doesn't reference the §4.2 table.** Spec §3.4 L580-582:

> L580: `    constellation_trust = min(1.0,`
> L581: `        base_trust * (1 + coherence_bonus) * (1 + witness_density * 0.1)`
> L582: `    )`

The cap is `1.0` (universal), not the anchor-composition-derived ceiling from §4.2.

SDK formula at `binding.py:524-528`:

> L524: `    trust = base_trust * (1 + cb) * (1 + cwd * 0.1)`
> L525: ` `
> L526: `    # Clamp to ceiling`
> L527: `    ceiling = constellation_trust_ceiling(constellation)`
> L528: `    return round(min(trust, ceiling), 4)`

SDK clamps to `constellation_trust_ceiling(constellation)` which derives the ceiling from anchor composition via the table.

**(c) §3.4 docstring at L552 claims `"Key insight: More devices = higher trust ceiling"` — but the formula has no ceiling logic that varies with device composition. The docstring is unsupported by the function body.**

**Shipped test vector** — `binding-vectors.json:88-99`:

> ```json
> {
>   "name": "constellation_trust_single_device",
>   "input": {"anchor_type": "phone_secure_element", "days_since_witness": 0},
>   "expected": {"trust": 0.75, "reason": "0.95 base capped at 0.75 single_phone_se ceiling"}
> }
> ```

Test vector explicitly states the cap is 0.75 (single_phone_se ceiling), NOT 1.0 (universal cap). Spec formula would return 0.95 × 1.0 × 1.0 × 1.0 = 0.95 (capped at 1.0); test vector expects 0.75.

**BC#3 corpus-grep**: `grep -rn "single_tpm2\|single_phone_se" web4-standard/` returns matches only in `binding.py:109-111,409-415` and `binding-vectors.json:67-86`. No matches in the spec — confirms the table key naming was not exported into the spec text.

**Why MEDIUM**: All three sub-problems unify under a single root cause — the spec hasn't materially integrated the trust-ceiling concept into the trust formula. SDK has done the integration. Spec needs to follow.

**Why bundled (BC#2 combinability rationale)**: (a), (b), (c) all point to the same design integration failure between §3.4 and §4.2. Per the C18 H2/M1 structural-bundling pattern (when adjacent findings have shared root cause, bundle them), these belong together. Not bundled with M1 because M1 is the `default_recovery_quorum` function, structurally orthogonal to trust computation.

---

### M3 — Multi-device exception classes absent from `errors.md` W4_ERR taxonomy

**Spec sites** — three undefined exception classes raised in normative pseudocode:

> L644: `        raise InsufficientQuorumError(`
> L703: `        raise InsufficientRecoveryQuorum(`
> L710: `        raise NoHardwareAnchorError(`

None of these have a `W4_ERR_*` code mapped in the canonical errors taxonomy.

**BC#3 corpus-grep** — `grep -rn "W4_ERR_BINDING\|W4_ERR_MULTI_DEVICE\|W4_ERR_QUORUM\|W4_ERR_RECOVERY\|W4_ERR_ENROLLMENT\|W4_ERR_ANCHOR\|InsufficientQuorum\|NoHardwareAnchor\|RecoveryQuorum" web4-standard/core-spec/errors.md`:

> L14: `  "code": "W4_ERR_BINDING_EXISTS",`
> L33: `### 2.1 Binding Errors (W4_ERR_BINDING_*)`
> L37: `| W4_ERR_BINDING_EXISTS | Binding Already Exists | 409 | Entity already has an active binding |`
> L38: `| W4_ERR_BINDING_INVALID | Invalid Binding | 400 | Binding parameters are malformed |`
> L39: `| W4_ERR_BINDING_REVOKED | Binding Revoked | 410 | Referenced binding has been revoked |`
> L40: `| W4_ERR_BINDING_PROOF_FAIL | Binding Proof Failed | 401 | Binding proof signature verification failed |`

`errors.md` has 4 W4_ERR_BINDING_* codes, but none for QUORUM / RECOVERY / ENROLLMENT / ANCHOR. The three multi-device exceptions are spec-local.

**SDK behavior** — `web4-standard/implementation/sdk/web4/binding.py` uses generic `ValueError` everywhere for these conditions (sites L222, L272, L279, L284, L287, L324, L333, L335, L341, L557, L559, L561, L563), bypassing the W4_ERR taxonomy entirely.

**Why MEDIUM**: Same pattern as C16-H1 (SAL undefined `WitnessDeficit`), C17-M4 (`dictionary-entities.md` bare exceptions without W4_ERR_DICT mapping), and C18-M2 (acp-framework.md undefined ACP error classes). **This is the 4th C-series spec to surface the canonical-errors-taxonomy gap** — the cross-audit cluster now spans C16-H1 + C17-M4 + C18-M2 + C19-M3.

**Cross-audit cluster status** (per BC#7): canonical-errors-taxonomy = 4-audit convergence. Document-not-solve per C-series BC#6 corpus-normalization-is-own-scope rule.

---

### M4 — §7.1 LCT-extension claim unilateral; `LCT-linked-context-token.md` does not acknowledge the extension

**Spec site** — `§7.1 LCT Core Spec` at L967-972:

> L967: `### 7.1 LCT Core Spec`
> L968: ` `
> L969: `This protocol extends [`LCT-linked-context-token.md`](LCT-linked-context-token.md):`
> L970: `- Adds `device_constellation` to root LCT structure`
> L971: `- Adds `root_attestation` and `cross_device_witnesses` to device LCT`
> L972: `- Extends T3 tensor with `hardware_binding_strength` and `constellation_coherence``

**BC#3 corpus-grep** — `grep -n "device_constellation\|cross_device_witnesses\|root_attestation\|binding_mode\|multi.device\|hardware_anchor" web4-standard/core-spec/LCT-linked-context-token.md`:

> L68: `    "hardware_anchor": "eat:mb64:hw:...",`
> L235: `def create_lct_binding(entity_type, private_key, hardware_anchor=None):`
> L245: `        "hardware_anchor": hardware_anchor,  # Optional EAT token`

LCT spec mentions `hardware_anchor` (a generic optional EAT field), but has **zero references** to `device_constellation`, `cross_device_witnesses`, `root_attestation`, `binding_mode`, or any multi-device concept. The LCT spec does not acknowledge the extension declared by §7.1.

**Why MEDIUM**: The extension claim is one-sided. The LCT spec needs a forward-reference to multi-device-lct-binding.md (and ideally a stub showing the optional `device_constellation` and `root_attestation` fields). Until that's done, any LCT-spec-only implementer will produce an LCT structure that the multi-device protocol cannot consume.

**Note on cross-spec normalization scope**: per BC#6 (C-series cross-corpus normalization is its own scope), this finding documents-not-solves the gap. A future LCT-spec audit (C20+) would flag the absence from the LCT side.

---

### M5 — §4.1 + §2.3 T3 sub-dimensions not defined in `t3v3-ontology.ttl`

**Spec sites**:

`§2.3` example T3 tensor at L221-231 lists 8 dimension names:

> L222: `  "t3_tensor": {`
> L223: `    "dimensions": {`
> L224: `      "technical_competence": 0.85,`
> L225: `      "social_reliability": 0.92,`
> L226: `      "temporal_consistency": 0.88,`
> L227: `      "witness_count": 0.95,`
> L228: `      "lineage_depth": 0.67,`
> L229: `      "context_alignment": 0.88,`
> L230: `      "hardware_binding_strength": 0.94,`
> L231: `      "constellation_coherence": 0.91`
> L232: `    },`

`§4.1 Trust Tensor Extensions` at L759-770 specifically names two as additions:

> L759: `The multi-device binding adds two dimensions to the T3 tensor:`
> ...
> L765: `      "hardware_binding_strength": 0.0-1.0,`
> L766: `      "constellation_coherence": 0.0-1.0`

**BC#3 corpus-grep** — `grep -n "hardware_binding_strength\|constellation_coherence\|witness_count\|lineage_depth\|context_alignment\|technical_competence\|social_reliability\|temporal_consistency" web4-standard/ontology/*.ttl web4-standard/ontology/*.jsonld 2>/dev/null`:

> (no matches)

None of the 8 dimension names are defined in the canonical T3/V3 ontology (`web4-core-ontology.ttl`, `t3v3-ontology.ttl`, `t3v3.jsonld`).

**Additional cross-check** — `web4-standard/core-spec/t3-v3-tensors.md`:

> L567: `| `constellation_coherence` multiplier | "1.4× CI bonus" | Measures identity strength, not economic scaling; ... | [`multi-device-lct-binding.md`](multi-device-lct-binding.md) §4.4 |`
> L568: `| CI thresholds and labels | "CI > 0.8 = strong" | Derived labels from `constellation_coherence`; not standalone protocol primitives | [`multi-device-lct-binding.md`](multi-device-lct-binding.md) §4.4 |`

`t3-v3-tensors.md` mentions `constellation_coherence` ONLY in the "things that are NOT standalone primitives" warning table — does not define it as a canonical sub-dimension. The 7 other dimension names are not mentioned at all.

**Flat-vs-tree T3 model conflict**: per CLAUDE.md, T3 has 3 root dimensions (`talent`, `training`, `temperament`), each modeled as an RDF sub-graph via `web4:subDimensionOf`. The §2.3 example flat-lists 8 dimensions with no mapping to the 3 root dims, contradicting the canonical 3-root-dim tree structure.

**Why MEDIUM**: The spec claims to extend the T3 tensor with two new dimensions, but the T3 ontology (`t3v3-ontology.ttl`) and the T3 spec (`t3-v3-tensors.md`) do not acknowledge them as canonical sub-dimensions. The other 6 dimensions are legacy "flat T3" listings predating the 3-root-dim tree model — they need either explicit mapping (`hardware_binding_strength web4:subDimensionOf web4:Talent`) or removal from the example.

**Cross-audit cluster status** (per BC#7): subordinate-ontology cluster = C16-M8 + C17-M1 + C18-M6 + **C19-M5** = 4-audit convergence. Document-not-solve per BC#6.

---

### M6 — `DeviceStatus.SUSPENDED` exists in SDK but is not mentioned in the spec

**SDK** — `web4-standard/implementation/sdk/web4/binding.py:81-86`:

> L81: `class DeviceStatus(str, Enum):`
> L82: `    """Device lifecycle within a constellation."""`
> L83: ` `
> L84: `    ACTIVE = "active"`
> L85: `    SUSPENDED = "suspended"`
> L86: `    REVOKED = "revoked"`

**BC#3 corpus-grep** — `grep -n "SUSPENDED\|suspended" web4-standard/core-spec/multi-device-lct-binding.md`:

> (no matches)

`grep -n 'status.*=.*"' web4-standard/core-spec/multi-device-lct-binding.md`:

> L555: `    active = [d for d in devices if d.status == "active"]`
> L670: `    device_to_remove.status = "revoked"`
> L745: `            device.status = "revoked"`

Spec references only `"active"` and `"revoked"` device statuses. SDK defines a 3rd state `SUSPENDED` that has no spec-level documentation — no lifecycle transitions, no semantics, no entry/exit conditions.

**Why MEDIUM**: Either the spec is under-specified (missing the SUSPENDED state and its transitions) or the SDK has added a state that should not exist at the wire level. Implementation conformance cannot be verified for SUSPENDED-state behavior — there's no normative authority for it. SDK adds it as a defensive measure (suspended ≠ revoked ≠ active), which is sound design, but the spec needs to document it.

**Bonus observation** (does not change severity): the device removal pseudocode at §3.5 L668-672 does not distinguish suspension from revocation either — once `remove_device` is called, status becomes `"revoked"` immediately. No spec-level concept of a recoverable suspended state.

---

### M7 — §7.3 ATP costs (10/1/5/20) not aligned with `atp-adp-cycle.md`

**Spec site** — `§7.3 ATP/ADP Cycle` at L982-988:

> L982: `### 7.3 ATP/ADP Cycle`
> L983: ` `
> L984: `Device operations consume ATP:`
> L985: `- Enrollment ceremony: 10 ATP`
> L986: `- Cross-device witnessing: 1 ATP per pair`
> L987: `- Device removal: 5 ATP`
> L988: `- Recovery ceremony: 20 ATP`

**BC#3 corpus-grep** — `grep -n "enrollment\|cross.device\|cross.witness\|recovery\|device\|multi.device\|ATP.cost\|10 ATP\|5 ATP\|20 ATP\|1 ATP" web4-standard/core-spec/atp-adp-cycle.md` (filtered to multi-device-relevant lines):

> L313: `      "rate": "1 ATP per kWh",`
> L511: `    energy: "1 ATP per kWh"`
> L512: `    compute: "10 ATP per TFLOP"`
> L513: `    storage: "1 ATP per TB-day"`
> L514: `    bandwidth: "0.1 ATP per GB"`
> L635: `charging: 1 ATP per kWh generated`

`atp-adp-cycle.md` documents ATP rates only for energy/compute/storage/bandwidth — not for enrollment, cross-witnessing, device removal, or recovery. The four specific ATP costs (10/1/5/20) in §7.3 are spec-local parameters with no canonical reference in the ATP economic protocol.

**Why MEDIUM**: §7.3 reads as if these costs are derived from or coordinated with `atp-adp-cycle.md`, but they are not. They are arbitrary numbers chosen by this spec. Either `atp-adp-cycle.md` needs to add an "identity operations" cost category (with these or other numbers), or §7.3 should label these as informational example costs rather than normative requirements. The coincidence that the "compute: 10 ATP per TFLOP" rate equals the "Enrollment ceremony: 10 ATP" cost is unintentional — different operations, different ATP semantics.

---

## LOW (3)

### L1 — `cross_device_witnesses[].mutual: true` flag is redundant under §3.3 algorithm

**Spec site** — `§2.4` device LCT example at L277-284:

> L277: `  "cross_device_witnesses": [`
> L278: `    {`
> L279: `      "device_lct": "lct:web4:device:laptop:...",`
> L280: `      "last_witness": "2026-01-13T11:00:00Z",`
> L281: `      "witness_count": 42,`
> L282: `      "mutual": true`
> L283: `    }`
> L284: `  ],`

The `mutual: true` flag implies the existence of `mutual: false` — but §3.3 `cross_witness` algorithm (L497-534) writes **mutually** on both devices unconditionally:

> L531: `    device_a.device_lct.record_cross_witness(device_b.device_lct.lct_id)`
> L532: `    device_b.device_lct.record_cross_witness(device_a.device_lct.lct_id)`

Both ends always record. `mutual` is always true under the protocol. The flag is structurally redundant.

**SDK behavior**: `binding.py` does not model a `mutual` field on cross-witness records (`DeviceRecord.cross_witnesses: List[str]` at L184 is just a flat list of LCT IDs).

**Why LOW**: Redundant schema field, no wire-correctness impact. Removable in spec cleanup. Alternatively, document a use case for `mutual: false` (e.g., one-way witnessing of a sleeping/offline peer) — but no such use case appears in §3.3.

---

### L2 — §2.4 device LCT schema omits the `revocation` object referenced by §3.5

**Spec site** — `§3.5 Device Removal` at L670-672:

> L670: `    device_to_remove.status = "revoked"`
> L671: `    device_to_remove.revocation.reason = reason`
> L672: `    device_to_remove.revocation.ts = utc_now()`

References `device_to_remove.revocation.reason` and `device_to_remove.revocation.ts`. But §2.4 Device LCT Structure (L241-293) defines no `revocation` field. The schema offers no place for revocation metadata to live.

**SDK behavior**: `binding.py:185-186` stores revocation metadata as flat fields on `DeviceRecord`:

> L185: `    revoked_at: str = ""`
> L186: `    revocation_reason: str = ""`

SDK uses two top-level fields, not a nested `revocation` object.

**Why LOW**: Schema gap, fixable by adding to §2.4 a `revocation: {reason: ..., ts: ...}` optional object (or flattening to `revoked_at` / `revocation_reason` per SDK). Informational; no wire-blocking impact.

---

### L3 — §5.3 "Review within last 24h" window is unsubstantiated

**Spec site** — `§5.3 Compromise Response` at L880-887:

> L883: `1. **Immediate**: Revoke device LCT`
> L884: `2. **Broadcast**: Alert to all societies where root LCT has membership`
> L885: `3. **Review**: All actions from device within last 24h flagged for review`
> L886: `4. **Recovery**: Trigger re-enrollment ceremony for remaining devices`

The 24h window is introduced as a normative review threshold with no derivation, no parameter table reference, and no cross-spec coordination. The number is arbitrary.

**BC#3 corpus-grep** — `grep -rn "24h\|24.hour" web4-standard/core-spec/` returns no other normative references to a 24h review window. It is local to this spec.

**Why LOW**: Informational gap. Either the 24h window should be labeled as an example threshold (with each society choosing its own), or it should reference a sibling spec that defines compromise-response windows. As written, it asserts normative force without justification.

---

## Demoted / Considered-but-not-included

Per BC#8 (audit-inflation guard), the following candidate findings were considered during scoping and rejected with rationale.

### D1 — Snake-case throughout this spec

**Considered**: `device_lct`, `anchor_type`, `cross_device_witnesses`, `device_constellation`, etc. all use snake_case. This conflicts with camelCase used in some other specs (e.g., `roleLCT`, `proofOfAgency`).

**Demoted because**: LCT-linked-context-token.md uses snake_case throughout (`lct_id`, `mrh`, `binding`, `t3_tensor`, `hardware_anchor`) and is canonical for LCT-related field naming. multi-device-lct-binding.md correctly follows LCT-spec convention. The snake/camel split between LCT-corpus and R6/R7/ACP corpus is a known cross-corpus issue documented in C17/C18 (M3, L1 in C18). Not a defect in this spec.

### D2 — §4.4 "constellation_coherence vs CI" normative paragraph quality

**Considered**: §4.4 L818-846 establishes `constellation_coherence` as canonical and labels "CI" / multiplier values as simulation parameters.

**Demoted because**: this paragraph is well-written and correctly applies the "canonical-term-defined-once" discipline. No defect — it's an exemplar.

### D3 — §3.6 mass-revocation pattern inconsistent with §3.5 quorum-required pattern

**Considered**: §3.6 L743-746 mass-revokes all non-participating devices during recovery without per-device quorum, but §3.5 requires per-device quorum for removal.

**Demoted because**: this is a design choice (recovery IS the quorum), not a defect. The act of meeting the recovery quorum (≥ recovery_quorum hardware-bound devices participating) inherently authorizes the cascade revocation of non-participating devices. Worth surfacing in design notes but not a wire-actionable inconsistency.

### D4 — ANCHOR_WEIGHTS in §3.4 (0.95 phone, 0.98 fido2, 0.93 tpm, 0.40 software) differ from §4.2 trust ceilings (0.75 phone, 0.80 fido2, [missing] tpm, 0.40 software)

**Considered**: 0.95 anchor_weight ≠ 0.75 ceiling for single phone SE.

**Demoted because**: these serve different roles. `anchor_weight` is a per-device multiplier inside the trust formula; `trust ceiling` is a per-composition cap applied after. They are not the same quantity. Coexistence is by design. The single-TPM2-row gap (counted under M2) is the real defect; the multiplier-vs-ceiling magnitude difference is intentional.

---

## Cross-Audit Cluster Status (per BC#7)

Per established C-series discipline, the following cross-audit clusters are extended by this audit:

### Canonical-errors-taxonomy cluster (4-audit convergence)

| Audit | Finding | Spec | Exception name(s) |
|-------|---------|------|-------------------|
| C16 | H1 | `web4-society-authority-law.md` | `WitnessDeficit` (undefined locally) |
| C17 | M4 | `dictionary-entities.md` | bare exceptions without W4_ERR_DICT mapping |
| C18 | M2 | `acp-framework.md` | undefined ACP error classes |
| **C19** | **M3** | **`multi-device-lct-binding.md`** | **`InsufficientQuorumError`, `InsufficientRecoveryQuorum`, `NoHardwareAnchorError`** |

Pattern: every C-series spec audited so far has at least one exception class raised in normative pseudocode that has no canonical `W4_ERR_*` mapping in `errors.md`. The shipped SDK responds by using generic `ValueError` (or domain-specific local classes in the case of acp.py). A `W4_ERR_MULTI_DEVICE_*` family (or addition of these to `W4_ERR_BINDING_*` with `_QUORUM`/`_ANCHOR` suffixes) would close the C19-M3 instance. Per BC#6, cross-corpus normalization is its own scope — this audit documents the cluster, does not solve it.

### Subordinate-ontology cluster (4-audit convergence)

| Audit | Finding | Spec | Predicate / dimension(s) |
|-------|---------|------|---------------------------|
| C16 | M8 | `web4-society-authority-law.md` | SAL predicates absent from `web4-core-ontology.ttl` |
| C17 | M1 | `dictionary-entities.md` | 6 dictionary predicates absent from ontology |
| C18 | M6 | `acp-framework.md` | 12 ACP predicates absent from ontology |
| **C19** | **M5** | **`multi-device-lct-binding.md`** | **8 T3 sub-dimensions absent from `t3v3-ontology.ttl`** |

Pattern: every C-series spec asserts semantic terms (predicates, sub-dimensions, classes) that the canonical ontology files do not model. Per BC#6, cross-corpus ontology normalization is its own scope.

### Test-vectors-as-first-class-authority pattern (2 audits)

| Audit | Finding | Test vector contradicting spec |
|-------|---------|-------------------------------|
| C18 | H3 | `acp-jsonld-validation.json:480-491` (flagship §2.1 example fails own conformance vector) |
| **C19** | **M1, M2** | **`binding-vectors.json:23-34, 88-99` (recovery quorum + trust ceiling vectors disagree with spec)** |

Two distinct C-series specs now exhibit the same pattern: shipped test vectors agree with the SDK and disagree with the spec normative content. Establishes test vectors as a co-equal authority alongside SDK + JSON-LD schema. Going forward, audits should always check test vectors when present.

---

## Implementation-track flag (per BC#6 — flag only, do not prescribe)

| Finding | Type |
|---------|------|
| H1, H2, H3, M1, M2, M6 | Wire-actionable (spec-only; SDK + test vectors canonical) |
| M3, M5 | Cross-corpus cluster member (4-audit); design-Q |
| M4, M7 | Cross-spec reciprocity (LCT spec / atp-adp-cycle.md edit); design-Q |
| L1, L2, L3 | Spec-only cleanup |

Per BC#6, this table flags type per finding without prescribing remediation diffs. A future remediation PR (likely the next exit's scope) will classify wire-actionable findings as autonomous-actionable vs design-Q with its own policy review.

---

## Authority Summary

- **SDK** is the canonical authority for shape/name/formula questions where it deviates from the spec (H1, H2, H3, M1, M2, M6).
- **Test vectors** (`binding-vectors.json`) are co-equal canonical authority for algorithmic conformance (M1 quorum, M2 ceiling).
- **Errors taxonomy** (`errors.md`) is the canonical authority for W4_ERR_* code assignment (M3).
- **LCT spec** (`LCT-linked-context-token.md`) is the canonical authority for LCT field acceptance — and currently does not acknowledge the multi-device extension (M4).
- **T3 ontology** (`t3v3-ontology.ttl` + `t3-v3-tensors.md`) is the canonical authority for trust dimension naming — and currently does not define the 8 multi-device-cited dimensions (M5).
- **ATP cycle spec** (`atp-adp-cycle.md`) is the canonical authority for ATP rate/cost assignment — and currently does not define multi-device operation costs (M7).

---

*"Identity is coherence across witnesses. Internal consistency is coherence within a spec."*
