# C8 Audit: `entity-types.md` Internal Consistency

**Date**: 2026-05-22
**Auditor**: Autonomous session (Legion, web4 track)
**Document**: `web4-standard/core-spec/entity-types.md` (706 lines)
**Methodology**: C-series internal consistency audit (same as C2, C5, C6, C7)
**SDK alignment**: Checked against `web4/entity.py`, `web4/lct.py` — full compliance (15 types, all modes, energy patterns, interaction rules match)

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 3 | H1, H2, H3 |
| MEDIUM | 4 | M1, M2, M3, M4 |
| LOW | 3 | L1, L2, L3 |
| **Total** | **10** | |

The document has significant **section numbering corruption** in the §3–§5 range: duplicate section numbers, heading-level inconsistencies, and a numbering collision that makes two different sections share the same §4.2/§4.3 and §5/§5.1 addresses. The content itself is sound and aligns with the SDK, but the structural issues make the document ambiguous to reference.

---

## HIGH Findings

### H1: Duplicate §3.2 — Two Sections Share the Same Number

**Lines**: 156 and 165
**Issue**: Two consecutive `### 3.2` headings:
- Line 156: `### 3.2 The Role Revolution`
- Line 165: `### 3.2 Role LCT Structure`

**Impact**: Any cross-reference to "§3.2" is ambiguous — it could mean either section. The second §3.2 should be §3.3, with current §3.3 and §3.4 renumbered accordingly.

**Remediation**: Renumber to `### 3.2 The Role Revolution`, `### 3.3 Role LCT Structure`, `### 3.4 Role Hierarchy` (was 3.3), `### 3.5 Example Roles per Entity Type` (was 3.4).

---

### H2: Duplicate §5 and §5.1 — Two Top-Level Sections Share the Same Number

**Lines**: 371/439 (§5) and 373/441 (§5.1)
**Issue**: Two separate `## 5.` sections:
- Line 371: `## 5. Entity Lifecycle`
- Line 439: `## 5. Entity Interactions`

Each contains a `### 5.1`:
- Line 373: `### 5.1 Entity Creation and Birth Certificate (SAL-compliant)`
- Line 441: `### 5.1 Valid Interaction Patterns`

**Impact**: "§5" and "§5.1" are ambiguous references — could mean lifecycle or interactions. This is the most structurally damaging finding: it makes the entire second half of the document's section addressing unreliable.

**Remediation**: Renumber "Entity Interactions" as §6, pushing all subsequent sections (current §6–§13) up by one to §7–§14. Alternatively, merge lifecycle and interactions under a single §5 with appropriate subsection numbering.

---

### H3: §4.2/§4.3 Numbering Collision — Lifecycle Subsections Reuse SAL Role Numbers

**Lines**: 421 and 430
**Issue**: Two subsections under §5 "Entity Lifecycle" are numbered `### 4.2` and `### 4.3`:
- Line 421: `### 4.2 Entity Evolution`
- Line 430: `### 4.3 Entity Termination`

These collide with the actual §4 "SAL-Specific Roles" subsections:
- Line 275: `### 4.2 Authority Role`
- Line 282: `### 4.3 Law Oracle Role`

**Impact**: "§4.2" could mean either "Authority Role" or "Entity Evolution" depending on context. This appears to be a copy-paste error where these subsections were moved from §4 to §5 but their numbering wasn't updated.

