# C7: `society-roles.md` Internal Consistency Audit

**Date**: 2026-05-21
**Auditor**: Autonomous session (Claude Opus 4.6, Legion)
**Document**: `web4-standard/core-spec/society-roles.md` (381 lines, v0.1.0 DRAFT, 2026-05-13)
**Cross-referenced**: `SOCIETY_SPECIFICATION.md`, `inter-society-protocol.md`, `mcp-protocol.md`, `entity-types.md`, `web4-society-authority-law.md`, `LCT-linked-context-token.md`, `t3-v3-tensors.md`, `r6-framework.md`, `r7-framework.md`, SDK `web4/role.py`

**Series**: C7 (following C2: mcp-protocol.md, C5: presence-protocol.md, C6: inter-society-protocol.md)

---

## Summary

9 findings: **1 HIGH**, **4 MEDIUM**, **4 LOW**. The document is conceptually sound and well-structured. The three-tier role taxonomy is internally consistent in its definitions, and the fractal composability semantics (§5) are architecturally coherent. The findings are concentrated in two areas: (1) a factual omission in the solo-founder example (H1), and (2) missing entries in the §7 relationship table (M1, M2, M4). No conceptual or architectural issues.

---

## Findings

### HIGH

#### H1: §5.1 Multi-Hat Pattern omits Law Oracle from the 7-role solo-founder example

**Severity**: HIGH — internal factual inconsistency

**Location**: Lines 326–334

**Issue**: §5.1 lists the roles a solo human fills in a solo society:

> - Citizen role (base membership)
> - Sovereign role (charter authority)
> - Treasurer role (ATP ops)
> - Administrator role (execution)
> - Archivist role (ledger writes)
> - Policy-Entity role (per-action decisions; possibly with AI-assist)

This is 6 roles. §2 (line 45) mandates: "Every Web4-compliant society MUST have these seven roles filled." The missing 7th is **Law Oracle** (§2.2).

**Cross-document inconsistency**:
- `inter-society-protocol.md` §2.1 step 3 requires the founder to "publish a society charter (RDF graph) containing at least one foundational law" — implying the founder acts as Law Oracle.
- The SDK's `bootstrap_society_roles()` creates all 7 role assignments including `SocietyRole.LAW_ORACLE` for the solo founder.

**Remediation**: Add `- Law Oracle role (law publishing; possibly minimal — one foundational law per charter)` to the §5.1 list, between Sovereign and Policy-Entity (maintaining the §2 ordering).

---

### MEDIUM

#### M1: §7 relationship table omits `mcp-protocol.md`

**Severity**: MEDIUM — significant cross-reference gap

**Location**: Lines 357–367

**Issue**: `mcp-protocol.md` references `society-roles.md` at 5 specific locations:

| mcp-protocol.md line | Reference | Context |
|---|---|---|
| 394 | §2.3 (Policy-Entity) | responding society's Policy-Entity signs reputation envelope |
| 398 | §4.1 (Witness) | Witness role required for high-consequence actions |
| 402 | §2.6 (Archivist) | Archivist persists signed reputation envelope to ledger |
| 473 | §4.1 (Witness) | cross-society R7 witnessing |
| 549 | §2.4 (Treasurer) | Treasurer conducts exchange-rate negotiation |

As the inter-society action protocol per the canonical equation (`Web4 = MCP + …`), `mcp-protocol.md` is a primary consumer of the role taxonomy. Its absence from the §7 relationship table leaves a significant documentation gap.

**Remediation**: Add row to §7 table:

```
| `mcp-protocol.md` | MCP actions consume the role taxonomy directly: Policy-Entity signs action decisions (§7.4), Witness co-signs high-consequence actions (§7.5), Archivist persists audit bundles (§7.5), Treasurer negotiates exchange rates (§7.7). |
```

#### M2: §7 relationship table omits `web4-society-authority-law.md` (SAL spec)

**Severity**: MEDIUM — omitted bidirectional dependency

**Location**: Lines 357–367

**Issue**: The SAL spec defines 5 of the same roles from the Society–Authority–Law perspective:

| SAL §section | Role | Normative additions beyond society-roles.md |
|---|---|---|
| §5.1 | Citizen | Immutable birth pairing, cannot be revoked |
| §5.2 | Authority | Scoped delegation, machine-readable policy publication |
| §5.3 | Law Oracle | Versioned law datasets, deterministic Q&A endpoints |
| §5.4 | Witness | Co-signing, timestamping, availability proofs |
| §5.5 | Auditor | MRH traversal, T3/V3 adjustment with evidence + rate limits |

