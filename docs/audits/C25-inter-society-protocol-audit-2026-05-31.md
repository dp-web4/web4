# C25: `inter-society-protocol.md` Internal Consistency RE-Audit

**Date**: 2026-05-31
**Track**: web4 (Legion autonomous session, slot `180057`, exit #140)
**Instrument**: Same as C12-C24 C-series internal-consistency instrument; delta RE-audit of prior C6 (2026-05-21)
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2, 375 lines, unchanged since `4ff9669d` 2026-05-21)
**Cross-referenced (read at audit-write per BC#14)**:
- `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (post-C22 remediation #252)
- `web4-standard/core-spec/web4-society-authority-law.md` (post-C16 + C23 remediations)
- `web4-standard/core-spec/LCT-linked-context-token.md` (post-C24 remediation #256)
- `web4-standard/core-spec/mcp-protocol.md` (v0.1.3 amendment §1.1 + §7.3-7.7 WIP)
- `web4-standard/implementation/sdk/web4/role.py` (BASE_MANDATORY_ROLES + validate_minimum_viable)

**Prior audit**: `docs/audits/inter-society-protocol-internal-consistency-2026-05-21.md` (C6) — 13 findings; PR #215 (`4ff9669d`) resolved 12, deferred 1 (L2 informational).

---

## Summary

| Severity | NEW (C25) | C6-Carried |
|----------|----------:|-----------:|
| HIGH     | 1 | 0 |
| MEDIUM   | 2 | 0 |
| LOW      | 1 | 1 (DEFERRED, expected) |
| INFO     | 2 | 0 |
| **Total NEW** | **6** | **1 deferred** |

**3-bucket classification of NEW findings** (per C24 pattern):

| Bucket | IDs | Count |
|--------|-----|------:|
| Autonomous-actionable | M2, INFO1, INFO2 | 3 |
| Design-Q | H1, M1, L1 | 3 |
| SDK cross-track | (none) | 0 |

**Anti-padding note**: This is a delta RE-audit on a 375-line spec that has NOT been modified since its prior C6 remediation. NEW findings emerge from drift against upstream changes in *other* specs (SOCIETY_SPEC C22, SAL C16/C23, LCT C24, mcp-protocol v0.1.3 amendment), not from new edits in ISP itself. Six honest findings; not envelope-matched to C24 (6) — coincidence, not target.

**C24 zero-carry precedent context**: C24 was a clean RE-audit because the LCT spec had been substantively re-edited between C9 and C24. ISP has NOT been re-edited between C6 and C25; the NEW findings here are drift-from-others, not internal regression. Both shapes are valid; the pattern difference is worth noting in the cross-cutting observations.

---

## §A: C6-Carried Verification Block

Explicit enumeration of all 13 C6 findings with current status (RESOLVED / STILL-OPEN / REGRESSED / DEFERRED-CARRY). Per the discipline established by C24 RE-audit (zero-carry result evidenced by enumeration), every prior finding is checked at this audit's write-time.

| C6 ID | Severity | Title | Current Status | Evidence at audit-write |
|-------|----------|-------|----------------|-------------------------|
| H1 | HIGH | Duplicate §4 subsection numbering | **RESOLVED** | §4 currently consecutively numbered §4.1–§4.7 (L183, L195, L212, L223, L229, L237, L250) |
| H2 | HIGH | Header version stale (v0.1.0 vs v0.1.2) | **RESOLVED** | Header L3: `Status: Core Specification v0.1.2 (DRAFT)` |
| H3 | HIGH | §8 table omits `mcp-protocol.md` | **RESOLVED** | §8 L359 has mcp-protocol.md row |
| M1 | MEDIUM | §2.1 wrong internal cross-references | **RESOLVED** | L72 `per §7` (Ledger Anchoring ✓) and L75 `see §6 on minimum viable society` (✓) |
| M2 | MEDIUM | §9 RESOLVED items lack version disambiguation | **RESOLVED-WITH-CAVEAT** | §9 L366/368 now read `mcp-protocol.md v0.1.3 / v0.1.4` (document name disambiguated per C6-rem). **Caveat**: the version tags themselves are now stale — see NEW INFO1 below. The C6 remediation was correctly applied; the staleness is a *new* drift surface from mcp-protocol's lack of a version field. |
| M3 | MEDIUM | §8 table omits `society-roles.md` | **RESOLVED** | §8 L360 has society-roles.md row |
| M4 | MEDIUM | "≥3 birth witnesses" vague attribution | **RESOLVED** | §2.1 footnote L83 cites `LCT-linked-context-token.md` for the ≥3 witness requirement |
| M5 | MEDIUM | `AttestationEnvelope` dangling reference | **RESOLVED** | §4.6 L246 cites `schemas/attestation-envelope.schema.json` and SDK `web4/attestation.py` |
| L1 | LOW | §1.3 Eurozone exit analogy misleading | **RESOLVED** | §1.3 L42 now reads "(members chose to join EUR; can theoretically exit, though no member has yet done so — the right exists but is untested)" |
| L2 | LOW | §4.1 "Gesellian economic experiment" niche | **DEFERRED-CARRY** | §4.1 L191 still mentions Gesellian framing. Per C6 audit L277 deferral rationale (informational, technically accurate, no action needed), this is expected and remains acceptable. No NEW recommendation; L2 stays carried as informational. |
| L3 | LOW | Cross-spec gap — Diplomat role reference | **RESOLVED** | §2.2 step 1 L90-91 cites `the Diplomat role per society-roles.md` |
| L4 | LOW | §2.2 "birth certificates" undefined terminology | **RESOLVED** | §2.2 step 3 L105 now says `D SHALL mint constituent-society LCTs for A, B, [C, ...]` |
| L5 | LOW | §3.2 Option 1 ANCHORED capitalization | **RESOLVED** | §3.2 Option 1 L142 now uses RFC 2119 SHALL framing: `Exchange transactions SHALL be witnessed by both societies and anchored in both ledgers.` |

**§A result**: 12/12 C6 substantive remediations hold cleanly. L2 deferred-carry persists as expected (technically accurate, no action). **Zero C6 regression**. All NEW findings (below) are drift-from-upstream, not internal regression.

---

## NEW C25 Findings

### HIGH Findings

#### H1: ISP §6.2 ⊥ SOCIETY_SPEC §1.2.5 ⊥ SDK `BASE_MANDATORY_ROLES` — three-way drift on canonical 7-role enumeration

**Lines affected**: ISP L320-326 (§6.2 "Minimum Viable Semantic Society"), cross-spec SOCIETY_SPECIFICATION.md L60 (§1.2.5), SDK `role.py` L118-126 (`BASE_MANDATORY_ROLES`) + L341-392 (`validate_minimum_viable`).

**Drift surface**: SOCIETY_SPEC §1.2.5 (added by C22-H1 remediation in PR #252) states:

> "`inter-society-protocol.md` §6.2 (referenced by the SDK's `validate_minimum_viable`) enumerates **seven base-mandatory roles** — Sovereign, Law Oracle, Policy Entity, Treasurer, Administrator, Archivist, and Citizen"

**The actual ISP §6.2** (this spec, L320-326) enumerates THREE semantic criteria, not seven roles:

1. Internal differentiation
2. Witnessing capacity
3. Reified resource grounded externally

There is **no 7-role enumeration anywhere in ISP §6.2** (or anywhere else in ISP). The 7-role list lives only in the SDK at `role.py:118-126` (`BASE_MANDATORY_ROLES`), and is correctly referenced by SOCIETY_SPEC §1.2.5 by *name* but incorrectly *attributed* to ISP §6.2.

**The SDK docstring** (`role.py` L348-352) correctly cites ISP §6.2 for the 3 *semantic* criteria:

> "Per `inter-society-protocol.md` §6.2, a society is semantically viable when it has internal differentiation, witnessing capacity, and externally-grounded ATP reification. This function checks the role-structural requirements (items 1 and 2 from §6.2); ATP reification (item 3) is outside the role module's scope."

The SDK then ALSO enforces 7 base-mandatory roles via `BASE_MANDATORY_ROLES` — a *separate* SDK-side enrichment not derived from ISP §6.2.

**Three-way mismatch**:

| Source | Claim about 7 base-mandatory roles |
|--------|------------------------------------|
| SOCIETY_SPEC §1.2.5 | "ISP §6.2 enumerates the 7 roles" |
| ISP §6.2 (actual) | Silent on roles; enumerates 3 semantic criteria |
| SDK `BASE_MANDATORY_ROLES` | Lists the 7 roles (Sovereign, Law Oracle, Policy Entity, Treasurer, Administrator, Archivist, Citizen) |
| SDK docstring | Cites ISP §6.2 for the 3 semantic criteria only |

**Why this is a HIGH**: The bidirectional cross-reference established by C22-H1 remediation is structurally broken. A reader following SOCIETY_SPEC §1.2.5 → ISP §6.2 will find no 7-role list. The SDK is the de facto canonical source; neither spec acknowledges this.

**Classification: design-Q.** The autonomous fix is NOT obvious because the architectural decision of *where the canonical 7-role list lives* is not yet made. Three remediation paths:

- **Option A**: Add a new §6.4 (or amend §6.2) in ISP enumerating the 7 base-mandatory roles, making SOCIETY_SPEC §1.2.5's claim true. ISP becomes the spec-side anchor; SDK derives from ISP.
- **Option B**: Update SOCIETY_SPEC §1.2.5 to cite the SDK (and/or a new section in SOCIETY_SPEC itself) as the authoritative source, removing the false claim about ISP §6.2.
- **Option C**: Add a §6.4 to ISP that references SDK `BASE_MANDATORY_ROLES` as the canonical source (SDK becomes the spec-side anchor through ISP's pointer).

**Recommendation**: Defer to operator. The structural choice (where the 7-role list is normatively defined) is foundational and should not be made autonomously by remediation.

**Auditor-blindspot-pattern application**: This finding was surfaced by the primitive-clustered third pass on primitive (e) — 7-role enumeration. The linear walkthrough of ISP would not have found it (§6.2 reads coherent on its own); the cross-reference check (pass 2) might have caught the inbound reference from SOCIETY_SPEC §1.2.5, but only the primitive-clustered third pass (verifying ISP/SOCIETY_SPEC/SDK alignment on the *same* primitive simultaneously) revealed the three-way drift cleanly. **First live application of the pattern; pattern validated**.

---

### MEDIUM Findings

#### M1: ISP §3.2 Option 1 omits referent-grounded model — drift from mcp-protocol §7.7.1 (Normative)

**Lines affected**: ISP L133-144 (§3.2 Option 1 "Retain + Exchange"), cross-spec mcp-protocol.md §7.7.1 L525-534.

**Drift surface**: ISP §3.2 Option 1 enumerates exchange-rate forms as:

```
The exchange rate MAY be:
  - Fixed (renegotiated periodically)
  - Market-derived (continuous price discovery via repeated exchanges)
  - Pegged (one anchors to the other's policy)
```

mcp-protocol §7.7.1 (Normative status per §7.7 conformance map L515) declares:

> "A common reading of 'exchange rate' imports the foreign-exchange market mental model: two societies maintain a floating bilateral rate `ATP_A : ATP_B` independent of any particular transaction. **This is NOT the Web4 model.** In Web4, exchange rates are **grounded in the substance of the R6/R7 action being performed**."

ISP §3.2 Option 1's enumeration ("Fixed / Market-derived / Pegged") is about *time-stability* of the rate (a HOW-axis). mcp-protocol §7.7.1 referent-grounding is about *what the rate is grounded against* (a WHAT-axis). The two axes are orthogonal — a referent-grounded rate can be fixed, market-derived, or pegged. **But ISP §3.2 Option 1's text does not tell the reader that the WHAT is referent-grounded per the canonical Web4 model.**

ISP §9 line 368 acknowledges referent-grounding in the future-work-RESOLVED block, but this resolution sits OUTSIDE the actual protocol text in §3.2 Option 1 where exchange-rate semantics are defined. A reader following §3.2 Option 1 to learn what an exchange rate is in Web4 will not encounter the referent-grounded model.

**Why this is MEDIUM, not HIGH**: The §9 resolution-block does carry the correct conceptual update, so a careful reader following all of §3 → §9 will arrive at the right framing. But the protocol text in §3.2 Option 1 itself leaves the impression that abstract floating bilateral rates are within scope, which mcp-protocol §7.7.1 (Normative) explicitly rejects.

**Classification: design-Q.** The fix is not purely autonomous because §7.7 is WIP v0.1.0-draft (memory note: "do not depend on wire format"). Adding referent-grounded language to ISP §3.2 Option 1 BEFORE §7.7 stabilizes risks coupling ISP to a wire format that may evolve. Two paths:

- **Option A** (preferred for cross-spec coherence): Add a paragraph or note to ISP §3.2 Option 1 stating that the *substance* of any exchange rate in Web4 is referent-grounded per mcp-protocol §7.7.1 (the *normative* sub-section, not the wire format sub-sections), while the Option 1 enumeration governs *rate stability over time*.
- **Option B**: Defer this finding until mcp-protocol §7.7 reaches v0.1.0-final, then update ISP §3.2 Option 1 to fully reference §7.7.
- **Option C**: Update ISP §3.2 Option 1 with an inline forward-pointer marker (e.g., "see also §9 and `mcp-protocol.md` §7.7.1 for the referent-grounded substance model") — minimally invasive, doesn't depend on §7.7 wire stability.

**Recommendation**: Option C as autonomous-actionable interim; Option A as the longer-term target after §7.7 stabilizes.

**Auditor-blindspot-pattern application**: Found via primitive (b) exchange-rate negotiation pass. Linear walkthrough of ISP §3.2 alone reads consistent; only cross-spec verification against mcp-protocol §7.7.1's normative declaration exposes the gap.

---

#### M2: ISP §8 Relationship table omits `web4-society-authority-law.md` (SAL); ISP §2/§5 lack SAL cross-references

**Lines affected**: ISP §8 L350-360 (Relationship table), ISP §2 (genesis, L54-114), ISP §5.1 (secession, L268-287).

**Drift surface**: ISP §8 Relationship table currently lists 9 specs: LCT, SOCIETY_SPECIFICATION, atp-adp-cycle, mrh-tensors, t3-v3-tensors, r6-framework, r7-framework, mcp-protocol, society-roles. It does NOT list `web4-society-authority-law.md` (SAL), even though:

1. **ISP §2 (genesis)** discusses charter publication (§2.1 step 3), citizenship admission criteria (§2.1 step 3 + step 6), and birth witnesses (§2.1 step 5). SAL §2 ("Genesis: Birth Certificate and Citizen Role") defines all of these authoritatively — with the canonical JSON-LD Birth Certificate shape (SAL §2.2) and the immutable-record requirements (SAL §3.4).
2. **ISP §2.2 step 4** says "constituent societies retain authority over their own citizens" — this directly maps to SAL §3.1 (Society Topology) `web4:memberOf` edges and SAL §3.5 (Societies as Citizens, Fractal Membership).
3. **ISP §5.1 step 1** says "A SHALL announce intent-to-secede to D, with reason recorded in A's ledger" — but the "ledger" is unspecified relative to SAL §3.4 Immutable Record (`sal.event` topics including `sal.role.bind` which would govern citizenship change). After C16+C23 SAL remediations, the IR is the canonical place for SAL-relevant updates.
4. **ISP §8 SOCIETY_SPECIFICATION row** says "extends with genesis, first-contact, secession" — but the C22-H1 remediation added a *bidirectional* dependency (SOCIETY_SPEC §1.2.5 now references ISP §6.2 and vice-versa is needed per H1 above). The §8 entry doesn't reflect the post-C22 bidirectionality.

**Why this is MEDIUM**: ISP is functionally coherent without these cross-refs (a reader can navigate spec-by-spec), but the §8 table is the formal "where to look next" register. Omitting SAL after the C16+C23 remediations made SAL the canonical citizenship/birth/IR spec is a real navigation gap.

**Classification: autonomous-actionable.** Concrete edits:
- Add SAL row to §8 table with description (e.g., "Defines genesis Citizen role, Birth Certificate canonical shape, fractal Society Topology, and Immutable Record service — all referenced implicitly by ISP §2 genesis and ISP §5 secession lifecycle.")
- Optionally update ISP §2.1 step 3-5 and ISP §5.1 step 1 with inline SAL cross-refs.
- Optionally update ISP §8 SOCIETY_SPECIFICATION row to acknowledge the C22-H1 bidirectional dependency.

---

### LOW Findings

#### L1: ISP doesn't define `established` / `federated` as state names referenced by mcp-protocol §7.4

**Lines affected**: ISP §3 (entire first-contact protocol), cross-spec mcp-protocol.md §7.4 L417 (`interaction_type` field), L443 (cross-spec citation).

**Drift surface**: mcp-protocol §7.4 (Cross-Society LCT Envelope) defines an `interaction_type` field with enum values:

```
"interaction_type": "first_contact | established | federated"
```

And L443 says: `first_contact (per inter-society-protocol.md §3.1) requires additional discovery exchange before R7 can complete; established and federated proceed normally`.

But ISP §3 does NOT define `established` or `federated` as state names:
- ISP §3 uses "first-contact protocol" generically (§3 heading and §3.1, §3.3).
- ISP §3.2 enumerates 3 sovereign Options: Option 1 (Retain + Exchange), Option 2 (Adoption), Option 3 (Federation with Shared Currency).
- "established" is not used in ISP as a state-name.
- "federated" likely maps to Option 3, but the mapping is implicit.

mcp-protocol §7.4 imports ISP terminology incorrectly: `first_contact` is correct (matches ISP §3.1), but `established` and `federated` are mcp-protocol-private states that are not anchored in ISP.

**Why this is LOW**: The implicit mapping is recoverable (`established` ≈ post-first-contact bilateral relationship under Option 1 or 2; `federated` ≈ Option 3). No wire-format consequence in practice. But it's a cross-spec terminology gap — mcp-protocol §7.4 reads as if it's citing ISP for these state names, when ISP doesn't define them.

**Classification: design-Q** (small one). Fix options:
- **Option A**: Add a state-naming sub-section to ISP §3 enumerating the three post-discovery states (`first_contact` mid-discovery; `established` for Option 1/2 bilateral; `federated` for Option 3), giving mcp-protocol §7.4 a real anchor.
- **Option B**: Update mcp-protocol §7.4 to drop the cross-ref to ISP for these state names (treat them as mcp-protocol-private).
- **Option C**: Defer until either spec needs a state-machine formalism.

**Recommendation**: Defer to operator; this is the smallest of the surfaced design-Qs and least urgent.

**Auditor-blindspot-pattern application**: Found via primitive (a) cross-society R6/R7 envelope shape pass — verifying mcp-protocol §7.4 imports against ISP §3 terminology revealed the gap. Linear walkthrough of either spec alone reads consistent.

---

### INFO Findings

#### INFO1: ISP §9 references `mcp-protocol.md v0.1.3` / `v0.1.4` but mcp-protocol has no version field

**Lines affected**: ISP §9 L366 ("RESOLVED — `mcp-protocol.md` v0.1.3 (2026-05-14)"), L367 ("RESOLVED — `mcp-protocol.md` v0.1.3 (2026-05-14)"), L368 ("RESOLVED — `mcp-protocol.md` v0.1.4 (2026-05-14, WIP)").

**Drift surface**: mcp-protocol.md does not carry a top-level version header. The only version-tagged content is `§7.7` with its own status banner ("STATUS: WIP v0.1.0-draft, 2026-05-14"). So:

- `v0.1.3` (referring to the §7.3-7.6 amendments per memory) has no anchor in the source document.
- `v0.1.4` (referring to §7.7) is also not present; §7.7's own status is `WIP v0.1.0-draft`.

These version tags were valid at C6 audit-write time as commit-history descriptions but have become stale provenance markers. Per BC#13, date/version staleness alone is INFO unless coupled with normative date-dependency. No normative dependency here — the *section references* (`§7.3`, `§7.4`, `§7.5`, `§7.6`, `§7.7`) all remain valid; only the version-tag descriptors are stale.

**Classification: autonomous-actionable.** Either strip the version tags (`mcp-protocol.md §7.3` instead of `mcp-protocol.md v0.1.3 §7.3`) or update to the actual status banner (`mcp-protocol.md §7.7 (WIP v0.1.0-draft, 2026-05-14)`).

---

#### INFO2: ISP header date `2026-05-13` lags actual last edit `2026-05-21` (PR #215, C6 remediation)

**Lines affected**: ISP L4 (`Date: 2026-05-13`).

**Drift surface**: PR #215 (`4ff9669d`, 2026-05-21) substantively edited ISP (C6 remediation: §4 renumbering, §8 table additions, §2.1 footnote, etc.) but did not bump the header date. Result: header date lags last substantive edit by 8 days.

Per BC#15 (date-bump discipline established in C22 cycle, exit #136), dates should bump on substantive edits — but BC#15 was established AFTER PR #215, so this is not a regression of BC#15; it's pre-existing staleness that BC#15 would now catch.

**Classification: autonomous-actionable.** Bump header date to `2026-05-21` (matching last substantive edit) at the next remediation. Note: this audit is read-only; the date bump belongs in the C25 remediation cycle, not this session.

Per BC#13, this is INFO not LOW since the date is descriptive provenance, not a normative time-dependency.

---

## Primitive-Clustered Third Pass — Methodology + Results

**Pattern**: `auditor-blindspot-pattern` (established in exit #138 / C24 RE-audit, surfaced when linear-walkthrough auditors detected single-section anomalies more easily than cross-section contradictions).

**Application**: After the linear walkthrough (pass 1, surfacing zero new internal findings beyond confirming C6 status) and cross-reference check (pass 2, surfacing M2 SAL gap from §8 table review), apply a third pass that clusters by *primitive being normatively defined* and verifies ALL sites that touch that primitive across the spec corpus + SDK + vectors simultaneously.

**Five primitives clustered**:

| Primitive | Hypothesis at pass start | Result | Finding |
|-----------|---------------------------|--------|---------|
| (a) Cross-society R6/R7 envelope shape | ISP §9 cross-ref to mcp §7.3-7.6 may be stale | mcp-protocol §7.4 uses state-names not defined in ISP | L1 surfaced |
| (b) Exchange-rate negotiation | ISP §3.2 Option 1 enumeration may not reflect §7.7 referent-grounding | Confirmed: §3.2 Option 1 doesn't cross-ref §7.7.1 referent-grounded model | M1 surfaced |
| (c) Witness chain across society boundaries | ISP §2.1 step 5 may drift from LCT §3.3 post-C24 binding_proof shape | Different abstraction levels (protocol vs wire) — no conflict | No finding |
| (d) Genesis/first-contact/federation/secession lifecycle | ISP §2/§3/§5 should map cleanly to SOCIETY_SPEC §1.2 + SAL §3.1/§3.4 | SAL §3.4 Immutable Record not referenced from ISP §5.1 secession; §8 omits SAL | Bundled into M2 |
| (e) 7-role enumeration §6.2 | C22-H1 anchor claim should hold | **MAJOR DRIFT**: SOCIETY_SPEC §1.2.5 claims ISP §6.2 enumerates 7 roles; actual §6.2 has 3 semantic criteria | H1 surfaced |

**Pattern result**: The primitive-clustered pass surfaced **all 4 substantive NEW findings** (1H + 2M + 1L). The linear walkthrough alone would have surfaced none (because the spec is internally coherent and was already remediated under C6). The cross-reference pass alone would have caught at most M2 (SAL gap from §8 table). Without the primitive-clustered third pass, the H1 7-role drift would have been missed — exactly the failure mode the auditor-blindspot-pattern predicts.

**First live application validates the pattern.** Recommend continued use in C26+ RE-audits where the source spec has had upstream churn without internal edits.

---

## Cross-Cutting Observations

### Observation 1: ISP is structurally clean post-C6; all NEW findings are drift-from-others
The spec text itself has not regressed since the C6 remediation. The H1+M1+M2+L1 NEW findings each arise from changes in *other* specs (SOCIETY_SPEC C22-H1, mcp-protocol v0.1.3 amendment, SAL C16+C23 remediations) whose authors did not update ISP in lockstep. This is the expected shape of a delta RE-audit on a stable spec — the audit is mostly an "is the rest of the corpus still consistent with this spec" check.

### Observation 2: ISP/SAL/LCT triangle closure — partial
Memory framed the C25 audit as "closing the ISP/SAL/LCT consistency triangle". Result:
- **ISP ↔ LCT**: clean (LCT §3.3 binding_proof is at a different abstraction level; no conflict; M5 C6-rem citation still valid).
- **ISP ↔ SAL**: **GAP** — §8 table omits SAL, §2/§5 lack cross-refs. The triangle's third side is the weakest. (M2 captures this.)
- **ISP ↔ SOCIETY_SPEC** (via SAL bridge): **BROKEN** — H1's three-way drift on §6.2 is the most severe finding in this audit.

The "triangle" framing was apt; the audit revealed that the triangle is incomplete on the ISP↔SAL edge.

### Observation 3: §7.7 WIP framing trap (per policy-review sharpening #2) — handled
The C25 audit deliberately distinguished references to §7.7's *concept* (referent-grounded model in M1) from references to §7.7's *wire format* (which is v0.1.0-draft, do-not-depend). M1's recommendation (Option C, minimally invasive forward-pointer) explicitly avoids coupling ISP to §7.7's wire format. INFO1 also captures the WIP version-tag staleness without escalating to LOW. No "depends-on-WIP" finding surfaced because ISP §3.2 doesn't actually import §7.7's wire fields — it would just benefit from the concept-level pointer.

### Observation 4: Anti-padding posture maintained
6 NEW findings vs C24's 6, C23's 7, C22's 8, C21's 16, C20's 13, C19's 13, C18's 11, C17's 10. ISP's smaller surface (375L vs C20's 700L vs C19's 1007L) and structural stability since C6 explain the smaller honest count. No INFO/LOW manufactured to inflate the envelope; one C6-deferred carry (L2) is left as-is per its original deferral rationale.

### Observation 5: Subordinate-ontology cluster — NOT extended by this audit
This audit did NOT touch the recurring sub-ontology / ontology-zero cluster (which stood at 7 audits as of #139). ISP is not a primary anchor for that cluster (T3/V3 sub-dimensions and TTL ontology references appear in other specs). The cluster remains at 7; no new contribution.

### Observation 6: Snake/camel cluster — NOT extended by this audit
ISP's identifiers (`atp_settlement`, `genesis_block_hash`, `lct_id`, `interaction_type`, etc.) appear consistent in snake_case throughout. No drift surfaced. Cluster remains at 4.

---

## Remediation Classification (3-bucket split per C24 pattern)

For the next-session C25 remediation cycle:

### Autonomous-actionable (3 findings — direct remediation)
- **M2**: Add SAL row to ISP §8 table + add cross-refs in §2 (genesis) and §5.1 (secession) to SAL §2/§3.1/§3.4. Optionally update §8 SOCIETY_SPECIFICATION row to acknowledge post-C22 bidirectional dependency.
- **INFO1**: Strip stale version tags (`v0.1.3` / `v0.1.4`) from §9 L366-368; either remove version-tag descriptors or replace with current `§7.7 (WIP v0.1.0-draft, 2026-05-14)` form.
- **INFO2**: Bump header date L4 to `2026-05-21` (matching last substantive edit per BC#15). Apply BC#15 discipline going forward.

### Design-Q (3 findings — operator engagement)
- **H1**: Where does the canonical 7-role list live? (Option A: ISP §6.4 new section / Option B: SOCIETY_SPEC §1.2.5 corrected to cite SDK / Option C: ISP §6.4 references SDK.) Architectural decision; not safe to remediate autonomously.
- **M1**: How to acknowledge §7.7.1 referent-grounded model in ISP §3.2 without depending on §7.7 wire format. (Option A: full paragraph after §7.7 stabilizes / Option B: defer until §7.7 v0.1.0-final / Option C: minimal forward-pointer now.) Recommend Option C as autonomous interim, but ultimate framing is a design-Q.
- **L1**: Should `established` / `federated` be ISP-defined state names (Option A) or mcp-protocol-private (Option B)? Smallest of the design-Qs; least urgent.

### SDK cross-track (0 findings)
None. The SDK's `BASE_MANDATORY_ROLES` and `validate_minimum_viable` are *correctly implemented* (the SDK docstring cites ISP §6.2 for the 3 semantic criteria it actually contains; the 7-role enforcement is an independent SDK-side enrichment). The drift in H1 is between *two specs* (SOCIETY_SPEC and ISP); the SDK is the bystander, not the drifting party. No SDK-side action required for any C25 finding.

---

## C25 Audit Provenance

- **Audit-write methodology**: Three-pass — (1) linear walkthrough end-to-end, (2) cross-reference check (every §-reference verified against target spec at audit-write time, BC#14), (3) primitive-clustered third pass on 5 ISP-specific primitives (auditor-blindspot-pattern).
- **Source files read at audit-write**: ISP (full 375L), SOCIETY_SPECIFICATION.md §1.2.5 region, SAL §3.1/§3.4 region, LCT §3 region, mcp-protocol.md §1.1/§7.3-7.7 regions, SDK `role.py` (full file).
- **BCs applied**: BC#5 (corpus sweep — verified all SOCIETY_SPEC §1.2.5 / SDK / ISP §6.2 sites at audit-write), BC#12 (count verification — confirmed SDK BASE_MANDATORY_ROLES = 7 items vs SOCIETY_SPEC §1.2.5 "seven" claim), BC#13 (date-staleness as INFO not LOW), BC#14 (SDK behavioral verification at audit-write — confirmed `validate_minimum_viable` semantics by reading the function), BC#15 (date-bump discipline applied as audit-side check, not spec-side touch).
- **First live application of**: `auditor-blindspot-pattern` (#138 → C25, primitive-clustered third pass surfaced H1 + L1 + M1).
- **Streak posture**: First audit post-#138 streak reset. No streak pressure. Findings are what the spec deserves.

---

**Audit date**: 2026-05-31
**Source spec date**: 2026-05-13 (header L4; pre-existing 8-day lag captured as INFO2)
**Auditor**: Legion autonomous session, exit #140, slot `180057`, LEAD voice