**Remediation**: Renumber to `### 5.2 Entity Evolution` and `### 5.3 Entity Termination` (after H2's renumbering cascade, these become §5.2 and §5.3 under the lifecycle section).

---

## MEDIUM Findings

### M1: §3.4 Heading Level Inconsistency — `##` Instead of `###`

**Line**: 238
**Issue**: `## 3.4 Example Roles per Entity Type` uses a `##` (h2) heading, but all other §3.x subsections use `###` (h3):
- Line 124: `### 3.1 The Citizen Role`
- Line 156: `### 3.2 The Role Revolution`
- Line 165: `### 3.2 Role LCT Structure`
- Line 209: `### 3.3 Role Hierarchy`
- Line 238: `## 3.4 Example Roles per Entity Type` ← wrong level

**Impact**: §3.4 renders at the same visual level as §3 itself, breaking the heading hierarchy. In table-of-contents generators, it appears as a sibling of §3 rather than a child.

**Remediation**: Change `## 3.4` to `### 3.4` (or `### 3.5` after H1 renumbering).

---

### M2: Missing RFC 2119 Notation Section

**Lines**: N/A (absent)
**Issue**: The document uses RFC 2119 keywords (MUST, MUST NOT, SHOULD) in §6 and §7:
- Line 474: "Implementations MUST:"
- Line 481: "Implementations MUST:"
- Line 492: "Implementations SHOULD:"
- Line 502: "an entity's type MUST NOT change"

But there is no RFC 2119 notation section declaring these keywords as normative. The C7 remediation (PR #217) added such a section to `society-roles.md` (§0, before §1). The C6 remediation added one to `inter-society-protocol.md`. This document lacks one.

**Impact**: Without the notation section, MUST/SHOULD/MUST NOT are technically non-normative — a reader cannot distinguish between conversational emphasis and specification-grade requirements.

**Remediation**: Add a "Notation" section before §1 (as §0 or unnumbered) matching the pattern in `society-roles.md`:
```
## Notation
Key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in this document
are to be interpreted as described in RFC 2119.
```

---

### M3: Misplaced "Auditor Adjustment Policy" Block Under §4.7 Client Role

**Lines**: 320–335
**Issue**: The `#### Auditor Adjustment Policy` subheading and its JSON example block appear under `### 4.7 Client Role (AGY)`, but the content describes auditor behavior (T3/V3 adjustments, evidence-based audit requests) — not client behavior.

The Auditor role is defined in §4.5. The Client role is defined in §4.7. The auditor JSON block is structurally placed as a child of §4.7 but semantically belongs under §4.5.

The `#### Agency Grant Structure (AGY)` block at line 337 correctly belongs under §4.7 (client/agent grant structure).

**Impact**: A reader consulting §4.5 for auditor behavior won't find the adjustment policy JSON. A reader consulting §4.7 for client behavior will find an unrelated auditor example.

**Remediation**: Move lines 320–335 (the `#### Auditor Adjustment Policy` heading and JSON block) from under §4.7 to under §4.5 (after line 302).

---

### M4: Cross-Reference to LCT Spec for "Role-LCT Pairing Mechanics" — Content Not There

**Line**: 262
**Issue**: §3.4 says:
> For the role-LCT pairing mechanics see `LCT-linked-context-token.md`

However, `LCT-linked-context-token.md` does not have a dedicated section on role-LCT pairing mechanics. The closest content is:
- General pairing relationships in its MRH structure (§5.2)
- Permanent citizen pairing requirements (§4.2)

The actual role-LCT pairing mechanics are described in `entity-types.md` itself at §3.3 (lines 220–231, "Role-Agent Pairing" six-step process).

**Impact**: A reader following the cross-reference will not find the promised content.

**Remediation**: Either:
1. Change the reference to point to `entity-types.md` §3.3 (self-reference), or
2. Add a role-LCT pairing section to `LCT-linked-context-token.md` (scope expansion — out of bounds for entity-types.md remediation alone)

---

## LOW Findings

### L1: "blockchain" in Pseudocode Comment vs "Immutable Ledger" Elsewhere

**Line**: 415
**Issue**: The birth certificate pseudocode contains:
```python
    # Record in blockchain
    record_birth_certificate(birth_cert)
```

But the normative spec text at line 382 (step 5) says:
> "Birth Certificate Recording: Written to society's immutable ledger"

Web4 consistently uses "immutable ledger" (technology-agnostic) rather than "blockchain" (implementation-specific). The pseudocode comment is the only instance of "blockchain" in the document.

**Remediation**: Change comment to `# Record in immutable ledger`.

---

### L2: Self-Referential "see §3 below" in §3.4 Table

**Line**: 248
**Issue**: The Role row in the §3.4 example-roles table says:
> "Roles fill roles in a degenerate sense — see §3 below."

But the reader is already in §3.4, which is part of §3. "§3 below" makes no sense when you're already inside §3. This appears to be a stale reference from when the table was elsewhere in the document.

**Remediation**: Either remove the reference ("Roles fill roles in a degenerate sense.") or make it specific ("see §3.2 above" or equivalent after renumbering).

---

### L3: §11 Citizen Role Examples Redundancy with §3.1

**Lines**: 623–644 (§11) vs 124–154 (§3.1)
**Issue**: §11 "Citizen Role Examples" covers:
- Context-specific citizens (line 625): nation, platform, network, organization, ecosystem
- Birth certificate as proof of origin (line 637): provenance, legitimacy, context, inheritance, witnesses

§3.1 "The Citizen Role: Universal Birth Certificate" covers:
- Citizen role characteristics (line 129): universal, contextual, foundational, immutable, inherited
- Birth certificate structure (line 136): JSON example with witnesses, genesis block, initial rights

There is significant overlap: both discuss context-specificity, both discuss birth certificates. §11 adds a table and a bullet list, but no new normative content beyond §3.1.

**Impact**: Minor. The redundancy is not contradictory — the sections say the same things in different formats. However, it inflates the document and creates maintenance risk (updates to citizen semantics must be made in two places).

**Remediation**: Consider merging §11 content into §3.1 (adding the context table to the existing citizen role section) and removing §11 as a standalone section.

---

## SDK Alignment Note

The SDK (`web4/entity.py`, `web4/lct.py`) is **fully aligned** with the document's normative content:
- All 15 entity types defined with matching names, descriptions, modes, and energy patterns
- Behavioral modes (Agentic, Responsive, Delegative) correctly distributed
- Energy patterns (Active/Passive) and R6 capability correctly assigned
- Interaction rules (Binding, Pairing, Witnessing, Delegation) implemented per spec
- 48 tests passing, comprehensive coverage

The findings above are entirely structural/editorial — no content-level misalignment was found.

---

## Remediation Priority Groups

### Group 1: Section Renumbering (H1 + H2 + H3)

All three HIGH findings are aspects of a single problem: section numbering corruption. They should be remediated together in a single pass to avoid partial renumbering that creates new collisions.

**Approach**: Renumber the entire document's §3–§14 sections in one pass:
- §3.2 → split into §3.2 + §3.3, cascade §3.3→§3.4, §3.4→§3.5
- §5 "Entity Lifecycle" keeps §5; fix subsections to §5.1/§5.2/§5.3
- §5 "Entity Interactions" becomes §6; cascade §6→§7 through §13→§14
- Remove stale §4.2/§4.3 numbering under lifecycle section

### Group 2: Structural Fixes (M1 + M3)

- Fix §3.4 heading level (`##` → `###`)
- Move Auditor Adjustment Policy block from §4.7 to §4.5

### Group 3: Notation and References (M2 + M4)

- Add RFC 2119 notation section
- Fix or flag the LCT cross-reference

### Group 4: Editorial Polish (L1 + L2 + L3)

- Fix "blockchain" comment
- Fix self-referential §3 reference
- Consider §11 merge (optional — can defer)

---

## Cross-Reference to Prior Audits

| Audit | Spec | Findings | Remediated |
|-------|------|----------|------------|
| C2 | mcp-protocol.md | 13 (4H, 5M, 4L) | PRs #200, #201, #203 |
| C5 | presence-protocol.md | 13 (2H, 6M, 5L) | PRs #206, #207, #208, #209 |
| C6 | inter-society-protocol.md | 13 (3H, 5M, 5L) | PR #215 (12/13) |
| C7 | society-roles.md | 9 (1H, 4M, 4L) | PR #217 |
| **C8** | **entity-types.md** | **10 (3H, 4M, 3L)** | **Pending** |
