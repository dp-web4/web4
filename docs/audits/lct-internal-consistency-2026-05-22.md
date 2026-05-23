# C9 Audit: `LCT-linked-context-token.md` Internal Consistency

**Date**: 2026-05-22
**Auditor**: Autonomous session (Legion, web4 track)
**Document**: `web4-standard/core-spec/LCT-linked-context-token.md` (657 lines, 13 sections)
**Methodology**: C-series internal consistency audit (same as C2, C5, C6, C7, C8)
**SDK alignment**: Not in scope for this audit (LCT spec is the foundational structural document; SDK `web4/lct.py` alignment is a separate concern)

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 2 | H1, H2 |
| MEDIUM | 4 | M1, M2, M3, M4 |
| LOW | 2 | L1, L2 |
| **Total** | **8** | |

The document has **clean section numbering** (§1–§13, no duplicates, no collisions) — a marked improvement over the structural corruption found in C8 entity-types.md. The findings are predominantly **content-level inconsistencies**: a phantom V3 dimension claim, entity type list drift between two sections, incorrect validation pseudocode, missing RFC 2119 notation, and a normative ambiguity in birth certificate requirements. The structural hierarchy is sound with two minor editorial items.

---

## HIGH Findings

### H1: §10.3 Claims V3 "Contains energy_balance Dimension" — Not Defined in §6.2

**Line**: 548
**Issue**: §10.3 "LCT and ATP/ADP" states:
> - **V3 tensor**: Contains energy_balance dimension

However, §6.2 (the normative V3 definition within this same document) defines V3 with three root dimensions — **valuation**, **veracity**, **validity** — and optional `sub_dimensions`. The term `energy_balance` does not appear in §6.2 at all.

Cross-spec check: `lct-capability-levels.md` (L146, L230, L266) uses `energy_balance` as a V3 **sub-dimension** under `v3_tensor.dimensions`. This confirms `energy_balance` is a context-specific sub-dimension, not a guaranteed root component.

**Impact**: §10.3 asserts V3 "Contains" energy_balance as if it's a standard, always-present part of the tensor. This contradicts §6.2's definition where sub_dimensions are OPTIONAL and domain-specific. A reader implementing V3 from §6.2 would never include energy_balance; a reader implementing ATP/ADP integration from §10.3 would assume it's always there.

**Remediation**: Rewrite §10.3 first bullet to:
> - **V3 tensor**: ATP/ADP balance MAY be tracked via a context-specific `energy_balance` sub-dimension (see `lct-capability-levels.md`)

---

### H2: §1.2 ↔ §2.3 Entity Type List Mismatch

**Lines**: 24 (§1.2) and 62 (§2.3)
**Issue**: The entity type enumeration differs between two sections of the same document:

| Source | Types Listed | Count |
|--------|-------------|-------|
| §1.2 Terminology | human, AI, device, service, role, task, resource, oracle, accumulator, dictionary | 10 |
| §2.3 Canonical Structure | human, ai, organization, role, task, resource, device, service, oracle, accumulator, dictionary, hybrid | 12 |
| entity-types.md §2.1 (normative) | Human, AI, Society, Organization, Role, Task, Resource, Device, Service, Oracle, Accumulator, Dictionary, Hybrid, Policy, Infrastructure | 15 |

Discrepancies:
- §1.2 omits: **organization**, **hybrid** (present in §2.3)
- §2.3 omits: **society**, **policy**, **infrastructure** (present in entity-types.md)
- §1.2 omits: **society**, **organization**, **hybrid**, **policy**, **infrastructure** (present in entity-types.md)

**Impact**: Internal inconsistency — a reader of §1.2 gets a different entity type set than a reader of §2.3. Both are also stale relative to the normative entity-types.md taxonomy (15 types).

**Remediation**: Both §1.2 and §2.3 should reference or enumerate the canonical 15-type set from entity-types.md. For §1.2, update the Entity definition to include all 15 types. For §2.3 `binding.entity_type`, update the enum to include all 15 types.

---

## MEDIUM Findings

### M1: §11.1 Incorrect Birth Certificate Validation Logic

**Line**: 580
**Issue**: The `validate_lct()` pseudocode in §11.1 contains:
```python
    # Birth certificate validation
    if "birth_certificate" in lct:
        assert len(lct["birth_certificate"]["birth_witnesses"]) >= 3
        assert "citizen_role" in lct["mrh"]["paired"]
```

The second assertion (`assert "citizen_role" in lct["mrh"]["paired"]`) is semantically incorrect. Per §2.3, `mrh.paired` is an **array of objects**:
```json
"paired": [
  {
    "lct_id": "lct:web4:role:citizen:...",
    "pairing_type": "birth_certificate",
    "permanent": true,
    "ts": "2025-10-01T00:00:00Z"
  }
]
```

The Python `in` operator on a list of dicts would check if the string `"citizen_role"` equals any dict in the list — which would always be `False`. The correct check is shown in §11.2's `validate_birth_certificate()`:
```python
citizen_pairing = [
    p for p in lct["mrh"]["paired"]
    if p["pairing_type"] == "birth_certificate"
]
assert len(citizen_pairing) == 1
assert citizen_pairing[0]["permanent"] == True
```

