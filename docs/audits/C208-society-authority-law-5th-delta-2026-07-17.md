# C208: web4-society-authority-law.md (SAL) — Fifth Delta Re-Audit

**Date**: 2026-07-17
**Auditor**: Autonomous session (legion-web4-20260717-060036)
**Document**: `web4-standard/core-spec/web4-society-authority-law.md` (SAL, 419 lines, blob `0849ebbe`)
**Prior audit**: C170 (`docs/audits/C170-society-authority-law-4th-delta-2026-07-10.md`, merged, #503-era)
**Prior remediation**: C59 / PR #330 (`0d756773`).

**Lineage**: C16 → C21 → C23 → C58 → C98 → C134 → C170 → **C208**.

**Framing**: **First NON-frozen SAL delta since C59.** SAL was byte-frozen from `0d756773` through the C170 snapshot; it MOVED exactly once since, via **PR #523** (`1354e4c2`, "W4IP Phase 3 (N2): Effector Role — first-class registration across entity-types, society-roles, and SAL"), blob `02ab3a42`→`0849ebbe`. Per the frozen-target discipline this turn inverts: §A verifies the C59 remediation now survives an *additive* mover (not a frozen no-op), and §B is a **targeted regression-check of the #523 Effector mover** per [[feedback_remediation_introduced_regression]] — read the mover's rationale, verify every new citation resolves, refute-by-default on the flagship, then sweep the moving corpus window.

**The delta (ground truth)**: `git diff 0d756773..HEAD -- <SAL>` = exactly two purely-additive hunks (no deletions, no line moves):
1. **NEW §5.6 Effector** (8 bullets) inserted after the §5.5 Auditor `audit_adjust` code block (L233–241).
2. **§7.1.1** header `(Witness/Auditor/Ledger)`→`(Witness/Auditor/Effector/Ledger)` + two NEW required triples: `web4:hasEffector` (society → effector role, where the role is defined) and `web4:respondedBy` (entity → effector enactment).

SAL grew 408→419 (+11). No C59-remediated anchor is within either hunk region.

**Counts**:
- **§A**: C59-rem **10/10 HELD** (the mover is purely additive; all remediated anchors byte-unchanged). 0 regressed, 0 encoding artifacts (`grep -nE '&#|&amp;|â€' <SAL>` = empty), each new triple appears exactly once. Mirror-movement sweep run. All standing carries re-verified OPEN.
- **§B**: **0 net-new defects on SAL — 4th consecutive fully-clean SAL delta (C98 + C134 + C170 + C208), and the first to pass a regression-check rather than inherit a freeze.** The #523 Effector mover is **regression-CLEAN**: all three §5.6 citations + both §7.1.1 triples resolve exactly, and §5.6 is verbatim-consistent with its two sister registrations (`entity-types.md §4.8`, `society-roles.md` Effector). 1 positive impl convergence (web4-policy `Response` enum), 3 carry facets (all route; none net-new), 1 considered-and-refuted INFO (§5 header).
- **§C**: **ONE autonomous-actionable item — C170-N1** (`CLAUDE.md:48` glossary path `02-glossary`→`13-glossary`; carried unremediated since C170, the C171 slot never applied it). Guidance file, no spec mutation, no operator gate → **applied this turn**. All DESIGN-Q / cross-track carries STAND, route to the standing operator memo. **Zero SAL/spec mutation.**

---

## §A. Prior-Finding Verification (live evidence at moved HEAD `0849ebbe`)

### A.1 — C59 remediation #330 HELD (10/10) against an additive mover

Unlike C98/C134/C170 (which verified against a byte-frozen SAL), this turn verifies against a MOVED blob. The verification is nonetheless clean because **#523 is purely additive**: `git diff --stat` shows only insertions in two regions (the §5.5→§5.6 boundary at L230, and the §7.1.1 triple list at L270). Every one of the 10 C59-remediated sites sits outside both hunks and is byte-identical to the HEAD at which C98/C134/C170 confirmed them present-and-unregressed. Regression sweeps: `grep -nE '&#|&amp;|â€|Â '` → empty; each new triple (`web4:hasEffector`, `web4:respondedBy`) grep-count = 1 (no duplication/malformation). The C98 site-table stands verbatim.

### A.2 — Mirror / carry-section movement since C170

The #523 diff touched **only §5.6 (new) and §7.1.1**. Every carry-bearing SAL section audited in prior deltas — **§3.3** (delegation), **§3.5** (law-inheritance / B15), **§3.6** (dormant-defer vs new_citizen wake / B15 · C58-B10), **§7.1**, **§7.2** (namespace / C16-M8·B6) — is **byte-frozen since C170**. Their carries therefore stand trivially on the SAL side; the live sides were re-checked:

| Carry | SAL side | Live side re-check | Verdict |
|---|---|---|---|
| **C58-B10 / B15** (§3.6 dormant-defer ↔ SMS §4.1 new_citizen wake) | §3.6 frozen | SOCIETY_METABOLIC_STATES §4.1 confirmed clean at C206 (#535); two-sided contradiction intact | **STANDS — do NOT re-open** (dual-anchored; C170/C206 both logged it two-sided-open) |
| **B15** (law-composition: §3.5 child-override-ranked vs SOCIETY_SPEC §3.2.1 extend-not-contradict vs role-extension strictest-wins) | §3.5 frozen | third-model site `role-extension-schema.md §2.1` unchanged since C170 | **STANDS** — three competing models, one operator answer settles all |
| **C16-M8 / B6** (§7.2 `ontology#` hash vs `hub-law.ttl` `ontology/` slash) | §7.2 frozen | `hub-law.ttl` still slash; `role-extension.ttl` still hash; still no `sal-ontology.ttl` | **STANDS** — see §B.2 for the new-triple facet |
| **C33** (`lct:web4:` example strings, typed-path vs key-derived) | §2.2/§5.5/§14 frozen | `lct.rs:190` key-derived pick unchanged | **STANDS** |
| **C23-H1** (birth-cert 3-way) | §2.3 frozen | no new birth-cert struct in-window | **STANDS** |
| all other C16/C23/C58 design-Q + cross-track | frozen | referents frozen | **STAND** per the C170 §A.3 table |

Zero mirror drift on the pre-existing surface; all C98/C134/C170 mirror-convergence results stand.

---

## §B. #523 Effector-Mover Regression-Check + Moving-Window Adjudication

**Method**: the mover's *rationale* was read first (per the C140 remediated-mover rule): #523 is the normative expression of W4IP N2, registering the Effector — the Auditor's response-side sibling — as a first-class role across three surfaces (SAL §5.6, `entity-types.md §4.8`, `society-roles.md`). Each new citation was resolved to its target; the flagship contradiction candidate was given the full refute-by-default treatment; then the corpus window (web4-policy Rust crate, ontology `.ttl` set) was swept.

### B.1 — §5.6 Effector + §7.1.1 triples: all citations resolve exactly; tri-file registration mutually consistent — 0 net-new

Every citation SAL §5.6 introduces was resolved at live HEAD and **resolves exactly**:

| SAL §5.6 / §7.1.1 claim | Cited target | Resolution |
|---|---|---|
| response vocabulary `notice \| quarantine \| correct \| rehabilitate` + kinetic class | `hub-law-schema.md` "Response vocabulary" (L148–189) | **EXACT** — table L185–189 defines exactly those four graded rungs + kinetic class `slash\|suspend\|revoke\|terminate\|halt` (L189) |
| gate **RWOA + S + V + F** | `hub-law-schema.md` §"Gating — RWOA + S + V + F" (L212) | **EXACT** — F-a forfeiture predicate (L217), F-b proportionality bound (L224); base invariant RWOA+S+V at §0 L14, Effector adds F |
| recognition evidence = Coercive/Extractive Behavior Rules deltas | `reputation-computation.md §4` | **EXACT** — "Coercive/Extractive Behavior Rules" heading at L339; L387 "recognition-evidence that any response to a coercive act must" bind |
| kinetic rungs are **parse-don't-enact** | `hub-law-schema.md` L206 | **EXACT** — "validator MUST accept … engine MUST NOT enact them (law-inert)" |
| quarantine reversibility clause ("a containment that cannot be lifted is not `quarantine` … MUST be declared under the kinetic class") | `hub-law-schema.md` L186 | **VERBATIM-ALIGNED** — L186 states the identical rule |
| role shape | `entity-types.md §4.8` (L399) | **EXACT** — §4.8 Effector Role, same vocabulary, same RWOA+S+V+F gate (F-a/F-b), same parse-don't-enact, Effector Enactment Request JSON |
| delegation | SAL §3.3 (`web4:delegatesTo`) | **CONSISTENT** — §3.3 is the generic authority→sub-authority delegation surface; Effector is scope-limited authority |

The **third registration surface**, `society-roles.md` "Effector" (L234–236), independently cross-references all three of the above (`hub-law-schema.md` vocab, `entity-types.md §4.8` shape, `web4-society-authority-law.md §5.6` registration) and states the same gate (`RWOA+S+V+F`) and the same recognition/response/kinetic model. The three surfaces are mutually consistent with no divergence — the registration is **coherent across the tri-file mover**. `society-roles.md` L378 also updates its SAL-scope description to "Citizen, Authority, Law Oracle, Witness, Auditor, **and Effector**".

**Flagship refutation (§5.6 vs SAL's own accountability surface).** The strongest net-new candidate: §5.6 imports a *fourth* gate clause (**F**, forfeiture) that SAL never defines elsewhere, potentially conflicting with SAL's RWOA+S+V framing. **REFUTED**: (a) SAL does not define RWOA+S+V anywhere as an internal spec term — §5.6 is SAL's *first* citation of the accountability invariant, sourced entirely from `hub-law-schema.md`, so there is no SAL-internal statement for F to contradict; (b) F is the deliberate W4IP N2 extension ("inheritance-plus-F", F distinct from R/W by design — the load-bearing claim the 0d thread asked to attack), documented as F-a/F-b in both `hub-law-schema.md` L212 and `entity-types.md §4.8`; (c) §5.6's own text closes the autoimmunity gap ("an Effector acting without evidence fails its own gate") consistent with entity-types §4.8. No MUST is contradicted. Candidate dies.

### B.2 — §7.1.1 new triples: ontology absence is standing (C16-M8/B6 facet), conditional clause is correct — 0 net-new

1. **Ontology-absence facet (C16-M8/B6 / M7-class — NOT net-new).** Grep of the entire canonical `web4-standard/ontology/` set for the SAL §7.1/§7.1.1 triple family (`hasWitness`, `hasAuditor`, `adjustedBy`, `recordsOn`, `attestedBy`, `hasLawOracle`, `hasAuthority`, `memberOf`, and now `hasEffector`, `respondedBy`) returns **empty** — the SAL triple vocabulary has *never* been in the canonical ontology (no `sal-ontology.ttl`; C170 §A.3 already ledgered this absence). #523 widened the absent set by 2 triples but introduced **no new absence class**. Facet recorded on the standing carry; NOT net-new; route to the ontology-track/operator, do NOT self-apply.
2. **Conditional-clause correctness (B7 facet — not a defect).** `web4:hasEffector (society → effector role, where the role is defined)` carries an inline conditional ("where the role is defined") that `hasWitness`/`hasAuditor` lack. This is the *correct* modeling — Effector is not one of the 7 base-mandatory roles (`society-roles.md` tiering; it is a context/special-powers role), so it is conditionally required. Notably this is the very conditionality carry **B7** argues `hasWitness`/`hasAuditor` should adopt (their unconditional "MUST maintain" listing vs the tiered/context-mandatory model). The new triple thus *demonstrates* the pattern B7 wants — a strengthening data point on B7, not a defect on the Effector triple. Facet recorded; NOT net-new.

### B.3 — Corpus-window impl mirror: web4-policy `Response` enum — POSITIVE convergence + a role-side lag note

`web4-policy/src/lib.rs` defines `pub enum Response` with **exactly** the ratified vocabulary — `Notice`, `Quarantine`, `Correct`, `Rehabilitate` (L170–179) + kinetic `Slash|Suspend|Revoke|Terminate|Halt` (L180–189) — plus `is_kinetic()`, `consequence_class()` (Notice/Quarantine/Rehabilitate→Reversible, Correct→Costly, matching `hub-law-schema.md` L185–189), and an explicit **parse-don't-enact** doc-contract ("valid to PARSE but law-inert … nothing … may enact them"), with tests asserting all of it (L885–900). This is a **faithful deployment of the response vocabulary SAL §5.6 cites** — a positive convergence for the vocabulary half of the Effector.

**Cross-track note (route, informative, NOT a spec defect):** web4-policy mirrors the *vocabulary* only. It has no `Effector` role struct, no RWOA+S+V+F gate, no Enactment Transcript, and no `hasEffector`/`respondedBy` triples. The **role-side** obligations SAL §5.6 adds (Enactment Transcript with the 7 named fields, the F-gate, the immutable-record write, the two RDF triples) have **no impl mirror yet** — expected for a brand-new W4IP role. Routed as impl-lag, not a SAL finding; SAL is the canonical source here and is correct.

### B.4 — Considered-and-refuted INFO: §5 section header

The §5 header reads `## 5. Roles: Citizen, Authority, Oracle` while §5 defines **six** subsections (5.1 Citizen, 5.2 Authority, 5.3 Law Oracle, 5.4 Witness, 5.5 Auditor, 5.6 Effector). Candidate: #523 added §5.6 without refreshing the header. **Refuted as net-new**: (a) snapshot-presence guard — the header already omitted Witness (§5.4) and Auditor (§5.5) at the C170 snapshot `0d756773` (verified via `git show`), so the drift *pre-exists* the window and was never introduced by #523; (b) the header reads as an **archetype summary** (the three foundational role families: Citizen / Authority / Oracle) which the subsections elaborate, not an exhaustive enumeration — a defensible style that survived 6 prior SAL audits unflagged. Logged as INFO only (an eventual editorial header refresh to name all six would be an improvement, but it is neither new nor a normative defect, and belongs to a remediation slot, not this audit turn).

---

## §C. Autonomous / Design-Q / Cross-Track Split

**Autonomous-actionable — ONE item, applied this turn:**
- **C170-N1** (carried unremediated since C170; the C171 slot never applied it — verified `c171bedb` is an unrelated C29 data-formats fix): project **`CLAUDE.md:48`** cites the terminology-protection glossary at `whitepaper/sections/02-glossary/index.md`, a path DELETED by the 2026-07-09 whitepaper rewrite (glossary now at `13-glossary/index.md`). Every session following the terminology-protection instruction dereferenced a dead path. **Fix applied**: `02-glossary`→`13-glossary` (guidance file; no `web4-standard/**` touch; no operator gate; no normative content). Explicitly attributed as its own logical change per the policy-review binding condition. **C170-N1 CLOSED.**

**Carry updates recorded this turn (all route to the standing operator memo; none self-applied):**
- **C16-M8/B6 facet**: SAL §7.1.1 triple family widened by `hasEffector`+`respondedBy`, still 100% absent from canonical ontology (no `sal-ontology.ttl`). Absence class unchanged; not incremented.
- **B7 facet**: new `hasEffector` triple carries the conditional ("where the role is defined") that B7 argues `hasWitness`/`hasAuditor` should adopt — strengthens B7, no re-adjudication.
- **B15 / C58-B10, B15 law-composition, C33, C23-H1**: all SAL-side sections frozen; carries STAND verbatim (do NOT re-open §3.6 dual-anchor — two-sided-open, C206-confirmed on the SMS side).

**Cross-track / positive movements logged (route, no SAL action):**
- web4-policy `Response` enum faithfully deploys the `hub-law-schema.md` response vocabulary SAL §5.6 cites (POSITIVE convergence). Effector *role-side* obligations (transcript, F-gate, triples) have no impl mirror yet (impl-lag, informative).
- §5 header archetype-summary vs 6 subsections: editorial-only, routed to a future remediation slot as an optional header refresh (not a defect).

**Zero SAL / spec mutation this turn.** The only file edit is the C170-N1 guidance fix in `CLAUDE.md`.

---

## §D. Lessons

1. **A purely-additive mover makes the regression-check tractable and the freeze-inheritance honest.** SAL's first move since C59 was two insertions that touched no remediated anchor and no carry-bearing section — so §A's "10/10 HELD" is *earned* by a diff read, not inherited from a freeze, while §B could focus entirely on whether the *new* text is internally and cross-file coherent. The pattern: when a mover is additive, verify the additions resolve and the untouched carries are literally byte-frozen; don't re-run a full finder pass over unchanged prose.
2. **A tri-file first-class registration is its own consistency test.** #523 registered the Effector across SAL §5.6, `entity-types.md §4.8`, and `society-roles.md` simultaneously. The audit's highest-value check was not "does §5.6 contradict SAL" (it doesn't — the flagship F-gate candidate died because SAL had no prior RWOA+S+V statement to contradict) but "do the three registration surfaces agree with each other and with the `hub-law-schema.md` vocabulary they all cite" — and they do, verbatim on the load-bearing clauses (parse-don't-enact, quarantine-reversibility, F-a/F-b).
3. **A new triple can strengthen an old carry by modeling it correctly.** `hasEffector`'s inline "where the role is defined" conditional is exactly the shape carry B7 argues `hasWitness`/`hasAuditor` should have. The window didn't resolve B7 — it gave the operator a worked example, inside the same section, of the conditional pattern B7 wants.
4. **The one actionable defect in a spec-clean window was again a guidance file.** As at C170, SAL and its spec siblings were clean, and the sole autonomous fix lived in `CLAUDE.md`. C170-N1 was *routed* to the C171 slot and then silently dropped (the slot ran an unrelated C29 fix). A "route to the next remediation slot" is not a durable owner — an autonomous-actionable guidance fix small enough to apply in-audit should be applied in-audit (with explicit §C attribution), not deferred to a slot that may never claim it.

---

*End of C208 audit. Zero SAL/spec mutation. C170-N1 CLOSED (one-line guidance fix in `CLAUDE.md`). #523 Effector mover = REGRESSION-CLEAN; 4th consecutive fully-clean SAL delta. Next rotation target: +2 from SAL per the fixed order → **C210 = LCT-linked-context-token.md** (lineage C9→C24→C60→C100→C135→C172→C210). SAL's next delta re-checks whether the Effector role acquires an impl mirror (web4-policy role-side / SDK) and whether `sal-ontology.ttl` ever lands.*
