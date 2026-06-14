# Delta Re-Audit: `lct-capability-levels.md`

**Audit ID**: C56 (delta re-audit; prior audit **C20**, 2026-05-29)
**Date**: 2026-06-14
**Auditor**: legion-web4-20260614-120047 (LEAD, autonomous, v2 protocol)
**Spec under audit**: `web4-standard/core-spec/lct-capability-levels.md` (719 lines, unchanged since C20 remediation #248)
**Prior audit**: `docs/audits/lct-capability-levels-internal-consistency-2026-05-29.md`
**Audit type**: Audit-only — remediation is the next-turn task (C57).

## Authority precedence (C-series default)

```
SDK Python (web4/capability.py, web4/lct.py) + canonical TTL (t3v3-ontology.ttl)
  + shipped test vectors (test-vectors/capability/*) + JSON-LD schema  >  spec prose
```

Where no SDK / ontology / test-vector / sibling-spec covers a topic, items are
flagged **DESIGN-Q** (operator input) rather than wire-defect.

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH     | 0     | — |
| MEDIUM   | 6     | A1, B1, B3, B4, B5a, B7 |
| LOW      | 7     | B2, B5b, B6, B8, B9, B10, B13 |
| INFO     | 4     | B11, B12, B14, B15 |
| **Total (excl. duplicates/refuted)** | **17** | |

- **§A**: 7/7 remediated C20 findings **HELD**; 6 design-Q + 2 cross-track **still OPEN**; mirror check **clean** (no introduced drift). **One in-file H1-incomplete survivor (A1).**
- **§B**: workflow `wf_4ef58250-24d` (46 agents, 10 lenses incl. sdk-align + primitive-cluster, refute-by-default + per-candidate verify): **36 raw → 35 verifier-survivors → 16 distinct** after dedup (0 HIGH). **Flagship §B cluster: `gate-prose-over-specifies-vs-sdk`** (NEW) — §2.5/§2.6/§2.7 "Additional Requirements" list Level-N gates the SDK assessor + shipped vectors do not enforce.
- **Disposition note**: the schema-validation-vector findings (KYC `requirements` strings + divergent `trust_range` bands) re-derive C20's already-**DEMOTED D1/D2** and are re-demoted here (the JSON-LD schema imposes no value constraint → shape-only fixtures). The finder pool was not given C20's DEMOTED list; this is an audit-instrument note, not a fresh defect.

---

## §A — Prior-finding verification

**Regression sweep**: `git log b6383e71..HEAD -- lct-capability-levels.md` is **EMPTY**.
The file is byte-identical to C20 remediation #248 (`b6383e71`). No `#252`-style
date-bump touched it. **In-file regression is therefore impossible** — every C20
remediation is trivially HELD in the diff sense, so §A's value here is the
*mirror* check (per the C54 lesson) and the *completeness* check of the C20
remediations themselves.

### Remediated C20 findings (7) — all HELD

| C20 | Fix | Current state | Verdict |
|-----|-----|---------------|---------|
| H1 | T3/V3 6-dim→3-root rename | examples L242+ use talent/training/temperament; L99-100 "All 3 root" | **HELD** (but INCOMPLETE — see A1) |
| H2 | NEVER-Use inversion | L37/38 forbid "Old 6-flat-dimension schema" | HELD |
| H3 | V3 roots + `energy_balance`→sub-dim | V3 examples valuation/veracity/validity; L221 demotes `energy_balance` to sub-dim of valuation | HELD |
| M1 | ref-impl pointer→SDK | L711 → `implementation/sdk/web4/capability.py`; target **exists** | HELD |
| M2 | §3.1 15-type table + society dedup + policy/infra | SDK `ENTITY_LEVEL_RANGES` confirms SOCIETY(4,5)/POLICY(3,4)/INFRASTRUCTURE(3,5) — spec rows match SDK exactly | HELD |
| M4 | birth-cert circular rephrase | §8.3 L674 "post-issuance requirements" | HELD (but introduced a mis-cite — see B8) |
| L3 | stub `reason` field | §4.3 stubs carry `"reason": "Not implemented at this level"` | HELD |

### Mirror check (C54 lesson) — CLEAN

The C20 remediation moved the spec **toward** the canonical anchors (ontology +
SDK + test-vectors were *already* 3-root; the spec was the lone dissenter). Verified
the mirrors remain canonical: `t3v3-ontology.ttl` still declares 3 BASE dims; SDK
level-ranges still match the M2-added rows; the M1 pointer still resolves. **No
one-sided introduced drift** — the clean inverse of C54's #250 (which edited spec
text and left SDK strings + sibling paragraphs stale). The single exception is the
cross-reference M4 *added*, which does not support its claim (B8).