The SAL spec adds detailed normative requirements (ledger interfaces, SPARQL queries, error conditions, T3/V3 implications) that society-roles.md's role descriptions do not cover. Readers of society-roles.md may not know this companion treatment exists.

**Remediation**: Add row to §7 table:

```
| `web4-society-authority-law.md` | The SAL spec defines Citizen, Authority, Law Oracle, Witness, and Auditor from the Society–Authority–Law perspective with detailed normative requirements (birth certificates, delegation chains, ledger interfaces, audit transcripts). This spec provides the role taxonomy; SAL provides the operational protocol for a subset of those roles. |
```

#### M3: §2.3 references hardbound's private code path

**Severity**: MEDIUM — private-repository reference in public spec

**Location**: Line 100

**Issue**: §2.3 Policy-Entity notes: "This is the role hardbound's `src/core/policy-entity.ts` realizes operationally." `hardbound` is a private enterprise repository. External readers of the public spec cannot access or verify this reference. Public specifications should be self-contained.

**Remediation**: Remove the hardbound reference, or replace with a spec-level statement such as: "This role is the per-action policy evaluation function that enterprise implementations realize operationally."

#### M4: §7 table misattributes cross-society R7 Witness to `inter-society-protocol.md`

**Severity**: MEDIUM — incorrect attribution

**Location**: Line 363

**Issue**: The `inter-society-protocol.md` row in §7 states:

> "Inter-society interactions reference the Diplomat role; **cross-society R7 actions reference the Witness role**"

Cross-society R7 actions are specified in `mcp-protocol.md` §7.5 ("Cross-Society Witnessing and R7 Reputation Propagation"), not in `inter-society-protocol.md`. The inter-society protocol defines genesis, first-contact, and secession — not the R7 action protocol itself.

`inter-society-protocol.md` does discuss witnessing in §4.6 ("Resource Measurement and Attestation"), but this is about ATP resource measurement witnessing, not about cross-society R7 action witnessing.

**Remediation**: Revise the `inter-society-protocol.md` row to:

```
| `inter-society-protocol.md` | Inter-society interactions reference the Diplomat role (§2.2 federation genesis). This spec's §6.2 defines semantic viability criteria that constrain role composition. ATP measurement witnessing (§4.6) involves the Witness role at the resource attestation layer. Bidirectional dependency. |
```

And add the R7 Witness attribution to the proposed `mcp-protocol.md` row (M1).

---

### LOW

#### L1: No RFC 2119 notation section

**Severity**: LOW — editorial convention

**Location**: Document-wide

**Issue**: MUST, SHOULD, and MAY are used normatively throughout (lines 19, 37, 38, 41, 45, 180, etc.) but no notation or terminology section defines their semantics per RFC 2119 / BCP 14. Other core specs include this:
- `web4-society-authority-law.md` §0: "MUST/SHOULD/MAY: As defined in RFC 2119"
- `mcp-protocol.md`: notation section
- `presence-protocol.md`: notation section

**Remediation**: Add a notation paragraph before §1 or at the top of §1: "Key words MUST, MUST NOT, SHOULD, SHOULD NOT, MAY in this document are to be interpreted as described in RFC 2119."

#### L2: §1.2 and §3 context-mandatory example lists diverge without cross-reference

**Severity**: LOW — editorial gap

**Location**: Lines 25–33 (§1.2) vs lines 182–192 (§3 table)

**Issue**: §1.2 lists 7 illustrative outward-role → inward-role examples. §3's table has 9 rows, adding Public-Service-Provider and Recovery-Service. Both are explicitly non-exhaustive ("Examples:" / "illustrative"), so this is not technically inconsistent. However, §1.2 doesn't cross-reference §3 for the fuller table, which may confuse readers who read §1.2 as the complete set.

**Remediation**: Add to §1.2 after the examples list: "See §3 for the full illustrative table of context-mandatory mappings."

#### L3: Inconsistent outward-role terminology for federation membership

**Severity**: LOW — terminology inconsistency

**Location**: Lines 30 (§1.2), 190 (§3 table), 230 (§4.2 header)

**Issue**: Three different terms for the same outward-facing posture:
- §1.2: "**Diplomat-Federation**" (outward role name)
- §3 table: "**Federation-Member**" (outward role name)
- §4.2: "**Diplomat / Federation-Representative**" (role name)

