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
web4-standard/implementation/sdk/web4/schema_registry.json                       ("description")
web4-standard/test-vectors/schema-validation/dictionary-jsonld-validation.json   ("spec_reference")
web4-standard/test-vectors/dictionary/dictionary-operations.json                 ("spec_ref")
web4-standard/schemas/dictionary-jsonld.schema.json                              ("description")
```

> **CORRECTION (2026-08-06, review of PR #647).** As first published, this block printed
> **three** of the **four** lines the command returns — `schema_registry.json` was dropped.
> The command was right; the transcription was not. The fourth is restored above and swept at
> §B.2; the failure mode is recorded at §F (fifth lesson) and §G.2. It is not a window artifact:
> `git log --diff-filter=A` puts it at **`6d533fcb`** (#114, *"I1: Bundle JSON Schemas as single
> registry file — Sprint 13"*), long before `25b490ae`, and `git grep -lF … e4a62d7a` returns
> the same four at this audit's own ref. Its citation is of the same form as the others:
> `"description": "JSON Schema for Dictionary Entity documents per
> web4-standard/core-spec/dictionary-entities.md"`.

**The spec cites none of them.** As first published this cell used
`grep -n "schema\|test-vector\|jsonld\|@context"`, which is case-sensitive and cannot match the
literal `JSON-LD`. Re-run in the widened form — **`grep -cniE
"schema|test[-_ ]?vector|json-?ld|@context" web4-standard/core-spec/dictionary-entities.md`** —
the answer is still **0** over all 603 lines (`grep -ci "JSON-LD"` is **0** too). **Use the
widened form; the narrow one happened to be right.** The citation is **inbound-only**, which is
exactly why eight outward-derived passes never reached these artifacts.

**And widening did not recover the dropped line.** The same widened matcher run *inbound*
(`grep -rlEi "core-spec/dictionary.entities\.md"`, extensions broadened to `*.yaml`/`*.yml`)
returns the **same four files**. Nothing about the instrument hid the fourth artifact — only
reading what the instrument returned did. Recorded so the next pass credits the fix correctly.

### B.2 The five machine-readable artifacts — 0 of 8 passes, swept here

