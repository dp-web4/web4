# C322 — `dictionary-entities.md`, 8th delta audit

**Date:** 2026-08-06 · **Track:** web4 (Legion, autonomous) · **Protocol:** v2
**Target:** `web4-standard/core-spec/dictionary-entities.md`
**Prior pass:** C282 (2026-07-29, PR #589) — 6th consecutive pass with the target byte-frozen
**Window:** `25b490ae (C282 merge, 2026-07-30) .. HEAD e4a62d7a (2026-08-06)`
**Mutation of `web4-standard/`:** **ZERO** (all findings routed, none self-applied)

---

## Preconditions (stated before the work, per policy review)

**P1 — the freeze proof is a precondition, not a conclusion.** If the target blob is not
`8e06a23c` / 603 lines at HEAD, C282's authorized §A collapse is void and §A reopens at full
scope.

> **Result: CONFIRMED.** `git rev-parse HEAD:web4-standard/core-spec/dictionary-entities.md`
> = `8e06a23cc2cc9f87e53c34e4f2ed25c82f130771`, **603 lines**. Last touched by `95d20919`
> (C53, 2026-06-12) — **54 days, 8 rotation passes.**

**P2 — the mirror set is derived in both citation directions before any gate is run**
(§B.1), so it cannot be retrofitted to whatever the gate returns.

**P3 — no finding of this pass may be counted as evidence *for* continuing this rotation.**
Recorded before §D is written. See §D.2.

---

## §A — Freeze proof (collapsed, per the C282 policy ruling, second application)

Target blob unchanged ⇒ the **9 C53 remediations** (B1, B3a, B3b, B3c, B4, B5, B19, B20, B21 —
`95d20919`, PR #324) **HOLD BY CONSTRUCTION**. Not re-derived here; C204, C242 and C282 each
performed and labelled that derivation, and C282's reviewer ruled a seventh re-derivation
padding.

The reads **not** settled by blob identity:

| Check | Result |
|---|---|
| Mirror freshness | `sdk/web4/dictionary.py` `edd97183`, `tests/test_dictionary.py` `d8f71420`, `protocols/web4-dictionary-entities.md` `b28d8f9e` — **all three byte-identical to C282's recorded blobs.** SDK bundle B15–B18/B24/B25 stands verbatim. |
| Window | **37 commits** `25b490ae..HEAD`; **2** touch `web4-standard/` (`e4a62d7a` = this track's own C320 audit doc; `8d3808db` = #637, below); **`git log 25b490ae..HEAD -- '*dictionar*'` = 0 commits.** |
| **#637 interaction** (`8d3808db`, the one non-audit `web4-standard/` commit in-window) | `validate_context_refs.py` requires a backing `schemas/contexts/<name>.jsonld` for every `https://web4.io/contexts/<name>.jsonld` cited under `test-vectors/`. Dictionary's vectors cite `contexts/dictionary.jsonld`, which **exists** (`5f803c97`). **Dictionary passes the new gate; it is not the carried `KNOWN_MISSING` entry** (that is `t3v3.jsonld`, C310-N3). |
| C90 inbound-carry read (siblings C284–C320) | **No sibling carry routes here.** C314 (acp, 2026-08-05) uses `contexts/dictionary.jsonld` as a *control* in its own coverage measurement — corroborating, re-measured independently at §B.2 with a different instrument, not inherited. |

---

## §B — The mirror set, re-derived in both directions

### B.1 Subject-matter derivation, written before the gate (v13/v14)

C282 derived this lineage's mirror set **outward** from the spec: *which artifacts implement
the five subject-matter faces?* That derivation is correct and is not disturbed. Method carry
**v14** requires the **second** direction as well: *which artifacts cite this spec?*

Running the inbound direction for the first time in this lineage:

```
$ grep -rlF "core-spec/dictionary-entities.md" web4-standard/ --include=*.json --include=*.jsonld
web4-standard/test-vectors/schema-validation/dictionary-jsonld-validation.json   ("spec_reference")
web4-standard/test-vectors/dictionary/dictionary-operations.json                 ("spec_ref")
web4-standard/schemas/dictionary-jsonld.schema.json                              ("description")
```

**The spec cites none of them.** `grep -n "schema\|test-vector\|jsonld\|@context"
web4-standard/core-spec/dictionary-entities.md` returns **0 hits** — the citation is
**inbound-only**, which is exactly why eight outward-derived passes never reached them.

### B.2 The four machine-readable artifacts — 0 of 8 passes, swept here

| Artifact | Blob | Mentions across **both** audit trees, all 8 passes |
|---|---|---:|
| `schemas/dictionary-jsonld.schema.json` | `f32292dd` | **0** |
| `schemas/contexts/dictionary.jsonld` | `5f803c97` | **0** |
| `test-vectors/dictionary/dictionary-operations.json` | `55d58bf6` | **0** |
| `test-vectors/schema-validation/dictionary-jsonld-validation.json` | `f39252d4` (#80) | **0** |

**Instrument (v17 — both trees, `-F` per [[feedback_loose_matcher_certifies_absence]]):**
`grep -rlF "<path>" docs/audits/ web4-standard/docs/audits/`, run over **204** files in
`docs/audits/` and **2** in `web4-standard/docs/audits/`. Re-run after this document was
written: **205 / 2**, the extra being C322 itself.

**Disambiguation, so the zero is not read wider than it is.** The *string* `schema-validation`
appears in **10** audit docs — all of them other lineages (C37/C86/C314 acp, C306 atp-adp,
C310 t3-v3, C312 reputation, C318 mrh, C56 + two 2026-05 internal-consistency docs). **Zero of
the eight dictionary passes.** C242:138 does say "any schema … or test vector" — but as a
*no-mutation* claim, not a read. These are the dictionary spec's **normative conformance
surface**, and this lineage has never opened them.

**Sweep result — CLEAN on all four.** This is the only part of this fire that is actually
about a dictionary artifact, and it found nothing wrong:

| Measurement | Instrument | Result |
|---|---|---|
| Validation vectors behave as declared | `Draft202012Validator(dictionary-jsonld.schema.json)` over all 50 | **17/17** valid documents pass, **33/33** invalid fail. Self-consistent. |
| Vector count vs the SDK test's published figure | `test_schema_validation_vectors.py:10-19` claims 278 total / 92 valid / 186 invalid, "dictionary (50)" | Re-derived across all 9 files: **278 = 92 + 186**, dictionary **50 = 17 + 33**. **Every published figure is exact.** |
| JSON-LD context coverage (the C314-N1 measurement, re-derived) | schema `properties` keys at every nesting depth vs `@context` terms | **32 of 32 schema properties are defined in the context (100%)**; 39 context terms total (32 props + 5 type names + `web4`/`xsd` prefixes). Corroborates C314's use of this file as its 100% control, measured independently. |
| Operations vector | `dictionary-operations.json` | 5 vectors (`dict-001`…`dict-005`), `spec_ref` resolves, suite/version well-formed. |

**No finding is raised against any of the four.** Recorded as **I-1** so the set enters the
swept list and cannot be re-discovered as novel.

### B.3 The carry row set (v19 — primary instrument this fire)

v19, born last fire at C320: *every existing guard re-verifies a carry that is **present**, so
a row that stops being typed is invisible to all of them.* Reconstructed from the lineage's
oldest full ledger (C52) forward.

**Instrument, stated exactly.** `grep -ow "B<n>" <pass> | wc -l` — **occurrence** counts, not
line counts. This distinction is load-bearing: the eight ids all co-occur on **one** ledger line
in C204 and C242, so a `grep -c` (which counts *lines*) returns `1` for each and hides that they
share a row. Occurrences at HEAD:

| id | C204 | C242 | **C282** |
|---|:--:|:--:|:--:|
| B2, B6, B8, B10, B11, B22, B23 | **1 each** | **1 each** | **0 each** |
| B7 (raw, **with collider**) | 4 | 2 | 1 |
| **B7 (C52-B7 only, collider removed)** | **1** | **1** | **0** |
| C17-INFO3 | 1 | 1 | **0** |

**`B7` has a collider and its raw count must not be reused naively** (the C306 `B1`-23-hits
discipline). `-w` matches `B7` inside the *distinct* cross-doc id **`C64-B7`**, which appears
3× in C204 (`:81`, `:132`, `:175`), 1× in C242 (`:117`), and 1× in C282 (`:326`). Subtracting
it: **C52-B7 is present once in C204, once in C242, and zero times in C282** — the same shape as
the other seven. C282's sole `B7` occurrence is `C64-B7`, a carry it *did* keep.

Earlier passes (C52/C94/C132/C166) all carry the set; C17-INFO3 is additionally gapped at
C94/C132/C166 and is recorded, not re-argued, per C306-I-4.

C204 and C242 each carry these ids in one explicit ledger row —
*"**B2/B6/B7/B8/B10/B11/B22/B23**, **C17-M4/M6**, **C64-B7**, **C17-INFO3**, **B15–B18/B24/B25**
| operator DESIGN-Q / cross-doc / SDK | OPEN, unchanged (all anchors frozen)"* (C204:132,
C242:117). C282's counterpart, §D.3 (`:324-331`), names `C52-B9`, `C17-M1/H2/M4/M6`, `B26`,
`C64-B7`, `B3d`, `B3c`, the C158 fence, and `B15–B18/B24/B25` — and **not one of the nine.**
**No disposition is recorded for any of them anywhere in C282.**

They were never remediated. C53's own commit message is explicit:

> "NOT touched (operator-owned design-Q): B2/L206 floor-source gate … **All 13 design-Q + 6
> cross-track SDK findings remain carried.**"

**All eight B-rows re-verified TRUE at HEAD** against the byte-frozen 603 lines:

| id | claim | verification at HEAD |
|---|---|---|
| **B2** | §4.2 gates on `request.trust_requirements.minimum`, a key defined nowhere | `:206` `if dictionary.t3 < request.trust_requirements.minimum:` — the `:189` block defines `minimum_fidelity` / `require_witness` / `atp_stake`. **No `minimum`.** |
| **B6** | frames all translations as R6 while the trust model is R7-tier | `R6` at `:403`, `:405`, `:407`; **`R7` = 0 occurrences in the file** |
| **B7** | `proposal_threshold: 10` on a 0–1 reputation scale | `:344` `"proposal_threshold": 10,  // Min reputation to propose`; reputations at `:333`/`:339` are `0.95`/`0.92` |
| **B8** | SPARQL treats `web4:coverage` as a scalar; §2.2 defines it as counts | `:368` `web4:coverage ?coverage ;` + `:372` `FILTER(?coverage > 0.9)` vs `:55` `"coverage": { terms/concepts/relationships }` |
| **B10** | `fidelity` gated on, never defined/computed/returned | gated `:190` / `:413` (`minimum_fidelity`), reported `:534` (`fidelity: 0.93`); §4.2's flow returns `confidence` |
| **B11** | MUST-5 unenforceable — "critical" undefined | `:475` `5. Critical translations MUST require ATP stake`; `grep -i critical` = **1 hit**, the MUST itself |
| **B22** | 10% stake reward creates ATP outside the cycle spec's only creation path | `:568` `return amount * 1.1  # 10% reward` |
| **B23** | `trust_acceptable: true` at 0.874 with no chain-level criterion | `:273` `"trust_acceptable": true` under `:272` `"cumulative_degradation": 0.126` |

**The backstop, published prominently because it sets the severity.** All nine survive in this
track's **out-of-repo standing ledger** — `carries.md:26` carries the eight B-rows as *"C52
DESIGN-Q additions"* with their full text, and `:55` carries `INFO3`. **This is a contraction
of the in-repo audit-doc lineage, not a loss from the system.**

#### What actually caused it — the proposed explanation was wrong

This finding was first drafted as *"C282's anti-padding §A collapse had an unpriced ledger
cost."* **That is refuted by the artifacts and is not the finding.**

- C282 is **397 lines** — the **longest document in the lineage**, 2.4× C242's 164. It was not
  budget-constrained; the §A collapse freed ~30 lines and §B′ absorbed ~93 of them.
- The rows died in **§D.3**, a section **no policy-review change touched**. C282's three
  binding changes were the §A collapse, the P2 stop rule, and the cadence datapoint.
- The mechanism is a **format conversion**. C242's §C.1 was a **per-row table** under the
  header *"Carry Ledger (re-derived from lineage prose, not from C204's §C)"*. C282 replaced it
  with an **8-line prose paragraph** titled "Carries unchanged". **The nine ids died in the
  table→prose conversion.**

The rule that breaks is this lineage's own, and it predates C282:
**[[feedback_prose_is_not_ledger]]** — *an item in prose but never promoted into the ledger
vanishes at the next delta.* C282 cites that carry by name in its §F. It then moved its own
ledger into prose in the same document.

#### Severity: **LOW**, against this corpus's two calibration points

| precedent | facts | severity |
|---|---|---|
| **C306-I-4** | `B6-SDK` gapped **two** consecutive passes, recovered | **INFO** |
| **C320-N1** | 4 rows dropped at C164, 3 still true, and *"they exist **nowhere else in the repository**"* | **MED** |

C320's MED was **explicitly load-bearing on the no-backstop clause** — its §B states the
absence as a searched result across both trees and every tracked path. **These nine have a
backstop.** That is the exact distinguisher C320 relied on, and it is present here and absent
there.

Two counter-arguments, resolved against myself rather than silently in my favour:
1. *"Still true at HEAD carries MED."* It does not. **Still-true is what *open* means**; it
   distinguishes nothing.
2. *"`carries.md` is also outside the repo, so the backstop is no better than none."* This
   cuts both ways and is the strongest case for MED. It fails on **realized harm**: all nine
   were **operator-owned design-Q from birth** (C53's words), never track-actionable, so no
   remediation was ever blocked by the drop. C320's rows, by contrast, were SDK-track items
   with a live fix path. **LOW.**

**One row is gapped one pass only** (C17-INFO3 is absent from C94/C132/C166 as well) and is
recorded, not re-argued, per C306-I-4.

---

## §C — Carry Ledger (re-derived from lineage prose, C52 forward — **not** from C282's §D.3)

Header discipline restored from C242 (dropped by C282). **Per-row, with an explicit disposition
column, so the next pass inherits a row set rather than a paragraph.** Additive only; no prior
audit doc is edited (C163 no-retro-edit ruling).

### C.1 — Restored rows (the C322-N1 set)

| Carry | Class | Disposition at C322 |
|---|---|---|
| **B2** | operator DESIGN-Q | **OPEN — RESTORED.** `:206` verified; T3-floor source undecided |
| **B6** | operator DESIGN-Q | **OPEN — RESTORED.** R6-vs-R7 positioning; `R7` = 0 in file |
| **B7** | operator DESIGN-Q | **OPEN — RESTORED.** `:344` scale mismatch verified |
| **B8** | operator DESIGN-Q | **OPEN — RESTORED.** `:368`/`:372` vs `:55` verified (couples C40-D1) |
| **B10** | operator DESIGN-Q | **OPEN — RESTORED.** fidelity↔confidence term identity |
| **B11** | operator DESIGN-Q | **OPEN — RESTORED.** `:475` "critical" undefined |
| **B22** | operator DESIGN-Q | **OPEN — RESTORED.** `:568` vs §2.2 sole ATP-creation path |
| **B23** | operator DESIGN-Q | **OPEN — RESTORED.** `:273` chain-level criterion undefined |
| **C17-INFO3** | INFO (cross-doc) | **OPEN — RESTORED.** `mcp-protocol.md:306` stale `roleType`; owned by the mcp lineage |

### C.2 — Rows C282 did carry (re-verified present, unchanged)

| Carry | Class | Disposition at C322 |
|---|---|---|
| **C52-B9** | operator DESIGN-Q | OPEN — `:570` partial-slash formula present verbatim; `atp-adp §2.4` anchor frozen |
| **C17-M1** | operator DESIGN-Q | OPEN — `grep -riE dictionar web4-standard/ontology/` = **0**; six `web4:*` predicates still undefined |
| **C17-H2** | operator DESIGN-Q | OPEN — unchanged |
| **C17-M4 / C17-M6** | operator DESIGN-Q | OPEN — unchanged, anchors frozen |
| **B26** (root: B12/B13/B14) | INFO design-Q, 3-doc canonicity | OPEN — all three anchors frozen (`8e06a23c`, `b28d8f9e`, entity-types §10.2) |
| **B3d / B3c** | INFO → C33 id-scheme bundle | OPEN — carried in `carries.md` |
| **C64-B7** | cross-doc | OPEN — unchanged |
| **C158 `//`-fence** | INFO-corpus (inbound) | OPEN — target frozen ⇒ count unchanged |
| **B15–B18, B24, B25** | cross-track SDK bundle | OPEN — mirror byte-frozen; stands verbatim. *(Expanded to individual ids here: the range notation survived six passes, but v18 warns a folded carry loses its own row.)* |
| **C280-N3** | inbound, CBP-owned | OPEN |
| **C282-N1** | MED → CBP + SDK-conditional | **OPEN, DOES NOT ESCALATE** — see C.3 |
| **C282-N2** | INFO → CBP | OPEN — `#579` byte-frozen since `4665a430` (2026-07-27), §6 frozen |

### C.3 — C282's two mandated regression checks (both NEGATIVE)

C282 §E: *"if #580 ratified and the SDK is unmoved, N1 escalates from survey-completeness to a
live spec-vs-implementation conflict, and C36-N5's remedy must be re-adjudicated with it."*

| half | measured | result |
|---|---|---|
| SDK moved? | `dictionary.py:769-772` — all three `.get(d.lct_id, 1.0)` defaults present; docstring `:754` still reads *"If not provided, defaults to 1.0 (assume perfect)"*; `grep -rc unmeasured web4-standard/implementation/sdk/` = **0** | **UNMOVED** |
| #580 ratified? | `proposals/resilience-to-incomplete-information.md` header reads **`Status: proposal, for fleet review`**, byte-frozen at `954ee391` since 2026-07-27; **0 window commits under `web4-standard/proposals/`** | **NOT RATIFIED** |

**The escalation condition is a conjunction and its second half is false. C282-N1 does not
escalate, and C36-N5 (`binding.py:468` `a_fresh = 1.0`, present at HEAD) is not re-adjudicated
here.** Recorded because it kills the most attractive escalation available to this fire.

### C.4 — NET-NEW against the target: **NONE.** Seventh consecutive clean pass on the spec.

---

## §D — Routing (routes, never applies)

### D.1 — C322-N2 (INFO → the test-vector owner; **corpus-wide, NOT a dictionary finding**)

**The schema-validation vectors publish a per-vector error contract that no consumer verifies.**

Each file's `meta.description` states: *"Each 'invalid' document MUST fail **with the indicated
error**."* All **186** invalid vectors across the 9 files carry `error_kind`, `error_path`, and
often `error_field`. Neither consumer checks them:
`test-vectors/schema-validation/validate_schema_vectors.py:120-123` computes `error_kinds` only
to render a `--verbose` line and never compares it; `implementation/sdk/tests/
test_schema_validation_vectors.py` asserts pass/fail only.

**Dictionary slice (the entry point that justifies its presence here):** of 33 invalid vectors,
**1** declares an `error_kind` that a Draft 2020-12 validator reports at top level, **9** match
`best_match`, **21** have a declared `error_path` matching `best_match`.

**Corpus context (disclosed, not claimed as this pass's yield):**

| root shape | files | kind == `best_match` |
|---|---|---|
| plain object | lct, attestation-envelope, r7-action | **42 / 42 (100%)** |
| root `oneOf` | atp, acp, t3v3, entity, capability, dictionary | **31 / 144** |
| | **total** | **73 / 186** |

Under a root `oneOf` every sub-error is nested inside a single `oneOf` failure, so the declared
kind is not reachable at top level and its recoverability depends entirely on how a given
language's validator surfaces `oneOf` context. The vectors' stated purpose is cross-language
interoperability, which is exactly where that is not portable. **The three object-rooted files
are 100% accurate, so this is a deviation, not an idiom.**

**Not a re-file of C318's refuted candidate.** C318's killed flagship was
`test-vectors/validate_vectors.py` **suite coverage** ("validator certifies 2 of 22 suites").
This is a **different file** (`schema-validation/validate_schema_vectors.py`), a **different
mechanism** (an unverified declared field, not uncovered suites). Stated so a future pass does
not re-collide with the refuted candidate.

**Routed to the test-vector owner per C318-N3's precedent. Capped at INFO. Not counted as a
dictionary finding. Explicitly out of bounds for this track to fix** — the remedy is a ~10-line
comparison in another owner's file, and writing it inside an audit is the circuit breaker.

### D.2 — Cadence: this fire **strengthens** C282's proposal (P3 discharged)

C282 routed a proposal to move this file to **event-triggered** auditing on the grounds that
*"every finding this lineage has produced since C53 came from the window, never the file."*

This window has **zero dictionary commits**. This pass's three findings are: the audit
lineage's own bookkeeping (N1), a clean sweep (I-1), and a corpus-wide validator gap (N2).
**None came from `dictionary-entities.md`.** The spec side is clean for the seventh
consecutive pass.

**A finding about the audit process is not evidence that the audit should keep firing on this
file.** N1 does not rescue the rotation and is not offered as if it did. This is the **ninth**
consecutive datapoint for the cadence proposal. Routed to the open **CADENCE DESIGN-Q**
(opened C270). **Rotation order unchanged this fire: C324 remains SOCIETY_METABOLIC.**

### D.3 — To the operator memo

Design-Q **B2/B6/B7/B8/B9/B10/B11/B22/B23/B26**, **C17-M1/H2/M4/M6**, **C64-B7** — one memo,
unchanged in substance, **now with the nine restored rows visible in §C.1 rather than only in
an out-of-repo file.** Flagship **B-D1** remains UNANSWERED.

---

## §E — Guard for the next dictionary delta (C362, or on event trigger)

- Target byte-frozen at `8e06a23c` since `95d20919`; SDK `edd97183` / `d8f71420`; sister doc
  `b28d8f9e`; schema `f32292dd`; context `5f803c97`; vectors `55d58bf6` / `f39252d4`. If all
  unchanged, §A is a freeze proof — **do not re-derive the 9 C53 remediations an eighth time.**
- **§C is now a per-row table again. Do not convert it to prose.** That conversion is what
  C322-N1 is. If a future pass compresses it, every id it drops must carry a disposition.
- **The four machine-readable artifacts are now IN the swept set and may not contract** (v8).
  They swept **clean** at C322 — check only whether they *changed*, do not re-discover them as
  novel. Re-run: 50 vectors 17/33 pass-fail; context **32/32** schema props; SDK test's
  278/92/186 figures.
- **C282-N1 regression (one grep, unchanged):** did `select_best_dictionary`'s `.get(…, 1.0)`
  defaults change, **and** did #580 leave `Status: proposal, for fleet review`? Escalation needs
  **both**; at C322 the second is false.
- **C322-N2 regression:** did `validate_schema_vectors.py` gain an `error_kind` comparison?
- **Do not re-open:** C282's R-1 (ontology-predicate cluster, 74% corpus-wide) or R-2 (SPARQL
  `FILTER` idiom); the `hub/` gate (NEGATIVE on subject-matter grounds, and re-confirmed
  unmoved here — do not re-gate without new evidence); the I-1 false mirror in
  `web4-core/python/…/trust/attestation/` (a metaphor); Effector/W4IP; LCT §1.2.
- **Do not re-file C322-N2 as a coverage finding** — it is an unverified-declared-field finding,
  and C318's suite-coverage candidate on the *sibling* validator is REFUTED.
- `protocols/` cluster remains gated by **D0** (operator-unanswered). Do not re-audit.

---

## §F — Method lesson

**v19 found the row loss; the *causal story* it invited was false, and the artifacts said so.**

The drop was real and measured at 1/1/0 across C204/C242/C282. The explanation that presented
itself — *"the anti-padding collapse squeezed the ledger out"* — was clean, blamed a named
prior decision, and was **refuted by line counts**: C282 is the longest document in the
lineage. The rows died in a section no review change touched, in a **table→prose conversion**
the author chose. **A row-loss finding must name the mechanism that lost the row, not the
policy nearest to it in the document.** Measuring the drop is the cheap half; attributing it
is where the error lives, and the attribution is the part a future pass will cite.

**Second lesson — v14's second direction is not symmetric, and the asymmetry is the whole
gap.** Eight passes derived the mirror set *outward*: what does this spec point at? The spec
points at **nothing** — `grep` for `schema|test-vector|jsonld|@context` in 603 lines returns
zero. Three artifacts point *inward* at it by exact path. **A spec that cites nothing is not a
spec with no mirrors; it is a spec whose mirrors can only be found from the other end.** The
outward derivation was not merely incomplete here — it was *structurally incapable* of
returning anything, and it returned a confident set six times.

**Third — the sweep that closes an 8-pass gap came back clean, and that is the honest result.**
50 vectors self-consistent, 100% context coverage, every published count exact. There is a pull
to make a never-read artifact yield something proportional to how long it went unread. It
didn't. The finding is the **gap**, recorded as INFO; the artifacts are fine.

**Fourth — severity is set by the backstop, not by the truth of the rows.** All nine restored
rows are true at HEAD. That fact is worth zero severity: still-true is what *open* means. What
separated this from C320's MED was one clause in C320's own text — *"they exist nowhere else in
the repository"* — and checking whether it held here. It did not. **Read the precedent's
load-bearing clause, not its severity label.**

---

## §G — Post-write re-run (v17), and the one cell it corrected

Every number in this document was re-derived **after** it was written, at a different scope or
with a different tool than it was drafted with ([[feedback_publish_the_instrument]]).

| cell | drafted with | re-run with | result |
|---|---|---|---|
| audit-tree file counts | `ls docs/audits/*.md` (204 / 2) | same, post-write | **205 / 2** ✓ (delta = C322) |
| four artifacts at 0 mentions | `grep -rlF` over both trees | same, `\| grep -v C322` | **0 / 0 / 0 / 0** ✓ |
| `schema-validation` in 10 docs | filesystem `grep -rlF` | same, post-write | **11** ✓ (delta = C322); **0** dictionary passes ✓ |
| window 37 / 2 / 0 | `git log --oneline \| wc -l` | same | **37 / 2 / 0** ✓ |
| C242 164L, C282 397L | `wc -l` | same | ✓ |
| 278 = 92 + 186; 73/186; 42/42; 31/144; dictionary 1/9/21 of 33 | ad-hoc script | **independently re-written script** | **all exact** ✓ |
| ontology `dictionar` = 0; SDK `unmeasured` = 0 | filesystem `grep -r` | **`git grep` at HEAD** | **0 / 0** ✓ |
| spec `R7` = 0; `critical` = 1; outbound citations = 0 | filesystem `grep -n` | **`git grep -ow` at HEAD** | **0 / 1 / 0** ✓ |
| **§B.3 row-set counts** | **`grep -c`** | **`grep -ow \| wc -l`** | ✗ **CORRECTED — see below** |

**The one failure, published.** §B.3 was drafted with `grep -c`, which counts **matching lines,
not occurrences**. Two errors followed from that single choice: (i) the eight ids all sit on
**one** ledger line in C204/C242, so `1 each` concealed that they share a row rather than
holding eight; and (ii) `B7` collides with the distinct cross-doc id **`C64-B7`**, whose raw
occurrence counts are 4 / 2 / 1 — so a reader re-running the published instrument on `B7` would
get a **non-zero** number for C282 and read the finding as contradicted. The table now publishes
occurrence counts with the collider named and subtracted. **The verdict never moved** (C52-B7 is
still 1 / 1 / **0**), but the instrument would not have survived a re-grep — which is the whole
reason C282's own §F earned this rule, one pass ago, in this same lineage.

---

*C322 — 1 LOW (N1, carry row-set contraction, 9 rows restored), 1 INFO routed corpus-wide
(N2), 1 INFO record (I-1, four artifacts swept for the first time in 8 passes, all clean),
1 escalation condition tested and NEGATIVE. Zero net-new against the target — seventh
consecutive clean pass on a blob byte-frozen 54 days. Zero mutation of `web4-standard/`.
C323 = declared NO-OP on the spec side. Ninth consecutive datapoint for the cadence proposal;
this pass produced no finding from the file it audited.*
