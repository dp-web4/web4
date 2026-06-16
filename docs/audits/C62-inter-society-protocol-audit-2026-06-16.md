# C62: `inter-society-protocol.md` Internal Consistency RE-Audit (2nd delta)

**Date**: 2026-06-16
**Track**: web4 (Legion autonomous session, slot `000047`, exit #194)
**Instrument**: C-series delta RE-audit; 2nd delta on `inter-society-protocol.md` (lineage C6 → C25 → remediation #258 → **C62**)
**Source**: `web4-standard/core-spec/inter-society-protocol.md` (v0.1.2 DRAFT, 380 lines, last edited `1aebf3ed` PR #258, 2026-06-01)
**Method**: §A prior-finding verification + #258 regression sweep + mirror check (file NOT byte-identical to C25 → completeness-only method does NOT apply); §B multi-agent finder workflow (`wf_fd537bb9-7f6`, 46 agents, 11 lenses, refute-by-default verify + synthesis-time dedup).

**Cross-referenced (read live at audit-write per BC#14)**:
- `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (post-C50/C51 remediation #318 — §1.2.5 re-attribution)
- `web4-standard/core-spec/web4-society-authority-law.md` (SAL, post-C16/C23/C58/C59)
- `web4-standard/core-spec/mcp-protocol.md` (§7.3–§7.7 — §7.7 now carries per-subsection status banner)
- `web4-standard/core-spec/atp-adp-cycle.md`
- `web4-standard/core-spec/society-roles.md` (§2 base-mandatory roles)
- `web4-standard/implementation/sdk/web4/role.py` (`BASE_MANDATORY_ROLES`, `validate_minimum_viable`)

**Prior audits**: `docs/audits/inter-society-protocol-internal-consistency-2026-05-21.md` (C6, 13 findings → PR #215 resolved 12/deferred 1); `docs/audits/C25-inter-society-protocol-audit-2026-05-31.md` (C25, 6 NEW + 1 carry → PR #257 audit, PR #258 remediation: 3 autonomous applied, 3 design-Q deferred).

---

## Summary

| Severity | NEW (C62) |
|----------|----------:|
| HIGH     | 0 |
| MEDIUM   | 4 |
| LOW      | 11 |
| INFO     | 1 |
| **Total NEW distinct** | **16** |

**§B workflow yield**: 35 raw candidate findings → 27 confirmed / 8 refuted (refute-by-default) → **16 distinct** after synthesis-time dedup (heavy clustering on the exchange-rate and `established`/`federated` axes — see §B dedup note).

**3-bucket classification of NEW findings**:

| Bucket | IDs | Count |
|--------|-----|------:|
| Autonomous-actionable | B3, B4, B5, B6, B7, B8, B9, B14, B16 | 9 |
| Design-Q | B1, B2, B10, B11, B15 | 5 |
| Cross-track (SDK / sister-doc) | B12, B13 | 2 |

**Anti-padding note**: 2nd delta re-audit on a 380-line spec that has been edited ONCE since its prior audit (#258, +9/−4). The NEW findings are predominantly (a) the two C25 design-Q carries (M1/L1) re-derived and **sharpened** by upstream movement (mcp §7.7 sub-sections promoted to Normative since #258), and (b) cross-spec contradictions against `atp-adp-cycle.md` that were never lensed in C6/C25 (the ATP-as-form section §4 had not been cross-checked against the ATP/ADP source spec). Two genuine internal RFC-2119 / primitive contradictions (B4, B5) are the flagships. No INFO/LOW manufactured to fill an envelope; the count is what the spec deserves.

**Positive movement (headline)**: **C25-H1 (the most severe C25 finding) is RESOLVED downstream** — see §A.

---

## §A: Prior-Finding Verification Block

### A.1 — C25 findings (audit #257, remediation #258)

| C25 ID | Sev | Disposition | Current status | Evidence at audit-write |
|--------|-----|-------------|----------------|-------------------------|
| M2 | MED | autonomous → #258 | **HELD** | §8 table SAL row present (L358); §2.1 "Note on the genesis record" → SAL §2/§2.2 (L85); §5.1 step 1 → SAL §3.4 Immutable Record (L276-277). *Caveat: the §8 SAL row carries a mild mis-cite introduced by #258 — see B8.* |
| INFO1 | INFO | autonomous → #258 | **HELD** | §9 L371-373 no longer carry fabricated `v0.1.3`/`v0.1.4` tags; now "2026-05-14 amendment" + §7.7 "WIP v0.1.0-draft" status banner. *Caveat: the §7.7 "WIP" label is now itself stale — see B3.* |
| INFO2 | INFO | autonomous → #258 | **HELD** | Header L4 `Date: 2026-06-01` (matches #258 edit per BC#15). |
| **H1** | **HIGH** | design-Q (deferred) | **RESOLVED downstream** | C25-H1 = SOCIETY_SPEC §1.2.5 wrongly claimed "ISP §6.2 enumerates seven base-mandatory roles". **C51 remediation #318** rewrote §1.2.5 (L60) to attribute the 7 roles to **`society-roles.md` §2** (which does enumerate them, §2.1–§2.7) and to describe ISP §6.2 correctly as *semantic viability* GUIDANCE (L62). The three-way drift is closed: society-roles.md §2 = canonical 7-role home; ISP §6.2 = 3 semantic criteria; SDK `BASE_MANDATORY_ROLES` = 7 (matches society-roles.md). No ISP-side residue of the old mis-attribution remains (refute-confirmed by the `roles` finder's H1-residue check). |
| M1 | MED | design-Q (deferred) | **STILL OPEN, sharpened** | §3.2 Option 1 (L139-143) still enumerates abstract Fixed/Market/Pegged rates with no referent-grounding cross-ref. **Sharpened**: mcp §7.7.1 (the referent-grounded premise) is now declared **Normative** (was WIP at C25), strengthening the case. Re-derived as **B2**. |
| L1 | LOW | design-Q (deferred) | **STILL OPEN, sharpened** | mcp §7.4 `interaction_type` enum still uses `established`/`federated` state-names ISP §3 never defines. **Sharpened**: mcp §7.3 L397 now makes these labels load-bearing for normative `propagation_scope` defaults. Re-derived as **B1**. |

### A.2 — C6 carry

| C6 ID | Sev | Status | Evidence |
|-------|-----|--------|----------|
| L2 (Gesellian framing) | LOW | **DEFERRED-CARRY persists (expected)** | §4.1 L193 still says "not a Gesellian economic experiment". Per C6 + C25 deferral rationale (informational, technically accurate). No new action. |

**C6 substantive set (12 resolved at C25)**: spot-re-verified HELD — §4 consecutively numbered §4.1–§4.7 (no duplicate numbering, C6-H1); header v0.1.2 (C6-H2); §8 table has mcp-protocol row L364 (C6-H3) + society-roles row L365 (C6-M3); §2.1 footnote cites LCT for ≥3 witnesses (C6-M4); §4.6 cites AttestationEnvelope schema + SDK (C6-M5, *though the schema path is now broken — see B7*); §1.3 Eurozone hedge present (C6-L1, *re-surfaced as B14*); §3.2 SHALL framing (C6-L5). **0 C6 regressions.**

### A.3 — #258 regression sweep (per-file, via git, NOT by assumption)

`git show 1aebf3ed` touched **only** `inter-society-protocol.md` (1 file, +9/−4). Four hunks: header date bump; §2.1 genesis note; §5.1 secession note; §8 SAL row + §9 version-tag cleanup. Per-file check confirms #258 introduced **no edits to any sister file** (contrast C50, where the same-era #252 broke a sister doc — provenance re-checked per file per the standing lesson).

**One remediation-introduced facet**: the §8 SAL row added by #258 cites "fractal Society Topology and `web4:memberOf` edges (SAL §3.1)" — but `web4:memberOf` is normatively defined in **SAL §3.3** (MRH RDF Edges, Normative) and chained in §3.5, not §3.1 (which is "Society Topology" prose). Mild mis-cite → **B8** (autonomous, LOW). This continues the remediation-introduced-defect pattern (a delta-audit must check the *content* the prior remediation wrote, not just that it "held").

---

## §B: NEW Findings (C62)

### MEDIUM

#### B4 (autonomous-actionable) — §2.2 step 4: normative `SHALL` contradicted by its own "voluntary / can decline" gloss — **FLAGSHIP**
**Lines**: L107-109.
**Defect**: §2.2 Federation-Based Genesis step 4 reads:
> "4. A, B, [C, ...] **SHALL** update their own LCTs to record citizenship in D *(this is voluntary at any time; constituents can decline if charter changes)*"
A RFC-2119 `SHALL` (mandatory) immediately qualified by "this is voluntary ... constituents can decline" is internally contradictory — the parenthetical negates the normative force of the keyword. This is a genuine internal-consistency defect (not cross-spec): the reader cannot tell whether recording citizenship in D is required or optional.
**Fix (autonomous)**: Either downgrade `SHALL` → `MAY` (if recording is genuinely voluntary, which the surrounding overlay-not-owner framing in L115 supports), or remove the "voluntary/can decline" gloss and keep `SHALL` (if D-genesis requires constituents to record membership). The overlay/consent architecture (§1.3, L115) favors `MAY`/`SHOULD`.

#### B5 (autonomous-actionable) — §4.5 says a society "MAY mint … ATP" but `atp-adp-cycle.md` mints only ADP — **FLAGSHIP cross-spec primitive contradiction**
**Lines**: ISP §4.5 L233-235; cross: `atp-adp-cycle.md` §2.1 L37-39.
**Defect**: ISP §4.5 ("First ATP" Resolution) states "A society **MAY mint any quantity of its own ATP**" (L235) and L233 "mint excessive ATP". But `atp-adp-cycle.md` §2.1 is explicit: **"Minting (ADP Creation) — Societies mint tokens in the discharged (ADP) state"**; charged ATP is reached *only* via the charging transition (ADP→ATP), which §4 of that spec gates with "Charging MUST require value proof" (L584). So "minting ATP" is a category error against the source spec's core primitive: you mint ADP, you charge to ATP. C6/C25 never cross-checked §4 against `atp-adp-cycle.md` (the ATP-form section was audited only internally), so this is first-surfaced.
**Fix (autonomous)**: Reword §4.5 to "mint any quantity of its own ADP (and charge it to ATP per its policy)" or "issue any quantity of its own ATP" with a note that issuance follows the mint-ADP→charge form of `atp-adp-cycle.md` §2.1–§2.2. Keeps the "no protocol-level issuance constraint" point (which is the actual claim) without contradicting the mint/charge primitive.

#### B1 (design-Q) — mcp §7.4 `interaction_type` imports state-names `established`/`federated` that ISP §3 never defines [C25-L1 re-derived + sharpened]
**Lines**: ISP §3 (L117-179); cross: mcp `§7.4` L417 (enum `first_contact | established | federated`), L442-443 (grounds `first_contact` in ISP §3.1; "established and federated proceed normally"), **§7.3 L397** (normative `propagation_scope` defaults branch on the three values).
**Defect**: mcp §7.4's normative cross-society envelope treats `first_contact`/`established`/`federated` as peer interaction states of one lineage and explicitly attributes `first_contact` to ISP §3.1 — but ISP §3 defines **no** `established` or `federated` relationship state. §3.2 yields three sovereign *Options* (Retain+Exchange / Adoption / Federation-forming-D); §3.3 yields Defer / observational / mediator outcomes. "established" appears in ISP only as a verb (L123, L175); "federated" never appears as a state label. **Sharpened since C25**: §7.3 L397 now makes these labels load-bearing for normative SHOULD `propagation_scope` defaults, so an implementer cannot map a relationship to `established`/`federated` from ISP §3.
**Why design-Q**: cleanest fix is cross-track (mcp defines the three states locally or stops attributing them to ISP §3); the ISP-autonomous alternative is to add a short §3.x naming post-first-contact relationship states (`established` = mutual recognition under Option 1/2; `federated` = constituent of a shared D under Option 3) so the mcp enum gains an ISP referent. Architectural choice → operator.

#### B2 (design-Q) — §3.2 Option 1 enumerates abstract bilateral ATP_A:ATP_B rates that mcp §7.7.1 (now Normative) declares "NOT the Web4 model" [C25-M1 re-derived + sharpened]
**Lines**: ISP §3.2 Option 1 L139-143; also §4.4 L227-229, §4.5 L235; cross: mcp `§7.7.1` L514 (**Normative**), L524-528.
**Defect**: §3.2 Option 1 ("A and B negotiate an exchange rate (ATP_A : ATP_B)… Fixed / Market-derived / Pegged") plus the §4.4 FX-market analogy describe exactly the *abstract floating bilateral rate* mental model that mcp §7.7.1 now disavows: "two societies maintain a floating bilateral rate ATP_A : ATP_B independent of any particular transaction. **This is NOT the Web4 model.**" In Web4 rates are *referent-grounded* (grounded in the substance of the R6/R7 action). **Sharpened since C25**: §7.7.1 was WIP at C25 but is now declared **Normative** ("a design invariant, not WIP"), so ISP §3.2's model now contradicts a *normative* invariant, not merely a draft.
**Why design-Q (with autonomous interim)**: C25-M1's Option C (minimal forward-pointer) is autonomous-safe now that §7.7.1 is stable — add "(the *substance* of any rate is referent-grounded per `mcp-protocol.md` §7.7.1; the enumeration below governs rate *stability over time*)" to §3.2 Option 1. Full reframe of §3.2/§4.4 is the design-Q. Recommend the autonomous interim cross-ref be applied in C63, full reframe deferred.

### LOW

#### B3 (autonomous-actionable) — §8 L364 + §9 L373 label mcp §7.7 blanket "WIP" though §7.7.1/§7.7.4 are now Normative
**Lines**: ISP §8 L364 ("§7.7 (WIP) specifies referent-grounded…"), §9 L373 ("§7.7 (WIP v0.1.0-draft, 2026-05-14) … currently WIP pending fleet review"); cross: mcp §7.7 banner L513-520 (§7.7.1 Normative L514, §7.7.4 Normative L517; only §7.7.2/3/7 Normative-draft, §7.7.5/6 Informative).
**Defect**: Since #258, mcp §7.7 gained a per-subsection status banner: the referent-grounded premise (§7.7.1) and form/substance boundary (§7.7.4) ISP relies on are **Normative design invariants**, not WIP. ISP's blanket "WIP" / "WIP pending fleet review" framing now understates the settled status of the architecture it cites. Same class as the C25-INFO1 metadata cleanup.
**Fix (autonomous)**: Refine both lines to "§7.7 (architecture Normative per §7.7.1/§7.7.4; wire format WIP)".

#### B6 (autonomous-actionable) — §2.1 step 5 "Birth witnesses (MAY be ≥3 …)" puts optionality on the *count*, making the mandatory quorum read as optional
**Lines**: L75 vs L83 note vs §6.1 L318.
**Defect**: §2.1 step 5 reads "Birth witnesses (**MAY be ≥3** entities under founder's control; see §6 …)". The L83 note and §6.1 treat ≥3 as a *mandatory* quorum (from `LCT-linked-context-token.md`); the L75 phrasing misplaces the `MAY` onto the count "≥3" rather than onto "under the founder's control", making it read as if having ≥3 witnesses is optional. Internal contradiction with L83 ("requires ≥3 birth witnesses").
**Fix (autonomous)**: "Birth witnesses — ≥3 required per `LCT-linked-context-token.md`; these MAY be entities under the founder's control (see §6)."

#### B7 (autonomous-actionable) — §4.6 cites a broken schema path
**Lines**: ISP §4.6 L248 (`schemas/attestation-envelope.schema.json`); actual file `web4-standard/schemas/attestation-envelope-jsonld.schema.json`.
**Defect**: The cited path is missing the `-jsonld` infix; the file does not exist at the cited path. Verified by `ls web4-standard/schemas/`. Introduced at C6-M5 remediation (the dangling-reference fix pointed at a not-quite-right filename).
**Fix (autonomous)**: Correct to `schemas/attestation-envelope-jsonld.schema.json`.

#### B8 (autonomous-actionable) — §8 SAL row mis-cites SAL §3.1 for `web4:memberOf` (remediation-introduced by #258)
**Lines**: ISP §8 L358; cross: SAL §3.1 (Topology prose), §3.3 (MRH RDF Edges, Normative, L92 `web4:memberOf`), §3.5 (chaining).
**Defect**: The #258-added SAL row says "the fractal Society Topology and `web4:memberOf` edges (SAL §3.1)". `web4:memberOf` is normatively defined in SAL **§3.3**, not §3.1. Mild but precise mis-cite born in the prior remediation.
**Fix (autonomous)**: "(SAL §3.1 topology; `web4:memberOf` edges per SAL §3.3/§3.5)".

#### B9 (autonomous-actionable) — §2.2 federation-genesis has no cross-ref to SOCIETY_SPEC §4.2.1 incorporate_child / incorporated_by formation events
**Lines**: ISP §2.2 steps 3-4 (L107-109); cross: SOCIETY_SPEC §4.2.1 (L337, L347).
**Defect**: §2.2 step 3 ("D SHALL mint constituent-society LCTs") and step 4 (constituents record citizenship in D) describe exactly the incorporation lifecycle that SOCIETY_SPEC §4.2.1 records as `incorporate_child`/`incorporated_by` formation events. No cross-ref. (Symmetric to the §5.1→SAL §3.4 cross-ref #258 already added for secession; genesis was left without the analogous pointer.)
**Fix (autonomous)**: Add an inline pointer in §2.2 to SOCIETY_SPEC §4.2.1 formation events.

#### B14 (autonomous-actionable) — §1.3 Eurozone analogy weakly supports the "always-can-exit" invariant
**Lines**: §1.3 L40-42.
**Defect**: §1.3 lists Eurozone as "structurally analogous" to Web4's "a constituent society can always exit (per §5)" — but the Eurozone has no defined euro-exit mechanism (the existing C6-L1 hedge "can theoretically exit, though no member has yet done so" acknowledges this). The analogy is the *weakest* of the four listed (NATO/UN/standards-bodies all have clear withdrawal mechanisms). Already softened by C6-L1; this is a residual analogy-quality nit, not a fresh defect.
**Fix (autonomous, optional)**: Either strengthen the hedge or demote Eurozone below the cleaner NATO/UN/IETF analogies. **Note**: C6-L1 already remediated this once; consider leaving as-is unless C63 has spare scope (low value).

#### B16 (autonomous-actionable) — §8 society-roles.md row claims "Bidirectional dependency" but cites only the Diplomat/§6.2 half
**Lines**: ISP §8 L365.
**Defect**: The society-roles.md row says "Defines roles (including Diplomat) … This spec's §6.2 defines semantic viability criteria that constrain role composition. **Bidirectional dependency.**" The "bidirectional" claim is under-supported — it names the ISP→society-roles direction (Diplomat) and the §6.2 constraint, but the reciprocal society-roles→ISP edges (e.g., the Witness role in society-roles §4.6 that ISP §2/§4.6 witnessing relies on) are not surfaced. Minor completeness nit.
**Fix (autonomous, optional)**: Either name the reciprocal edge or soften "Bidirectional dependency" to match what is actually cited. Low value.

#### B10 (design-Q) — §4.1/§4.3 permit charging ATP on a forward "pledged commitment" vs `atp-adp-cycle.md` "Charging MUST require value proof"
**Lines**: ISP §4.1 L194, §4.3 L218 (ATP-as-Commitment), §4.2 L202; cross: `atp-adp-cycle.md` L584 ("Charging MUST require value proof").
**Defect**: §4.1 says a society moves ADP→ATP "when it accounts for actual resource availability **or pledged commitment**"; §4.3 ATP-as-Commitment credits ATP as a "forward-looking pledge … *future capacity*, not past contribution". `atp-adp-cycle.md` normatively requires *value proof* for charging — a forward pledge without delivered value is in tension. This is a genuine conceptual-model question (does Web4 permit charging on commitment, or only on proven value?), not a typo.
**Why design-Q**: resolving it picks a side between two specs' models of what "charging" means. Operator-owned. (Note: §4.3 itself flags "the difference between pledged and delivered is itself audit-relevant signal" — a reconciliation path exists but is unspecified.)

#### B15 (design-Q) — §5.1 exit conditioned on settlement "per D's settlement policy" gives D unilateral control of an exit precondition
**Lines**: §5.1 step 4 L284 vs §1.3 L38-40 (no-compulsion invariant).
**Defect**: §5.1 step 4 makes a seceding constituent "Settle outstanding ATP balances in D's currency (**per D's settlement policy**)". Since D writes its own settlement policy, D unilaterally controls a precondition of A's exit — in tension with §1.3's "no mechanism for any society to assert authority over another without consent" and "a constituent society can always exit". A hostile D could set a punitive settlement policy that effectively blocks exit.
**Why design-Q**: the fix is a normative-protection decision (e.g., "settlement policy MUST NOT impose conditions that prevent exit", or a default fallback when D's policy is abusive). Architectural → operator.

#### B11 (design-Q / cross-track) — §4.1 "ATP is not currency / not a medium of exchange" vs `atp-adp-cycle.md`'s pervasive "native currency" framing
**Lines**: ISP §4.1 L187 ("a unit of account, not a medium of exchange with intrinsic value"), L189 ("ATP-in-cells is also not currency"); cross: `atp-adp-cycle.md` L5 ("managed by societies as their **native currency**"), §5 ("Inter-Society **Currency** Exchange").
**Defect**: The two specs take opposite rhetorical stances on whether ATP is "currency". ISP §4 argues emphatically it is a unit-of-account, not currency; `atp-adp-cycle.md` calls it the society's "native currency" and titles its §5 "Currency Exchange". Not a wire-format conflict, but a corpus-level framing inconsistency a reader will notice.
**Why design-Q/cross-track**: reconciling requires deciding the canonical framing (likely: ATP is a society-internal unit-of-account that *functions as* currency in inter-society exchange — both partly right). Owner is `atp-adp-cycle.md` (the ATP/ADP SSOT) + operator. Route cross-track.

### INFO

#### B13 (cross-track) — §2.1 routes to SAL §2.2 as the canonical Birth Certificate, but SAL §2.2's example shows only 2 witnesses (< the ≥3 quorum ISP states)
**Lines**: ISP §2.1 L85 (pointer); cross: SAL §2.2 (Birth Certificate JSON-LD example, ~L55).
**Defect**: #258 routed ISP genesis to SAL §2.2 as the canonical Birth Certificate shape, but SAL §2.2's worked example carries fewer than 3 witnesses, contradicting the ≥3 quorum ISP §2.1/§6.1 and `LCT-linked-context-token.md` require. The defect is in SAL, not ISP; ISP's pointer is correct. **Folds into the standing SAL operator bundle (C58-B1 birthcert §2.1-vs-§2.2 cluster).** Route cross-track; no ISP-side action.

### Cross-track (SDK)

#### B12 (cross-track) — SDK `validate_minimum_viable` operationalizes §6.2 items 1 & 2 more weakly than the spec prose (mitigated by §6.3 GUIDANCE framing)
**Lines**: ISP §6.2 items 1-2 (L328-329); cross: SDK `role.py` `validate_minimum_viable` (~L376-390).
**Defect**: §6.2 item 1 ("internal differentiation") is defined as *authority* differentiation ("role A's authority is meaningfully different from role B's"), and item 2 ("witnessing capacity") requires *independent judgment* ("not just rubber-stamp"). The SDK approximates item 1 as a distinct-entity/filler count and item 2 as mere presence of a Witness/Auditor role — dropping the authority-difference and independent-judgment discriminators. **Mitigant**: ISP §6.3 states explicitly these criteria are "GUIDANCE, not protocol enforcement", so a structural SDK approximation is arguably within bounds; the SDK docstring also scopes itself to "the role-structural side". Still a documented spec↔SDK semantic gap worth a docstring note.
**Why cross-track**: the SDK owns any tightening; no ISP-side fix. Route to SDK track (low priority given the GUIDANCE framing).

---

## §B dedup note (35 raw → 16 distinct)

Heavy clustering on two axes drove the 35→16 reduction:
- **`established`/`federated` undefined** (C25-L1): 4 finders independently surfaced it (envelope, lifecycle, crossref, demoted) → merged into **B1**.
- **Abstract exchange-rate vs referent-grounding** (C25-M1): 6 raw findings (envelope×2, exchange-rate×2, crossref, demoted) spanning §3.2/§4.4/§4.5 → merged into **B2** (model) + **B3** (the distinct WIP-label staleness, which 4 more finders + several *refuted* candidates also hit).
- **Witness quorum optionality** (§2.1 L75): 2 finders (witness, rfc2119) → **B6**.
- **SDK §6.2 weakening**: 3 finders (roles, sdk-align×2) → **B12**.

**8 refuted** (refute-by-default working as intended): e.g. "self-bootstrap genesis has no LCT-creation enforcement" (refuted — out of ISP scope, LCT spec owns); "§5.2 dissolution records no event" (refuted — SOCIETY_SPEC §4.2.1 `dissolve` covers it); "H1-residue: ISP still mis-attributes 7 roles" (**refuted — confirms C25-H1 fully resolved**, no ISP residue); plus 4 duplicate WIP-label candidates collapsed into B3.

---

## Cross-Cutting Observations

1. **C25-H1 resolved downstream is the headline.** The most severe C25 finding (the three-way 7-role drift) was closed not by ISP remediation but by C51's edit to SOCIETY_SPEC §1.2.5. This validates the delta-audit discipline: re-verifying prior design-Q carries against the *current* corpus (not the corpus at C25) caught a resolution that a naive "is ISP unchanged?" check would have missed. **The two surviving C25 design-Q (M1/L1) were each *sharpened* by upstream movement** (mcp §7.7.1/§7.7.4 promoted to Normative since #258) — the opposite direction from H1. Delta audits must re-evaluate carries in both directions: some resolve, some harden.

2. **§4 (ATP form/substance) was never cross-checked against `atp-adp-cycle.md` until C62.** C6 and C25 audited §4 internally only. The first cross-spec pass against the ATP/ADP SSOT surfaced three contradictions (B5 mint-ATP-vs-ADP, B10 charge-on-pledge-vs-value-proof, B11 currency-vs-unit-of-account) — one of them (B5) a flagship MEDIUM on a core primitive. **Lesson: a spec section that *re-narrates* another spec's primitive (here, ISP §4 re-explaining ATP/ADP) must be lensed against that primitive's SSOT, even if the section reads internally coherent.**

3. **Remediation-introduced mis-cite (B8) continues the established pattern.** #258's §8 SAL row cited the wrong SAL sub-section for `web4:memberOf`. Small, but it is the third consecutive cycle (C54/C56/C60-era) where a remediation's *own new content* carried a defect the next audit caught. The pre-merge mini-audit threshold (+58 lines) would not have caught this — #258 was only +9, well under threshold. **Sub-lesson: cite-accuracy of remediation-added cross-refs is a recurring miss independent of diff size; a remediation that adds a §-citation should verify the target sub-section, not just that the target file exists.**

4. **Subordinate-ontology / snake-camel clusters: NOT extended.** ISP identifiers (`genesis_block_hash`, `interaction_type`, `atp_settlement`) consistent snake_case; ISP is not a primary anchor for the sub-ontology cluster. No contribution.

5. **Anti-padding held.** 16 distinct on a 380-line twice-audited spec, with 4 MEDIUM that are all genuine (2 internal RFC-2119/primitive contradictions, 2 sharpened cross-spec carries) and 0 HIGH. The LOW tier is real cross-ref/wording defects, not envelope filler.

---

## §D: Lessons → Memory

1. **Re-verify design-Q carries against the *current* corpus, bidirectionally** — some resolve downstream (C25-H1 via C51), some harden (C25-M1/L1 via mcp §7.7 promotion). A delta audit's §A must check both. (Extends the C56 completeness lesson.)
2. **Cross-check re-narrating sections against the primitive's SSOT** — ISP §4 re-explained ATP/ADP and drifted from `atp-adp-cycle.md` on a core primitive (B5). Any section that paraphrases another spec's primitive needs a lens against that SSOT, even when internally coherent. (NEW — feeds finder-lens checklist.)
3. **Remediation-added cross-refs must verify the target sub-section** — #258 cited SAL §3.1 for an edge defined in SAL §3.3 (B8). Cite-accuracy of newly-added §-references is a recurring miss independent of diff size (the +58 mini-audit threshold doesn't catch +9 cite errors). (Extends [[feedback_remediation_introduced_regression]].)

---

## Remediation Routing (for C63)

### Autonomous-actionable (9 — direct ISP-internal edits)
- **B4** (MED): §2.2 step 4 — resolve SHALL-vs-voluntary (recommend `SHALL`→`MAY`/`SHOULD` per overlay framing). *[flagship]*
- **B5** (MED): §4.5 — "mint ATP" → mint-ADP-then-charge (or "issue ATP") per `atp-adp-cycle.md` §2.1. *[flagship]*
- **B3** (LOW): §8 L364 + §9 L373 — refine §7.7 "WIP" to "architecture Normative (§7.7.1/§7.7.4); wire format WIP".
- **B6** (LOW): §2.1 L75 — re-place the `MAY` so ≥3 reads mandatory.
- **B7** (LOW): §4.6 L248 — fix schema path to `attestation-envelope-jsonld.schema.json`.
- **B8** (LOW): §8 L358 — `web4:memberOf` cite §3.1 → §3.3/§3.5 (remediation-introduced).
- **B9** (LOW): §2.2 — add SOCIETY_SPEC §4.2.1 formation-event cross-ref (symmetric to §5.1).
- **B14** (LOW, optional/low-value): §1.3 Eurozone analogy — strengthen hedge or demote (C6-L1 already softened once).
- **B16** (LOW, optional/low-value): §8 society-roles row — support or soften "Bidirectional dependency".
- **B2-interim** (the autonomous half of B2): §3.2 Option 1 — add referent-grounding forward-pointer to mcp §7.7.1 (now safe; §7.7.1 Normative).

### Design-Q (operator engagement)
- **B1**: where do `established`/`federated` relationship states live — ISP §3.x (autonomous-able) or mcp-private (cross-track)? [C25-L1, now load-bearing]
- **B2-full**: full reframe of §3.2/§4.4 abstract-rate language vs referent-grounded model. [C25-M1]
- **B10**: does Web4 permit charging ATP on a forward commitment, or only on proven value? (ISP §4.3 vs `atp-adp-cycle.md` value-proof MUST).
- **B11**: canonical framing of ATP as "currency" vs "unit-of-account" (ISP §4.1 vs `atp-adp-cycle.md`). [cross-track owner = atp-adp-cycle]
- **B15**: normative protection so D's settlement policy cannot block a constituent's exit (§5.1 vs §1.3 no-compulsion).

### Cross-track (SDK / sister-doc — route, do not fix in ISP)
- **B12** (SDK): docstring/behavior note that `validate_minimum_viable` is a structural approximation of §6.2 items 1-2 (mitigated by §6.3 GUIDANCE).
- **B13** (SAL): SAL §2.2 Birth Certificate example shows <3 witnesses — folds into the C58-B1 SAL birthcert operator bundle.

### Carried (no C63 action)
- C6-L2 (Gesellian framing) — deferred-carry persists, informational.

---

**Audit date**: 2026-06-16
**Source spec date**: 2026-06-01 (header L4; current)
**Auditor**: Legion autonomous session, exit #194, slot `000047`, LEAD voice
**Workflow**: `wf_fd537bb9-7f6` (46 agents, 11 lenses, refute-by-default verify)
