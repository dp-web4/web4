# C50 — Delta Re-Audit: SOCIETY_SPECIFICATION.md

**Date**: 2026-06-12
**Auditor**: Legion autonomous web4 track (slot 000047, v2 protocol; THIRD execution attempt — slots 060047 and 120047 died at session limits with zero artifacts)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (446 lines, head `c76d6e70`)
**Prior audit**: C22 (`docs/audits/C22-society-specification-audit-2026-05-30.md`, PR #251)
**Prior remediation**: PR #252 (`252e77bd`, 2026-05-30) — 8 autonomous-actionable findings applied (H1, H2, H3, M1, M2, L1, L2, I1); 2 design-Q deferred (M6, I2); 5 cross-track deferred (M3, M4, M5, I3, I4)
**Staleness at audit**: 13 days since #252; no commits have touched the target or sister specs since (`git log 252e77bd..c76d6e70 -- <target>` empty beyond #252 itself)
**Method**: §A LEAD-direct re-verification of all 8 applied findings + #252 regression sweep; §B multi-agent finder sweep with refute-by-default adversarial verification; §C carries record-only.

---

## §A — Prior-Finding Verification (held / regressed)

Verdict summary: **7 of 8 HELD, 1 REGRESSED (H1 → C50-R1, remediation-introduced)**.
The §A clean streak (C40 / C42 / C44 / C46 / C48) **BREAKS at C50**.

All line cites below are against today's checkout (head `c76d6e70`).

### C50-R1 (flagship) — C22-H1 remediation §1.2.5 mis-cites ISP §6.2 as home of the 7 base-mandatory roles and asserts protocol enforcement that ISP explicitly disclaims — REGRESSED (remediation-introduced)

**What #252 added (for C22-H1)**: §1.2.5 "Operational-Minimum Cross-Reference" (L55–62), distinguishing the §1.2 *conceptual* minimum from the *operational* minimum, cross-referencing SAL §3.1 and `inter-society-protocol.md` §6.2.

**Defect component (a) — wrong citation for the role enumeration.**
- `SOCIETY_SPECIFICATION.md` L60 claims: *"`inter-society-protocol.md` §6.2 (referenced by the SDK's `validate_minimum_viable`) enumerates **seven base-mandatory roles** — Sovereign, Law Oracle, Policy Entity, Treasurer, Administrator, Archivist, and Citizen…"*
- Actual ISP §6.2 (`inter-society-protocol.md` L324–330) is titled **"Minimum Viable Semantic Society"** and contains exactly three *semantic* criteria — internal differentiation, witnessing capacity, externally-grounded ATP referent. It enumerates **no roles**.
- The seven base-mandatory roles actually live in **`society-roles.md` §2** (L49–51: *"Every Web4-compliant society MUST have these seven roles filled"*, listing Sovereign + Law Oracle + Policy-Entity + Treasurer + Administrator + Archivist + Citizen).
- The SDK confirms the split: `role.py` module header (L2, L19) and class docstring (L44) anchor the taxonomy to `society-roles.md §2-§4`; `BASE_MANDATORY_ROLES` (role.py:118–126) implements that list. `validate_minimum_viable` (role.py:341–353) cites ISP §6.2 **only for the semantic criteria** ("items 1 and 2 from §6.2"), not for any role list. §1.2.5 conflated the SDK's semantic-viability citation with the role-enumeration home.

**Defect component (b) — false enforcement claim.**
- L62 claims: *"Conformance to the role-structural minimum is checked by `inter-society-protocol.md §6.2` at federation-admission time"*.
- ISP §6.3 (L338) states the direct opposite: *"These are GUIDANCE, not protocol enforcement. The Web4 protocol does not adjudicate whether a society is 'real enough.'"* — viability is discovered socially via first-contact (§3) outcomes, not checked at admission.

**Wrong at birth, seeded by the audit itself.** ISP §6.2 never enumerated roles — at #252 time it already read exactly as today (verified via `git show 252e77bd:…inter-society-protocol.md`), and `society-roles.md` predates #252 (C7 audit cycle #217). The seed error is in C22-H1's own text, which described `role.py:341` as referencing "`inter-society-protocol.md §6.2`: 7 base-mandatory roles" — a mis-reading that #252 faithfully propagated into normative spec prose.

**Classification**: REGRESSED, remediation-introduced (the C36 lesson firing on live data — second confirmed instance of the class). Routed to **C51 remediation** per policy execution notes (twice-carried from slots 060047/120047): NOT a design-Q, NOT fixable in this audit-only session. Suggested C51 shape: re-point the role-enumeration citation at `society-roles.md` §2; replace the enforcement claim with ISP §6.3-faithful language (guidance + social discovery, with `validate_minimum_viable` as the SDK's *voluntary* conformance check); keep the SAL §3.1 sentence (verified accurate — see C50-A2 note below). Note the relationship to carry-C39/C25-H1 (7-role normative home): C51 should cite the role home as it stands today; the carry's open question (whether ISP should *also* normatively reference the list) remains operator-owned.

### C50-A2 — C22-H1 (the cross-reference scaffold itself): PARTIALLY HELD

The §1.2.5 paragraph #252 added does what C22-H1 asked structurally — §1.2 now acknowledges the conceptual-vs-operational distinction and points at the sister specs. The SAL half is accurate: `web4-society-authority-law.md` §3.1 does require Authority Role LCT + Quorum Policy (spot-verified this session). The ISP half is the regression above. Recorded as PARTIALLY HELD with the defect carried as C50-R1; not double-counted.

### C50-A3 — C22-H2 (economic event vocabulary): HELD

- L287: `"action": "deposit|allocate|reclaim"`; L288: `"token_type": "ATP"`; L292: the layer-separation disclaimer (treasury vocabulary vs R6/cycle-layer charge/discharge per `atp-adp-cycle.md` §2) — all present and intact.
- SDK still matches: `society.py:94` `ECONOMIC = "economic"  # allocate/deposit/reclaim`. No drift.

### C50-A4 — C22-H3 (Rejection non-record note): HELD

- L130: the Note on `Rejection` present, naming the exact 5-value `CitizenshipStatus` enum and the no-record semantics.
- SDK still matches: `federation.py:91–98` — APPLIED / PROVISIONAL / ACTIVE / SUSPENDED / TERMINATED, no REJECTED. No drift.

### C50-A5 — C22-M1 (§7.1 false-future framing): HELD

- L429: intro paragraph present, routing core inter-society primitives to `mcp-protocol.md` §7 + `inter-society-protocol.md` and scoping the bullets to further extensions. Bullets (L431–433) preserved with the "beyond §7.4 reputation envelopes" qualifier.

### C50-A6 — C22-M2 (minimum-record categories): HELD

- §1.2.2 (L33–39): 5 categories (citizenship / law / economic / metabolic / formation), "Witness attestations" removed, participant-not-event note present (L39) with cross-ref to §4.2.1 as canonical enumeration.
- §4.2.1 items 4–5 (L294–320): metabolic + formation JSON with SDK-exact strings.
- SDK still matches: `society.py:95–96` `METABOLIC = "metabolic"` / `FORMATION = "formation"` (BC#14 strings un-suffixed); recording sites unchanged (society.py:340/372/385/596/792). No drift.

### C50-A7 — C22-L1 (participatory validators inheritance): HELD

- L248: inheritance paragraph present under the §4.1.3 JSON, cross-refs §3.2.1 + §4.1.2, explains the intentional absence of `validators`.

### C50-A8 — C22-L2 (T3/V3 tensor naming): HELD

- L53: "Holds society-level T3 (trust) and V3 (value) tensors (see `t3-v3-tensors.md` and §5.3)". Consistent with corpus-wide V3-vocabulary remediations (C47/C49) — no `value`-tensor vocabulary drift here.

### C50-A9 — C22-I1 (date staleness, 2-file): HELD

- `SOCIETY_SPECIFICATION.md` L4: `## Date: 2026-05-30`; `SOCIETY_METABOLIC_STATES.md` L4: `## Date: 2026-05-30`. Both bumped, both intact.

### #252 regression sweep (beyond the 8 finding sites)

**Corrected after §B** (the as-committed checkpoint-1 text claimed "no second remediation-introduced defect"; the LEAD hunk-walk verified each hunk's *internal* accuracy and SDK-string fidelity, which held — but missed contradictions the inserted prose creates *against other sections and sister specs*). The §B multi-agent sweep found **eight further #252-introduced defects**: C50-B1, B2, B5, B7, B8, B11, B12, B26. Together with C50-R1 that is **nine defects introduced by one remediation PR** — the largest remediation-introduced cluster recorded in the C-series (prior instances: C36 single, C46-M1 single). Method lesson recorded in §D.

**Correction to C50-A2**: §A above says the SAL half of §1.2.5 is "accurate". Precisely: SAL §3.1's *requirement list* (Authority Role LCT + Quorum Policy) is correctly reported, but §1.2.5's *characterization* of the Quorum Policy is not — see C50-B8.

---

## §B — Fresh Delta Findings

**Method**: 10 finder lenses (internal coherence, corpus vocab drift, SAL, ISP+society-roles, metabolic+ATP-cycle, SDK society.py, SDK federation/role, JSON shapes, MCP+R6, did:web4/EUDI fresh-sister) → dedup → per-finding refute-by-default adversarial verification (62 agents total, workflow `wf_f9e49980-7cc`). Raw 53 → 52 deduped → 48 confirmed / 4 refuted → **28 distinct findings** after LEAD consolidation of cross-lens overlaps (multiple lenses independently confirmed the same defect clusters — convergence noted per finding). LEAD spot-re-verified the load-bearing anchors of B1, B8, B12, B26 directly.

Severity profile: **2 HIGH / 18 MEDIUM / 5 LOW / 3 INFO**. Class profile: **19 autonomous-actionable / 3 design-Q / 6 cross-track**.

### HIGH

#### C50-B1 — §1.2.2's "canonical enumeration" claim (added by #252) omits SAL §3.4's MUST-store record classes — HIGH, autonomous-actionable, remediation-introduced

L39 (added by #252/M2) declares §4.2.1 "the canonical enumeration of recorded event types and their minimum field-sets". SAL §3.4 (L107–111) MUSTs the society ledger to store **Birth Certificates, role pairings, delegations, law dataset digests, witness attestations, and auditor adjustments** — none of which appear in §4.2.1's five event types. The "canonical" claim overclaims: an implementer treating §4.2.1 as exhaustive ships a ledger that cannot satisfy SAL §3.4. Wrinkle: SAL §3.4 also MUST-stores *witness attestations*, which #252/M2 deliberately removed from §1.2.2's list as "participants, not events" — defensible for per-entry witnessing but unreconciled against SAL's storage list. Fix shape (C51): scope L39's claim (e.g. "canonical enumeration of *society-lifecycle* event types; SAL §3.4 defines additional SAL record classes the ledger MUST store") or extend the taxonomy; reconcile the witness-attestation framing with SAL §3.4 explicitly.

#### C50-B2 — §1.2.2's universal per-entry `witnesses` claim contradicted by §4.2.1's own canonical field-sets: law_change and economic_event have NO `witnesses` (and no `timestamp`) — HIGH, autonomous-actionable, remediation-introduced (4 lenses converged)

L39 (added by #252): "Witnesses participate in every recorded event via the per-entry `witnesses` field". But the §4.2.1 field-sets L39 itself declares canonical omit `witnesses` from law_change (L270–277: type, action, law_id, change_description, voting_record, effective_date) and economic_event (L283–289: type, action, amount, token_type, recipient_lct, purpose). Both blocks also lack an entry `timestamp` (block 2 has only `effective_date`, which for a `propose` action is not recording time; block 3 has no time field at all) — undermining §4.2.2's provenance model. Citizenship (L263), metabolic (L303), formation (L317) all carry both fields, so this is within-section inconsistency, not uniform minimalism — and the spec demonstrably annotates intentional omissions elsewhere (L248 participatory `validators`). Sister-spec sharpening: SAL §5.4 requires witness **co-signed ledger entries for SAL-critical events** (law updates are `sal.law.update` events per SAL §3.4) — so spec-conformant implementations ship unwitnessed law-change and treasury events in direct conflict with SAL. §4.2.2 additionally uses `witnessed_by` (L353), not the `witnesses` name L39 declares (see C50-B23). Fix shape (C51): add `witnesses` + `timestamp` to blocks 2–3.

### MEDIUM — autonomous-actionable

#### C50-B3 — Citizenship event vocabulary three-way split; §2.3's recorded statuses APPLIED/PROVISIONAL/TERMINATED have no producing action in the canonical enum (4 lenses converged)

L34 (§1.2.2): "join/leave/suspend/reinstate". L260 (§4.2.1, canonical): `grant|revoke|suspend|reinstate`. §2.3/L130: recorded statuses include PROVISIONAL and TERMINATED, and L130 (itself the C22-H3 remediation note) asserts Provisional and Termination are *recorded* status transitions — yet no canonical action expresses a provisional grant or an application, and `revoke` vs `Termination` must be guessed. PROVISIONAL is unexpressable in the canonical format. Cross-track facets (recorded under §C, not autonomously fixable here): SDK emits `terminate` not `revoke` (society.py:462–559); society-roles.md §2.5 Administrator uses `admit/exit` (a fourth verb set). C51 spec-side: harmonize L34 to the canonical enum and extend the enum (or add a mapping note) covering apply/provisional-grant/terminate.

#### C50-B4 — §2.4 and §4.2.1 block 1: two incompatible canonical shapes for the same citizenship-grant record (3 lenses converged)

§2.4 (L134–145): `event_type: "citizenship_granted"` (fused type+action, past tense), `witness_lcts`, int timestamp `1737142857`, `status`, no `action`, no `law_reference`. §4.2.1 block 1 (L257–266): `type: "citizenship_event"` + `action` enum + `witnesses` + `law_reference`, string timestamp. L39 declares §4.2.1 canonical, making §2.4's own record non-conformant to it. The layer-separation defense (state record vs ledger event) fails: §2.4's JSON leads with `event_type` + `timestamp`, presenting as an event, yet matches neither the canonical event shape nor the SDK state record (`CitizenshipRecord` has no `event_type`, uses `granted_at`/ISO-8601 — federation.py:116–137). Distinct from carry-M3 (spec-vs-SDK naming) — this is spec-internal on different keys. C51: reconcile §2.4 to the canonical shape or label it explicitly as the *state-record* projection with field mapping.

#### C50-B5 — §4.2.1's five canonical blocks use two different envelope schemas — remediation-introduced drift

Blocks 4–5 (L296–319, added by #252 "matching the SDK shape") use `{type, action, data{…}, witnesses, timestamp}` mirroring SDK LedgerEntry (society.py:110–115). Blocks 1–3 are flat with payload fields top-level and no `data{}`. An implementer cannot derive a uniform LedgerEntry schema from the canonical enumeration — half conforms to the SDK envelope, half does not. C51: normalize all five blocks to one envelope (the SDK-shaped one, per BC#14 spirit).

#### C50-B6 — §6.3 assigns "Participatory (distributed)" to the apex Global Web4 Society, contradicting §4.1.3's parent-delegation definition

§4.1.3 (L233–248): participatory = participates in **parent** society ledger, parent consensus, required `parent_ledger`, "validation authority is delegated to the parent" (L248, itself the C22-L1 addition). §6.3 (L417–421): the apex society — "Citizens: All Web4 societies (fractal)", no possible parent — is labeled "Ledger: Participatory (distributed)". The §4.1.3 JSON shape literally cannot represent the spec's own flagship example; "participatory" is being used to mean "distributed/public", a different concept. (§5.2 L389's "Confined → Witnessed → Participatory" growth path is a trimmed facet — reconcilable under a federation reading, recorded here as context.) C51: relabel §6.3 (e.g. Witnessed/distributed or a federated-consensus description) or define a fourth type.

#### C50-B7 — #252 narrowed economic_event `token_type` from `ATP|ADP` to `ATP`, contradicting §1.1/§1.2.3's ATP/ADP pool — remediation-introduced; couples carry-M5 (2 lenses converged)

L286 now `"token_type": "ATP"` (pre-#252: `"ATP|ADP"`). §1.1 L16 ("Shared economy (ATP/ADP token pool)") and §1.2.3 L42–44 ("Society-managed ATP/ADP token pool… Initial ADP allocation (can be zero)") were untouched. Per atp-adp-cycle.md §2.1, societies mint in the ADP state — so the §1.2.3-mandated initial ADP allocation is unrecordable under the ATP-only enum. The #252 commit message shows this was deliberate ("treasury is ATP-only per SDK… also resolves spec-side half of M5") — but C22-M5 was explicitly classified design-Q/cross-track ("not autonomous within an audit-only PR") with the audit judging "spec is correct per cycle semantics"; the remediation unilaterally took the opposite (SDK-aligned) side without adding the §1.2.3 cycle-layer clarification that option required. C51: either restore `ATP|ADP` at L286 or add the §1.2.3 clarification — coherently with however the operator resolves M5.

#### C50-B8 — §1.2.5 mischaracterizes SAL §3.1's Quorum Policy — remediation-introduced, same paragraph as flagship C50-R1

L59 characterizes the Quorum Policy as "binding that authority to a specified governance mechanism" / "a verifiable decision rule". SAL L74 defines it as "**witness/attestation requirements per action type**", defined by the Law Oracle (SAL §5.4 L197: "Quorum policy defined by **Law Oracle**"). It is a witnessing-requirements table, not an authority-binding decision rule. Since C51 must rewrite §1.2.5 for C50-R1 anyway, fold this in: characterize the Quorum Policy per SAL L74.

#### C50-B9 — §5.1 "2 entities" bootstrap minimum vs ISP/society-roles solo-founder genesis

§5.1 L380 ("2 entities agreeing to form society") and §1.3 are silent on the solo-founder path that ISP §2.1 genesis and §6.3 ("society-of-one for bootstrap purposes") plus society-roles.md §2 L51 ("a solo founder fills all seven") explicitly support; §1.3 also omits ISP §2.1's genesis SHALLs (witness quorum etc.). C51: align §5.1/§1.3 prose with the already-settled corpus position.

#### C50-B10 — Canonical event enumeration has no event type for ISP §5's SHALL-recorded secession/dissolution events

ISP §5 (L275, L287, L299–304) SHALL-requires recording constituent secession and federation dissolution; §4.2.1's formation enum (L312: `genesis|bootstrap|operational|incorporate_child|incorporated_by`) is join-only. C51: extend the formation action enum (or add a sixth event type) mirroring ISP §5 vocabulary; SDK counterpart recorded cross-track (§C).

#### C50-B11 — L292 layer-separation note assigns *charging* to the R6 layer; atp-adp-cycle.md ties only *discharge* to R6 — remediation-introduced

L292 (added by #252/H2): "ATP-cycle state transitions (charge / discharge) operate at the R6/cycle layer… recorded separately on R6 transactions". atp-adp-cycle.md ties discharge to R6 transactions (L106–107) but records charging as a standalone value-creation/pool event (L126; cross-society pool-level charge/discharge L475–476, L585) — not "on R6 transactions". C51: correct L292 to route discharge to R6 and charge to the value-creation event per the cycle spec.

#### C50-B12 — §7.1 mis-cites mcp-protocol.md §7.4 as home of "reputation envelopes" — remediation-introduced

L433 (bullet expanded by #252/M1): "beyond `mcp-protocol.md §7.4`'s reputation envelopes". mcp-protocol.md §7.4 (L404) is the **Cross-Society LCT Envelope** (context headers + atp_settlement) — zero reputation content; the signed Reputation envelope lives in §7.3 (L402) and §7.5 (L470, L487). Structurally identical mis-cite class to C50-R1, in a different #252 hunk. The lead sentence at L429 routes correctly; only the pin-cite is wrong. C51: cite §7.3/§7.5.

### MEDIUM — design-Q

#### C50-B13 — "Law Oracle" name collision: codified-rules structure (§1.2.1) vs base-mandatory publisher role (SAL / society-roles §2.2) (2 lenses converged)

§1.2.1 L23–24 defines Law Oracle as "Codified rules governing entity behavior" (the corpus juris). SAL (L18, L152) and society-roles.md §2.2 (L71–88: "Publishes machine-readable laws… the corpus juris itself, not the lawyer" — note society-roles' own gloss says the *analogue* is the corpus, but the role is the publisher entity) bind the same name to a role-bearing LCT. The target's own §1.2.5 L59 then treats §1.2.1's Law Oracle as a role-bearing element. No Treasury/Treasurer-style structure-vs-role disambiguation exists for this pair. Operator decision: rename one side (e.g. "Law Corpus" vs "Law Oracle role") or add normative disambiguation. → operator DESIGN-Q bundle.

#### C50-B14 — Citizenship revocability: §2.3 Termination/revoke vs SAL §5.1 "pairing… cannot be revoked" (2 lenses converged)

§2.3 (L120–128) + L260 `revoke` mandate a termination lifecycle; SAL §5.1 (L180–183) declares the Citizen pairing permanent and irrevocable. Neither doc carves out genesis-vs-subsequent or pairing-vs-status. The SDK implements both and self-contradicts (federation.py:8–9 docstring claims immutability; terminate_citizen at :565–568, :625–633 permanently ends it). Likely resolution shape (operator's): pairing is permanent as *historical fact*, status is revocable — but that needs normative wording on both sides. → operator DESIGN-Q bundle.

#### C50-B15 — Law inheritance model conflict: §3.2.1 optional + no-contradiction vs SAL default-on + conditioned child overrides

§3.2.1 (L166–169): inheritance MAY (set at incorporation); "Local laws can extend but not contradict inherited laws". SAL (L127–135): inheritance default-on; child norms MAY override conditionally and rank above parent norms in precedence. Mutually incompatible conflict-resolution models. → operator DESIGN-Q bundle. (SDK facet recorded cross-track: C50-B19.)

### MEDIUM — cross-track

#### C50-B16 — SDK ledger-conformance bundle: canonical MUST field-sets and amendment machinery unimplemented (3 raw findings consolidated)

(a) SDK never records §4.2.1's MUST minimum fields `law_reference`, `change_description`, `voting_record`, `effective_date`, `recipient_lct` (society.py:463, :656–661, :690–694). (b) §4.2.2's amendment wire-shape (`amendment_type`, `reason`, `law_authorization`, `status: "superseded"`) has no SDK counterpart; `SocietyLedger.amend()` (society.py:155–181) is not law-driven. (c) `create_society` bypasses three MUST-record categories — founder citizenship grants, initial-law ratification, and seed deposit never hit the ledger (society.py:332–414). SDK-track fixes; surface at SDK's next pass.

#### C50-B17 — §2.3 lifecycle vs SDK `_CITIZENSHIP_TRANSITIONS`: Provisional dead-end; Termination only via Suspension

federation.py:102–108's graph cannot express §2.3's Provisional→Active progression or direct Active→Termination. Which side is right is a design choice → cross-track (SDK or spec at operator's pick).

#### C50-B18 — §3.1/§3.2.2 "societies are citizens of other societies" has no SDK surface: fractal tree fully disjoint from citizenship machinery

federation.py:526–529 + society.py:773–815: incorporation creates parent/child links but never a CitizenshipRecord; child societies are never citizens. SDK-track.

#### C50-B19 — SDK `merge_law`/`effective_law` silently lets child law override parent with no conflict check, contradicting §3.2.1's no-contradiction rule

federation.py:389–416, :535–553; default behavior discards parent law entirely. SDK-track (couples B15's design-Q — implement whichever model the operator picks).

#### C50-B20 — LCT identifier examples now also conflict with newly-normative did:web4 UUID `lct-id` — fresh delta to the C33 id-scheme bundle

Target examples (`lct-agent-alice-12345` L137–140, `citizen_lct_1` L213) match neither `lct:web4:mb32:` (LCT spec L64/L260, startswith-check L594) nor did:web4's RFC 4122 UUID `lct-id` (did-web4-method.md L38–46, normative since `391e7ade`; web4-core did.rs:27–42 parses UUID-only). did:web4 adds a *third* mutually-incompatible format requirement post-dating C33. → joins operator id-scheme DESIGN-Q (C33 bundle) as new evidence; data-formats.md §6.2 deferral note remains the normative home.

### LOW

#### C50-B21 — "Minimum viable" term collision: §1.2.5's seven-role operational minimum vs §5.1's 2-entity conceptual minimum — autonomous-actionable

L60–62 binds "minimum viable" (via `validate_minimum_viable`) to the operational/role-structural bar; §5.1 L377–383 uses "Minimum viable society" for the 2-entity bootstrap sketch. C51: qualify §5.1's heading/prose (e.g. "minimal bootstrap example (conceptual minimum, §1.2)").

#### C50-B22 — §4.3 example "Alice owns 100 ATP" uses ownership/balance semantics contradicting ATP's society-managed non-accumulable model — autonomous-actionable

L366–370 vs atp-adp-cycle.md L24–26, L33, L287–294 (allocation, not ownership; anti-hoarding). Also sits one subsection after the spec's own allocate/reclaim framing. C51: rewrite the example in allocation vocabulary ("Alice's allocation is 100 ATP…").

#### C50-B23 — Field-name synonym pairs inside §4.2: `law_reference` vs `law_authorization`; `witnesses` vs `witnessed_by` — autonomous-actionable

L264 vs L344; L263/303/317 vs L353. Implementer modeling a shared envelope must guess rename-vs-distinct. C51: pick one name per slot (suggest `law_reference`, `witnesses` per L39's declaration).

#### C50-B24 — Mint and slash events have no home in the deposit|allocate|reclaim taxonomy and aren't covered by the L292 carve-out — autonomous-actionable (2 raw consolidated)

atp-adp-cycle.md §2.1 TokenMinting (L48–66, witnessed) and §2.4 slashing (L181, L206, L211–215: supply destroyed, "recorded on the ledger") are ledger-recorded pool-supply events fitting neither bucket; minting creates new ADP (not a deposit of existing tokens), slashing destroys supply (not a reclaim). "deposit" appears nowhere in atp-adp-cycle.md. C51: extend the economic action vocabulary (`mint`, `slash`) or add an explicit mapping note. (Couples carry-C34-M2 slashing-authority for the *who*; this is the *where-recorded* gap.) SDK counterpart cross-track.

#### C50-B25 — SDK dual role taxonomies: federation.py `RoleType` (5 values) cannot represent 5 of the 7 base-mandatory roles `SocietyRole` (role.py) defines — cross-track

federation.py:78–86 vs role.py:43–126. SDK-track consolidation.

### INFO

#### C50-B26 — §1.2.5 heading level `###` while siblings §1.2.1–§1.2.4 are `####` — remediation-introduced hygiene, autonomous-actionable

L55 vs L23/31/41/48: §1.2.5 renders as a sibling of §1.2, not a child. C51: demote to `####` (and renumber the TOC if any).

#### C50-B27 — §7.2/§7.3 "Future Considerations" not updated alongside remediated §7.1 — autonomous-actionable

Asset division, citizenship migration on exit, and third-party mediation are now partially specified by ISP §5 (L174–179, L283–306) and society-roles.md §3 (Mediator); §7.2/§7.3 (L435–443) retain pure-future framing — the same defect class C22-M1 fixed for §7.1. C51: add the same routing note.

#### C50-B28 — §1.2.4 society-LCT purposes lack cross-ref to did:web4 as the normative interop face — autonomous-actionable

§1.2.4 (L48–53) cites the tensor spec but not did-web4-method.md (L17–25, normative since 2026-06-11 — a timing artifact, target last touched 2026-05-30). C51: add one cross-ref line under "Enables inter-society relationships".

### Refuted in verification (transparency)

Four findings were killed by refute-by-default verification: (1) genesis-without-Birth-Certificate vs SAL §2.1 — dissolved by LCT spec §3.2 "Self-Issued LCT (Bootstrap)" carve-out; (2) §6.3 Global Society vs ISP anti-hierarchy — dissolved by ISP §1.2/§1.3 overlay-by-consent language (cross-doc overcall pattern); (3) "minimum viable" collision with ISP §6 — entangled double-count of flagship C50-R1; (4) §1.3 phase-attribution vs SDK atomic creation — ledger entries ARE phase-attributed; in-memory enum transient has no behavioral surface.

---

## §C — Carries (record-only; NO self-resolution)

- **carry-C39/C25-H1 (7-role home)**: SURFACED as flagship C50-R1. Citation fix = C51 autonomous; the deeper question (should ISP normatively reference the role list at federation level?) remains in the operator DESIGN-Q bundle.
- **carry-NEW-K (§4.2.1 `_event`-suffix)**: CONFIRMED and sharpened by §B sweep — #252 added blocks 4–5 with SDK-bare type strings (`metabolic`, `formation`) while leaving `citizenship_event`/`economic_event` suffixed (L259, L283); SDK enum is all-bare (society.py:92–96). Half-harmonized. Recommend C51 folds this in as autonomous per BC#14 (SDK-exact strings); spec-vs-SDK facet stays with the carry.
- **C22-M6 (rights/obligations 4-way defaults)**: OPEN, unchanged — operator DESIGN-Q bundle.
- **C22-I2 (status label "Foundational Concept" vs MUST)**: OPEN, unchanged (L5 intact). DESIGN-Q.
- **C22-M3 (snake/camel + `society_lct`/`witness_lcts` vs SDK)**: OPEN; §B adds intra-file facets (B4) and a did:web4 facet (B20). Cluster unchanged in ownership.
- **C22-M4 (§5.3 aspirational trust inputs)**: OPEN, unchanged — subordinate-ontology/SDK cluster.
- **C22-M5 (Treasury ADP gap)**: OPEN — and now COUPLED with C50-B7: #252 unilaterally took the SDK-aligned side at L286 while M5 was still an open design-Q. The operator's M5 decision now has a spec-internal contradiction waiting on it.
- **C22-I3 (test-vector coverage)**: OPEN, unchanged.
- **C22-I4 (zero Society predicates in core ontology)**: OPEN, unchanged — subordinate-ontology cluster (7 audits, past operator-engagement threshold since C20).
- **NEW cross-track from §B**: B16–B19 (SDK ledger-conformance + lifecycle-graph + fractal-citizenship + merge_law) join the SDK-track backlog; B20 joins the C33 id-scheme bundle; B25 joins SDK role-taxonomy consolidation.
- **NEW design-Q from §B**: B13 (Law Oracle name collision), B14 (revocability vs SAL §5.1), B15 (inheritance model vs SAL) join the operator DESIGN-Q bundle.

---

## §D — Method note (for the audit ledger)

The LEAD-direct §A hunk-walk validated each #252 hunk *internally* (strings vs SDK, dates, JSON shape) and found only the flagship. The multi-agent §B sweep found eight more #252-introduced defects — all of the class "inserted prose contradicts a *different* section or sister spec". Lesson: a remediation-regression sweep must check each inserted claim against (a) the sections it cites, (b) the sections that cite it, and (c) sister specs sharing its vocabulary — internal-accuracy checking alone systematically misses this class. This extends the C36 lesson (delta re-audits must check remediation-introduced defects) with a *how*: the check must be cross-referential, not hunk-local. Also: 9 introduced defects from one remediation PR suggests remediation PRs above a size threshold (+58 lines of new normative prose) warrant their own mini-audit before merge.

---

## Verdict

- **§A**: 7/8 HELD, 1 REGRESSED (C50-R1). Clean streak (C40/C42/C44/C46/C48) **BREAKS**.
- **§B**: 28 distinct findings (2 HIGH / 18 MEDIUM / 5 LOW / 3 INFO; 19 autonomous / 3 design-Q / 6 cross-track). Nine total #252-introduced defects (R1 + B1, B2, B5, B7, B8, B11, B12, B26).
- **Next**: C51 remediation turn takes the 19 autonomous findings (may sub-batch — the §1.2.5 rewrite [R1+B8], the §4.2.1 envelope/witnesses/vocabulary cluster [B1–B5, B10, B24, carry-NEW-K], and the singles [B6, B7, B9, B11, B12, B21–B23, B26–B28] are natural cohesion groups); design-Q and cross-track items routed per §C.