**Impact**: §11.1 gives implementers incorrect validation logic. Anyone copying this pseudocode would produce a validator that falsely rejects all birth certificate LCTs (the `in` check would never match).

**Remediation**: Replace the §11.1 birth certificate check with a simplified version of §11.2's correct approach:
```python
    if "birth_certificate" in lct:
        assert len(lct["birth_certificate"]["birth_witnesses"]) >= 3
        assert any(
            p["pairing_type"] == "birth_certificate" and p["permanent"]
            for p in lct["mrh"]["paired"]
        )
```

---

### M2: Missing RFC 2119 Notation Section

**Lines**: N/A (absent)
**Issue**: The document uses RFC 2119 keywords extensively:
- §2.1 (L36): "Every LCT **MUST** contain"
- §2.2 (L47): "LCTs **MAY** contain"
- §3.2 (L215): "entities **MAY** create self-issued LCTs"
- §4.2 (L270): "it **MUST**"
- §5.3 (L334): "**MUST** be updated when"
- §6.3 (L413): "**SHOULD** be recomputed"
- §9.1–9.3 (L506–526): "MUST" (6 instances)
- §11.1 (L564): "**MUST** provide validation"

But there is no RFC 2119 notation section declaring these keywords as normative. The C6 and C8 remediations added such sections to their respective specs, establishing the pattern.

**Impact**: Without the notation section, MUST/SHOULD/MAY are technically non-normative — a reader cannot distinguish specification-grade requirements from conversational emphasis.

**Remediation**: Add a "Notation" section before §1 matching the established pattern:
```
## Notation

Key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in this document
are to be interpreted as described in RFC 2119.
```

---

### M3: §4.2 `genesis_block_hash` Normative Ambiguity

**Lines**: 277 (§4.2) and 303 (§4.3)
**Issue**: §4.2 lists `genesis_block_hash` under the MUST requirements:
> For an LCT to serve as a birth certificate, it MUST:
> 1. **Contain `birth_certificate` section** with:
>    - `genesis_block_hash`: Blockchain anchor (if applicable)

The "(if applicable)" qualifier weakens the MUST — if the hash is only required "if applicable," it's not a strict MUST but a conditional requirement. This ambiguity is confirmed by §4.3's comparison table:

| Property | Birth Certificate LCT | Regular LCT |
|----------|----------------------|-------------|
| Blockchain Anchor | **Recommended** | Optional |

§4.2 says MUST + "(if applicable)". §4.3 says **Recommended**. These are three different normative strengths for the same field (MUST, conditional, and Recommended).

**Impact**: An implementer cannot determine whether `genesis_block_hash` is required, recommended, or optional for birth certificate LCTs.

**Remediation**: Choose one normative strength and apply consistently. Since §4.3 says "Recommended" (not "Required"), the §4.2 listing should either:
1. Move `genesis_block_hash` to a separate "RECOMMENDED" list below the MUST list, or
2. Qualify it inline: `genesis_block_hash`: Blockchain anchor (**RECOMMENDED**, omit if no blockchain anchor is available)

---

### M4: §3.2 Self-Issued LCT Sets `birth_certificate.issuing_society = null`

**Lines**: 222 (§3.2 step 5), 270 (§4.2), 47–52 (§2.2)
**Issue**: §3.2 "Self-Issued LCT (Bootstrap)" step 5 says:
> 5. Set birth_certificate.issuing_society = null

This creates three contradictions:
1. **vs §4.2**: Birth certificates MUST contain `issuing_society: LCT of the society issuing the certificate`. Setting it to `null` fails this requirement.
2. **vs §2.2**: The `birth_certificate` is listed as OPTIONAL. A self-issued LCT (which by definition has no issuing society) should simply **omit** the optional section rather than populate it with null values.
3. **vs §4.3**: The comparison table explicitly says a "Regular LCT" can be issued by "Self or Society" and has "Optional" citizenship — confirming self-issued LCTs are Regular, not Birth Certificate LCTs.

