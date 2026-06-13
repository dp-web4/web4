# C52 — Delta Re-Audit: dictionary-entities.md

**Date**: 2026-06-12
**Auditor**: Legion autonomous web4 track (slot 120047, v2 protocol)
**Target**: `web4-standard/core-spec/dictionary-entities.md` (603 lines; §A verified at head `958a5625`, §B at head `320c5387` — `git log 958a5625..320c5387 -- <target>, sdk/web4/dictionary.py` is EMPTY, so both sections audited the identical file content; the 120047 session died after committing §A/§C, and the 180047 session completed §B/§D under a fresh policy approval inheriting the same scope)
**Prior audit**: C17 (`docs/audits/dictionary-entities-internal-consistency-2026-05-27.md`, PR #241)
**Prior remediation**: PR #242 (`991a0092`, 2026-05-28, +28/−13) — 7 autonomous-actionable findings applied (H1, H2-rename, M2, M3, M5, L1, L2); 4 design-Q deferred (M1 ontology, M4 error taxonomy, M6 threshold semantics, H2 role-value); 1 cross-track (INFO1 SDK dataclass)
**Staleness at audit**: 15 days since #242; no commits have touched the target since (`git log 991a0092..958a5625 -- <target>` empty). **Oldest never-delta-re-audited file in the corpus** at selection time.
**Sister-spec drift exposure**: the corpus-wide `value`→`valuation` V3 renames (#277/#279/#305/#309/#311), attestation `witness`→`lct` key fixes (C46/C48), C33 id-scheme consolidation, mcp-protocol §7.3–7.6 amendments, and the creation of `web4-standard/implementation/sdk/web4/dictionary.py` (C17-INFO1 recorded it as absent) ALL post-date #242 — this spec has never been audited against any of them.
**Method**: §A LEAD-direct re-verification of all 7 applied findings + cross-referential #242 regression sweep (C50 §D lesson: hunk-local sweeps miss cross-referential defects); §B multi-agent finder sweep with refute-by-default adversarial verification + primitive-clustered third pass; §C carries record-only. Per policy execution note 1, SDK-comparison findings default to cross-track/design-Q (no autonomous side-taking on spec-vs-SDK canon — the C22-M5/C50-B7 lesson).

---

## §A — Prior-Finding Verification (held / regressed)

Verdict summary: **7 of 7 HELD, 0 REGRESSED.** The §A clean property recovers after breaking at C50 (streak before the break: C40/C42/C44/C46/C48).

All line cites below are against today's checkout (head `958a5625`).

### C52-A1 — C17-H1 (SPARQL predicate typo): HELD

- L366: `web4:sourceDomain "medical" ;` — the one-character typo (`sourceDomai`) is fixed; predicate now matches the correctly-spelled `web4:targetDomain` on L367.
- Sweep: `sourceDomai\b` has zero hits in the spec corpus today.
- (The predicates themselves remain absent from the canonical ontology — that is deferred C17-M1, tracked in §C, not a regression of H1.)

### C52-A2 — C17-H2, rename half (`roleType` → `roleLCT`): HELD

- L418: `"roleLCT": "lct:web4:role:dictionary-translator:..."` with the inline non-normativity disclaimer (L419–420) referencing the deferred H2 role-value DESIGN-Q, exactly as #242 shipped it.
- `roleType` has zero hits in the target today. The known cross-doc residual (C17-INFO3: `mcp-protocol.md:306` stale `"roleType": "web4:Developer"`) is tracked in §C — re-verified still present today (`mcp-protocol.md` L306), unchanged by the C35 cycle.
- The role-VALUE question (whether `dictionary-translator` enters the SocietyRole enum, and its hyphen-vs-underscore form) remains an open DESIGN-Q (§C); the disclaimer comment keeps the spec honest meanwhile.

### C52-A3 — C17-M2 (`witness_attestation` → `witnesses`): HELD

- L274: `"witnesses": ["lct:web4:witness:domain-expert"]` — plural array-of-LCT-refs, corpus-canonical convention.
- `witness_attestation` has zero hits in the target today; the object-shaped `witness_attestation` record remains reserved by mcp-protocol/schema_registry as intended.

### C52-A4 — C17-M3 (`trust_requirements` outer-key disambiguation): HELD

- L67: §2.2 outer key is `dictionary_trust_config` ({minimum_t3, stake_required} — LCT-default-config scope).
- L189: §4.1 per-request override shape retains `trust_requirements` ({minimum_fidelity, require_witness, atp_stake}).
- The two-scope split #242 established is intact. **Cross-referential residue routed to §B**: §4.2 pseudocode (L206) reads `request.trust_requirements.minimum` and compares it against `dictionary.t3` — a field the disambiguated §4.1 shape does not define (its keys are `minimum_fidelity`/`require_witness`/`atp_stake`, none of them a T3 floor; the T3 floor lives in §2.2's `minimum_t3`). This incoherence is **pre-existing** (L206 is unchanged by #242 — verified in the diff), so it is NOT a remediation-introduced regression; but the M3 disambiguation made it *visible* that the pseudocode references a field from the wrong scope. Adversarially verified in §B (see C52-B2) rather than asserted here.

### C52-A5 — C17-M5 (`:v2` suffix drop): HELD

- L48: `"lct_id": "lct:web4:dictionary:medical-legal"` — no version suffix; the dedicated `"version": "2.3.1"` field (L54) is the sole version carrier.
- Sweep: `lct:web4:dictionary:*:v2`-shaped ids have zero hits in the target today. (Pre-existing `lct:web4:dict:` short-form ids elsewhere in the file are a separate fresh-finding candidate — §B, C52-B3 — not an M5 regression: M5's scope was the `:v2` suffix only.)

### C52-A6 — C17-L1 (bare thresholds → named constants): HELD

- L220: `if target_concepts.ambiguity > AMBIGUITY_GATE:` and L317: `if dictionary.changes > VERSION_BUMP_DELTA:` — both #242 constants present, UPPER_SNAKE_CASE per pseudocode convention.
- Bare `> threshold` has zero hits in the target today. (L246's literal `confidence < 0.95` was not in L1's scope — it is M6-adjacent threshold-semantics material, tracked in §C; a third-bare-threshold observation is evaluated fresh in §B.)

### C52-A7 — C17-L2 (§10.1 chain reshape to §4.3 mirror): HELD

- §10.1 (L499–521): `translation_chain[]` with `{step, from, to, dictionary, output, confidence, degradation}`, top-level `cumulative_degradation: 0.12` with arithmetic comment, full-LCT-form `witnesses` — exactly the #242 shape.
- Arithmetic re-verified: 1 − (0.94 × 0.94) = 0.1164 ≈ 0.12 ✓; §4.3's 1 − (0.95 × 0.92) = 0.126 ✓.
- Known deliberate asymmetries (no regression): §10.1 adds `output` (absent in §4.3 by design — §4.3 is the tracking record, §10.1 the worked example) and omits §4.3's `trust_acceptable`. Id-token consistency *between* the two mirrored examples (`lct:web4:dictionary:medical-insurance` vs `lct:web4:dict:med-legal`) is a fresh-finding candidate — §B (C52-B3).

### #242 regression sweep (cross-referential, all 7 hunks)

Each hunk was re-read in place and its inserted tokens traced to their cross-references:

1. **H1 hunk** (L366): inserted predicate matches L367's existing spelling; no new claims introduced. Clean.
2. **H2 hunk** (L418–420): inserted role-LCT value is explicitly disclaimed as illustrative; the disclaimer's pointer ("C17 audit H2 role-value DESIGN-Q") cites a real, still-open deferral. Clean.
3. **M2 hunk** (L274): inserted key matches the 7-file corpus convention; array shape preserved. Clean.
4. **M3 hunk** (L67): rename only; inner shape untouched. The §4.2 L206 incoherence it exposes is pre-existing (see C52-A4). Clean as a hunk.
5. **M5 hunk** (L48): id now matches the `lct:web4:dictionary:<pair>` long form used at L82–84/L163–165. Clean.
6. **L1 hunks** (L220, L317): constants introduced but (like the pre-existing `lossy_threshold`/`proposal_threshold` pattern they cite) given no defined values — consistent with pseudocode convention; no semantic claim added. Clean.
7. **L2 hunk** (§10.1): arithmetic verified above; inserted dictionary ids use the canonical long form; inserted witness LCTs match §4.3's form. Clean.

**No remediation-introduced defects found in #242.** Contrast with C50 (nine #252-introduced defects): #242 was a small (+28/−13), mechanically-scoped remediation whose inserted text makes almost no cross-referential claims — consistent with the C50 §D size-threshold lesson (+58-line remediations are where cross-referential risk concentrates).

---

## §B — Fresh Delta Findings

**Method**: workflow `wf_8e0d8013-9b8`, 81 agents — 10 finder lenses (internal-coherence, v3-t3-vocab, id-scheme, r6-cross, atp-cross, sdk-align, mcp-witness-cross, sibling-cross, threshold-semantics, primitive-clustered) each followed by a refute-by-default adversarial verifier per finding. **71 raw findings → 57 CONFIRMED / 6 DOWNGRADED / 8 REFUTED → 26 distinct** after cross-lens dedup (the two §A-routed candidates alone consumed 17 raw slots: B2 surfaced in 9 lenses, B3 in 8).

**Headline**: **0 HIGH** — both HIGH candidates were downgraded on adversarial verification (B12's "unsatisfiable RFC-2119 conflict" framing failed: MAY-vs-MUST is satisfiable, only MUST-vs-MUST-NOT is not; B2's HIGH overstated blast radius for pseudocode). Tally: **18 MED / 6 LOW / 2 INFO**; classified **7 autonomous / 13 design-Q / 6 cross-track**. The MED density is driven almost entirely by post-C17 corpus waves the file slept through (`value`→`valuation` V3 rename, the R6/R7 split, the SDK module the file has never been reconciled with, the sibling protocols/ spec) rather than internal rot — consistent with §A's clean verdict on the C17 remediation itself.

All target line cites verified verbatim by the finder AND independently re-verified by its adversarial verifier.

### Autonomous (mechanically fixable on the target's own terms) — for a C53 remediation turn

#### C52-B1 [MED] §4.2 `witness_required` ignores the request's `require_witness` flag

- §4.1 defines `"require_witness": true` in the request's `trust_requirements` (L191); §4.2's flow computes `witness_required=confidence < 0.95` from confidence alone (L246) — the only assignment in the flow, which reads `request.trust_requirements` exactly once (L206, `.minimum`) and never `.require_witness`. A request explicitly demanding a witness gets `witness_required=False` whenever confidence ≥ 0.95; the defined field is dead on the file's own flow. (§7.1 L414's `rules.require_witness` is likewise unconsumed; §9.1 MUST-3 only requires witness*ability*.)
- **The SDK is AHEAD of the spec here**: `dictionary.py` `record_translation` (L661–665) computes `witness_required = confidence < 0.95 or request.require_witness` — exactly the fix the spec pseudocode needs. Distinct from carry C17-M6 (this is a dead defined field, not the numeric-relationship question). Mechanical fix: OR the flag into L246.

#### C52-B2 [MED → design-Q, see below] — listed under design-Q (routed candidate 1)

#### C52-B3 [MED] Dictionary LCT id forms inconsistent across the file (routed candidate 2 — CONFIRMED, decomposed)

Census: 7 long-form `lct:web4:dictionary:` (L48, 162–164, 417, 505, 512) vs 4 short-form `lct:web4:dict:` (L259, 267, 531, 545); declared `entity_type: "dictionary"` (L49) and the LCT-spec enum token is `dictionary` (LCT-linked-context-token.md:68).

- **B3a [MED, autonomous]** Same entity, three spellings: the §2.2 worked-example medical↔legal dictionary is `lct:web4:dictionary:medical-legal` (L48, L162), `lct:web4:dict:med-legal` (L259, §4.3 step 1), and hybrid `lct:web4:dictionary:med-legal` (L417, §7.1). No alias is declared; the §4.3 chain and §7.1 R6 example cannot be traced back to the §2.2 LCT. Normalize to the §2.2 form.
- **B3b [MED, autonomous]** Legal↔insurance pair: `lct:web4:dictionary:legal-insurance` (L164, §3.4 with `transitive_closure: true`), `lct:web4:dict:legal-ins` (L267), and **pair-order-reversed** `lct:web4:dictionary:insurance-legal` (L512, §10.1). The directional-naming refutation fails on the file's own model (L53 `bidirectional: true`); contrast the consistent sibling pair `medical-insurance` (L163 = L505). No pair-ordering rule exists in the file.
- **B3c [LOW, autonomous]** Residual short-form `dict:` tokens at L531/L545 (`gpt4-claude3`, `chinese-business`) — unique entities, no collision, but contradict the file's dominant token, L49, and the LCT-spec enum.
- **B3d [INFO, design-Q]** All 21 LCT id literals are human-readable typed forms, not the LCT spec's canonical `lct:web4:mb32:` hash form (LCT-linked-context-token.md:64, 260; only the prefix assert at :594 passes). Recorded per the C44-§B precedent (typed forms internally consistent ≠ fresh defect) and the C50-B20 precedent (new per-file evidence joins the standing C33 id-scheme operator bundle). Sibling note for the bundle: protocols/web4-dictionary-entities.md exclusively uses short `dict:` + underscore pairs — which form a corpus-wide normalization targets is the bundle's question, but B3a–B3c are fixable on the target's own terms (its §2.2 declares the long form).

#### C52-B4 [MED] L41 lists V3 as "Veracity, Validity, Value" — deprecated name, non-canonical order

- L41: `**V3 Tensor**: Quality of translations (Veracity, Validity, Value)` vs t3v3-ontology.ttl:29 `(Valuation/Veracity/Validity)` and t3-v3-tensors.md L199/214/220 headings. The corpus-wide `value`→`valuation` rename (#277/#279/#305/#309/#311) all post-date this file's last touch — a genuine stale holdout, the last known one in an audited core-spec file. Mechanical fix: `(Valuation, Veracity, Validity)`.

#### C52-B5 [MED] §7.1 R6 role block keys the actor as `entity`; r6-framework canon is `actor`

- L416–417: `"role": { "entity": "lct:web4:dictionary:med-legal", ...` vs r6-framework.md:59 `"actor": "lct:web4:entity:alice"` and its settlement pseudocode `r6_action.role.actor` (:313/:325/:336; r7-framework.md:69/672 agree). The target explicitly defers to R6 ("Every translation follows R6", L407), so this is a mechanical rename on the target, not a canon choice.

#### C52-B19 [LOW] Fidelity-floor key spelled two ways: `minimum_fidelity` (§4.1 L190) vs `min_fidelity` (§7.1 L413)

- SDK uses `minimum_fidelity` (dictionary.py:219). Normalize §7.1 to §4.1's spelling.

#### C52-B20 [LOW] §4.2 L202 reads `request.source`/`request.target`; the §4.1 shape defines `source_domain`/`target_domain`

- L202: `if not dictionary.covers_domains(request.source, request.target):` vs L182–183. The same function correctly uses `request.source_content` (L210) and `request.target_domain` (L229). Single obvious rename.

#### C52-B21 [LOW] §11.2 `stake_on_translation` uses unbound variable `actual_confidence`

- Signature (L565) takes only `(self, amount, confidence_claim)`; the body branches on and divides by `actual_confidence` (L567, L570), never a parameter or assignment — the settlement input the whole mechanism depends on is unbound. Mechanical: add the parameter (the deeper settlement-semantics question is B9, design-Q).

### Design-Q (operator decision required — no side-taking per the C22-M5/C50-B7 lesson)

#### C52-B2 [MED] §4.2 L206 gates on `request.trust_requirements.minimum`, a key defined nowhere, and compares a T3 tensor to a scalar (routed candidate 1 — CONFIRMED by 9 lenses)

- L206: `if dictionary.t3 < request.trust_requirements.minimum:` — but §4.1's shape (L189–193) has only `minimum_fidelity`/`require_witness`/`atp_stake`, and the only defined T3 floor is §2.2 `dictionary_trust_config.minimum_t3` (L67–72), per-dimension and dictionary-side, not request-side. Pre-existing (L206 unchanged by #242 — verified in §A); the M3 disambiguation made it visible.
- Why design-Q and not autonomous: the fix requires choosing the floor source — §2.2's per-dimension floors, a new request-side scalar, or the SDK's composite gate (`meets_trust_requirement(minimum_t3_composite)`, dictionary.py:644–646). The doc itself scalarizes T3 elsewhere via `dict.t3.average()` (L391), so even the comparison repair has two candidate idioms. M6-adjacent but distinct: M6 is how the thresholds *relate*; B2 is a reference to a threshold that *does not exist*.

#### C52-B6 [MED] The file frames ALL translations as R6 while its own trust model is R7-tier; "R7" never appears

- L407 "Every translation follows R6:" yet the lifecycle is reputation-bearing (L461 each success increases T3; L311–314 updates both tensors), which under today's split is R7's tier (r6-framework.md:5–7: R6 is for "routine, low-consequence tasks... For consequential actions where the outcome should shape future trust, use R7"). Git-verified timeline: the R6 framing dates to file creation (2025-09-15, `a497f3c6`); r7-framework.md arrived 2025-10-14 — the file predates the split and has never been repositioned. The dictionary-side instance of the standing R6-vs-R7 scoping question (couples carry CT-failure).

#### C52-B7 [MED] §5.2 `proposal_threshold: 10` is commented "Min reputation to propose" on a 0–1 reputation scale

- Same JSON block: reputations 0.95/0.92 (L333, L339) and `approval_quorum: 0.66 // Weighted by reputation` (L345) establish the 0–1 scale; L344's gate of 10 is unsatisfiable by any contributor. Either the value or the label is wrong — choosing (rescale vs relabel to contributions/ATP) is a spec decision. (One lens judged this LOW-autonomous via comment-fix; the conservative class wins.)

#### C52-B8 [MED] §6.1 SPARQL filters `web4:coverage` as a 0–1 scalar; §2.2 defines coverage as a counts object

- L368/372/378 (`FILTER(?coverage > 0.9)`, `ORDER BY DESC(?trust * ?coverage)`) vs L55–59 (`"coverage": { "terms": 15000, "concepts": 3200, "relationships": 8500 }`). No mapping from counts to a fraction exists; a reader cannot implement the filter against the defined shape. Distinct from C17-M1 (predicate *absence* from the ontology); this is a shape contradiction internal to the target. Couples the M1/C40-D1 ontology decision.

#### C52-B9 [MED] §11.2 "Partial slash" is incoherent with atp-adp-cycle slash semantics

- L569–570: automatic, formula-driven forfeiture (`return amount * (actual_confidence / confidence_claim) # Partial slash`) vs atp-adp-cycle.md §2.4: slash is authority-gated (`has_slashing_authority`), evidence-backed, witnessed, and **destroys** ATP from total_supply (:210–212). The target's version has no authority, no evidence, no witnesses, and never says where the forfeited fraction goes. L475's MUST prevents dismissing §11.2 as illustrative-only.

#### C52-B10 [MED] `fidelity` is gated on but never defined, computed, or returned — and §10.2 reports `fidelity` where every other example reports `confidence`

- Floors at L190 (`minimum_fidelity`) and L413 (`min_fidelity`), but the §4.2 flow computes only `confidence` (L233) and `TranslationResult` (L241–247) carries no fidelity field; L534 reports `fidelity: 0.93` vs L548 `confidence: 0.85` for analogous outputs. The spec never states whether fidelity ≡ confidence. Term-identity gap, not the excluded M6 numeric question.

#### C52-B11 [MED] §9.1 MUST-5 ("Critical translations MUST require ATP stake") is unenforceable: "critical" is undefined

- L475 is the only occurrence of "critical" in the file; candidate definers fail (L73's comment shifts to equally-undefined "high-risk"; §4.1 L192 is a non-normative example; §11.2 is voluntary quality-claim staking, not a criticality gate). SDK corroboration: `atp_stake` (default 0.0) is carried but never read or enforced (`record_translation`, dictionary.py:661–665). Defining the precondition is an operator call.

#### C52-B12 [MED, downgraded from HIGH] Target makes multi-hop translation MAY; the sibling spec lists chain+parallel under MUST

- L485–487 (§9.3 MAY: "Dictionaries MAY support multi-hop translation") vs protocols/web4-dictionary-entities.md:273–279 (§9.1 "Implementations MUST: ... Support chain and parallel translation"). Downgrade rationale: MAY-vs-MUST is not an unsatisfiable RFC-2119 conflict (an implementation supporting chaining satisfies both); the real defect is divergent conformance *floors* for the same entity type. Root cause is B26.

#### C52-B13 [MED] Dictionary LCT wire structure diverges wholesale from the sibling spec

- Target §2.2 (L50–74): `dictionary_spec` + scalar `source_domain`/`target_domain` + T3-based `dictionary_trust_config` vs sibling §3.1 (:32–61): `dictionary_definition` + `domains.source`/`domains.target` arrays + non-tensor `trust_metrics` (accuracy_score/preservation_rate/verification_count). Two incompatible canonical JSONs for the same entity type. Root cause is B26.

#### C52-B14 [MED] Translation-chain record shape diverges from the sibling on the same mechanism and math

- Target §4.3 per-hop `{step, from, to, dictionary, confidence, degradation}` + chain-level `{cumulative_degradation, trust_acceptable, witnesses}` (L255–274) vs sibling per-hop `{hop, dictionary, trust_before, trust_after, degradation}` + `{total_trust_preservation, acceptable_threshold, translation_valid}` (:125–143). Verifier note: the one shared numeric key, `degradation`, carries *different semantics* across the two docs. Root cause is B26.

#### C52-B22 [LOW, downgraded] §11.2's 10% stake reward creates ATP outside the cycle spec's only creation path

- L565–568 (`return amount * 1.1 # 10% reward`) vs atp-adp-cycle.md:39 (societies mint only ADP) and §2.2 charging as the sole ADP→ATP path (MUST-4 :584). Whether translation-quality claims count as a chargeable value proof under a society's economic law (§2.2.1 delegation) is the open question — hence LOW design-Q, not a contradiction.

#### C52-B23 [LOW, downgraded] §4.3 declares `trust_acceptable: true` at 0.874 effective fidelity with no chain-level acceptability criterion defined

- L272–273 vs the per-request 0.95 (L190) and per-rules 0.9 (L413) — but those floors belong to *different illustrative scenarios*, so "violates its own thresholds" dissolved on verification; what remains is that no chain-level criterion exists for `trust_acceptable` to be checked against.

#### C52-B26 [INFO] Title collision: the target and protocols/web4-dictionary-entities.md are both titled "Web4 Dictionary Entities Specification", both normative, neither cross-references or defers to the other

- One operator decision (canonical/merge/scope note) resolves B12/B13/B14 at the root. Increments the standing subordinate-ontology/sibling-spec cluster.

### Cross-track (SDK-side or spec↔SDK canon choice — first-ever sdk-align pass; routes to the SDK bundle)

#### C52-B15 [MED] §4.1 nests trust fields under `trust_requirements`; SDK `TranslationRequest` flattens them to top level

- Spec L189–193 vs dictionary.py:215–221 (flat `minimum_fidelity`/`require_witness`/`atp_stake`, no grouping). Any wire mapping of SDK requests will not match the spec example. Which structure is canon is exactly the question the M5/B7 lesson forbids deciding unilaterally.

#### C52-B16 [MED] §4.3 chain JSON keys diverge wholesale from SDK `TranslationChain.to_jsonld`, whose docstring claims §4.3 conformance

- Spec `from`/`to`/`dictionary`/`witnesses`/`trust_acceptable` vs SDK `source_domain`/`target_domain`/`dictionary_lct_id`/`witness_lct_ids` + added `cumulative_confidence`/`length`, omitting `trust_acceptable` (dictionary.py:359–381, docstring "per dictionary-entities spec §4.3"). One side's claim of conformance is false today.

#### C52-B17 [MED] §2.2 `dictionary_trust_config` (per-dimension T3 floors + `stake_required`) has no SDK counterpart

- SDK's only trust gate is `meets_trust_requirement(minimum_t3_composite)` on the composite (dictionary.py:644–646); per-dimension floors and the stake requirement cannot be expressed. Couples B2's floor-source question.

#### C52-B18 [MED] §5.1 updates both T3 and V3 tensors; SDK `apply_feedback` updates only T3 — V3 is permanently static in the canonical implementation

- Spec L310–314 (`t3_delta=` + `v3_delta=`) vs dictionary.py:691–696 (both feedback branches mutate only `lct.t3`; module-wide, v3 is read-only). The "Quality of translations" tensor (§2.1) never moves.

#### C52-B24 [LOW] §6.2 scores five selection inputs including latency; SDK drops latency and hardcodes weights 0.4/0.3/0.2/0.1 as "spec §6.2" though §6.2 defines no weights

- Spec L390–396 vs dictionary.py:715–727.

#### C52-B25 [INFO] `AMBIGUITY_GATE`/`VERSION_BUMP_DELTA` have no defined values in the target and no SDK presence

- Pre-existing, NOT a #242 regression: `git show 991a0092` confirms #242 replaced an equally-undefined bare `threshold` token at both sites (L220, L317). Implementation-defined gap; record for whichever side eventually anchors values.

### Refuted (8) — the refute-by-default layer's wins

1. **Error-name convention inversion (L203/207 vs r6/r7 §7)** — duplicate of the excluded C17-M4 carry, same sites, same names, not a #311-fresh delta.
2. **ATP earning verbs unanchored (§11.1/§5.2)** — dissolves: atp-adp-cycle §2.2.1 deliberately delegates earning vocabularies to society law.
3. **§7.1 R6-only framing leaves no witness slot (mcp §7.3)** — false premise: r6-framework §1.6 Result carries witness attestations.
4. **Bare witness LCT lists lack signature structure (mcp §7.3)** — the bare-list form is corpus-canonical (5 sibling specs use it identically; it was C17-M2's *deliberate* target shape).
5. **R6 example's 10 ATP cost is 10× the sibling economy** — `resource.required` is an escrow ceiling with refund at settlement, not a price.
6. **L246 bare 0.95 literal should be a named constant** — duplicate of C17-M6's carve-out: #242's L1 commit text explicitly enumerated and excluded this site.
7. **Staking party/amount never reconciled (100 vs 50 vs 10)** — already examined and demoted as a non-defect in the C17 audit itself.
8. **§10.1 cumulative_degradation 0.12 contradicts its own formula** — arithmetically wrong claim: 1 − 0.94² = 0.1164, and 0.12 is exactly that at the example's stated 2-decimal precision.

---

### C17 deferrals — current status, all re-verified against today's head

- **C17-M1 (ontology gap) — STILL OPEN.** The six `web4:*` predicates in §6.1 SPARQL (`Dictionary`, `sourceDomain`, `targetDomain`, `trustScore`, `coverage`, `lastUpdated`) remain absent from every file in `web4-standard/ontology/` (re-swept: `chapter-law.ttl`, `t3v3-ontology.ttl`, `web4-core-ontology.ttl` — zero hits). Couples the consolidated ontology-vocabulary DESIGN-Q (carry-C40-D1: per-term extend-ontology vs rewrite-example). Operator-owned.
- **C17-M4 (error taxonomy) — STILL OPEN.** `W4_ERR_DICT_*` does not exist in `errors.md`; `IncompetentDictionary`/`InsufficientDictionaryTrust` appear nowhere in the SDK. Couples the carry-C30 error-canonicity bundle and is the dictionary-side instance of the C46/C48-agency pattern (spec-raised exception with no catalog home + no SDK class). Operator-owned.
- **C17-M6 (threshold semantics) — STILL OPEN.** The T3-minimum (0.9) / fidelity floor (0.95) / witness gate (0.95) relationship remains undeclared. Narrow mechanical facets were separated out and evaluated fresh in §B (C52-B2 cluster); the design question itself stays deferred.
- **C17-H2 role-value — STILL OPEN.** `dictionary-translator` remains a disclaimed placeholder (L418–420). **New coupling since C17**: C50-B25 (SDK dual role taxonomies — federation.py `RoleType(5)` cannot represent 5 of 7 base-mandatory `SocietyRole` values) strengthens the case for resolving role taxonomy as ONE operator decision; the dictionary role-value should ride that decision, not precede it.
- **C17-INFO3 (mcp-protocol.md:306 stale `roleType`) — STILL PRESENT.** Re-verified today: `"roleType": "web4:Developer"` at `core-spec/mcp-protocol.md:306`, unchanged through the C35 cycle. Remains carried for an MCP-side pass.

### C17-INFO1 status CORRECTION (audit-text error, wrong at birth)

C17-INFO1 asserted: *"SDK … has NO Dictionary dataclass"*, evidenced by `grep -l -i "class.*Dictionary\b"` returning no matches. **The claim was false when written.** `web4-standard/implementation/sdk/web4/dictionary.py` — 779 lines, 13 classes including `DictionaryEntity`, `DictionarySpec`, `TranslationRequest`, `TranslationResult`, `TranslationChain`, exported via `__init__.py` — has existed since at least 2026-03-29 (`7fd83de4`, Sprint 11 era), two months before C17. The grep's `\b` after `Dictionary` cannot match any of the SDK's prefixed class names (`DictionaryEntity` has no word boundary after "Dictionary"), and no class is named bare `Dictionary`.

- **Classification**: audit-instrumentation error in C17 itself — the same wrong-at-birth class as C50-R1 (audit text seeding a false claim), in its harmless INFO-severity variant: nothing propagated into normative spec prose, but the carry ledger has carried a false premise for 16 days, and INFO1's substantive conclusion ("all §9.1 MUSTs are spec-only — no SDK enforcement exists") was never actually established. The real spec↔SDK relationship is audited for the first time in §B (sdk-align lens).
- **Method lesson (→ §D)**: word-boundary regexes silently exclude prefixed/suffixed identifiers; corpus sweeps that *establish absence* need a looser pattern (or a second sweep without `\b`) before an absence claim enters an audit record.

### New carries born this audit (→ ledger)

- **Operator DESIGN-Q bundle additions**: B2 (T3-floor source for the §4.2 gate), B6 (R6-vs-R7 positioning of dictionary translations — couples CT-failure), B7 (proposal_threshold scale), B8 (coverage scalar↔object, couples M1/C40-D1), B9 (slash semantics vs cycle spec), B10 (fidelity↔confidence term identity), B11 (MUST-5 "critical" definition), B22 (stake-reward mint path), B23 (chain-level acceptability criterion), B26 (**sibling-spec canonicity** — one decision resolves B12/B13/B14; recommend bundling with the existing subordinate-ontology cluster), B3d (id-form evidence → existing C33 bundle).
- **Cross-track SDK bundle additions**: B15 (request nesting), B16 (chain JSON-LD keys — one side's §4.3-conformance claim is false), B17 (trust-config expressibility), B18 (V3 never updated), B24 (selection weights/latency), B25 (unanchored constants).
- **C17-INFO1 ledger flip**: from "SDK dataclass missing (cross-track)" to "CLOSED-INVALID (wrong at birth); superseded by the C52 sdk-align findings B15–B18/B24/B25, which audit the actually-existing SDK."

---

## §D — Method Notes

1. **\b-regex blindspot (from §C INFO1 correction)**: absence claims require a loose-pattern second sweep (`grep "Dictionary"` without `\b`) before entering an audit record. C17-INFO1 carried a false premise for 16 days because `class.*Dictionary\b` cannot match `DictionaryEntity`. Same wrong-at-birth class as C50-R1, INFO-severity variant.
2. **Refute-by-default earned its cost again**: 8/71 raw findings (11%) refuted, and both would-be HIGHs downgraded to MED — the §B headline ("0 HIGH") exists only because verifiers killed the overstatements. Three refutations were *duplicate-of-carry* catches (M4, M6/L1-scope, C17-demoted staking) — the verifier prompt's carry-list is doing real dedup work, not just truth-checking.
3. **Routed-candidate lens collision**: pre-routing the two §A candidates into "their" lenses caused 17 of 71 raw slots to be re-derivations of B2/B3 (9 and 8 lenses respectively) — every lens that *touched* those lines re-reported them. Future sweeps: pin each routed candidate to exactly one named lens and instruct the other nine to treat it as a known-exclusion, freeing finder capacity for genuinely fresh material.
4. **Sibling-root-cause compression**: B12/B13/B14 (3 MEDs) + B26 share one root — two identically-titled normative specs for the same entity type. The per-primitive consolidation pattern (C33 lesson) applies: surface as ONE operator decision, not four findings. §B classifies them separately for honesty but the ledger should bundle them.
5. **First sdk-align pass vindicates the lens**: 6 confirmed cross-track findings from one new lens, including one inverted defect (B1: the SDK is *ahead* of the spec — pseudocode lags its own implementation) and one false conformance docstring (B16). INFO1's never-established conclusion ("§9.1 MUSTs are spec-only") is now actually answered: MUST-3 witnessability is SDK-enforced (better than spec pseudocode), MUST-5 stake is not enforced on either side (B11).
6. **Delta-cycle economics**: the file slept through 4 corpus waves (V3 rename, R6/R7 split, SDK creation, sibling-spec emergence) in 16 days; 18 of 26 findings trace to those waves rather than to defects present at C17 time. Staleness-ranked target selection (this session's basis) is finding exactly what it should.

---

## Disposition

- **§A**: 7/7 C17 findings HELD, 0 regressed; #242 regression sweep CLEAN — the §A clean property recovers after C50's break.
- **§B**: 26 distinct fresh findings (0 HIGH / 18 MED / 6 LOW / 2 INFO; 7 autonomous, 13 design-Q, 6 cross-track).
- **For a C53 remediation turn (autonomous set)**: B1, B3a/B3b/B3c, B4, B5, B19, B20, B21 — all single-file, mechanical, on the target's own terms. Estimated well under the +58-line mini-audit threshold, but per standing practice the pre-merge mini-audit is now kept for *every* remediation.
- **For the operator**: DESIGN-Q bundle per §C "New carries"; the sibling-canonicity decision (B26) has the highest leverage (resolves 3 MEDs at the root).
- **For the SDK track**: cross-track bundle per §C "New carries" (B15–B18, B24, B25).

