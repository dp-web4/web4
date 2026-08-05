# C312 — reputation-computation.md 8th Delta Re-Audit

**Date**: 2026-08-04 (18:00 slot `web4-20260804-180032`)
**Target**: `web4-standard/core-spec/reputation-computation.md` (blob `bfdac3ba`, 870 lines, at HEAD)
**Lineage**: C15 → C44/C45 → C84/C85 → C123/C124 → C156/C157 → C194/C195 → C232 → C272 → **C312**
**Window**: `e0d2d4db..HEAD` (C272's own audit commit, 2026-07-28 → `e5f221a4`, 2026-08-04) — **60 commits**
**Method**: v2 protocol; delta re-audit of a byte-frozen target, refute-by-default, all citations
re-derived at live HEAD. Method carries v2–v15 applied; v7/v13/v14 (widen the surface) are the ones
that paid.

---

## Headline

The target is **byte-frozen since `2bc3bafb` (#541)** — 17 days, the same blob C232 and C272 audited.
All four tracked delta-shape mirrors are likewise frozen. `web4-standard/` saw **exactly one changed
file** in 60 commits. That combination is precisely the v13 false-clean trap, so this pass spent its
budget on the surface the lineage has never swept rather than on the bytes it has swept eight times.

It paid, once, in a tree gated by **0 of 8** prior passes:

> **The standard's own JSON Schema forbids a `ReputationDelta` field that two of the standard's own
> core specs emit — and that one of them dereferences.**

`schemas/r7-action-jsonld.schema.json` `$defs.reputation_delta` is `additionalProperties: false` and
has no `role_pairing_in_mrh`. The target's §1 field table `:72` lists it (Required: No) and its §1
"Complete Schema" example emits it at `:26`; `r7-framework.md` emits it at `:273` and `:703`,
constructs it at `:425`, and at **`:535` reads `reputation.role_pairing_in_mrh.mrh_link`** as an
argument to `apply_t3_v3_updates_to_role_pairing`. Machine-verified below: the spec's own emitted
examples fail the standard's own schema with **exactly one** error each, and pass when the field is
removed.

This is **not filed as net-new.** The field is the subject of **carry-C46**, open since C46 and
recorded "STANDS" at every pass since. What is new is its **class**: C46 records the field as an
unimplemented denormalized convenience (*absent* from the SDK deltas). The schema does not merely
omit it — it **rejects** it, and the `:535` dereference was never recorded. Absence is not
prohibition. Per [[feedback_carry_gains_reach_not_truth]] that routes as **reach-escalation with a
class change**, not as a new finding. → **C312-N1 (MEDIUM, routed — the remedy forks across two
owners).**

**The pre-registered net-new candidate was refuted.** Before the sweep, the policy reviewer required
that any `web4:observationCount` finding route as reach-escalation on **C310-N2** (two days old,
open), leaving exactly one candidate admissible as net-new: the *semantic* tension between the
ontology's new `observationCount` comment and the target's `:747` "not their count." It **fails** —
the two name different properties (§B.3). Under the reviewer's binding ruling that findings count
must never size the deliverable, that refutation is a deliverable, not a shortfall.

**§A: 0 regressions, all carries HELD, 2 recorded paths re-verified.**
**§B: 1 reach-escalation (MED) + 1 LOW + 1 INFO instrument finding. ZERO mutation.**
**C313 disposition: NO-OP** — every item here is operator/author-owned.

---

## §A — Regression Verification

Kept deliberately tight (policy-review condition 3): the frozen mirror set gets **verification, not
narration**. Held rows get a binary re-verification citing the owning pass; no re-argument of merits.

| Carry | Live-HEAD result |
|---|---|
| **C194-N1** (HIGH, SDK) — Rust `ReputationDelta` wire shape | **STANDS** — `r6.rs` byte-frozen `3f941988` (2026-07-09), 0 commits in window. **Direction re-derived (v12), and it survives**: unlike C304-N1's inversion, the standard's own `$defs.reputation_delta` does **not** back the Rust shape — `sovereign_strength` is absent from the schema, as it is from the spec (`grep -rn sovereign_strength web4-standard/` = **0**, re-run). Carry points the same way it was filed. |
| **C194-N3/N4** (operator DESIGN-Q) — §7 Talent-decay layer split + 10× rate | **STAND** — target §7 untouched; `t3-v3-tensors.md` unmoved in window. Neither side moved. |
| **C194-N5** (W4IP-N5) — bad-faith-emergency lacks its sibling's disclaimer | **HELD** — `:367-371` unchanged, asymmetry with `:363-366` intact. |
| **C194-N7** (SDK) — `r6.py to_jsonld()` truthiness-drops Required:Yes fields | **HELD** — `r6.py` frozen `766611ef`. **Gains a second face from §B.1**: the schema requires only 4 fields, so a truthiness-dropped `t3_delta` is rejected by the *spec table* but accepted by the *schema*. |
| **C194-N8** (SDK) — wasm hardcodes empty factors | **HELD** — mirror unmoved. |
| **C156-3** (spec + Python-SDK owners) — Rust `sovereign_strength` ahead of both | **STANDS** — gate re-run at HEAD: `grep -rn sovereign_strength web4-standard/` = **0**. |
| **C156-4** (hub track) — temporal fold code-triggered, not Law-Oracle-rule-triggered | **HELD** — C272's corrected paths re-verified at HEAD: `temporal_delta` at `rest.rs:3014`, `grep -n temporal hub/hub-lib/src/law.rs` = **0**. The 20-file `hub/hub-lib` wave in this window did **not** add a temporal law section. |
| **carry-C46** — `role_pairing_in_mrh` denormalized convenience | **STANDS — and its CLASS CHANGES.** See **C312-N1**. `:26` and `:72` byte-identical; still absent from both SDK deltas (`grep -c role_pairing` → `reputation.py` **0**, `r6.py` **0**). New: the standard's own schema *forbids* it, and `r7-framework.md:535` *reads* it. |
| **C232-N1** (LOW) — `reputation.delta.category` has no producer-side field | **STANDS, unbridged, and now confirmed from a third side**: §1 field table re-read = **15 fields**, no `category`; `grep -c '"category"'` in `r7-action-jsonld.schema.json` = **0**. The standard's schema agrees with the spec that no producer-side field exists; the consumers (`web4-policy`, `hub-law-schema.md:240/:292`, `law.rs:471`) still select on it. |
| **C272-N1** (MED, prospective) — #580 "Absence NEVER grants" vs §4 fail-open | **STANDS, unrouted-back.** #580 unchanged in window (`proposals/` untouched); §4 `:290-301` unchanged. No answer recorded from either referent. |
| C194-N2 / C194-N6 | **remain CLOSED** (#526); C214-N1 remains VERIFIED; C154-N1 remains consumed; C192-N1 remains closed. |

**§A verdict: 0 regressions, 0 carries invalidated, 0 carries closed. One carry (C46) changes class.**

---

## §B′ — Mirror set, re-derived at live HEAD (the instrument, published)

**Pre-registered admission criterion (written before the sweep, per v7).** M1 = computes or carries a
`ReputationDelta`. M2 = an in-standard **normative peer** that constrains one (schema, JSON-LD
context, conformance suite, ontology) — classified by **role, not path**. M3 = consumes one. Evidence-
only artifacts are read but cannot carry a finding.

### B′.1 — Tracked delta-shape mirrors (M1): all frozen, verified not narrated

| Mirror | Blob / last mover | In-window commits |
|---|---|---|
| `implementation/sdk/web4/reputation.py` | `759eaefa` (2026-04-17) | 0 |
| `implementation/sdk/web4/r6.py` | `766611ef` (2026-05-14) | 0 |
| `web4-core/src/r6.rs` | `3f941988` (2026-07-09) | 0 |
| `web4-trust-core/src/bindings/wasm.rs` | `3f941988` (2026-07-09) | 0 |

**Correction to a recorded path.** C272's §B′ lists `wasm.rs` without a tree prefix; at HEAD the file
is `web4-trust-core/src/bindings/wasm.rs` (C194-N8 cited it correctly; the C272 shorthand was lossy).
`git log -1 -- web4-core/src/wasm.rs` returns empty — recorded so the next pass does not read that
empty result as a deleted mirror.

`web4-policy` remains a **CONSUMER, not a mirror** (C272 guard **re-tested, not inherited**: it still
selects over `reputation.delta.category` and computes no delta). The 20-file `hub/hub-lib` wave is
emitter/consumer-side; `grep -c role_pairing`/`temporal` over `law.rs` confirm it did not reach this
file's surface.

### B′.2 — Lineage citation census, re-measured (and it disagrees with two prior numbers)

Method carry v9: *a number an agent or a reviewer hands you is not a measurement.* The policy reviewer
supplied a census; I re-ran it; **we disagree, and so did my own first matcher.** All three results
published rather than reconciled silently.

Matcher A: `grep -c -F '<token>' <doc>` (GNU grep — **matching lines**).
Matcher B: `grep -c -inE 'test.?vector|conformance vector|rep-00' <doc>`.
Scope: the lineage's **8 audit passes** — internal-consistency (pre-C-series), C44, C84, C123, C156,
C194, C232, C272 — named explicitly rather than globbed.

**Scope correction, found by the mandatory post-write re-run** ([[feedback_publish_the_instrument]]:
re-run every count *after* writing, because your own document changes the scope). The draft of this
section described the set as *"the 8 docs matching `docs/audits/*reputation*`"*. That glob returns
**11** prior docs, not 8 — it also picks up the three **remediation** docs (C124, C157, C195), which
are not audit passes. The denominator of 8 is correct for *passes*; the glob naming it was not. All
published values below re-verified against the explicitly-named set and unchanged. The zeros are in
fact **wider** than published: over all 11 prior docs, `schemas/`, `testing/conformance/` and
`t3v3-ontology` still return 0, 0 and 0 from the remediation docs too. Reported at the narrower,
defensible denominator.

| Tree / artifact | Matcher A | Matcher B (correct) | Reviewer's figure |
|---|---|---|---|
| `test-vectors/` (reputation vectors) | 5 of 8 | **7 of 8** | 5 of 8 |
| `ontology/t3v3-ontology.ttl` | 3 of 8 | **3 of 8**, none since C84 | 3 of 8, none since C84 ✓ |
| `schemas/` (any) | **0 of 8** | **0 of 8** | not measured |
| `schemas/contexts/` | **0 of 8** | **0 of 8** | 0 of 8 ✓ |
| `testing/conformance/` | **0 of 8** | **0 of 8** | 0 of 8 ✓ |
| `deployment/` | **0 of 8** | **0 of 8** | 0 of 8 ✓ |

**Why the vector cell moved from 5 to 7.** Matcher A is a path-shaped token, and the artifact **changed
path mid-lineage**: C44 cites it as `implementation/sdk/web4/tests/vectors/reputation-operations.json`,
while C123 onward cite `test-vectors/reputation/reputation-operations.json`; C232 cites it by phrase
("conformance vector", `rep-002`) with no path at all. A path-shaped matcher silently under-reports a
lineage across a file move — the same failure shape as v11's casing rider, on the path axis. The
reviewer's set and my Matcher-A set were both wrong, in *different* cells (the reviewer had C44 in and
C156 out; Matcher A had the reverse).

**Chased, and refuted, before it cost anything.** A mid-lineage path change is the C306-N1 duplicate-
suite shape, so it was tested directly: `find . -name reputation-operations.json` returns **exactly one
file**, and `web4-standard/implementation/sdk/web4/tests/vectors/` is **absent** at HEAD. It was a move,
not a fork. **No duplicate IDs, no finding.**

### B′.3 — First-time gating: the subject-matter artifact set

Derived by `grep -rl -iE 'reputation'` over `schemas/ test-vectors/ testing/ ontology/ deployment/`
(paths published; `deployment/` returned **0** for token `reputation`). **16 artifacts** carry the
target's subject matter. The lineage has gated **one** of them.

The three trees gated for the first time in eight passes are `schemas/`, `schemas/contexts/`, and
`testing/conformance/`. **`schemas/` is where C312-N1 lives.** Note the distinction, because the two
instrument defects are different: `t3v3-ontology.ttl` was **dropped** from a set that once held it
(contraction, v8 → C312-N3); `schemas/` was **never derived into the set at all** (under-derivation,
v7/v14). Only the second one paid.

Newly-gated artifacts and their disposition:

| Artifact | Role | Result |
|---|---|---|
| `schemas/r7-action-jsonld.schema.json` | **M2 normative peer** | **C312-N1, C312-N2** |
| `schemas/contexts/r7-action.jsonld` | M2 | clean (see §B.3 refutation) |
| `ontology/r7-action.jsonld` | M2 (OWL face) | clean (see §B.3 refutation) |
| `testing/conformance/r6-r7-actions.json` | M2 | clean; states a `role_lct` MUST invariant (`:147`) the schema and spec both honour |
| `test-vectors/schema-validation/r7-action-jsonld-validation.json` | M2 | clean; **0** `role_pairing` occurrences — the reason N1 is latent |
| `ontology/hub-law.ttl`, `ontology/role-extension.*`, `test-vectors/{atp,capability,lct,r6}/…` | evidence-only | no findings |

---

## §B — Findings

### C312-N1 (MEDIUM — reach-escalation with a CLASS CHANGE on carry-C46; route, do NOT self-apply) — the standard's own schema rejects a `ReputationDelta` field two core specs emit and one dereferences

**The six spec-side sites** (`grep -rn role_pairing_in_mrh web4-standard/`, full output, 6 hits):

| Site | Kind |
|---|---|
| `reputation-computation.md:26` | §1 "Complete Schema" **emitted example** |
| `reputation-computation.md:72` | §1 field table — **normative row**, Required: No |
| `r7-framework.md:273` | emitted example |
| `r7-framework.md:425` | pseudocode **constructs** it (`role_pairing_in_mrh=mrh_role_link`) |
| `r7-framework.md:535` | pseudocode **dereferences** it: `mrh_link=reputation.role_pairing_in_mrh.mrh_link` |
| `r7-framework.md:703` | emitted example |

**The schema side.** `schemas/r7-action-jsonld.schema.json` `$defs.reputation_delta` (`:317-363`) has
14 properties, `additionalProperties: false` (`:362`), and **no `role_pairing_in_mrh`**. Its own
`description` declares it authoritative *"per r7-framework.md"* — the very file that constructs and
dereferences the field.

**Machine verification (instrument published; run at HEAD).** Fenced ```json blocks containing the
field were extracted from both core specs and validated against `$defs.reputation_delta` with
`jsonschema.Draft202012Validator`, each with a **control** run identical but for removing the field:

```
web4-standard/core-spec/reputation-computation.md:21   1 error  -> Additional properties are not allowed ('role_pairing_in_mrh' was unexpected)
    CONTROL (field removed): 0 errors
web4-standard/core-spec/r7-framework.md:268            1 error  -> Additional properties are not allowed ('role_pairing_in_mrh' was unexpected)
    CONTROL (field removed): 0 errors
```

**Instrument caveats, stated rather than buried** (v13 #6 — an identically-shaped disagreement is a
signature of the verifier). The first run reported **3 of 3 blocks UNPARSEABLE**, which is that
signature; the cause was the specs' `+0.01` signed-numeric literals, not the schema. After normalising
`: +N` → `: N` (a display convention, not a data difference), 2 of 3 blocks parse and yield the result
above. The third (`r7-framework.md:667`) contains bare `[...]`/`{...}` ellipsis placeholders and is
**prose-illustrative, not machine-parseable**; it was checked by inspection and carries the field at
`:703`. So: **2 of 3 machine-validated, 1 inspected** — no block is silently dropped.

**Why it is latent, and why that bounds severity at MEDIUM** (v13 #5 — bound by the consumption
mechanism). `grep -c role_pairing` over `test-vectors/schema-validation/r7-action-jsonld-validation.json`
= **0** and over `testing/conformance/r6-r7-actions.json` = **0**: no published vector exercises the
field, so both suites pass and no shipped implementation trips it. The SDK never emits it
(`reputation.py` **0**, `r6.py` **0**). The contradiction is real, machine-checkable, and currently
unexercised.

**Direction (v12), and why it is routed rather than resolved.** The corpus splits and the remedy
**forks across two owners**:
- *Option A — add the field to the schema.* Enshrines a field the target itself calls "derivable from
  `role_lct` … carried only as a denormalized convenience" (`:72`) and that no implementation emits.
- *Option B — drop it from the specs.* **Breaks `r7-framework.md:535`**, which passes
  `reputation.role_pairing_in_mrh.mrh_link` into `apply_t3_v3_updates_to_role_pairing`. Under Option B
  that pseudocode needs a replacement source for `mrh_link` — the field's stated derivation
  ("derivable from `role_lct` via the entity↔role MRH pairing") is exactly the resolution step
  `:535` was written to avoid.

Because Option B rewrites reference pseudocode in a **sibling** core spec and Option A amends a
published schema, this is not the auditor's to pick. **Referents: (a) the `r7-framework.md` /
schema owner — pick A or B and apply it to all six sites at once; (b) carry-C46's holder — C46's
disposition is now blocked on that choice, and should not be re-recorded as "STANDS, absent from SDK"
again, because absence was never the whole fact.**

**Severity argued both ways** (per [[feedback_carry_gains_reach_not_truth]]). *For HIGH*: it is a
machine-checkable self-contradiction in ratified normative artifacts, it touches two core specs, and
one of them dereferences the field — a cross-language implementer generating from the schema and
reading the pseudocode gets irreconcilable instructions. *For LOW*: the field is optional, derivable,
unemitted by every implementation, and unexercised by every vector. **MEDIUM** is where those meet:
published conformance evidence disagrees with published normative prose, with no live breakage.

### C312-N2 (LOW — same owner as N1, one fix touches both) — the schema requires 4 of the 11 fields the target's table marks Required: Yes

Measured at HEAD (instrument re-run after the finding was written, per [[feedback_publish_the_instrument]]):

```
spec §1 table fields    : 15
schema properties       : 14
spec Required = Yes     : 11
schema "required"       : 4   [net_trust_change, net_value_change, role_lct, subject_lct]
spec-Yes NOT schema-req : 7   [action_id, action_target, action_type, reason, t3_delta, timestamp, v3_delta]
in spec, NOT in schema  : 1   [role_pairing_in_mrh]     <- N1
in schema, NOT in spec  : 0
```

A document omitting `action_id`, `action_type`, `action_target`, `reason`, `t3_delta`, `v3_delta` and
`timestamp` **passes the standard's schema and violates the standard's field table**. This is weaker
than N1 — an under-constrained schema is a common and often deliberate choice, and no text claims the
schema is exhaustive — so it is filed **LOW**, and only because the two `required` lists are supposed
to describe one wire shape. It **gives C194-N7 a second face**: a truthiness-dropped `t3_delta` is
rejected by the table and accepted by the schema.

**Instrument caveat, published.** My first field-table parser sliced a fixed line range and returned
**13** fields, placing `net_value_change` and `timestamp` in the "in schema, not in spec" column — both
false. Caught because the result disagreed with the target's own text. Re-parsed by regex over the
whole file; the numbers above are the corrected run. (v10 corollary: a verifier is a hypothesis.)

### C312-N3 (INFO — audit instrument; NOT routed to the operator; forward guard self-applied) — the T3/V3 ontology peer was dropped from this lineage's swept set for 5 consecutive passes

`ontology/t3v3-ontology.ttl` is cited by the lineage's first three docs (internal-consistency, C44,
C84 — last on **2026-06-22**) and by **0** of C123, C156, C194, C232, C272. Five consecutive passes
certified this file against a swept set that had silently lost a normative peer — and the gap spans
`01f410db`, the commit that *changed* that peer and is the sole `web4-standard/` change in this window.

Classified as **mirror-set CONTRACTION (v8 / C296 class)**, not ledger-emptied (C300): the §C carry
ledger did not empty, the *swept set* shrank. Measured in **passes, not weeks** — passes are this
track's unit for survival measurement.

**Held at INFO under a rule pre-registered before the sweep**, and applied mechanically: it escalates
to LOW/MED only if re-gating the dropped artifact demonstrates the contraction **caused a miss**. It
did not — the one candidate the re-gate produced (`observationCount` vs `:747`) is **refuted** in §B.3.
The finding that *did* pay came from `schemas/`, which is a different instrument defect
(**under-derivation**, never in the set) and is reported as such in §B′.3 rather than folded in here to
inflate this row. Recorded explicitly because an instrument finding about one's own lineage is the
single place where inflating severity makes a pass look more valuable.

**Forward guard, phrased as a behaviour rather than a path** (so it does not expire when the file
moves — [[feedback_guard_names_a_path_not_a_behaviour]]):

> *Any target whose subject matter is built on T3/V3 has the T3/V3 ontology peer in its swept set,
> whatever that peer is currently called or wherever it lives.*

### §B.3 — Self-refuted candidates (4 killed; DO NOT RESURRECT without re-running the baseline named)

- **PRE-REGISTERED CANDIDATE — "`web4:observationCount` makes evidence count load-bearing, colliding
  with the target's `:747` 'not their count'." REFUTED — one word, two properties (C290).**
  `t3v3-ontology.ttl:107-110` scopes `observationCount` to `rdfs:domain web4:DimensionScore` and
  comments that it exists so *"a relying party weighs a score by its evidence, **not just its value**."*
  Target `:747` states that the reputation **level** *"reflects the direction and consistency of
  accumulated deltas, not their count"* — a statement about how the **value** is computed
  (baseline + recency-weighted average, not accumulation). These are not in tension: the ontology's
  comment **presupposes** exactly what `:747` asserts, and `observationCount` is the mechanism that
  makes `:747`'s limitation safe for a relying party — count carried *beside* the value precisely
  because the value does not encode it. "Count" names a driver of the level in one and evidence
  metadata in the other. **This was the pass's only admissible net-new candidate and it is dead.**
- **"The standard ships two differing `r7-action.jsonld` files." REFUTED — ratified design.**
  `ontology/r7-action.jsonld` (`bbe5b1d9`, 2026-03-20, `ontology#`, camelCase) and
  `schemas/contexts/r7-action.jsonld` (`936c2d92`, 2026-03-24, `ns/`, snake_case) do differ, but
  `docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md:72` states verbatim:
  *"`ontology/t3v3.jsonld` and `ontology/r7-action.jsonld` — left in place for OWL tooling,"* with
  `:41-42` ratifying the separation of concerns. This is the guard C310 recorded (the `ns/` vs
  `ontology#` split is ratified and **not chargeable**); it is re-verified here on a second artifact
  pair. Checked before charging, per method carry v3.
- **"The OWL-tooling face cannot express `roleLCT`, the field carrying the conformance suite's MUST
  invariant (`r6-r7-actions.json:147`)." REFUTED by direct read** — `ontology/r7-action.jsonld:30`
  carries `"roleLCT": { "@id": "web4:roleLCT", "@type": "@id" }` and `:35` carries `actionType` under
  the term `action`. The apparent absence was an artifact of reading a `diff` hunk (which shows only
  changed lines) instead of the file. Recorded as a method note: **never charge an absence from a diff.**
- **"The reputation vectors forked into two suites at the mid-lineage path change." REFUTED** — one
  file at HEAD, old directory absent. See §B′.2.

**Also tested and clean.** The `hub/hub-lib` wave (20 files, the window's bulk) is DISJOINT: `law.rs`
gains no temporal section (`grep -n temporal` = 0) and no `role_pairing` anywhere. The whitepaper and
`docs/whitepaper-web` commits are publication-side. `web4-trust-core`'s two commits are `.gitignore`
and `Cargo.lock`. No protected term was redefined, so no glossary check applied. `deployment/`
(v13's operational tree, gated here for the first time) returns **0** for token `reputation`.

---

## §C — Carry Ledger (post-C312)

**Consumed/closed this audit**: none.

| Row | Status | Locus at HEAD |
|---|---|---|
| **carry-C46** | **STANDS — CLASS CHANGED, now blocked on C312-N1's fork** | `:26`, `:72`; schema `:317-363`; `r7-framework.md:535` |
| **C312-N1** (MED) | **NEW ROUTE** → (a) `r7-framework.md`/schema owner, (b) C46 holder | 6 spec sites + `$defs.reputation_delta` |
| **C312-N2** (LOW) | **NEW ROUTE** → same owner as N1 | schema `required` vs `:68-84` |
| **C312-N3** (INFO) | **self-applied forward guard**, not routed | this lineage's swept set |
| C194-N1 (HIGH, SDK) | STANDS — direction re-derived and **confirmed**, not inverted | `r6.rs` `3f941988` |
| C194-N3/N4 (operator DESIGN-Q) | STAND | target §7 |
| C194-N5, C194-N7, C194-N8 | HELD (N7 gains a second face via N2) | `:367-371`; `r6.py:649`; `wasm.rs:848` |
| C156-3, C156-4 | STAND — gates re-run at HEAD, both **0** | `web4-standard/`=0; `law.rs` temporal=0 |
| C232-N1 (LOW) | STANDS, unbridged — now confirmed from the schema side too | `:68-84`; schema `category`=0 |
| C272-N1 (MED, prospective) | STANDS, **no answer recorded from either referent** | `:290-301` vs #580 |
| C194-N2/N6, C214-N1, C154-N1, C192-N1 | remain closed / verified / consumed | — |

**C313 disposition: NO-OP.** N1 and N2 are owner-forked; N3's remedy is a method guard already
applied here. Nothing in this pass is the target's to fix, and **zero mutation** was performed.

**Rotation** → next fire = **acp = C314** (fixed round-robin; reputation followed by acp). Standing
proportionality ruling from C274 applies to that slot: if it opens on an empty window with the spec
still at `fb0075fc`, the correct output is a **short no-op record**, not a full delta doc.

### Guards for the next reputation delta (~C352)

1. **`schemas/`, `schemas/contexts/`, `testing/conformance/` are now IN this file's swept set** — they
   were gated for the first time at C312 after 0 of 8 passes, and `schemas/` is where the finding was.
   Do not let the set contract back.
2. **The T3/V3 ontology peer is in the swept set for any T3/V3-built target** (C312-N3's behaviour-
   phrased guard).
3. **Do NOT re-charge** the `ontology#`/`ns/` dual-context split (ratified, `RECONCILIATION:72`), the
   `observationCount`/`:747` semantic collision (refuted: two properties), the vector "fork" (one file),
   or the OWL-face `roleLCT` gap (present at `:30`).
4. **Check first whether C312-N1's fork was answered** — if either option was applied, all six
   `role_pairing_in_mrh` sites and the schema must have moved *together*; a partial application is the
   next defect.
5. **Path-shaped matchers under-report across file moves.** The reputation vectors changed path
   mid-lineage; a `test-vectors/`-shaped token missed 2 of 7 citing passes. Baseline every path matcher
   against a phrase matcher (v11's casing rider, on the path axis).

---

*Audit instrument: the frozen target was, for the fourth consecutive pass, the least informative
artifact in its own audit — but this time the yield did not come from the window at all. It came from
asking which of the standard's own normative artifacts had never been opened, and finding that the
answer was fifteen of sixteen. The one finding that survived was machine-checkable in ten lines, had
been true since 2026-03-24, and was invisible to eight passes because the swept set was inherited
rather than re-derived. The subtractive half was larger than the additive half: four candidates were
killed, including the only one the policy review admitted as net-new — and under the reviewer's
binding ruling that findings count must never size the deliverable, that is the pass working, not the
pass failing.*