"Diplomat-Federation" and "Federation-Member" describe the same outward role (a society that participates in a federation) but use inconsistent names. The §4.2 header "Diplomat / Federation-Representative" provides the role definition but uses yet another variant.

**Remediation**: Standardize the outward-role term across §1.2 and §3 (suggest "Federation-Member" since it describes the outward posture). Keep the §4.2 role name as "Diplomat / Federation-Representative" since that's the role definition (distinct from the outward posture that triggers it).

#### L4: §6 audit item 3 references witnessed pairings without spec treatment

**Severity**: LOW — implicit cross-reference

**Location**: Line 351

**Issue**: §6's audit checklist item 3 asks: "Are role-LCT pairings current and **witnessed**?" However, §2–§5 of this document never specify witnessing requirements for role-LCT assignment or rotation. Witnessing of pairings is specified in the LCT spec (`LCT-linked-context-token.md`) and the SAL spec (`web4-society-authority-law.md` §3.4, §5.4), but not in this document.

**Remediation**: Add a forward-reference note to §6 item 3: "(per `LCT-linked-context-token.md` witnessing requirements)" or briefly note that role-LCT pairing witnessing follows the general LCT pairing protocol.

---

## Findings Not Raised

1. **Header version v0.1.0 after PR #215 edit**: PR #215 changed one cross-reference in §4.1 (§4.4→§4.6). This was a follow-on from inter-society-protocol.md's §4 renumbering, not a substantive change to society-roles.md. A version bump is arguably unnecessary. Noted but not flagged.

2. **entity-types.md §4.6/§4.7 cross-references**: Verified. `entity-types.md` has §4.6 "Agent Role (AGY)" (line 304) and §4.7 "Client Role (AGY)" (line 312). Cross-references from society-roles.md §4.2 are correct.

3. **entity-types.md duplicate §3.2 numbering**: Observed duplicate §3.2 headers in entity-types.md (line 156 "The Role Revolution" and line 165 "Role LCT Structure"). This is an entity-types.md issue, not a society-roles.md finding. Noted for a potential future C8 audit of entity-types.md.

4. **"Example filling entities" lists not perfectly symmetric with entity-types.md §3.4**: The two documents' entity↔role mappings are illustrative by design and don't need to be identical. Minor asymmetries (e.g., Law Oracle doesn't list Human but entity-types.md doesn't list Law Oracle for Human) are consistent because both documents flag their lists as "illustrative."

---

## Remediation Priority Groups

### Group 1 (H1): Solo-founder completeness fix
- Add Law Oracle to §5.1 list
- **Files**: `society-roles.md` only
- **Risk**: Minimal — adding one list item

### Group 2 (M1 + M2 + M4): §7 relationship table completeness
- Add `mcp-protocol.md` row
- Add `web4-society-authority-law.md` row
- Fix `inter-society-protocol.md` row attribution
- **Files**: `society-roles.md` only
- **Risk**: Minimal — table additions and one row revision

### Group 3 (M3): Remove private-repo reference
- Replace hardbound code path with spec-level statement
- **Files**: `society-roles.md` only
- **Risk**: Minimal — editorial change

### Group 4 (L1 + L2 + L3 + L4): Editorial cleanup
- Add RFC 2119 notation
- Add §1.2→§3 cross-reference
- Standardize outward-role terminology
- Add witnessing forward-reference to §6
- **Files**: `society-roles.md` only
- **Risk**: Minimal — editorial changes

---

## Comparison with Prior Audits

| Audit | Document | Findings | Pattern |
|---|---|---|---|
| C2 | `mcp-protocol.md` (651 lines) | 13 (4 HIGH, 5 MEDIUM, 4 LOW) | Cross-reference failures + internal contradictions |
| C5 | `presence-protocol.md` (460 lines) | 13 (2 HIGH, 6 MEDIUM, 5 LOW) | Staleness + terminology drift |
| C6 | `inter-society-protocol.md` (376 lines) | 13 (3 HIGH, 5 MEDIUM, 5 LOW) | Numbering + version + relationship table |
| **C7** | **`society-roles.md` (381 lines)** | **9 (1 HIGH, 4 MEDIUM, 4 LOW)** | **Relationship table gaps + one factual omission** |

society-roles.md has the fewest findings of the four audited specs, consistent with its focused scope (role taxonomy) and its creation as a single cohesive document (2026-05-13) rather than an incrementally amended spec. The relationship table pattern (missing cross-references) recurs from C6 — these specs are new and their cross-reference surfaces are still stabilizing.