### §A FLAGSHIP — A1: H1 remediation INCOMPLETE (in-file survivor)

**Severity**: MEDIUM · **klass**: autonomous · **site**: `lct-capability-levels.md:170`

§2.4 Level-2 still reads `- `t3_tensor.dimensions`: All 6 with non-zero values`.
The C20 H1 site-list enumerated L99/L100 and fixed those, but **L170 was never in
the enumeration**, so the remediation left it asserting the now-forbidden "6
dimensions". It directly contradicts:
- L37 canon ("3 root dimensions … per t3v3-ontology.ttl"),
- the fixed L99-100 ("All 3 root dimensions"),
- the fixed §8.1 L661-662 ("Verify all 3 T3 root dimensions present").

A Level-2 validator reading L170 literally would expect 6 T3 dimensions. **Recommended C57 fix**: `All 6 with non-zero values` → `All 3 root dimensions non-zero`.
**False alarm cleared**: L236 `"witness_count": 10` is an MRH witnessing-record count field, not a T3 dimension (matches the C20 scope-precision note).

### Deferred C20 items (6 design-Q + 2 cross-track) — all still OPEN

M3 (§3.2 invents extended types — header present L409), M5 (zero `CapabilityLevel`/`TrustTier` in any ontology `.ttl`), M6 (no QueryRequest/Response schema or vector), M7 (Level-5-from-creation vs multi-device tension), L1 (downgrade silent on witness-loss/revocation), L2 (§9.3 "MRH mutual for Level 2" absent from §2.4), INFO1 (SDK `capability.py:281` substring `"citizen" in lct_id` unchanged), INFO2 (trust-tier labels SDK-only). See §C.

---

## §B — Fresh findings

Workflow `wf_4ef58250-24d`: 10 lenses (intra-doc, sdk-align, sibling, test-vector,
normative, wire-shape, terminology, primitive-cluster, numeric, lifecycle-sec),
each finding pinned to one lens, every candidate passed to an adversarial
refute-by-default verifier with a per-candidate corrected-site field. 36 raw → 35
survived verify → **16 distinct** after my dedup (the 35 collapse heavily: the
over-specification cluster alone produced 6 finder-instances across 4 lenses).

### FLAGSHIP CLUSTER — `gate-prose-over-specifies-vs-sdk` (NEW)

The §2.x "Additional Requirements over Level N" lists are the spec's normative
level gates. Cross-checked against the **authoritative** SDK assessor
(`capability.py` `assess_level`/`validate_level`) and the shipped behavioral
vectors (`test-vectors/capability/capability-levels.json`), **four requirements
are listed by the spec but enforced by neither the SDK gate nor any vector** — an
independent implementer following the prose would *reject valid LCTs* the canonical
SDK accepts. This is a genuinely new C-series pattern (prior over-spec findings
were single-site; this is a systematic 4-site cluster within one file).

| ID | Site | Spec requires | SDK gate / vector reality | Sev | klass |
|----|------|---------------|---------------------------|-----|-------|
| **B1** | §2.5 L220, L222 | `t3_tensor.computation_witnesses: ≥1 oracle` **and** `attestations: ≥1` for Level 3 | `assess_level` STANDARD (capability.py:333-341) gates only `_has_witnessing`+`_has_nonzero_v3`; grep finds **no** `attestation`/`computation_witness` predicate; vector `standard_with_witnessing` omits both yet expects level 3 | MEDIUM | autonomous-soften / cross-track-tighten |
| **B3** | §2.6 L287-288 | `lineage: ≥ genesis entry` **and** `revocation: status tracking` for Level 4 | `validate_level` FULL (capability.py:388-392) checks only birth-cert + permanent citizen pairing; vector `full_society_issued` carries neither yet expects level 4 | MEDIUM | autonomous-soften |
| **B4** | §2.7 L344-346 | `binding.hardware_type` **and** `hardware_attestation` for Level 5 | `_has_hardware_anchor` (capability.py:284-286) + validate_level HARDWARE gate on `hardware_anchor` only; vector `hardware_bound_device` omits both yet expects level 5 | MEDIUM | cross-track |
| **B2** | §2.5 L221 | `v3_tensor.dimensions.valuation` non-zero (valuation-specific) | `_has_nonzero_v3` (capability.py:266-268) accepts **any** V3 dim non-zero; latent (all shipped L3+ vectors set valuation>0) | LOW | design-q |

