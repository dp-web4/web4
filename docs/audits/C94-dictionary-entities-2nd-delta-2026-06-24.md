# C94 — Delta Re-Audit: dictionary-entities.md (2nd delta)

**Date**: 2026-06-24
**Auditor**: Legion autonomous web4 track (slot 180010, v2 protocol)
**Target**: `web4-standard/core-spec/dictionary-entities.md` (603 lines; head at audit `8c581465`)
**Lineage**: C17 (`dictionary-entities-internal-consistency-2026-05-27.md`, PR #241/#242) → C52 (`C52-dictionary-entities-audit-2026-06-12.md`, PR #323) → C53 remediation (PR #324, `95d20919`) → **C94** (this doc)
**Prior remediation under verification**: C53 (#324, `95d20919`, 2026-06-13, +11/−11) — 9 autonomous-actionable C52 findings applied (B1, B3a, B3b, B3c, B4, B5, B19, B20, B21).
**Staleness at audit**: **Frozen target.** `git log 95d20919..HEAD -- <target>` is EMPTY — the file is unchanged since C53 (11 days). The SDK counterpart `dictionary.py` (779 lines) is likewise unchanged (`git log 95d20919..HEAD -- <sdk>` EMPTY). This is a **frozen-target / moving-corpus** delta audit.
**Rotation note**: the C-series round-robin reached its end at mrh (C90/C91) and wrapped to the oldest last-audit, SOCIETY_SPEC (C92, #383). dictionary-entities.md is the next-oldest in rotation. The C93 remediation slot was a **no-op carry-surface** (C92 found 0 autonomous SOCIETY_SPEC defects), so the rotation advanced here.
**Method**: §A LEAD-direct re-verification of all 9 C53 findings + a #324 cross-referential regression sweep, independently re-verified by a refute-by-default adversarial verifier. §B scoped (per policy guidance) to the **corpus-delta surface** — the 20 corpus commits that landed in the C53→now window — plus one fresh full-file internal-coherence pass (refute-by-default); a clean frozen-target result is recorded as a positive result, not a prompt to manufacture marginal findings. §C carry re-verification (13 design-Q + 6 cross-track), bidirectional. §D method notes.

---

## §A — Prior-Finding Verification (held / regressed)

**Verdict: 9 of 9 HELD, 0 REGRESSED. #324 regression sweep CLEAN.** Confirmed by direct read AND an independent refute-by-default adversarial verifier (both agree on every line). All cites against head `8c581465`.

| C53 finding | Claim | Status | Current line |
|---|---|---|---|
| **B1** [MED] | §4.2 `witness_required=confidence < 0.95 or request.trust_requirements.require_witness` (flag OR'd in, no longer dead) | **HELD** | L246 |
| **B3a** [MED] | medical↔legal id is long form `lct:web4:dictionary:medical-legal` everywhere | **HELD** | L48, L162, L259 (§4.3 step1), L417 (§7.1 actor) |
| **B3b** [MED] | legal↔insurance pair is `lct:web4:dictionary:legal-insurance` (no `legal-ins`, no reversed `insurance-legal`) | **HELD** | L164, L267 (§4.3 step2), L512 (§10.1 step2) |
| **B3c** [LOW] | §10.2/§10.3 ids long form (`...:gpt4-claude3`, `...:chinese-business`) | **HELD** | L531, L545 |
| **B4** [MED] | §2.1 V3 = `(Valuation, Veracity, Validity)` (last stale `value`→`valuation` holdout) | **HELD** | L41 |
| **B5** [MED] | §7.1 R6 role keyed `"actor":` (r6-framework canon), not `"entity":` | **HELD** | L417 |
| **B19** [LOW] | §7.1 rules use `"minimum_fidelity":` not `"min_fidelity":` | **HELD** | L413 |
| **B20** [LOW] | §4.2 `request.source_domain, request.target_domain` not bare `request.source/.target` | **HELD** | L202 |
| **B21** [LOW] | §11.2 `stake_on_translation(self, amount, confidence_claim, actual_confidence)` (param bound) | **HELD** | L565 |

### #324 regression sweep (cross-referential)

Token sweeps on the current file: `lct:web4:dict:` short-form (excluding `dictionary:`) → **0 hits**; `roleType` → 0; `"min_fidelity"` → 0; `insurance-legal` / `med-legal` / `legal-ins` (non-`legal-insurance`) → 0; `"entity":` in the R6 block → 0; bare `request.source`/`.target` (no `_domain`) → 0; deprecated `Veracity, Validity, Value` V3 order → 0. The adversarial verifier independently re-walked all 9 hunks and the §10.1 chain (medical-insurance step1 / legal-insurance step2, internally consistent) and returned **clean**. C53 was a small (+11/−11), mechanically-scoped remediation — consistent with the C50 §D size-threshold lesson that cross-referential risk concentrates in larger (+58-line) remediations. **No remediation-introduced defects.** The §A clean property (recovered at C52 after the C50 break) continues.

---

## §B — Fresh Delta Findings

**Headline: 0 NEW autonomous target defects. The frozen target holds C52's coverage.** Per policy guidance, §B effort was scoped to the genuine corpus-delta surface (the 20 in-window commits) plus one fresh full-file internal pass; the clean result stands on its own.

### Corpus-delta surface — what actually moved in the C53→now window

Carry-relevant cross-ref targets that are **UNCHANGED** in-window (so the corresponding carries' cross-ref anchors are stable — no new drift): `t3v3-ontology.ttl`, `web4-core-ontology.ttl`, `r6-framework.md`, `r7-framework.md`, and the sibling `protocols/web4-dictionary-entities.md`. Four files changed (1 commit each — all the rotation's own remediations, not new corpus waves): `atp-adp-cycle.md` (C79 #368), `LCT-linked-context-token.md` (C61 #338), `errors.md` (C67 #347), `mcp-protocol.md` (C77 #366). Plus the new `referenced-acts.md` (171 lines) and `web4-core/src/act.rs` Act.kind work (#384). Assessed each for a NEW dictionary obligation:

- **`referenced-acts.md` / Act.kind (#384)** — contains **no** `dictionary` reference; the Act.kind registry lives in `web4-core` (Rust) and is not cross-referenced by the dictionary spec. **No new obligation.**
- **mcp C77** added a normative *"Implementations MUST set `entity_type` to a value in the recognized taxonomy"* (`mcp-protocol.md:118`). The target §2.2 L49 declares `"entity_type": "dictionary"`. Verified `dictionary` **IS** in the recognized taxonomy: LCT enum `LCT-linked-context-token.md:68` (`...|accumulator|dictionary|hybrid|...`) and `entity-types.md` (§2 table L32, AI/Service role tables L258/L265, §10). **COMPLIANT — no defect.** (Positive cross-ref result: a new normative MUST landed and the frozen target already satisfies it.)
- **atp-adp C79** made slashing (§2.4) more explicitly an authority-gated carve-out from total-supply conservation. This does **not** create a new finding but **HARDENS** the standing C52-B9 (§11.2's formula-driven, authority-less "partial slash" is now even more divergent from the cycle spec's slash semantics). Recorded as a hardening note on B9 in §C; no autonomous action (design-Q).
- **C61 LCT / C67 errors** diffs contain no dictionary-relevant lines (C17-M1 ontology gap and C17-M4 error-taxonomy gap both re-swept and **STILL OPEN** — `web4:Dictionary`/`sourceDomain`/`targetDomain`/`trustScore` absent from `ontology/`; `W4_ERR_DICT_*` / `IncompetentDictionary` / `InsufficientDictionaryTrust` absent from `errors.md`).

### Fresh full-file internal pass — 1 candidate, DEMOTED

#### C94-B1 [HIGH→INFO, DEMOTED] §3.2–3.4 dictionary-type examples show only type-distinguishing fields, not the full §2.2 LCT wrapper

- A finder lens flagged §3.2 (L106–128 `model_dictionary`), §3.3 (L135–150 `compression_dictionary`), §3.4 (L157–171 `meta_dictionary`) as HIGH: they open with a root `"type"` discriminator and carry only type-specific payloads (`embedding_alignment`/`token_mapping`, `codebook`/`reconstruction_fidelity`, `translates_between`/`provides`), lacking `lct_id`/`entity_type`/`compression_profile`/`dictionary_trust_config`/`mrh` — alleged §9.1 MUST-1 ("Every Dictionary MUST have a valid LCT") violation.
- **Adversarial demotion (HIGH→INFO).** These are **illustrative type-feature sketches**, not LCT records: the root `"type": "model_dictionary"` discriminator and the total absence of any `lct_id` signal "this section enumerates what differs per dictionary type," while §2.2 ("Dictionary LCT Structure") is the canonical complete form. §9.1 MUST-1 governs dictionary *entities*, not taxonomy illustration snippets. This is the same class as C52's refuted "illustrative ≠ normatively-incomplete" findings (e.g. C52-refuted #4, bare witness-LCT lists). Decisive evidence: §3.2–3.4 are **unchanged since file creation (2025-09-15, `a497f3c6`)** and C52's 81-agent sweep — which ran both an internal-coherence lens and a `specialized` lens — did not flag them; treating them as MUST-1 violations now would be an overcall, not a delta. **Not a defect.** The only residue worth recording: §3.2–3.4 could carry an explicit "type-specific fields only; see §2.2 for the full LCT wrapper" note (the pattern `entity-types.md` §10.2 L620 already uses to point to this spec) — an **INFO-grade documentation-clarity nicety, first-pass material, not a post-C53 delta**. Not routed to a remediation turn.

---

## §C — Carry Re-Verification (bidirectional)

All 13 C52 design-Q + 6 cross-track carries re-verified against today's head. **Status: all stand; two enrichments + one line-shift; none resolved, none newly autonomous.**

### Design-Q (operator-owned) — still open
- **C52-B2** (§4.2 L206 T3-floor source / tensor-vs-scalar) — OPEN, unchanged (L206 verbatim).
- **C52-B6** (R6-vs-R7 positioning) — OPEN; r6/r7-framework.md unchanged in-window. **Mild enrichment**: `entity-types.md:80` lists Dictionary among "R6-capable Responsive entities," corroborating the file's R6 framing — does not resolve the R7-tier-trust tension, but anchors the positioning question on the entity-types side too.
- **C52-B7** (`proposal_threshold: 10` scale) — OPEN (L344 verbatim).
- **C52-B8** (coverage scalar↔object; couples C17-M1) — OPEN.
- **C52-B9** (§11.2 partial-slash vs cycle slash semantics) — OPEN, **HARDENED** by atp-adp C79 (slashing re-affirmed as an authority-gated carve-out; §11.2's authority-less formula diverges further).
- **C52-B10** (`fidelity` undefined / §10.2 fidelity-vs-confidence) — OPEN (L534 `fidelity` vs L548 `confidence` verbatim).
- **C52-B11** (§9.1 MUST-5 "critical" undefined) — OPEN.
- **C52-B12 / B13 / B14 / B26** (sibling-spec canonicity vs `protocols/web4-dictionary-entities.md`) — OPEN; sibling **unchanged** in-window. **ENRICHMENT (→ B26 bundle): the divergence is 3-doc, not 2-doc.** `entity-types.md` §10.2 (L569–601) is a **third** normative Dictionary LCT structure (abbreviated; uses `trust_requirements` as the trust-config key vs the target's `dictionary_trust_config`). It is **subordinate** by its own pointer (L620 "For complete specification, see dictionary-entities.md"). Already recorded on the entity-types side as **C64-B7** (inbound cross-doc carry — see §C "inbound" below). The operator's sibling-canonicity decision should account for all three sources.
- **C52-B22** (10% stake reward / 1.1 mint path) — OPEN.
- **C52-B23** (chain-level `trust_acceptable` criterion undefined) — OPEN.
- **C17-M1** (§6.1 SPARQL `web4:*` predicates absent from ontology) — OPEN, re-swept zero hits in `ontology/`.
- **C17-M4** (`W4_ERR_DICT_*` / spec exceptions absent from errors.md + SDK) — OPEN, re-swept zero hits in `errors.md`.
- **C17-M6** (threshold-semantics relationship undeclared) — OPEN.
- **C17-H2** (`dictionary-translator` role value placeholder, L418–420) — OPEN; the disclaimer comment is intact. Couples C50-B25 (SDK dual role taxonomies) — resolve as one role-taxonomy operator decision; the dictionary role-value rides it.

### Cross-track (SDK-side) — still open, SDK frozen
`dictionary.py` is unchanged since C53, so **B15** (request nesting), **B16** (chain JSON-LD keys / false §4.3-conformance docstring), **B17** (trust-config expressibility), **B18** (V3 never updated), **B24** (selection weights/latency), **B25** (unanchored constants) **all stand verbatim**. Route to the SDK bundle.

### Inbound cross-doc carry (per the C90 [[feedback_cross_doc_carry_inbound]] lesson — read the sibling's own interval audit docs)
- **C64-B7** (from `C64-entity-types-2nd-delta-2026-06-16.md`) — entity-types §10.2 L585 trust-config key `trust_requirements` diverges from this file's §2.2 L67 `dictionary_trust_config`. Confirmed today; entity-types §10.2 is the subordinate side (its own L620 defers to this file). **Disposition: the fix belongs on the entity-types side** (sync §10.2's outer key + abbreviated structure to the canonical target), NOT on the target — so it is NOT an autonomous dictionary finding. Folds into the B26 3-doc sibling-canonicity bundle.

### Cross-doc carries elsewhere — re-verified
- **C17-INFO3** (`mcp-protocol.md` stale `"roleType": "web4:Developer"`) — **STILL PRESENT**, **line shifted 306→314** by the C77 remediation (which added explanatory roleType prose at L342 but did not fix the stale example). Remains carried for an MCP-side pass.

---

## §D — Method Notes

1. **Frozen-target audits earn their keep via the cross-ref + carry surface, not the target.** Target AND SDK unchanged for 11 days → §A is mechanical confirmation and the fresh-internal pass is near-certain to be empty (it was: 1 candidate, demoted). The real yield is (a) confirming a *new normative MUST landed elsewhere and the frozen file already complies* (mcp C77 entity_type taxonomy), (b) a standing carry *hardened* by a sibling remediation (B9 ← atp-adp C79), (c) an *inbound cross-doc carry* (C64-B7) that upgrades a known bundle from 2-doc to 3-doc. None of these are visible by reading the target alone — they require diffing the moved corpus and reading the siblings' own audit docs ([[feedback_cross_doc_carry_inbound]]).
2. **Overcall discipline held under the frozen-target temptation.** The lone fresh candidate (§3.2–3.4 "incomplete LCT") was a HIGH that dissolved on the standard test: is it illustrative-vs-normative, and did the prior exhaustive sweep (C52, 81 agents) see it? Both answers killed it. The pressure to "find something" on a frozen target is exactly where manufactured findings appear; the refute-by-default layer + the "did C52 miss it or accept it?" question are the guards. Recorded as INFO, not routed.
3. **Third-source discovery generalizes the sibling-canonicity pattern.** C52-B26 framed dictionary-spec divergence as a binary collision (target ↔ protocols/ sibling). entity-types §10.2 is a third normative structure with an explicit subordination pointer — the canonicity question is N-doc, and the operator decision wants the full set, not a pair. The subordination pointer (L620) is also the *resolution template* the protocols/ sibling lacks (C52-B26's title collision has no such pointer).
4. **Round-robin wrap is working as designed.** dictionary-entities.md surfaced as next-oldest after the C92 wrap; the frozen result confirms the staleness-ranked rotation is now in steady state (files churn slower than the audit cadence), so future wraps will increasingly hit frozen targets — the method should lean on the corpus-delta/carry surface accordingly.

---

## Disposition

- **§A**: 9/9 C53 findings HELD, 0 regressed; #324 regression sweep CLEAN (direct + adversarial). §A clean property continues.
- **§B**: **0 new autonomous target defects** — positive frozen-target result. 1 demoted INFO (§3.2–3.4 type-sketch clarity nicety, not routed). Corpus-delta confirmed: mcp C77 entity_type MUST → target COMPLIANT; B9 hardened by atp-adp C79; C64-B7 inbound (entity-types §10.2 = 3rd divergent Dictionary structure).
- **For a C95 remediation turn**: **NONE** — there is no autonomous SOCIETY/target fix to apply. The next remediation slot for this file is a no-op; rotation advances to the next-oldest file (SOCIETY_METABOLIC, last audited C54/C55).
- **For the operator**: B26 sibling-canonicity bundle now **3-doc** (target ↔ protocols/ ↔ entity-types §10.2); B9 hardened; the standing dictionary design-Q set (B2/B6/B7/B8/B10/B11/B22/B23 + C17-M1/M4/M6/H2) unchanged.
- **For the SDK track**: cross-track bundle (B15–B18, B24, B25) unchanged — SDK `dictionary.py` frozen.
- **For an MCP-side pass**: C17-INFO3 stale `roleType` now at `mcp-protocol.md:314`.
