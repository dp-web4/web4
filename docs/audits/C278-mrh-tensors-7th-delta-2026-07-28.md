# C278 Audit: `mrh-tensors.md` Seventh Delta Re-Audit

**Date**: 2026-07-28
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn, slot `web4-20260728-180011`
**Document**: `web4-standard/core-spec/mrh-tensors.md` (422 lines; **byte-frozen since C163 `b8740803`**, 2026-07-09 — blob `581e9b48` at HEAD)
**Lineage**: C10 → C40 → C41 (remed, #290) → C90 → C91 (remed, #382 `f0c82118`) → C129 → C130 → C162 (#490) → C163 (remed, #491 `b8740803`) → C200 (#532) → C238 (#558) → **C278** (this 7th delta)
**Method**: §A prior-finding + carry verification re-run at live HEAD, including the mandated re-**test** of C163's §4.2 hunk against `mrh.py` ground truth. §B four lenses: corpus delta (46 commits) / method-carry-v2 authority scan / **the C90 shared-example-data diff of mrh §5's frozen turtle against the `01f410db`-amended `t3v3-ontology.ttl`** / SDK-mirror-consumer gate re-derived at live HEAD. Every surviving candidate handed to an adversarial refuter with instructions to default to refuted; the auditor's own flagship attacked first and hardest.
**Reference materials**: `web4-standard/ontology/{t3v3-ontology.ttl,web4-core-ontology.ttl,role-extension.ttl,hub-law.ttl}`; SDK `web4/{mrh.py,trust.py}`; `web4-core/src/lct.rs`; `t3-v3-tensors.md`; proposals `resilience-to-incomplete-information.md` (#580), `dictionary-as-context-mandatory-role.md` (#579); `docs/PRD_ACTION_EVIDENCE.md`; sibling audit docs C40, C42, C238, C270, C272, C276; rdflib 7.x (scratch venv — see §D-4).

---

## Summary

| | Result |
|---|---|
| **§A** C163 §4.2 hunk (the mandated guard) | **HELD** — re-derived from `mrh.py`: exactly 3 `propagate_*`, all `List[float]`, no 4th, no restored `MRHEdge` param; **0 regression** |
| **§A** byte-freeze | **CONFIRMED** — `mrh-tensors.md` blob `581e9b48`, `mrh.py` blob `dea3fb4a`; `git diff b8740803 HEAD` empty for both |
| **§A** C91/C130 numeric + anchor carries | **HELD** — `:264`/`:325` = `0.92`, zero `0.90`; C130 FRACTAL anchor at `:174` |
| **§A** C238-N1 (D2 numeric, → t3-v3) | **CONSUMED** — C270 retired the numeric facet. Outbound routing closed after 2 deltas |
| **§A** C238-N2 (`edge_type` → D1/web4-core) | **OPEN** — receiving lineage has not acted; `lct.rs` untouched this window |
| **§B** new autonomous **mrh** (class-a) defects | **0** — 7th consecutive clean delta |
| **§B** corpus delta (46 commits) | **CLEAN** for the spec — 0 touch `mrh-tensors.md`/`mrh.py`/`trust.py` |
| **§B** SDK/`web4-core` mirror gate | **EMPTY** — `lct.rs`, `mrh.py`, `trust.py` all untouched. Recorded as empty; no datapoint manufactured (C266 precedent) |
| **§B-N1** (MED, cross-doc, routed) | **`01f410db` silently overturns the ratified C42-M3 resolution and leaves a normative t3-v3 note stating a now-false fact.** mrh is a party but needs **no edit** |
| **§B-N2** (INFO, routed) | `01f410db` = **first post-creation content edit to a `web4:`-core-namespace ontology file, ever**; issue #581's *general* property-extension ask went unanswered while the issue was closed — a dated D1 refresh |
| **§C** flagship as first drafted ("D1's option (a) is now unblocked") | **REFUTED / RESCOPED** — BC-C23-3 constrains the *auditor*, not the operator; nothing was blocked |
| **§C** second candidate (#580 precedent survey omits mrh) | **REFUTED** on two independent grounds — mrh's zeros are *mismatch*, not *absence*; and the charge-class was already routed by C272-N1 |

**Verdict: `mrh-tensors.md` remains byte-stable and correct — 7th consecutive clean delta, zero autonomous net-new mrh defects, zero mutation.** As at C200/C238, the entire yield is in the neighbourhood rather than the 422 frozen lines. This pass's yield is unusually sharp because the window contained the first content edit to a core-namespace ontology file in the project's history, landing ~8 hours before the audit — and that edit falsified a normative note in a *sibling* spec that a ratified C-series finding had put there.

The adversarial pass **changed the outcome twice**: it refuted the auditor's own flagship, refuted the second candidate outright, and surfaced N1 — which the auditor had missed and which is stronger than what it replaced.

---

## §A — Carry, Fix, and Prior-Finding Verification

### The mandated guard — C163's §4.2 hunk re-tested against `mrh.py` (HELD, 0 regression)

Per the standing forward guard, this is a re-**test** against ground truth, not a re-read, and explicitly **not** a re-flag of the C162/C163 §4.2 item.

- `grep -n "^def propagate" mrh.py` → **3**, at `:198` / `:214` / `:228`: `propagate_multiplicative(path_weights, decay_factor=0.7)`, `propagate_probabilistic(path_trusts)`, `propagate_maximal(path_trusts)`. **No 4th.**
- All three consume `List[float]`; **no `MRHEdge`-typed parameter restored**.
- The §4.2 note's three-part enumeration matches ground truth exactly. **HELD, 0 regression.**

### Byte-freeze

- `mrh-tensors.md` blob at HEAD = `581e9b48…`, `mrh.py` blob = `dea3fb4a…` — both byte-identical to the C238 guard values.
- `git diff b8740803 HEAD` empty for both. 46 commits landed since C238 (`68aa0a57`); **zero** touched `mrh-tensors.md`, `mrh.py`, or `trust.py`.

### C91 / C130 numeric + anchor carries

- `:264` `web4:training 0.92`, `:325` `web4:t3Score 0.92`; `grep "0\.90"` → **no match**. **HELD.**
- C130 FRACTAL re-anchor (`Default horizon_depth = 3`) at `:174`. **HELD.**

### Outbound routings from C238 — verified for *consumption*, not assumed

C238-§D-1 established that a routed correction is not closed until the receiving lineage consumes it. Both of C238's routings were re-checked at HEAD:

- **C238-N1** (D2 numeric facet "Surgeon `training` 0.92 vs 0.90", → t3-v3 lineage) — **CONSUMED.** C270 (t3-v3 7th delta, PR #577) retired the D2 numeric facet and verified it dead against `mrh-tensors.md:264`. The correction took two t3-v3 deltas (C230 re-carried it in error; C270 consumed it). **Routing closed.** Do not re-carry.
- **C238-N2** (`web4-core::Mrh` free-string `edge_type` gained `"birth_certificate"`, → D1/D4 + web4-core owners) — **OPEN.** `lct.rs` is untouched in this window, so there is nothing new to say and no evidence the owners acted. Carried forward unchanged.

### Standing DESIGN-Qs

- **D1** (ontology-vocabulary divergence, born C40) — **STILL-OPEN, and now aging under active ontology maintenance.** §B-N2 is a dated refresh; §B′ re-derives the divergence with a stated instrument.
- **D4** (`horizon_depth = 3` default / `MRH_MAX_HOPS = 4` cap / per-LCT `u32`) — three distinct roles per C200-N2(a), not conflicting values. Anchor `trust.py:91` present. Operator-gated, unchanged.
- **X4 / N1(a)** (structural §5-shrink, `:240-369` duplicating t3-v3 §5) — STILL-OPEN, and it is precisely the seam §B-N1 travels along.
- **N4** (`t3Score` vs `trustScore`, folds into D1) — unchanged in substance, **but its instrument was wrong**: see §B′.

---

## §B — New Findings (0 autonomous mrh defects; 2 routed cross-track)

### N1 (MEDIUM, class-b, ROUTED to the t3-v3 lineage + ontology owner) — `01f410db` silently overturns the ratified C42-M3 resolution, leaving a normative sibling note whose factual premise is now false

**The ratified finding.** `docs/audits/C42-t3-v3-tensors-audit-2026-06-09.md:38` records **M3** ("Ontology domain gap — V3Tensor binding properties undefined") as **HELD-REMEDIATED**, resolved by **option (c)**: rather than give V3Tensor its own binding properties, a normative note was added to the spec declaring that V3 *derives* its entity-role context from the co-located T3Tensor.

**The note is live** at `web4-standard/core-spec/t3-v3-tensors.md:428-434`:

> *"**Note on V3 entity-role binding:** The ontology (`t3v3-ontology.ttl`) declares `web4:entity` and `web4:role` with domain `web4:T3Tensor` only. V3 tensors derive their entity-role context from the co-located T3Tensor for the same entity-role pair, rather than carrying independent `web4:entity`/`web4:role` properties. This avoids domain violations in RDF validators while preserving the §1.1 principle that both T3 and V3 are role-contextual."*

**Both halves of that note broke on 2026-07-28, ~8 hours before this audit.** `01f410db` (operator dp-web4, closes #581) added a `web4:Tensor` superclass, made `T3Tensor`/`V3Tensor` `rdfs:subClassOf` it, and **moved `web4:entity` / `web4:role` / `web4:hasDimensionScore` up to `web4:Tensor`**. Machine-verified at HEAD (rdflib, 84 triples):

```
entity            -> rdfs:domain web4:Tensor
role              -> rdfs:domain web4:Tensor
hasDimensionScore -> rdfs:domain web4:Tensor
talent            -> rdfs:domain web4:T3Tensor      (type-specific shorthand, retained)
valuation         -> rdfs:domain web4:V3Tensor      (type-specific shorthand, retained)
observationCount  -> rdfs:domain web4:DimensionScore
```

1. **The factual premise is false.** The ontology no longer declares those properties "with domain `web4:T3Tensor` only."
2. **The design rule is negated.** `01f410db`'s stated reason for the move is that *"a correct projection emits them on V3Tensor nodes too"* — i.e. V3 tensors **do** carry independent `web4:entity`/`web4:role`. That is the direct contradiction of the option-(c) rule the note states.
3. **The note's own justification has evaporated.** It exists to "avoid domain violations in RDF validators"; after the widening there is no domain violation to avoid.

**No one has seen this.** `git log` per-file shows `t3v3-ontology.ttl` has exactly two content commits ever — `bedd3bf8` (2026-02-16) and `01f410db`. `grep -rl "01f410db\|observationCount\|web4:Tensor" docs/` → **empty**: no audit document mentions any of it. C270 (t3-v3 7th delta) predates the commit by four days; the next t3-v3 delta is ~C306. `01f410db` cites neither C42 nor the note.

**Class**: this is the **remediation-introduced-regression** class (born C36) at one hop — a *closed, ratified* finding reopened by a later commit in a different file, where neither side knows about the other.

**Why mrh is a party, and why mrh still needs no edit.** mrh `:248` (§5.1, normative) states: *"RDF triples explicitly bind trust **and value** tensors to role pairings."* mrh sides with `01f410db` and #581; the t3-v3 note sides against both. Because mrh §5 duplicates t3-v3 §5 (standing carry **X4**), this is the same seam X4 names — which is why it surfaced on an mrh pass at all. But **`mrh-tensors.md` contains no such note and asserts nothing falsified by the widening** (see §B′ for the machine-checked widening re-derivation). **Zero mrh mutation.**

**Disposition**: **routed** to the **t3-v3 audit lineage + the ontology owner**, to be adjudicated at ~C306 or sooner if the operator picks it up. The choice is theirs, not the auditor's: either amend/remove the t3-v3 note to match the widened ontology, or state that C42-M3's option (c) still governs the *spec* even though the ontology no longer enforces it. **The auditor must not edit an operator-authored commit's consequences into a ratified sibling spec.** No mrh edit, no ontology edit (BC-C23-3: no autonomous TTL drafting).

### N2 (INFO, class-b, ROUTED to the operator DESIGN-Q memo) — a dated D1 refresh: the first-ever core-namespace ontology edit answered #581's instance and closed the issue with its *general* ask unanswered

Two checkable facts, both new this window.

**(a) `01f410db` is the first post-creation content edit to a `web4:`-core-namespace ontology file in the project's history.** Per-file `git log`: `web4-core-ontology.ttl` → `a37f3011` (creation, 2026-02-22) and **never edited since**; `t3v3-ontology.ttl` → `bedd3bf8` (2026-02-16), then `01f410db`. The three other ontology-directory commits in the last 20 days (`cb788768`/`3fa0dafd` extending `hub-law.ttl` with a `law:Rule` superclass, `4f76f110` adding `role:oracleConsultSet`/`role:oracleWriteSet` *"so descriptors round-trip against the ontology"*, `7201a765` promoting `role-extension.ttl`) all act on **subordinate** namespaces (`law:`, `role:`) — which is exactly the cluster BC-C23-3 names, not the protected `web4:` core.

**(b) Issue #581 asked the general question and got the instance answered.** #581's own text:

> *"The ontology's stated extension mechanism (`subDimensionOf`) covers dimensions, not properties, so any consumer inventing the predicate produces triples that parse, look plausible, and **join with nothing**. **Ask:** add `web4:observationCount` … **or state the property-extension rule if new properties are meant to mint elsewhere**."*

That second clause — *is there a property-extension rule?* — **is D1's entire subject**. `01f410db` answered only the first clause and closed the issue. So the corpus now holds a dated, operator-authored statement that the general rule remains unstated, inside the commit that closed its own issue.

**Why this is a D1 refresh and not a new finding**: D1 (born C40, 2026-06-09, open 49 days) already consolidates "the spec's illustrative Turtle/SPARQL reference a vocabulary the canonical ontology does not define," including the `pairedWith`/`hasRelationship` gaps re-measured in §B′. What is new is the *aging under maintenance* signal: three operator ontology edits in 20 days, **none touching D1's terms**, plus a live implementer (hestia) that hit the identical "joins with nothing" failure mode D1 predicts and had it fixed for one predicate only.

**Disposition**: **routed** to the operator DESIGN-Q memo as a refresh on D1, framed as #581's unanswered general ask — *state the property-extension rule* — not as a request to draft TTL. **No autonomous TTL drafting** (BC-C23-3, operator-engagement-class). Not an mrh defect; no mrh mutation.

---

## §B′ — The three negatives, stated with their instruments

Per [[feedback_enumeration_and_grep_hypotheses]], each count below carries its scope; an unscoped count is a silent-failing hypothesis.

**1. `01f410db`'s own "purely widening" claim — RE-DERIVED and CONFIRMED for mrh.** The commit asserts *"purely widening: a T3Tensor is a Tensor, so nothing well-formed becomes ill-formed."* Not taken on faith (method carry v4). Machine-parsed all **4** ```turtle``` blocks in `mrh-tensors.md` (**52** triples, all parse clean under rdflib):

- Both bearers of `web4:entity` (`:260`, `:269`) are **explicitly** `a web4:T3Tensor` — nothing depends on domain entailment to acquire that type.
- §5.5's SPARQL (`:343`) binds `?tensor a web4:T3Tensor` explicitly.
- §5.3's Python-embedded SPARQL (`:297-301`) has **no** type clause — the one place a widening could have leaked V3Tensors into a T3 query — but it binds `web4:talent`/`training`/`temperament`, which **kept** `rdfs:domain web4:T3Tensor` (machine-verified above). Still T3-pinned.

**mrh loses no triple and no entailment. The claim holds for mrh.** The commit's independently-verified triple count (84) matches its message.

**2. `web4:observationCount` — mrh has NO obligation. Negative recorded.** `grep -c DimensionScore mrh-tensors.md` = **1**, and it is `:266`, a prose comment *inside* a turtle block, not an emitted triple. mrh emits **zero** `DimensionScore` nodes across all 4 blocks. The new predicate has no mrh surface — which is itself informative: only the commit's *domain widening* touches mrh's vocabulary, which is why N1 (not the new predicate) is the mrh-anchored result.

**3. SDK / `web4-core` mirror-consumer gate — EMPTY, and recorded as empty.** Consumer set re-derived at live HEAD rather than reused (per the standing method guard): Python SDK (`mrh.py`, `trust.py`), and the Rust crates `web4-core`, `web4-trust-core`, `web4-policy`, `hub/hub-lib`, `hub/hub-daemon`, `hub/hub-plugin`, `web4-core/python`. `git log 68aa0a57..HEAD --` over `web4-core/src/lct.rs`, `mrh.py`, `trust.py` → **empty**. `web4-core::Mrh` is unchanged in shape and value. **An empty gate is the honest result** (C266 precedent); no datapoint was manufactured to fill the slot.

**4. The D1 vocabulary divergence, re-measured — a D1 refresh, NOT net-new.** Two instruments, both reported, because they answer different questions:

| Instrument | Scope | Defined | Undefined |
|---|---|---|---|
| Parsed-triple predicates + `rdf:type` objects | the 4 ```turtle``` blocks only (52 triples); excludes SPARQL blocks and instance individuals | **10** | **11** — `RolePairing`, `bindingType`, `object`, `objectRole`, `pairedWith`, `predicate`, `subject`, `subjectRole`, `t3Score`, `timestamp`, `trustContext` |
| Whole-file `web4:` token grep | all of `mrh-tensors.md`; includes SPARQL blocks and individuals (`web4:Surgeon`, `web4:Mechanic`, …) | **21** | **22** (adds `hasRelationship`, `interactionType`, `memberOf`, `trustScore`, `witnessRole`, `Surgeon`, `Mechanic`, `Researcher`, `MedicalFacility`, `CarOwner`, `AutoRepair`) |

Both re-confirm C40's findings rather than extend them: **C40-X1** (`pairedWith` absent while its two siblings `boundTo` and `witnessedBy` are defined — only `web4:pairedWithRole` exists, `web4-core-ontology.ttl:97`) and **C40-D1** (`hasRelationship` undefined). One sharpening worth recording: `grep -c subPropertyOf web4-standard/ontology/*.ttl` = **0 in every file**, so §3.3's stated entailment premise (*"boundTo/pairedWith/witnessedBy are declared `rdfs:subPropertyOf hasRelationship` in §2.1"*) is backed **only** by the fenced turtle block inside the Markdown spec — no machine-loadable file carries it. That is a datapoint on D1, already covered by C40-F7/D1. **Refreshed D1 datapoint. Not a finding. Not incremented (BC-C23-3).**

**5. Standing carry N4 — its instrument was wrong; corrected.** C238 recorded N4 as *"both tokens present (grep = 4 occurrences of the pair)"*. Re-derived: of the 8 raw hits, `:342`/`:351`/`:352`/`:354` are the **SPARQL variable** `?trustScore`, not the predicate. The real divergence is **`web4:t3Score` at 3 predicate sites** (`:325`, `:333`, `:367`) vs **`web4:trustScore` at 1** (`:397`) — not the symmetric pair the old count implies. N4 stands as a D1 member with a corrected count.

---

## §C — The two candidates this pass raised, and why both died

Per [[feedback_refute_your_best_finding]], the refuter was pointed at the auditor's flagship first.

### C-1 — "BC-C23-3 blocked D1's option (a); `01f410db` unblocks it by precedent" — **REFUTED**

The auditor's first flagship read `01f410db` as a template that relieves the blocking premise on D1's resolution option (a) ("add the terms to the ontology"), which C40 had flagged as blocked because *"editing `web4-core-ontology.ttl` is protected per BC-C23-3."*

**Refuted on a category error.** BC-C23-3's flag is *"No autonomous TTL drafting (operator-engagement-flagged)"* — it constrains **the auditor**, not the operator. The operator was never blocked from editing the canonical ontology, so there was nothing for a precedent to unblock, and "a template for additive safety" supplies no decision input the operator lacked. A second refutation landed on the claim's most falsifiable sentence: "first commit doing this" is **false in the broad form** — `cb788768` (`law:Rule` superclass + 4 properties, parse-verified at 154 triples) and `4f76f110` (`role:` oracle sets, added *"so descriptors round-trip against the ontology"*) are structurally the same additive-extension-for-a-consumer move. Only the **narrow** form survives (first content edit to a `web4:`-core-namespace file), and that is what §B-N2(a) now asserts.

A third element was cut as unsupported: the auditor had sharpened the finding with `01f410db`'s closing line *"Piece 1 of projecting the trust ontology to the hub's society MRH,"* arguing the projection is aimed at MRH and will hit the `pairedWith`/`hasRelationship` hole next. Both #581 and the commit are entirely about `DimensionScore`/tensor-node vocabulary; **neither names an MRH relationship edge.** That is a forecast, not evidence, and it is recorded here as a forecast only.

### C-2 — "#580's precedent survey omits mrh's conservative defaults" — **REFUTED, twice over**

The auditor charged that #580's section *"This is already canon in two places — just never generalized"* omits the corpus's oldest instance of its own sharp-edge rule ("Absence NEVER grants"), namely mrh §5.3's `return 0.0  # No trust outside of role context` and the beyond-horizon-zero model.

**(1) The factual premise is wrong: neither anchor is an absence case.** At `mrh-tensors.md:306-310`, `self.role` is set in `__init__` (`:288`) and `interaction_type` is a supplied parameter — **nothing is missing**. The `0.0` fires on a **mismatch**, which is §5.1 role-scoping ("a person trusted as a surgeon has no inherent trust as a mechanic"), not a conservative default under incompleteness. `trust.py:91`'s beyond-horizon zero is the same: the path exists and is fully known; zero is *relevance* decay. Corroborating sweep: `grep -n "unknown\|missing\|absent\|Absence\|default" mrh-tensors.md` → **one** hit, `:232` `default=0.0`, an unrelated function kwarg. **mrh has no absence-handling machinery to be omitted from anyone's survey.** If anything a mismatch is #580's *"present but contradictory"* row, which #580 routes to adjudication — making mrh a counter-example, not a supporting precedent.

**(2) Wrong section, and the charge-class is already routed.** "This is already canon in two places" (`:29-45`) surveys precedent for the **permissive/corrective** half (claims 1-3). "Absence NEVER grants" lives at `:86`, in the separate `:81` *"the sharp edge"* section, as the guardrail **against** that permissiveness. A conservative-default instance is not a missing entry in a permissiveness survey. And **C272-N1 already routed "#580's precedent survey is incomplete" to #580's author + operator six days ago** — with a genuine counter-example (reputation §4 ratified fail-open delegation). A second same-class charge resting on a weaker and here-false exhibit is not a finding. **Dropped, not routed.**

---

## §B — Refuted / carry-not-new (default-to-refute upheld)

| Candidate | Disposition |
|-----------|-------------|
| `01f410db` breaks something in mrh's frozen §5 turtle | **REFUTED** — widening machine-re-derived; both `web4:entity` bearers explicitly `a web4:T3Tensor`; §5.3's untyped query still T3-pinned by retained shorthand domains. 0 triples, 0 entailments lost. |
| `web4:observationCount` creates an mrh obligation | **REFUTED** — mrh emits 0 `DimensionScore` nodes; the sole `DimensionScore` hit is prose. |
| BC-C23-3 blocked option (a); `01f410db` unblocks it | **REFUTED** — BC-C23-3 constrains the auditor, not the operator; and the "first such commit" claim is false in its broad form. See §C-1. |
| The MRH projection ("Piece 1") will hit the `pairedWith` hole | **NOT EVIDENCE** — recorded as an explicit forecast; neither #581 nor `01f410db` names an MRH relationship edge. |
| #580's precedent survey omits mrh | **REFUTED ×2** — mrh's zeros are mismatch/decay, not absence; wrong section; class already routed by C272-N1. See §C-2. |
| #579 (dictionary as context-mandatory role) re-scopes MRH | **REFUTED** — self-disclaiming at `:96-97` (*"This proposal does not alter that mechanism"*); its MRH references target `dictionary-entities.md §6`, not `mrh-tensors.md`. |
| README `5df662a5` ("MRH scopes what evidence *should* exist") re-scopes MRH | **REFUTED — concordant gloss.** An enumerable typed graph bounded by `horizon_depth` does make an in-horizon gap a detectable absence; this is derivable from §3.1/§3.3, adds no normative claim, and sits on a non-normative explainer surface. |
| AAEP PRD `752eadde` / hub strategy `780af6ef` contradict mrh | **REFUTED** — `grep -i "mrh\|markov\|horizon\|propagat\|relevanc"` over both = **0 hits**. Disjoint. |
| 22 undefined `web4:` tokens = new ontology defect | **REFUTED as net-new** — C40-D1/X1 restated with a better instrument; refreshed datapoint, not incremented (BC-C23-3). See §B′-4. |
| `web4-core::Mrh` changed since C238 | **REFUTED** — `lct.rs` untouched in window; gate empty, recorded empty. |
| §4.2 note under-enumerates API differences | **REFUTED** — re-derived from `mrh.py`; exactly 3 `propagate_*`; correct and complete. |
| C91/C130 fixes regressed | **REFUTED** — `:264`/`:325` = `0.92`, no `0.90`; C130 anchor at `:174`. |
| `horizon_depth = 3` vs `MRH_MAX_HOPS = 4` | **KNOWN CARRY D4** — three distinct roles per C200-N2(a). Not re-reported. |
| C10-L2 unnumbered preamble | **STILL-OPEN INFO by design** — C41 declined the demotion. |

---

## Disposition for C279 (paired remediation slot)

- **Apply autonomous: NONE.** Zero net-new autonomous mrh defects; `mrh-tensors.md` is byte-frozen and correct. **C279 is a genuine no-op** (C155/C161/C199/C201/C239 precedent), unless a cross-track owner routes something back.
- **Route cross-track (do NOT self-apply):**
  - **N1 (MED)** → the **t3-v3 audit lineage + ontology owner**: `01f410db` falsified the factual premise *and* negated the design rule of the C42-M3 option-(c) note at `t3-v3-tensors.md:428-434`, with no citation in either direction and no audit having seen it. Adjudicate at ~C306 or sooner. The remedy is a **t3-v3 spec decision** (amend/remove the note, or restate that the spec rule survives the ontology change) — **not** an mrh edit and **not** an auditor edit to an operator-authored consequence.
  - **N2 (INFO)** → the **operator DESIGN-Q memo**, as a dated D1 refresh: #581's general ask (*state the property-extension rule*) was closed unanswered, and D1's own terms are aging under three ontology edits in 20 days. Ask = state the rule; **no autonomous TTL drafting**.
  - **C238-N2 carried forward** unchanged (`edge_type` free-string vocabulary → D1/D4 + web4-core owners); the receiving lineage has not acted and `lct.rs` was untouched this window.
- **Closed this pass**: **C238-N1** — consumed by C270. Do not re-carry.
- **Defer — operator DESIGN-Q (unchanged bundle)**: **X4/N1(a)** structural §5-shrink (the seam N1 travels along); **D1** ontology-vocabulary (N4 + N2 + C238-N2 fold in); **D4** horizon-depth model.
- **No date bump**: `mrh-tensors.md` carries no date/version banner; audit-only turn.

---

## §D — Method Notes

1. **A byte-frozen spec can be made wrong by an edit to a file it does not mention — and the *sibling* spec is where the damage lands.** `01f410db` touched neither `mrh-tensors.md` nor `t3-v3-tensors.md`. It changed three `rdfs:domain` axioms in a `.ttl`, and in doing so falsified a normative note in `t3-v3-tensors.md` that a *ratified C-series remediation* (C42-M3, option (c)) had deliberately placed there. The C90 shared-example-data lens found it because it compares the spec's **emitted data** against the ontology's **axioms**, rather than comparing prose to prose. Generalize: when a window touches an ontology/schema, diff it against the *examples* of every spec that instantiates it, not just against the specs that cite it by name.

2. **Check whether the window's commit closed an issue that asked more than the commit answered.** #581 asked two things — add this predicate, *or* state the general property-extension rule — and was closed by a commit that did the first. Reading only the commit message would have missed it; reading the issue it closes is where the D1 refresh came from. Add to the delta method: for each window commit that says "closes #N", read #N.

3. **Point the refuter at the flagship, and be willing to lose it twice.** This pass raised two candidates and lost both — the first to a category error (BC-C23-3 constrains the auditor, not the operator) and the second to a false factual premise (mrh's zeros are *mismatch*, not *absence*). The refuter then supplied N1, which the auditor had not seen. Five consecutive deltas (C270, C272, C274, C276, C278) now say the same thing: on a frozen file, the auditor's own most attractive reading is the least reliable artifact in the audit, and the adversarial pass is not a formality — here it replaced the entire result.

4. **Baseline your instrument, and publish its scope with its number.** Three counts in this audit changed under re-derivation: the "first ontology edit ever" claim (true only for the `web4:` core namespace, false for `law:`/`role:`); the undefined-vocabulary count (**10/11** parsed-triple scope vs **21/22** whole-file scope — both correct, neither meaningful unscoped); and the standing **N4** count, where C238's *"grep = 4 occurrences of the pair"* silently counted the SPARQL **variable** `?trustScore` as the predicate `web4:trustScore` (real ratio: 3 predicate sites vs 1). Also recorded honestly: system `python3` has no `rdflib`, so every RDF claim here was made in a scratch venv (`rdflib` 7.x) — the 84-triple count independently reproduces the commit message's own figure. [[feedback_enumeration_and_grep_hypotheses]].

5. **The empty gate is a result.** `lct.rs`, `mrh.py`, `trust.py` were all untouched across 46 commits. C266 established that a fully-empty gate is reportable as empty; the temptation on a 7th consecutive clean delta is to manufacture a datapoint refresh to justify the slot. It is recorded empty.

---

*C278 verdict: `mrh-tensors.md` byte-stable and correct — 7th consecutive clean delta, zero autonomous net-new mrh defects, zero mutation. The C163 §4.2 remediation re-tested against `mrh.py` ground truth: exactly 3 propagation functions, enumeration correct and complete, 0 regression. C238-N1 verified CONSUMED by C270 (routing closed); C238-N2 still open and carried. The window's yield is one MEDIUM the auditor did not find on its own: `01f410db` — the first post-creation content edit to a `web4:`-core-namespace ontology file in the project's history, landing ~8 hours before this audit — widened `web4:entity`/`web4:role`/`web4:hasDimensionScore` from `T3Tensor` to a new `Tensor` superclass, thereby **falsifying the factual premise and negating the design rule of the normative note at `t3-v3-tensors.md:428-434` that the ratified C42-M3 remediation put there**, with no citation in either direction and no audit having seen it. mrh is a party via the standing X4 seam and its own §5.1 principle, but asserts nothing falsified and needs no edit — routed to the t3-v3 lineage + ontology owner. Both candidates the auditor raised on its own were REFUTED: the BC-C23-3 "unblocking precedent" on a category error, and the #580 precedent-survey charge on a false premise plus prior routing by C272-N1. Three negatives confirmed and recorded as negatives — the widening claim holds for mrh (machine re-derived), `observationCount` creates no mrh obligation, and the SDK mirror gate is empty. C279 is a no-op.*
