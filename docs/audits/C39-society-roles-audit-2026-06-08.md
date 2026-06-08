# C39: `society-roles.md` Delta Re-Audit

**Date**: 2026-06-08
**Auditor**: Autonomous session (Claude Opus 4.8, Legion) — multi-agent refute-by-default workflow
**Document**: `web4-standard/core-spec/society-roles.md` (391 lines, v0.1.0 DRAFT, header dated 2026-05-13; last substantively edited 2026-05-22 via #221)
**Prior audit**: `docs/audits/society-roles-internal-consistency-2026-05-21.md` (header-titled **C7**; 9 findings: 1H/4M/4L)
**Cross-referenced**: `mcp-protocol.md`, `entity-types.md`, `SOCIETY_SPECIFICATION.md`, `web4-society-authority-law.md` (SAL), `inter-society-protocol.md`, SDK `web4/role.py`
**Method**: §A holds-check (1 agent) + §B 6-dimension finders → adversarial refute-by-default verification (38 agents total)

**Series**: C39 (delta re-audit; alternation turn following C38 presence-protocol remediation #285)

---

## Summary

**§A holds-check: all 9 C7 findings HELD-REMEDIATED, 0 STILL-OPEN, 0 REGRESSED.** The #217 (resolve all 9 C7 findings) and #221 (resolve C7 residual cross-reference defects) passes correctly applied every C7 remediation. Notably, the C7 remediation correctly used the *live* mcp-protocol.md §7.3 numbering for the Policy-Entity/Archivist citations rather than the C7 audit's stale proposed §7.4/§7.5 — a clean remediation that read the current target doc.

**§B fresh audit: 31 raw findings → 26 confirmed / 3 deflated / 2 refuted.** Of the 26 confirmed, the large majority are *no-defect verifications* (positive confirmations that cross-references resolve) — the cross-reference layer of this document is, on the whole, clean. After deduplication (three finders independently flagged the same `§6.2` deixis bug), there are **5 autonomous-actionable defects** (1 MED, 3 LOW, 1 INFO) and **2 operator design-Q clusters** (both already on the carry list: carry-C25-H1, carry-C35-F9).

The one defect of note (**F1**) is a [[remediation-introduced-regression]]-class residual: the C7 **M4** remediation, when it rewrote the §7 `inter-society-protocol.md` row, copied the reciprocal sentence from inter-society-protocol.md verbatim ("This spec's §6.2 …") without rebinding the possessive — so the holds-check correctly read M4 as "section numbers all resolve" while the *deixis* silently broke. This is exactly the class the regression-checklist exists to catch, and it argues for adding a **deixis/possessive check** to that checklist (does "this spec" still mean the host file after a cross-doc row is copied?).

---

## §A — C7 Holds-Check (9/9 HELD-REMEDIATED)

| C7 | Severity | Status | Evidence (current society-roles.md) |
|----|----------|--------|--------------------------------------|
| H1 | HIGH | **HELD-REMEDIATED** | §5.1 (L333–340) now lists all 7 base-mandatory roles incl. the previously-missing **Law Oracle** (L336). |
| M1 | MED | **HELD-REMEDIATED** | §7 table (L371) has the `mcp-protocol.md` row; all 4 section refs verified (§7.3 Policy-Entity L394 + Archivist L402; §7.5 Witness L470; §7.7 Exchange Rate L509). Remediation used live §7.3, not the audit's stale §7.4. |
| M2 | MED | **HELD-REMEDIATED** | §7 table (L372) has the SAL row; SAL §5 verified to define exactly the 5 cited roles (Citizen/Authority/Law Oracle/Witness/Auditor). |
| M3 | MED | **HELD-REMEDIATED** | §2.3 Notes (L106) no longer references the private `hardbound` code path; now reads "enterprise implementations realize operationally." |
| M4 | MED | **HELD-REMEDIATED** (but introduced F1) | §7 ISP row (L370) rewritten; R7-Witness misattribution removed. Section numbers resolve — **but** the row carries a deixis defect (see **F1**). |
| L1 | LOW | **HELD-REMEDIATED** | `## Notation` section added (L15–17), RFC 2119. |
| L2 | LOW | **HELD-REMEDIATED** | §1.2 (L39) adds "See §3 for the full illustrative table…". |
| L3 | LOW | **HELD-REMEDIATED** | Outward-role term standardized to **Federation-Member** (§1.2 L34, §3 L196); §4.2 keeps role name "Diplomat / Federation-Representative". |
| L4 | LOW | **HELD-REMEDIATED** | §6 item 3 (L358) adds "(per `LCT-linked-context-token.md` witnessing requirements)". |

**Regression check (per [[remediation-introduced-regression]]):** All §7-table section *numbers* added by the C7 remediation resolve to the correct target documents (mcp §7.3/§7.5/§7.7; ISP §2.2/§6.2/§4.6). One *prose-level* regression escaped the section-number check — the ISP-row possessive deixis, captured as **F1** below.

---

## §B — New Findings (confirmed, deduplicated)

### Autonomous-actionable

#### F1 — §7 ISP-row "This spec's §6.2" deixis points at a non-existent self-section (MEDIUM)

**Location**: §7 Relationship to Other Specs, L370 (`inter-society-protocol.md` row)

The row reads: *"Inter-society interactions reference the Diplomat role (§2.2 federation genesis). **This spec's §6.2** defines semantic viability criteria that constrain role composition. ATP measurement witnessing (§4.6) involves the Witness role…"*

In society-roles.md, "this spec" = society-roles.md, but this file's §6 is "Audit Implications" (L352), a flat checklist with **no subsections** — there is no §6.2 here. All three section numbers (§2.2, §4.6, §6.2) are in fact sections of **inter-society-protocol.md** (§2.2 Federation-Based Genesis L87; §4.6 Resource Measurement and Attestation L239; §6.2 Minimum Viable Semantic Society L324). The defect is a copy-paste pronoun bug: the sentence is authored verbatim in inter-society-protocol.md L365 (where "This spec's §6.2" is *correct*) and was pasted into the society-roles.md row during the C7-M4 remediation without rebinding the possessive. A reader following "This spec's §6.2" inside society-roles.md lands on nothing.

**Severity**: MEDIUM (converged from MED/LOW across three finders) — purely editorial/navigational in an informative table; no normative, wire, or conformance impact, but it is a genuinely broken internal reference.
**Autonomous fix (next turn)**: change "This spec's §6.2" → "`inter-society-protocol.md` §6.2" (and, for clarity, qualify the bare §2.2/§4.6 in the same cell the same way). Classed as a **C7-M4-residual** that the #221 residual-cleanup pass missed.

#### F2 — §7 mcp-row cites §7.5 for the Witness co-signing requirement; the normative MUST lives in §7.3 (LOW)

**Location**: §7 table, L371 ("Witness co-signs high-consequence actions (§7.5)")

The normative co-signing obligation is established in mcp-protocol.md **§7.3** (L398: "For high-consequence actions … `reputation.witness_signatures` MUST contain at least one signature from a Witness role"). §7.5 ("Cross-Society Witnessing…", L470) governs witness *selection* and merely back-references §7.3 (L479: "consistent with the §7.3 normative requirement"). The row's other three citations all point at the *requirement-establishing* section, making the §7.5-only Witness cite the inconsistent one.
**Autonomous fix**: cite §7.3 (or §7.3+§7.5) for the Witness co-signing claim. No normative impact; citation-precision only.

#### F3 — §7 mcp-row cites §7.7 (WIP) without a status caveat (LOW)

**Location**: §7 table, L371 ("Treasurer negotiates exchange rates (§7.7)")

mcp §7.7 carries a prominent banner (mcp L511: "STATUS: WIP v0.1.0-draft … Implementations SHOULD NOT depend on the wire format until v0.1.0-final"). The §7 row presents the §7.7 reference as settled like the §7.3 citations. The cited content (Treasurer role assignment, §7.7.2) is the *stable* part of §7.7, so this is hygiene, not a broken reference.
**Autonomous fix**: annotate "(§7.7, WIP)" or similar. (Couples to the standing §7.7-promotion tracking; once mcp §7.7 reaches v0.1.0-final the caveat is removed.)

#### F4 — §2.7 cites entity-types.md §3.1 for citizen "mechanics"; mechanics actually live in §3.4 (INFO)

**Location**: §2.7, L181 ("the citizen-role mechanics are detailed in `entity-types.md` §3.1")

entity-types.md §3.1 ("The Citizen Role: Universal Birth Certificate") covers the citizen *principle/structure*; the operational *pairing mechanics* (prerequisite check, permanence, termination) are in §3.4 (L222–244). The §3.1 anchor is the right *concept* target and resolves correctly — this is a precision nit, not a dangling reference.
**Autonomous fix (optional)**: cite "§3.1 (and §3.4 for pairing mechanics)".

#### F5 — Solo-founder role count stated three ways (5 / "6+" / 7) (LOW)

**Location**: §2 L51 (example: "Sovereign + Treasurer + Administrator + Archivist + Citizen" = 5, omits Law Oracle + Policy-Entity); §5 table L325 ("fills 6+ of 7 base-mandatory roles"); §5.1 L333–340 (lists all 7).

Since all 7 base-mandatory roles MUST be filled, a solo-founder society necessarily has one entity filling all 7. The §2 line is explicitly illustrative ("e.g.") and the §5.1 line is a capability list ("can hold"), so none is *false* and the seven-role mandate is unambiguous — hence DEFLATED from MED to LOW. But a reader gets three different mental images of the same scenario.
**Autonomous fix (editorial)**: expand the §2 "e.g." to all seven (or note it is partial), and change §5's "6+" to "all 7" (the "6+" likely reflects §5.1's note that Policy-Entity may be AI-assisted = a second entity; if so, say that).

### Operator design-Q / cross-track (NOT for the next remediation turn)

#### D1/D2 — Canonical-home divergence + broken SOCIETY_SPEC citation (design-Q; carry-C25-H1)

**Location**: society-roles.md §2 (authoritative enumeration) + §7 SOCIETY_SPEC row (L368); vs `SOCIETY_SPECIFICATION.md` §1.2.5 (L60); vs SDK `role.py`.

society-roles.md §2 is written as *the* normative enumeration of the seven base-mandatory roles ("Every Web4-compliant society MUST have these seven roles filled"), and the SDK (`role.py` L2/L19) cites society-roles.md as the source. The SDK's `BASE_MANDATORY_ROLES` set matches the spec's seven **exactly** (verified: SOVEREIGN, LAW_ORACLE, POLICY_ENTITY, TREASURER, ADMINISTRATOR, ARCHIVIST, CITIZEN). **But** `SOCIETY_SPECIFICATION.md` §1.2.5 attributes the seven-role enumeration to `inter-society-protocol.md` §6.2 — and ISP §6.2 ("Minimum Viable Semantic Society") contains **no seven-role list at all** (only 3 abstract viability criteria; a grep of ISP finds zero occurrences of "Administrator"/"Archivist"/"base-mandatory"). So SOCIETY_SPEC's citation is *factually broken regardless of which doc is canonical*, and SOCIETY_SPEC never cites society-roles.md (the doc society-roles.md claims to "Extend").

This is the open **carry-C25-H1** "7-role canonical home" question (SOCIETY_SPEC §1.2.5 vs ISP §6.2 vs SDK `BASE_MANDATORY_ROLES`). **HIGH** as a corpus contradiction, but **operator-gated** — the operator must designate the canonical home before the SOCIETY_SPEC citation can be repointed. The fix lives in **SOCIETY_SPECIFICATION.md** (a C22-domain file), so it is **cross-track** for this audit's target. Recorded as evidence; not self-resolved.

#### D3 — Policy-Entity role-name casing diverges three ways (design-Q; carry-C35-F9)

**Location**: society-roles.md (hyphenated `Policy-Entity` ×14, fully internally consistent) vs `SOCIETY_SPECIFICATION.md` §1.2.5 (spaced "Policy Entity") vs SDK `role.py` (CamelCase `PolicyEntity`, enum value `policy_entity`).

Same base-mandatory role, three display spellings. Membership is identical (D-class, not a count divergence). This is the open **carry-C35-F9** naming question; exit #159 explicitly DECLINED to normalize a single file as a corpus-wide overcall, and society-roles.md is the *cited authority* for the hyphenated role-name form. Note entity-types.md legitimately uses BOTH forms with a real semantic split (hyphenated = society **role**; CamelCase = **entity-type/class** with `PolicyEntity.evaluate()` / PolicyGate, per the CLAUDE.md SOIA-SAGE framing). **Operator naming decision; do NOT change this file's hyphenation.**

### INFO / record-only

- **Header date staleness** (editorial B2): header `Date: 2026-05-13` (genesis) was not bumped by the #217/#221 C7 edits. Per **BC#13** this is INFO (no normative date-dependency in the file; the only other date, §9 L390 "2026-05-13 dialogue with dp", is a correct historical reference and must NOT change). Per **BC#15**, the *next remediation turn* (which will edit this file for F1–F5) should set `Date` to the edit date at that point.
- **Clean-pass verifications** (the bulk of §B confirmed): §2 "seven roles" count matches §2.1–§2.7; no orphan roles in §3/§5/§6; all entity-types.md §-refs resolve (§3.1/§4.2/§4.6/§4.7); all five reverse mcp→society-roles back-refs resolve (mcp L394/398/402/472/548); all ISP §-refs resolve (§2.2/§6.2/§4.6, bidirectional with ISP §8 L365); SAL §5 defines exactly the 5 cited roles; SDK `BASE_MANDATORY_ROLES` matches the spec's 7 exactly; RFC 2119 notation correct (no undeclared keywords). §1.2/§3 context-mandatory lists are a by-design superset (REFUTED as a defect).

---

## Deflated / Refuted (overcall discipline)

| ID | Dim | Raw | Verdict | Note |
|----|-----|-----|---------|------|
| B2 | internal | MED "3 inconsistent solo-founder counts" | DEFLATED→LOW | Real editorial nit (= F5); illustrative/capability lists need not match the mandate verbatim. |
| B3 | internal | LOW "§6.2 self-ref vs §6 has no subsections" | DEFLATED→LOW | Same root as F1; reframed from "missing subsection" to "un-rebound possessive." |
| B6 | society-sal-sdk | LOW "Diplomat cite §2.2 off by a few lines" | DEFLATED→DROP | §2.2 pointer is exactly correct; L93 is inside §2.2. |
| B5 | internal | INFO "§3 superset of §1.2" | REFUTED→DROP | By-design; both lists explicitly informative/non-exhaustive. |
| B2 | mcp | INFO "reverse back-refs resolve" | REFUTED→DROP | No-defect verification; all 5 resolve. |

---

## Remediation Priority (for the next, alternation-paired remediation turn)

**Group 1 — §7 table accuracy (F1 + F2 + F3):** rebind the ISP-row deixis (F1, the priority item), fix the Witness §7.5→§7.3 cite (F2), add the §7.7 WIP caveat (F3). All in §7, one cohesive edit cluster. `society-roles.md` only.

**Group 2 — editorial harmonization (F4 + F5):** citizen-mechanics §3.1→§3.1+§3.4 (F4); solo-founder count harmonization §2/§5 (F5). `society-roles.md` only.

**Group 3 — date hygiene:** bump header `Date` to the remediation date (BC#15), leaving §9 acknowledgment date untouched.

**NOT in scope (operator / cross-track):** D1/D2 canonical-home (carry-C25-H1; fix lives in SOCIETY_SPECIFICATION.md); D3 Policy-Entity casing (carry-C35-F9).

---

## Process Note

This audit reinforces the [[remediation-introduced-regression]] checklist with a new item: **after a remediation copies a cross-doc relationship-table row from a reciprocal spec, verify the deixis ("this spec", "that spec", bare §-refs) still resolves against the *host* file.** The C7-M4 remediation passed the section-number resolution check but introduced F1 by copying inter-society-protocol.md's reciprocal sentence without flipping "This spec's." The section-number check alone is insufficient; possessive/deictic correctness is a distinct axis.