**Why the direction matters (B1-B4)**: the C-series authority default (SDK+vectors
> prose) makes the *autonomous-safe* fix "soften the prose to SHOULD / descriptive".
But B1's `attestations`/`computation_witnesses` and B4's `hardware_attestation` are
*meaningful trust gates* — the operator may instead prefer to **tighten the SDK** to
enforce them (and add covering vectors). C57 should soften the prose autonomously
where safe (B3 lineage/revocation are benign-defaulting fields) and **route B1/B4 as
cross-track operator decisions** (relax-spec vs tighten-SDK). B2 is a genuine
semantic design-Q: is the Level-3 V3 gate "ATP-balance-as-valuation" (spec) or "any
V3 signal" (SDK)?

### Other autonomous findings

- **B5a — §6.1 upgrade table 1→2 omits the non-zero-T3 requirement.** MEDIUM, autonomous. §2.4 L170 (and SDK `_has_nonzero_t3`, capability.py:377-378) require non-zero T3 at Level 2, but the §6.1 row `1 → 2` (L611) lists only "Establish MRH relationship, add policy capability". An implementer following only the upgrade table mints a Level-2 LCT the validator rejects. (The adjacent `0 → 1` row *does* enumerate tensor work, so the omission is a genuine gap, not abbreviation.) Fix: add "set non-zero T3 dimensions".
- **B5b — §6.1 upgrade table 4→5 advertises an impossible transition.** LOW, autonomous. The row `4 → 5 | Bind to hardware (cannot be done post-hoc)` sits under "Entities MAY upgrade…" yet §6.2/§9.3 + SDK `can_upgrade` (capability.py:431-433) make it unreachable. The cell self-disqualifies inline so it is clumsy-not-trap. Fix: remove the row or reword to "re-issue as a new hardware-bound LCT". (Distinct from M7's multi-device tension.)
- **B6 — §2.6 L285 `birth_certificate: Complete with all fields` overstates the SDK minimum.** LOW, autonomous. `_has_birth_certificate` (capability.py:271-276) accepts a cert with only `issuing_society`+`citizen_role`+`birth_witnesses≥3` (3 of the 6 example fields); vectors `full_society_issued`/`hardware_bound_device` omit `genesis_block_hash` yet reach level 4/5. Fix: replace "Complete with all fields" with the precise SDK-backed minimum.
- **B8 — §8.3 mis-cites LCT-linked-context-token.md §3.1 (remediation-introduced).** LOW, autonomous. The C20-M4 fix added "(per `LCT-linked-context-token.md` §3.1, the birth certificate is what raises an entity to Level 4)". LCT §3.1 ("Genesis: Birth Certificate from Society", L192-217) describes issuance mechanics but contains **zero** capability-level language; the only Level-4 reference in the whole LCT spec is a back-link to *this* file. The Level-4 mapping is wholly internal to §2.6. Fix: split the cite — mechanics → LCT §3.1, Level-4 mapping → this spec's §2.6. **Notable**: this is the one place the M4 remediation introduced a forward-defect, of the same class as C54's mirror flagship but minor.
- **B9 — §2.5 Level-3 V3 `composite_score: 0.51` is arithmetically wrong (→ 0.50), propagated to §4.3.** LOW, autonomous. valuation 0.55/veracity 0.5/validity 0.45 under canonical V3 weights (0.3/0.35/0.35, per t3-v3-tensors.md:568) = 0.4975 ≈ 0.50; equal-weight = 0.50. The same file's T3 examples (§2.4 → 0.41, §2.5 → 0.625) recompute exactly, proving the author used the weighted formula and 0.51 is a fresh slip. Copied to §4.3 L522 `composite_v3: 0.51`. No vector pins 0.51. Fix: L258 + L522 → 0.50.
- **B10 — §2.5 Level-3 `mrh` example is invalid JSON.** LOW, autonomous. L229-230 use bare unquoted `[...]` inside a ` ```json ` block (the file's sole bare-ellipsis occurrence; other placeholders are quoted strings, and the L1 example uses valid `[]`). `json.loads` fails at that token. Fix: `[...]` → `[]` (per the L1 convention) or an elided real entry per the shipped vector.

### Cross-track / sharper-facet findings

- **B7 — §3.3 `ENTITY_LEVEL_RANGES` snippet + §2.3 examples instantiate non-canonical entity types.** MEDIUM, cross-track. §3.3 keys the dict on `"plugin": (1,2)`, `"session": (1,2)` and §2.3 sets `entity_type: "plugin"`, but the canonical SDK `EntityType` enum (lct.py:51) has exactly the 15 types and contains neither — `ENTITY_LEVEL_RANGES[EntityType.PLUGIN]` is non-constructible and `entity_level_range()` would `KeyError`. The shipped vector `minimal_self_issued` sidesteps this by typing a plugin-named LCT as `entity_type: "role"`. **Sharper facet of M3**: M3 flagged §3.2's *prose table* inventing the taxonomy; B7 is the concrete *instantiability* break in §3.3 code + §2.3 examples. Route with M3: either reconcile examples to canonical `EntityType` values (matching the vector) or route an SDK/ontology change to add the types.

### Design-Q / INFO

- **B11 — §2.1 Trust Tier column under-specified.** INFO/LOW. (a) Level-0 cell is the label "Untrusted" while Levels 1-5 give numeric ranges — heterogeneous cell kinds in one column (distinct from INFO2). (b) Adjacent ranges share endpoints (0.2/0.4/0.6/0.8) with **no inclusive/exclusive convention** → a score of exactly 0.4 is ambiguously Level 2 and Level 3. (c) Level-0 numeric range is unspecified: SDK pins (0.0,0.0), schema-vectors pin [0.0,0.1], spec is silent. Non-operational (SDK derives level from component-presence, never score→level), so LOW. Fix: state a half-open convention + an explicit Level-0 range (autonomous for the convention; design-q for the 0.0-0.0 vs 0.0-0.1 value).
- **B12 — §4.4 "Current (timestamp within 5 minutes)" is an un-testable MUST.** INFO, design-q. The 5-minute freshness window has no defined clock-skew/measurement point, no schema, and no vector (the query protocol has none — see M6). Bundle with M6 for one operator decision on the query-protocol authority surface.
- **B13 — `human` entity-type has no self-sovereign genesis path below Level 4.** LOW, design-q. §3.1 gives `human` typical level 4-5 and §6.2/§8.3 make Level 4 society-issuance-gated, so a human LCT can neither exist below 4 nor reach 4 without society issuance — while §2.3's "self-issued bootstrap" exists for other types. Deliberate-but-undocumented (the typical ranges are SHOULD-enforce advisory, not a hard floor). Operator: document "human LCTs are society-issued only" or widen the range.
- **B14 — §1.2 L38 NEVER-Use cell reuses `energy_balance` as its banned-schema example token.** INFO, autonomous. `energy_balance` is *banned* at L38 (as an example member of the old flat schema) yet *blessed* at L221 (and LCT §10.3 L573) as a valid sub-dimension of valuation. The usages are reconcilable (the verifier refuted the "self-contradiction" framing — L221 is the C20-H3-sanctioned sub-dim), but reusing the blessed token as the ban-example invites reader confusion. Optional fix: drop `energy_balance` from L38's example list (keep `contribution_history`, which is not blessed elsewhere); leave L221/L573 intact.
- **B15 — §2.4 `bound.type` vs §2.6 `paired.pairing_type` key naming.** INFO. Near-refuted: `bound` and `paired` are distinct MRH primitives (mrh-tensors.md), and vectors confirm `paired.pairing_type` is correct. Residual open question: should `bound` entries use `type` or the RDF-aligned `bindingType`? Route to a future MRH-consistency pass, not a cap-levels defect.

### Refuted / re-demoted (not counted)

- **Schema-validation-vector KYC `requirements` + divergent `trust_range` bands** (4 finder-instances): re-derives C20's **DEMOTED D1/D2**. The JSON-LD schema bounds `trust_range` only to `[0,1]` and `requirements` to array-of-strings with no enum — these are shape-only fixtures; the canonical `capability-levels.json` vectors match the SDK. **Re-DEMOTED.** Residual cleanliness note (optional cross-track): the KYC strings ("Government ID", "Biometric") are foreign to Web4 and could be regenerated from SDK `_LEVEL_REQUIREMENTS`; non-blocking.
- **"`energy_balance` is a phantom sub-dimension in no authoritative source"** (primitive-cluster): REFUTED — LCT §10.3 L573 canonically blesses it and the TTL is open-world by design. Only the SDK-gate-wording prong survives, already captured as B2.

---

## §C — Carry-ledger reconciliation

| Carry | Status at C56 | Note |
|-------|---------------|------|
| C20-M3 (§3.2 extended types) | OPEN; **sharpened by B7** | route B7 + M3 together (instantiability + taxonomy) |
| C20-M5 (`subordinate-ontology`) | OPEN | grep confirms no `CapabilityLevel`/`TrustTier` class/predicate in any `.ttl`. Cluster now **6 audits** (C16-M8/C17-M1/C18-M6/C19-M5/C20-M5 + this re-confirm) — past 5-threshold; unified TTL-extension PR overdue |
| C20-M6 (Query Req/Resp no schema/vector) | OPEN; **+B12** | bundle B12 (§4.4 freshness MUST) into the same operator decision |
| C20-M7 (Level-5-from-creation vs multi-device) | OPEN | B5b is a *distinct* in-file table defect, not M7 |
| C20-L1 (downgrade/witness-loss) | OPEN | unchanged |
| C20-L2 (§9.3 mutual-MRH for Level 2) | OPEN | unchanged |
| C20-INFO1 (SDK substring citizen-pairing) | OPEN | `capability.py:281` unchanged |
| C20-INFO2 (trust-tier labels SDK-only) | OPEN | B11 is a distinct facet (heterogeneous cell + boundary convention) |
| C20-D1/D2 (schema-vector ranges/KYC) | **re-DEMOTED** | shape-only fixtures; re-surfaced because finders lacked the DEMOTED list |

New design-Q for the operator bundle: **B2** (Level-3 V3 gate semantics), **B13** (human self-sovereign path), plus the B1/B4 relax-vs-tighten direction.

---

## §D — Method notes / lessons

1. **Byte-identical-since-remediation files shift §A's center of gravity from diff to completeness.** With zero commits since #248, no C20 fix could regress in-diff; the value was (a) the mirror check and (b) auditing whether the *remediations themselves were complete*. That completeness check is exactly what surfaced A1 (H1 left L170) and B8 (M4 added an unsupported cite). **Lesson: when a delta target is unchanged since its remediation, re-verify the remediation's own site-enumeration, not just "did it hold" — the original audit's site-list may have under-scoped.**
2. **Feed finders the DEMOTED list, not just HELD+DEFERRED.** Four finder-instances re-derived C20-D1/D2 because the prior-context block omitted demotions. The verifiers correctly downgraded but couldn't tag them DUPLICATE without the list. **Lesson: the prior-findings context block must include DEMOTED items with their demotion rationale.** (Updates the standard delta-audit recipe.)
3. **High verifier survival rate ≠ low dedup need.** 35/36 "survived" because each verifier judged its candidate in isolation and the refute-by-default bar was about *truth*, not *novelty*. The real reduction (35→16) was cross-lens clustering done at synthesis. **Lesson: a refute-by-default verify pass does not replace a synthesis-time dedup; the over-specification cluster alone was 6 instances of one defect.**
4. **New cluster `gate-prose-over-specifies-vs-sdk`** (B1-B4): the inverse of the usual "spec ahead of SDK" finding — here the *spec* over-asserts conformance bars the SDK ignores. Distinct from `test-vectors-as-authority` because the spec is stricter, not wrong-shaped. Worth tracking across future SDK-backed specs.

---

## Audit metadata

- Distinct findings (excl. duplicates/refuted): **17** (1 §A + 16 §B); 0 HIGH / 6 MEDIUM / 7 LOW / 4 INFO
- Workflow: `wf_4ef58250-24d`, 46 agents, 10 lenses, refute-by-default + per-candidate verify; 36 raw → 35 survived → 16 distinct
- §A: 7/7 C20 remediations HELD (1 incomplete); 8 deferred still OPEN; mirror check clean
- New cluster opened: `gate-prose-over-specifies-vs-sdk` (4 sites)
- Cross-track routes for C57: B1/B4 (relax-vs-tighten), B7+M3 (entity-type instantiability), M5 (6-audit subordinate-ontology), M6+B12 (query-protocol authority surface)

*"When a file is unchanged since its own remediation, audit the remediation, not the diff."*