**Impact**: An implementer following §3.2 literally would create LCTs with a malformed `birth_certificate` section (null issuing_society) that fails §4.2 validation. The intent is clear (self-issued LCTs don't have birth certificates), but the specification contradicts itself.

**Remediation**: Replace §3.2 step 5 with:
> 5. Omit `birth_certificate` section (self-issued LCTs are Regular LCTs per §4.3)

Or equivalently, remove step 5 entirely since §2.2 already marks birth_certificate as optional — its absence is the default for non-society-issued LCTs.

---

## LOW Findings

### L1: `birth_context` Field Undocumented

**Line**: 79 (§2.3)
**Issue**: The §2.3 canonical JSON structure includes:
```json
"birth_context": "nation|platform|network|organization|ecosystem"
```

This field appears in the `birth_certificate` object but is never defined, validated, or discussed in the prose sections (§4.1, §4.2, §4.3). Every other field in the canonical structure has corresponding prose in the relevant section:
- `issuing_society` → §4.2 item 1
- `citizen_role` → §4.2 item 2
- `birth_witnesses` → §4.2 item 3
- `birth_timestamp` → §4.2 item 4
- `genesis_block_hash` → §4.2 item 5
- `birth_context` → **not mentioned**

**Impact**: An implementer sees the field in the structure but has no normative guidance on its purpose, required vs optional status, or valid values. The enum values ("nation|platform|network|organization|ecosystem") appear only in the example.

**Remediation**: Either:
1. Add a bullet to §4.2 describing `birth_context` (purpose: society type classification; values: the 5 enum values; optional vs required), or
2. Remove it from §2.3 if it's not a normative part of the birth certificate structure

---

### L2: §5.2 Unnumbered Sub-Headings

**Lines**: 313, 319, 326
**Issue**: §5.2 "Relationship Types" contains three `####` (h4) sub-sections:
- `#### Binding Relationships (`mrh.bound`)`
- `#### Pairing Relationships (`mrh.paired`)`
- `#### Witnessing Relationships (`mrh.witnessing`)`

These are the only h4 sections in the document that are not numbered. Every other subsection at every level follows the numbered pattern (§1.1, §2.1, §5.2, etc.).

**Impact**: Minor editorial inconsistency. The unnumbered headings cannot be referenced by section number, unlike all other parts of the document.

**Remediation**: Number them as §5.2.1, §5.2.2, §5.2.3. Alternatively, leave as-is if the document convention is that h4 sections don't receive numbers (would need to be explicitly stated).

---

## Section Numbering Verification

Unlike C8 (entity-types.md), the LCT spec has **clean section numbering**:

```
§1 Introduction (§1.1, §1.2)
§2 LCT Structure (§2.1, §2.2, §2.3)
§3 LCT Creation Process (§3.1, §3.2, §3.3)
§4 Birth Certificate as Foundational Identity (§4.1, §4.2, §4.3)
§5 Markov Relevancy Horizon (§5.1, §5.2, §5.3, §5.4)
§6 Trust and Value Tensors (§6.1, §6.2, §6.3)
§7 LCT Lifecycle (§7.1, §7.2, §7.3, §7.4)
§8 Security Properties (§8.1, §8.2, §8.3)
§9 Implementation Requirements (§9.1, §9.2, §9.3)
§10 Relationship to Other Web4 Components (§10.1, §10.2, §10.3, §10.4)
§11 Compliance and Validation (§11.1, §11.2)
§12 Future Extensions (§12.1, §12.2)
§13 References
```

No duplicates, no collisions, heading hierarchy consistent (`##` for top-level, `###` for subsections, `####` only in §5.2).

---

## Remediation Priority Groups

### Group 1: Content Corrections (H1 + H2)

Both HIGH findings involve factual claims that contradict normative definitions within the same document.

- **H1**: §10.3 energy_balance — rewrite one bullet point
- **H2**: §1.2 + §2.3 entity type lists — update both enumerations to match entity-types.md canonical 15-type set

### Group 2: Validation and Specification Hygiene (M1 + M2 + M3 + M4)

- **M1**: §11.1 pseudocode — fix the birth certificate assertion
- **M2**: Add RFC 2119 notation section
- **M3**: §4.2 genesis_block_hash — clarify normative strength (RECOMMENDED vs MUST)
- **M4**: §3.2 step 5 — remove or rewrite null-issuer birth_certificate

### Group 3: Editorial Polish (L1 + L2)

- **L1**: Document or remove `birth_context` field
- **L2**: Number or explicitly exempt §5.2 sub-headings

---

## Cross-Reference to Prior Audits

| Audit | Spec | Findings | Remediated |
|-------|------|----------|------------|
| C2 | mcp-protocol.md | 13 (4H, 5M, 4L) | PRs #200, #201, #203 |
| C5 | presence-protocol.md | 13 (2H, 6M, 5L) | PRs #206, #207, #208, #209 |
| C6 | inter-society-protocol.md | 13 (3H, 5M, 5L) | PR #215 (12/13) |
| C7 | society-roles.md | 9 (1H, 4M, 4L) | PR #217 |
| C8 | entity-types.md | 10 (3H, 4M, 3L) | PR #219 (9/10, pending) |
| **C9** | **LCT-linked-context-token.md** | **8 (2H, 4M, 2L)** | **Pending** |

---

## Notes

**Clean structure**: Unlike entity-types.md (C8) which had severe section-numbering corruption (duplicate §3.2, duplicate §5, §4.x collision), the LCT spec has structurally sound numbering throughout. Findings here are content-level and specification-hygiene issues rather than structural defects.

**Entity type drift**: The H2 finding (entity type list mismatch) reflects a natural consequence of the taxonomy growing (from 10 to 15 types) without backfilling all references. entity-types.md is the normative source; the LCT spec's §1.2 and §2.3 are stale snapshots.

**Validation pseudocode quality**: §11.2 (`validate_birth_certificate`) is correctly implemented against the §2.3 data structure. Only §11.1 (`validate_lct`) has the semantic error (M1). The two validators have asymmetric quality.
