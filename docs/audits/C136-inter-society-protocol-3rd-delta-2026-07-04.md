# C136: `inter-society-protocol.md` (ISP) 3rd-delta RE-Audit

**Date**: 2026-07-04
**Track**: web4 (Legion autonomous session, slot `120036`)
**Instrument**: C-series delta RE-audit; **3rd delta** on `inter-society-protocol.md` (lineage C6 → C25 → **C62** → remediation **C63** (#341) → **C102** → **C136**)
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2 DRAFT, 384 lines, last edited `0405f331` PR #341, 2026-06-16 — **BYTE-FROZEN 18 days**; unchanged since the C102 snapshot)
**Method**: §A prior-finding token-by-token verification (held-by-construction on a byte-frozen target) + `&#` artifact sweep + bidirectional carry re-verification; §B **frozen-target corpus-delta surface** — ISP byte-identical to C63/C102, so §B yield is confined to the cited siblings that MOVED since the C102 snapshot (2026-06-25), each tested for disjointness at **cited-hunk granularity** with the snapshot-presence guard, and adversarially verified (refute-by-default) by two independent finders.

**Slot note (rotation):** this fire was the nominal **C136 LCT remediation** slot, but C135 found LCT fully-clean (0 net-new) → LCT remediation is a **no-op** → per the established no-op→advance pattern (7th instance; precedents C103/C131/C133/C134/C135) the round-robin advanced to the next rotation file, **ISP** (last audited C102).

**Cross-referenced (read live at audit-write)**:
- `web4-standard/core-spec/mcp-protocol.md` (post-C117 #422 `afab0c43`) — bears on B1, B2, B3
- `web4-standard/core-spec/atp-adp-cycle.md` (post-C119 #420 `e99b419e`) — bears on B5, B10, B11
- `web4-standard/core-spec/web4-society-authority-law.md` (SAL, **frozen since C59**, no movement) — bears on B13
- `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (**frozen**, no movement) — bears on B9
- `web4-standard/core-spec/society-roles.md` (**frozen**, no movement) — bears on B12, B16
- `web4-standard/core-spec/LCT-linked-context-token.md` (**frozen since C61**, no movement) — bears on B6
- `web4-standard/implementation/sdk/web4/role.py` (**frozen since C62**, no movement) — bears on B12

**Prior audits**: C6 (13 findings → #215), C25 (6 NEW → #258), **C62** (16 distinct → remediation #341 applied 9 autonomous + B2-interim), **C102** (2nd-delta, 0 net-new — first ISP clean delta).

---

## Summary

| Severity | NEW (C136) |
|----------|-----------:|
| HIGH     | 0 |
| MEDIUM   | 0 |
| LOW      | 0 |
| INFO     | 0 |
| **Total NEW distinct** | **0** |

**Result**: **POSITIVE FROZEN-TARGET.** ISP is byte-identical to its C63 remediation (`0405f331`, 18 days) and unchanged since the C102 snapshot. All 10 C63 remediations HELD by byte-freeze (nothing written → strongest possible hold); 0 regressions; 0 `&#` artifacts. §B over the two moved siblings (mcp-C117, atp-adp-C119) yields **0 net-new autonomous ISP defects** — both moved hunks are DISJOINT from ISP's cited surface at cited-hunk granularity, and the atp-adp delta additionally **corroborates** ISP's unit-of-account framing. This is **ISP's 2nd CONSECUTIVE fully-clean delta (C102 + C136)**. **C137 ISP remediation slot = NO-OP.**

**Headline (disjointness family — third shape reconfirmed):** both moved siblings changed a **normative-summary MUST-list item** the target does not cite. C117 → mcp **§12 MUST #6** (witnessing scope); C119 → atp-adp **§7.1 MUST #6** (T3/V3 value-tracking scope). ISP cites *neither* §12 nor §7.1 (grep-confirmed zero citations); its cited surface into both siblings (mcp §7.3–§7.7.x body; atp-adp §2.1–§2.2 + form/substance) was untouched. This is the C135 pattern (a moved sibling changed a ROW/hunk the target doesn't cite) applied twice over — diff at the cited-HUNK granularity, not the file, before calling a moved carry-sibling clean.

**Corroboration enrichment (C119 → ISP):** ISP's §4 frames inter-society ATP as a **unit of account decoupled from value tensors** (L191 "ATP is a unit of account, not a medium of exchange"); every ISP T3/V3 mention (L83/130/365/376) is a **trust** tensor (society-society trust / R7-Reputation projection), never a **value** tensor. C119's new §7.1 carve-out ("society-level aggregates MAY use non-tensor rollup accounting … not a T3/V3 dimension") is therefore *consistent with — indeed reinforces —* ISP's stance. Extends the C102 cross-cutting observation that sibling deltas corroborate resolved/standing findings as often as they stale them.

---

## §A: Prior-Finding Verification Block

ISP `git diff 0405f331 HEAD` = **empty** (byte-identical). On a byte-frozen target the C63 remediations are held *by construction* — nothing was written that could regress. Each is re-confirmed present at its current line per the C56 completeness method (verified against the C102 §A.1 table, which itself token-verified all 10 against the canonical C62 fix text):

| C62 ID | Sev | C63 fix | Current line | Status |
|--------|-----|---------|--------------|--------|
| **B4** | MED | §2.2 step 4 `SHALL`→`MAY` | L108 | **HELD (byte-freeze)** |
| **B5** | MED | §4.5 "mint ATP"→"mint ADP and charge it to ATP" + cite §2.1–§2.2 | L237/239 | **HELD** |
| **B3** | LOW | §8/§9 §7.7 architecture-Normative phrasing | L368/377 | **HELD** |
| **B6** | LOW | §2.1 ≥3-witness placement | L75 | **HELD** |
| **B7** | LOW | §4.6 schema path fix | L252 | **HELD** |
| **B8** | LOW | §8 `web4:memberOf` cite §3.3/§3.5 | L362 | **HELD** |
| **B9** | LOW | §2.2 SOCIETY_SPEC §4.2.1 formation-event cross-ref | L115 | **HELD** |
| **B14** | LOW | §1.3 demote Eurozone analogy to last | L42-45 | **HELD** |
| **B16** | LOW | §8 society-roles bidirectional dependency | L369 | **HELD** |
| **B2-interim** | (½ B2) | §3.2 forward-pointer to mcp §7.7.1 | L150 | **HELD** |

**10/10 HELD, 0 regressed. `&#` artifact sweep on ISP: CLEAN (0 hits).**

### A.2 — Regression / provenance sweep
No remediation touched ISP since C63 (`git log` on the file shows `0405f331` as HEAD-for-this-file). No sister-file edit introduced an ISP change. Nothing to regress.

### A.3 — Carry re-verification (bidirectional)
| ID | Status at C136 | Evidence |
|----|----------------|----------|
| C25-H1 (7-role drift) | **RESOLVED downstream (C51), re-confirmed** | §8 SAL/society-roles rows attribute roles correctly; no residue. |
| C6-L2 (Gesellian framing) | **deferred-carry persists (expected)** | ISP L197 informational, technically accurate. |

---

## §B: Corpus-Delta Surface (frozen target → moved siblings)

Of ISP's seven cited siblings, exactly **two** moved since the C102 snapshot (2026-06-25); the other five (SAL, SOCIETY_SPEC, society-roles, LCT, role.py) are frozen → their carries stand verbatim. Each moved sibling's changed hunk is tested against ISP's actual cited surface (grep-enumerated) at cited-hunk granularity, then adversarially verified refute-by-default.

### B.1 — mcp-protocol.md moved (C117 #422 `afab0c43`): bears on C62-B1, B2, B3

C117 applied C116-N1: a **single line** in mcp **§12 MUST #6** — relocated "for high-consequence actions," to scope the whole of item #6 (so both clause (a)←§7.5 and clause (b)←§7.3 inherit the high-consequence scope), closing a C77 remediation-introduced over-tightening. mcp §7.3 / §7.5 **body text unchanged** (per the commit's own C56 note).

**ISP's cited surface into mcp** (grep `mcp-protocol` on ISP): §7.7.1 (L150), §7.3–§7.6 (L368/375-377), §7.7.1/§7.7.4 (L368/377). **ISP does NOT cite mcp §12** (grep `§12` on ISP = 0 hits).

- **C62-B1 (design-Q) — STANDS.** mcp §7.3/§7.4 `established`/`federated` enum unchanged by C117; ISP §3 still defines no such relationship state. Route to operator/cross-track memo.
- **C62-B2-full (design-Q) — STANDS.** mcp §7.7.1 referent-grounded invariant unchanged; ISP §3.2/§4.4 abstract-rate language un-reframed. Operator-owned.
- **C62-B3 (RESOLVED) — cross-ref VERIFIED STABLE.** ISP §8 L368 / §9 L377 cite mcp §7.7.1/§7.7.4 as "architecture Normative"; those sections untouched by C117.

**Adversarial refutation (finder 1):** attempted to find an ISP claim of *unconditional* R7 witnessing that the new high-consequence-only §12 would contradict — **refuted**. ISP's own witnessing language (L146 "Exchange transactions SHALL be witnessed by both societies" — ISP's own scoped normative claim; L249 "Resource measurement SHOULD be witnessed"; §7.5 descriptive title cites at L375-376) carries **no all-actions scope claim** mirroring the OLD §12 phrasing. **mcp-C117 → 0 net-new ISP defects; changed hunk disjoint from ISP's cited surface.**

### B.2 — atp-adp-cycle.md moved (C119 #420 `e99b419e`): bears on C62-B5, B10, B11

C119 applied C118-N1: **two hunks** — (1) §4.2 `track_value_flow` reference-impl comment gained "— rollup accounting, outside §7.1 MUST #6 per its scope note"; (2) §7.1 **MUST #6** scoped "Value MUST be tracked through T3/V3" → "Entity-level value MUST be tracked … society-level aggregates MAY use non-tensor rollup accounting (§4.2)" + a new scope note. **MUST #4 ("Charging MUST require value proof") unchanged** (appears only as diff context). atp-adp §2.1/§2.2 (minting/charging) and §1/§5 (currency) **unchanged**.

**ISP's cited surface into atp-adp** (grep `atp-adp-cycle` on ISP): `Extends: … (ATP form)` (L6), form/substance framing (L30/187/363), minting/charging `§2.1–§2.2` (L239). **ISP does NOT cite atp-adp §7.1 or §4.2** (grep = 0 atp-adp-directed hits; the `§4.2` matches on ISP are ISP's *own* §4.2 and a `SOCIETY_SPECIFICATION.md §4.2.1` cite).

- **C62-B5 (RESOLVED) — cross-ref STABLE.** atp-adp §2.1/§2.2 minting/charging (which ISP §4.5 L239 cross-cites) untouched by C119. Reinforced.
- **C62-B10 (design-Q, two-sided) — STANDS.** Anchor = atp-adp §7.1 MUST **#4** "Charging MUST require value proof" (shown only as unchanged context in the C119 diff) + ISP §4.3 ATP-as-Commitment (frozen). Both anchors intact; still routes to operator.
- **C62-B11 (design-Q / cross-track) — STANDS.** Anchors = atp-adp §1 "native currency" / §5 "Currency Exchange" (untouched by C119) + ISP §4.1 unit-of-account (frozen). atp-adp owner + operator.

**Adversarial refutation (finder 2):** attempted to find an ISP claim that society-level/inter-society ATP value is tracked through T3/V3 (which the new carve-out would staleify) — **refuted, and inverted to corroboration.** ISP's §4 frames inter-society ATP as a unit of account *decoupled from* value tensors (L191); every ISP T3/V3 mention (L83/130/365/376) is a **trust** tensor, never **value**. The C119 carve-out is *consistent with / reinforces* ISP. No §4.2/§4.3 section-number aliasing between the docs (atp-adp's §4.2/§4.3 ≠ ISP's §4.2/§4.3). **atp-adp-C119 → 0 net-new ISP defects; both changed hunks disjoint; delta corroborates ISP.**

### B.3 — Frozen siblings (no movement → carries verbatim)
- **C62-B13 (SAL cross-track) — STANDS, live.** SAL frozen since C59; §2.2 birthcert example still <3 witnesses. Folds into the standing C58-B1 SAL bundle. No ISP-side action.
- **C62-B12 (SDK cross-track) — STANDS verbatim.** `role.py` `validate_minimum_viable` frozen since C62. SDK track.
- **C62-B9 / B16 / B6 targets stable.** SOCIETY_SPEC §4.2.1, society-roles.md, LCT-linked-context-token.md all frozen → cross-refs remain valid.
- **C62-B15 (design-Q) — STANDS.** D's settlement-policy-vs-exit tension; no sibling movement. Operator.

---

## §C: Standing Carries (status after C136 — unchanged from C102)

| ID | Class | Status |
|----|-------|--------|
| C62-B1 | design-Q (mcp `established`/`federated` undefined in ISP §3) | **OPEN, load-bearing** — operator/cross-track |
| C62-B2-full | design-Q (§3.2/§4.4 abstract-rate reframe) | **OPEN** — operator |
| C62-B10 | design-Q (charge-on-pledge vs value-proof) | **OPEN, TWO-SIDED** — operator (both ISP & atp-adp route it) |
| C62-B11 | design-Q / cross-track (currency vs unit-of-account) | **OPEN, partially acknowledged** — atp-adp owner + operator |
| C62-B15 | design-Q (settlement policy could block exit) | **OPEN** — operator |
| C62-B12 | cross-track SDK (`validate_minimum_viable`) | **OPEN, verbatim** — SDK track |
| C62-B13 | cross-track SAL (§2.2 example <3 witnesses) | **OPEN, live** — folds to C58-B1 SAL bundle |
| C6-L2 | deferred-carry (Gesellian framing) | persists, informational |

None gate a normal AUDIT turn. Surface as ONE decision memo when the operator is available. **No carry changed status since C102** (both moving siblings changed hunks disjoint from every carry anchor).

---

## Cross-Cutting Observations

1. **Eighth consecutive frozen-target audit in the rotation era (C92/C94/C96/C98/C100/C102/… and now ISP-C136).** Files churn slower than audit cadence, so 3rd-delta wraps hit doubly-frozen targets; §A is held-by-construction; §B yield is *entirely* the corpus-delta surface (diff what MOVED, at cited-hunk granularity, with the snapshot-presence guard).
2. **The disjointness verdict this cycle is doubly instructive: BOTH moved siblings changed a normative-summary MUST-list item (mcp §12 #6, atp-adp §7.1 #6), and ISP cites neither summary section.** This is exactly the C120/C121 signal that the MUST-vs-reference-impl defect class lives in normative-summary sections — and a corollary for the delta auditor: when a sibling's *only* movement is a normative-summary MUST edit, the first check is whether the target cites that summary section at all. Here, twice, it does not.
3. **A moved sibling can CORROBORATE the target, not only stale/reinforce a prior finding.** C119's society-aggregate carve-out actively strengthens ISP's unit-of-account/decoupled-from-value-tensors framing. Extends the C102 observation (siblings corroborate as often as they stale) — the bidirectional carry re-check must look for corroboration as a first-class outcome.

---

## §D: Lessons → Memory

1. **When a cited sibling's ONLY delta is a normative-summary MUST-list edit, disjointness is decided by whether the target cites that summary section — check §12/§7.1-style summary citations first, before the body.** Both C117 (mcp §12) and C119 (atp-adp §7.1) were normative-summary MUST edits; ISP cites neither → both disjoint in one grep. (Extends [[feedback_cross_doc_carry_inbound]] and the C120 doc-specific-MUST lesson.)
2. **Corroboration is a first-class delta outcome.** C119's carve-out reinforces ISP's value-tensor stance. Record sibling→target corroboration alongside stale/reinforce, so the carry ledger reflects a *strengthened* invariant, not merely an unchanged one.

---

## Remediation Routing (for C137)

**C137 ISP remediation slot = NO-OP.** 0 autonomous-actionable findings (frozen target; 2nd consecutive clean ISP delta). All non-autonomous outcomes route off-target, unchanged from C102/C103:
- **Operator design-Q memo**: B1 (`established`/`federated` home), B2-full (rate reframe), B10 (two-sided charge-on-pledge vs value-proof), B11 (currency framing, atp-adp owner), B15 (settlement-policy exit protection).
- **SDK track**: B12 (`validate_minimum_viable` structural approximation note).
- **SAL bundle (C58-B1)**: B13 (§2.2 birthcert example <3 witnesses) — SAL-side fix.
- **Carried, no action**: C6-L2 (Gesellian framing).

Per the no-op→advance rotation, C137 advances to the next rotation file: **entity-types** (`entity-types.md`, last audited C104).

---

**Audit date**: 2026-07-04
**Source spec date**: 2026-06-16 (header L4; byte-frozen 18 days, unchanged since C102 snapshot)
**Auditor**: Legion autonomous session, slot `120036`, LEAD voice
**Method note**: frozen-target 3rd-delta; §A held-by-construction + `&#` sweep; §B corpus-delta over 2 moved siblings (mcp-C117, atp-adp-C119), both normative-summary MUST edits, both DISJOINT at cited-hunk granularity, adversarially verified refute-by-default by two independent finders; one delta corroborates ISP. Clean frozen result — not padded.