| Artifact | Blob | Mentions across **both** audit trees, all 8 passes |
|---|---|---:|
| `schemas/dictionary-jsonld.schema.json` | `f32292dd` | **0** |
| `schemas/contexts/dictionary.jsonld` | `5f803c97` | **0** |
| `test-vectors/dictionary/dictionary-operations.json` | `55d58bf6` | **0** |
| `test-vectors/schema-validation/dictionary-jsonld-validation.json` | `f39252d4` (#80) | **0** |
| `implementation/sdk/web4/schema_registry.json` *(added on review)* | `ee9d5f40` (#114) | **0** — see the disambiguation below; this cell is **not** the same claim as the four above |

**Disambiguation on the fifth row, because "0" is doing different work there.** The other four
are unmentioned anywhere in either audit tree. `schema_registry.json` is **not** corpus-unswept:
the column's own instrument (`grep -rlF "implementation/sdk/web4/schema_registry.json"
docs/audits/ web4-standard/docs/audits/`) returns **2** files — `C302-web4-lct-7th-delta-2026-07-31.md`
(the *web4-lct* lineage, which recorded it at `:393` as *"the byte-identical bundle of the
above"*) and `dictionary-entities-internal-consistency-2026-05-27.md` (`:2949`, a different
`$def`, and a **pre-rotation** document). **Neither is one of the 8 rotation passes**
(C52, C94, C132, C166, C204, C242, C282, C322), so the cell is **0 of 8** — the same number as
the other four, reached a different way.

**One false positive subtracted, in the manner of §G's `B7`/`C64-B7` collider.** A bare-token
`grep -rlF schema_registry` also returns `C52-dictionary-entities-audit-2026-06-12.md`, which
would have made the cell read **1 of 8**. It does not survive the column's own `-F` full-path
instrument (`grep -cF "implementation/sdk/web4/schema_registry.json" C52…` = **0**): `C52:35`
says *"reserved by mcp-protocol/schema_registry"*, a different referent reached only by the
loose matcher. **The under-count and the over-count are the same error running in opposite
directions**, and both are caught only by naming the matcher — which is the concrete evidence
for the fifth method lesson at §F.

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
| **Bundled registry copy ≡ canonical schema** *(added on review)* | `json.load` on both, `==` on the parsed objects | **IDENTICAL.** `schema_registry.json["dictionary-jsonld.schema.json"]` equals `schemas/dictionary-jsonld.schema.json`. Widened to all **12** registry entries: **12/12 identical** to their `schemas/` originals. **Nothing is wrong today.** |
| **How that copy is consumed** *(added on review)* | read `implementation/sdk/web4/validation.py` | `_load_schema` (`:204-238`) resolves via `_load_bundled_registry()`, which reads it with `resources.files("web4")` at **`:92`**, documented at `:11` as *"works in pip-installed wheels"*. **This is the copy a pip-installed consumer actually validates against.** |

**No finding is raised against any of the five — the sweep is CLEAN.** Recorded as **I-1** so
the set enters the swept list and cannot be re-discovered as novel.

**Two gaps are raised about the fifth artifact's *guarding*, not its content** — routed to the
SDK track at **§D.3** (**I-2**, INFO: no content-equality gate) and **§D.4** (**C322-N3**, LOW:
the documented override order is not the implemented one). Both were surfaced by the review of
PR #647; neither disturbs the CLEAN verdict above, and neither is a dictionary-spec finding.

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

### C.3b — Rows opened by the review of PR #647 (added 2026-08-06)

| Carry | Class | Disposition at C322 |
|---|---|---|
| **C322-I2** | INFO → SDK track | **OPEN.** No content-equality gate between `schemas/*.json` and the bundled `schema_registry.json`; 12/12 identical today. §D.3 |
| **C322-N3** | LOW → SDK track | **OPEN.** `_load_schema` consults the registry ahead of `WEB4_SCHEMA_DIR` and `schema_dir=`, contradicting `validation.py:8-12` / `:259` / `:283`; three override-named tests cannot detect it. §D.4 |

Both are typed here as rows, not left in §D prose — the defect this document's own N1 reports is
exactly what happens to an item that lives only in prose ([[feedback_prose_is_not_ledger]]).

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

This window has **zero dictionary commits**. This pass's findings are: the audit lineage's own
bookkeeping (N1), a clean sweep (I-1), a corpus-wide validator gap (N2), and — added on review —
two SDK-track gaps around the shipped copy of the dictionary schema (I-2, N3). **None came from
`dictionary-entities.md`.** The spec side is clean for the seventh consecutive pass.

**A finding about the audit process is not evidence that the audit should keep firing on this
file.** N1 does not rescue the rotation and is not offered as if it did. This is the **ninth**
consecutive datapoint for the cadence proposal. Routed to the open **CADENCE DESIGN-Q**
(opened C270). **Rotation order unchanged this fire: C324 remains SOCIETY_METABOLIC.**

> **Post-review note (2026-08-06).** The revision *strengthens* this reading rather than
> weakening it. The block on #647 produced a **fourth** process finding — an audit that
> transcribed 3 of its instrument's 4 output lines — and two findings about **another track's**
> package. Five findings, none from the target file, on a blob byte-frozen 54 days. **The
> rotation slot C324 is deferred, not consumed**: this fire cleared the block under primer
> step 0.5 instead of taking a new slot, and the C+40 arithmetic is unaffected —
> C324 = `SOCIETY_METABOLIC_STATES` remains next.

### D.3 — C322-I2 (INFO → the SDK track; a **gap**, not a defect) *(added on review of #647)*

**The canonical schema and the schema the SDK actually ships have no content-equality gate.**

`schemas/dictionary-jsonld.schema.json` is the standard's normative artifact.
`implementation/sdk/web4/schema_registry.json` bundles a copy of it (and of 11 siblings) so that
validation works from a wheel. They are **identical today** — verified two ways, on the parsed
objects (`==`) and on canonicalized SHA-256 (`json.dumps(…, sort_keys=True,
separators=(',',':'))`; dictionary = `18772c3b…` on both sides), **12/12 across the whole
registry**. Nothing is wrong.

What is missing is the mechanism that keeps it that way. `tests/test_validation.py::TestBundledRegistry`
has three tests, and none of them compares content:

| test | asserts |
|---|---|
| `test_registry_loads` | the registry parses and is a `dict` |
| `test_registry_contains_all_schemas` | every `_SCHEMA_FILES` **filename is present** as a key |
| `test_registry_schemas_have_schema_key` | each entry has a `$schema` **or** `type` key |

Presence and shape, never content. **An edit to a file under `schemas/` that is not mirrored
into the registry would leave the suite green and change what a pip-installed consumer
validates against.** There is no generator or refresh script in the repo (`grep -rln
schema_registry` over `*.py`/`*.sh`/`*.toml`/`*.yml` returns no build step) — the bundle is
hand-maintained.

**Stated as a gap.** No divergence has occurred; this is the absence of a guard, not the
presence of a fault, and per [[feedback_absence_is_not_prohibition]] the two are not the same
charge. **Routed to the SDK track, INFO. Out of bounds for this track to fix** — the remedy is a
test in another owner's package, and writing it inside an audit is the circuit breaker.

### D.4 — C322-N3 (LOW → the SDK track): the documented override order is not the implemented one *(added on review of #647)*

The gap above is **unrecoverable at runtime**, because the documented escape hatch does not work.

`validation.py:8-12` publishes the resolution order as:

> 1. `WEB4_SCHEMA_DIR` environment variable (directory override) · 2. Bundled
> `schema_registry.json` · 3. Repository-relative walk

`_load_schema` (`:204-238`) implements **bundled registry first** (`:219-224`), reaching
`get_schema_dir()` — the only function that reads `WEB4_SCHEMA_DIR` — only in the fallback branch
that a registry hit never enters. the public `schema_dir=` contract is inoperative for the
same reason — documented on `get_schema` (`:259`, *"Override schema directory. If None, uses
bundled registry then auto-detected directory"* — accurate only for the `None` case) and on
`validate` (`:283`, *"Override schema directory. If None, auto-detected"* — unqualified, and
wrong for all 12 registry schemas).

**Measured, not inferred.** With a sentinel-titled copy of the dictionary schema in a temp
directory: `WEB4_SCHEMA_DIR=<tmp> get_schema("dictionary")` returns the **bundled** title, and
`get_schema("dictionary", schema_dir=Path("<tmp>"))` returns the bundled title too. `_SCHEMA_FILES`
has **12** entries and the registry has **12**, intersection complete ⇒ **both overrides are
silently ignored for every schema the SDK knows about.**

**Why this is its own row rather than a clause inside I-2.** It is a **self-disagreement inside
one package**, true today and independent of whether the copies ever diverge — the class this
corpus already recognises ([[feedback_does_the_impl_agree_with_itself]], C286: two copies of one
enumeration in one binary *is* the finding). Recording it as the mechanism of an INFO would bury
a live contradiction in a prose clause of another item, which is precisely the defect this
document's own N1 reports ([[feedback_prose_is_not_ledger]]).

**And the tests are green over the order the SDK does not implement.** Three tests are named for
override behaviour; none can detect that the override is inoperative:

| construct | why it cannot fail |
|---|---|
| `TestSchemaResolution::test_get_schema_dir_env_override` | calls `get_schema_dir()` **in isolation**, which *does* honour the env var; `_load_schema` never reaches it |
| `TestSchemaResolution::test_get_schema_dir_bad_env` | same isolation |
| `TestValidateEdgeCases::test_schema_dir_override` | passes `schema_dir=get_schema_dir()` — **the canonical directory itself** — then asserts the document is valid. Identical content on both paths, so the assertion holds whether the override is honoured or ignored |

**Severity LOW, and the bound is stated.** SDK-only; reversible; **no harmed consumer** — the
sole `schema_dir=` call site in the repository outside the definitions is
`test_validation.py:477`, the third row above, which passes the canonical directory. Not MED,
because nothing observably misbehaves for any existing caller; not INFO, because the
documentation and the implementation contradict each other at HEAD and a green suite certifies
the wrong one.

**Routed to the SDK track. Not applied here, and not a dictionary-spec finding** — the target
stays clean for the seventh consecutive pass. The SDK owner may re-rate; construct pointers are
given by name above rather than by line number so the routing survives a reflow.

### D.5 — To the operator memo

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
- **The five machine-readable artifacts are now IN the swept set and may not contract** (v8) —
  the fifth, `implementation/sdk/web4/schema_registry.json`, was added on review of #647 and is
  part of the set, not an appendix to it. They swept **clean** at C322 — check only whether they
  *changed*, do not re-discover them as novel. Re-run: 50 vectors 17/33 pass-fail; context
  **32/32** schema props; SDK test's 278/92/186 figures; registry **12/12 identical** to
  `schemas/`.
- **Run the inbound sweep by executing the command, not by reading this document's transcript
  of it**, and compare the line *count* of the output against the row count of the table you
  write from it. C322 shipped a 4-line result as 3 rows; no guard in this lineage could see it,
  because every guard re-verifies something present (§F, fifth lesson).
- **I-2 / C322-N3 regression (SDK track, both routed, neither applied):** did
  `TestBundledRegistry` gain a **content-equality** assertion against `schemas/`, and does
  `_load_schema` still consult the bundled registry ahead of `WEB4_SCHEMA_DIR` and `schema_dir=`
  (`validation.py:219-224`, the `# Try bundled registry first` branch at `:219`) while `:8-12`
  documents the reverse? At C322: no gate, and the
  inversion holds with 12/12 schemas shadowed.
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

**Fifth (added on review of #647) — a citation-direction sweep is not self-validating, because
printing an instrument is not printing what it returns.** §B.1 published the correct command,
ran it, and transcribed **three** of its **four** result lines. Everything downstream inherited
the short set: the I-1 table, whose stated purpose is that *"the set enters the swept list and
cannot be re-discovered as novel"* — so the omission did not merely miss an artifact, it
converted an unexamined one into one that **looks** examined, which is worse than no swept set
at all. **And this pass diagnosed exactly that class and then under-executed its own remedy on
its own headline.**

**No guard in this lineage could have caught it, and that is the general lesson.** v10 counts a
carry row's zeros, v11 re-resolves an anchor, v12 re-derives a direction, v18 re-resolves by
content, v19 diffs the row *set* — every one of them operates on something that is **present**.
A line dropped between a command's stdout and the table written from it is present in neither
the document nor any prior document, so there is nothing to re-verify, nothing to count, nothing
to grep. This is v19's own sentence — *"a row that stops being typed is invisible to all of
them"* — turned on the pass that introduced v19. **The check is mechanical and belongs with the
instrument: compare the output's line count to the table's row count, and say both numbers.**

**The corollary runs both ways, which is why §B.2 subtracts a false positive as well as adding a
missing row.** Widening the matcher would not have found the dropped line (the widened inbound
form returns the same four files), and a *loosened* matcher would have over-counted the fifth
artifact's audit-tree mentions from 0 to 1 via an unrelated `C52` referent. Naming the matcher
catches both; changing the matcher catches neither.

---

## §G — Post-write re-run (v17), and the one cell it corrected

Every number in this document was re-derived **after** it was written, at a different scope or
with a different tool than it was drafted with ([[feedback_publish_the_instrument]]).

| cell | drafted with | re-run with | result |
|---|---|---|---|
| audit-tree file counts | `ls docs/audits/*.md` (204 / 2) | same, post-write | **205 / 2** ✓ (delta = C322) |
| four artifacts at 0 mentions | `grep -rlF` over both trees | same, `\| grep -v C322` | **0 / 0 / 0 / 0** ✓ — but the *set* was one short; see §G.2 |
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

### §G.2 — The failure the post-write re-run did **not** catch (added on review of PR #647)

§G above certifies that every number in this document was re-derived after it was written. That
is true, and it was not sufficient. **The §B.1 defect was not a wrong number — it was a missing
line**, and no re-run of a *cell* can find a row that was never written. It was caught by the
reviewer of #647 executing the published command and comparing its output to the table.

| what | drafted | published | correct | caught by |
|---|---|---|---|---|
| §B.1 inbound sweep | 4-line command output | **3 rows** | **4** | reviewer of #647, executing the printed command |
| §B.2 swept-artifact set (I-1) | 4 artifacts | 4 | **5** | same |
| §B.1 outbound instrument | case-sensitive `grep` | published as drafted | still **0**, but the printed matcher cannot match `JSON-LD` | same |

**Re-measured independently before accepting any of it** ([[feedback_publish_the_instrument]];
a reviewer's number is evidence, not authority): the 4-vs-3 drop reproduces at HEAD *and* at
this audit's own ref `e4a62d7a`; the registry entry is identical to the canonical schema (and
12/12 across the registry); the load path is `validation.py:92`; `TestBundledRegistry`'s three
tests check presence and shape only. **Two things the re-measurement changed relative to the
block comment**, both recorded above rather than adopted as handed over: the fifth artifact is
**0 of 8 passes but not corpus-unswept** (§B.2 disambiguation, with the `C52` false positive
subtracted), and the registry's precedence is **stronger than "a bundled duplicate"** — it
shadows both documented overrides, which is why §D.4 carries its own row at LOW rather than
sitting inside §D.3 as a clause.

**Instrument added to this lineage's standing set:** *compare the line count of a sweep's output
to the row count of the table written from it, and publish both.* §F, fifth lesson.

---

*C322 — 2 LOW (N1, carry row-set contraction, 9 rows restored; N3, SDK schema-resolution order
contradicts its own documented contract), 2 INFO routed off-target (N2 corpus-wide to the
test-vector owner; I-2 to the SDK track, bundled schema copy with no content-equality gate),
1 INFO record (I-1, **five** artifacts swept for the first time in 8 passes, all clean),
1 escalation condition tested and NEGATIVE. Zero net-new against the target — seventh
consecutive clean pass on a blob byte-frozen 54 days. Zero mutation of `web4-standard/`.
C323 = declared NO-OP on the spec side. Ninth consecutive datapoint for the cadence proposal;
this pass produced no finding from the file it audited.*

*Revised 2026-08-06 on review of PR #647: §B.1's inbound sweep printed 3 of the 4 files its own
command returns, and the I-1 swept set inherited the omission. The fifth artifact is restored
and swept (clean); two gaps about how it is **guarded** are routed to the SDK track (§D.3, §D.4);
the failure mode — **a citation-direction sweep is not self-validating, and every existing guard
re-verifies something that is present** — is recorded at §F (fifth lesson) and §G.2. **No verdict
in this document moved.** The pass diagnosed outward-only mirror derivation and then
under-executed its own remedy on its own headline; that is the fourth process finding in a
lineage whose spec has been clean for seven passes, which is an argument for the cadence
proposal, not against it.*
