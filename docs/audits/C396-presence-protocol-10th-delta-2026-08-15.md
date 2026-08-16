# C396 — `presence-protocol.md`, 10th delta

**Date:** 2026-08-15
**Target:** `web4-standard/core-spec/presence-protocol.md` (blob `6414a7fe`, 722 L) and its bound artifact tree
**Slot:** C356 + 40 (rotation arithmetic)
**Form:** SHORT. C316 guard 7 caps this slot at a NO-OP record unless the pass asks a question no instrument has asked. It did — the *inverse* of the question nine passes asked — so findings are filed and the full mirror-set apparatus is not re-run.
**Lineage:** internal-consistency (2026-05-17) → C38 → C88 → C89 (remediation, `0beb1b93`) → C127 → C128 (remediation, `cf0d6cc5`) → C160 → C198 → C236 → C276 (#584) → C316 (#644) → C356 (#687) → **C396** (this 10th delta).

**Enumeration rule (stated per standing rule):** the inclusive rule. This lineage's non-C-numbered member is `docs/audits/presence-protocol-internal-consistency-2026-05-17.md`; it is counted in the 10 audit documents below.

---

## §A — Delta window

| Cell | Value | Command |
|---|---|---|
| Spec blob | `6414a7feecf1ef7760bbed0ae2cc279317c4006e`, 722 L — identical to C356's and C316's baseline | `git rev-parse HEAD:web4-standard/core-spec/presence-protocol.md` |
| Spec last touched | `0beb1b93` (C89, 2026-06-23) — 53 days | `git log -1 -- …/presence-protocol.md` |
| Vector file last touched | `0beb1b93`, same commit — the vectors have been frozen exactly as long as the spec | `git log -1 -- …/presence-protocol-conformance.json` |
| Window | `360c3660..HEAD` = **28** commits | `git rev-list --count 360c3660..HEAD` |
| Window commits touching a presence artifact | **0 of the 19 non-audit artifacts**; **0** including the 10 audit docs | `git log 360c3660..HEAD -- $(git ls-files \| grep presence)` |

**Seventh consecutive fire with both delta halves empty.**

### §A.1 — Denominator, and a correction to this pass's own first draft

`git ls-files | grep presence` returns **29** paths, **10** of which are this lineage's own audit documents ⇒ **19** non-audit artifacts. C356 published **16**. The difference is the **matcher, not growth**: under C356's narrower `grep -i presence-protocol` the figures at HEAD are **26 / 10 / 16**, identical to C356's once its own audit doc is added. Confirmed by dating every artifact — `git log --diff-filter=A` **per file** (never on a directory) puts all 19 at 2026-02-05 … 2026-05-16, months before C356. Nothing entered the set.

**Publish the flag with the count** (v63 — a figure's domain travels with it): `grep presence` = 29 is *case-sensitive*. `grep -i presence` = 30; the extra path is `docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md`.

**The filename denominator is a citation query and cannot return an orphan** (v48). `grep -rl 'presence-protocol' web4-standard/ | grep -v presence` returns **4** files no filename sweep reaches:

```
web4-standard/core-spec/core-protocol.md
web4-standard/core-spec/did-web4-method.md
web4-standard/docs/audits/C75-protocols-cluster-lifecycle-triage.md
web4-standard/testing/conformance/README.md
```

The last one is material to this pass's own finding and is charged in **I-1**. C356 recorded its artifact-token sweep as an empty negative; that was true of the sweep it ran, and this residue is what the *tree-crossing* form returns.

### §A.2 — C356's pre-registered regression set: 4 of 4 hold

| C356 guard 2 cell | C356 value | At HEAD | Verdict |
|---|---|---|---|
| (a) `format` sites across the 12 schemas | **14** (11 `uuid` + 3 `date-time`) | **14** (11 `uuid` + 3 `date-time`) | unmoved |
| (a) `pattern` sites | **6** | **6** | unmoved |
| (b) `grep -rn '\$vocabulary' web4-standard/` | **0** | **0** | unmoved |
| (c) README non-conformance rule + Draft 2020-12 named | present | `README.md:7` and `:78` — re-resolved **by content, not by line** | unmoved |
| (d) corpus non-conformance-off-validation lines | **1** | **1** | presence is still the sole venue |

**C356-N1 is neither remedied nor regressed.** It is re-confirmed incidentally in §B.3 below, on a field it had not been demonstrated against.

### §A.3 — Carries

| Carry | Check | Result |
|---|---|---|
| **C127-1** cross-track facet | `ls v0/common/` | **STILL OPEN** — `error_envelope`, `trust_state`, `witness_entry` only; no `Session`, no `VaultEntry` |
| **C198 B.2** trigger | `grep -rn presence web4-policy/src/*.rs` | **0** — not fired |
| **Consumer gate** | derived per C276's guard from `git grep -lE "hestia_"` across **all** languages first, then narrowed — not by reusing a prior token list | **NEGATIVE, 9th time.** Hits are the hub crates, `web4-core/src/lct.rs`, and 3 documents. No presence-protocol twin in-repo |
| **C316's routed N1** | discharged by C342 §F | **not re-reported** (C356 §A.3 settled this; if it regresses it is web4-lct's row) |

---

## §B — The question no instrument has asked

Nine passes asked, of the vector file: *do its `shapeMatchesSchema` refs resolve?* C127 (`:108`) answered "all 7 distinct refs resolve"; C160 (`:97`) and C378 (`:276`, another lineage, two days ago) re-ran the same forward direction. **This pass ran it backwards: which of the normative schemas is never an assertion target, and does anything execute the assertion at all?**

Instrument: walk **every node class** (`setup` as well as `steps`, per C356 guard 7) of all 14 scenarios; resolve each `shapeMatchesSchema` by `$id` **and** by JSON-Pointer fragment against the 12-schema store; then classify each of the 8 tools by what its assertion targets.

Measured: **17 tool-bearing nodes · 12 `shapeMatchesSchema` sites · 7 distinct targets · 7 of 7 resolve** (both `$id` and fragment). No dangling ref. The forward direction is clean, as it has been for nine passes.

Backwards:

| Tool | Invocations | Success-path output-shape assertion | Error-shape |
|---|---|---|---|
| `hestia_connect` | 2 | P0-001, P1-003 → own `$id` | — |
| `hestia_begin_action` | 5 | P0-002 → own `$id` (4 `setup` nodes bare) | — |
| `hestia_query_history` | 1 | P0-006 → own `$id` | — |
| `hestia_record_outcome` | 1 | P0-003 → own `$id` | — |
| `hestia_request_witness` | 1 | P0-008 → own `$id` | — |
| `hestia_query_policy` | 4 | P0-007, P1-001/2/4 → the **v1** `$id` (ratified — §E) | — |
| **`hestia_vault_get`** | 2 | **NONE** | P0-004, P0-005 → `error_envelope` |
| **`hestia_vault_set`** | 1 | **NONE** — bare `setup` node, `expect: {}` | — |

**6 of 8.** And by schema rather than by tool — the better denominator, because it is closed and project-internal: of the **12** normative schemas, **9 are reachable** (7 as direct targets, plus `trust_state` and `witness_entry` transitively via `$ref` from `record_outcome`/`query_history` outputs) and **3 are never reachable** — `v0/tools/hestia_query_policy` (ratified-intentional), `hestia_vault_get`, `hestia_vault_set`.

### §B.1 — Why the coverage gap is *not* the finding

Framed as *"the two credential tools have no success-path vector,"* this is a bare coverage-absence claim, and this corpus has already ratified the answer to it. `C372:411-412` declines a structurally identical observation — 5 of 15 entity types with no vector anywhere — in terms:

> **Not charged this pass (coverage ≠ defect, per v43)**

That is the "conformance suites are never exhaustive" objection, already house rule. C127-1 is the instructive contrast: it survived at LOW **not** because coverage was missing but because the README's closed-conjunction prose was *factually incomplete for a bound directory*. A prose defect survives; a coverage complaint does not.

So the coverage measurement is evidence. The finding is one rung down.

### §B.2 — N1 (MED): the §7-bound directory asserts a universal that is false, in the section whose job is to state coverage

`web4-standard/schemas/presence-protocol/README.md:69-71`, under the heading `## Validation` (`:67`):

> The conformance vectors in `web4-standard/testing/conformance/presence-protocol-conformance.json` **bind each tool's output** to the `$id` URLs above via `shapeMatchesSchema`.

*Each* tool's output. Measured: **6 of 8**. `hestia_vault_get`'s output `$id` is bound by nothing — its two bindings are both to `error_envelope`'s `$id`, i.e. to the failure shape. `hestia_vault_set` is bound to no `$id` at all. Neither vault schema `$id` occurs anywhere in the vector file: `grep -c 'schemas/presence-protocol.*vault' …conformance.json` = **0**.

This is not an undisclosed gap — charging *that* would be charging the project's disclosure discipline, which this corpus does well and which C378 correctly protects. **It is the opposite: the same document discloses vector-absence two paragraphs earlier and then contradicts itself.** `README.md:63-65` states that `Session` and `VaultEntry` *"also have no conformance vector. Authoring their schemas … and their `resources/read` vectors is pending."* `:44-45` ships a four-item *"known-gap ledger, not a permanent exemption."* `:72-74` self-discloses the absent standalone validator. The document's discipline is to name what is not covered — and then `:71` asserts a universal that its own §B table falsifies for two tools, one of which reads and releases credentials.

§7's precedence clause makes this directory normative: *"The Schemas directory is normatively bound by this clause, not only the vectors JSON."* The false sentence is inside the bound directory, in the section an implementer reads to learn what validation exists.

**The harm is a divergence between two MUSTs in the same §7 list.** Item 1 requires implementing all 8 tools *"with the documented input and output shapes"*; item 5 requires passing the vectors. Executed, not asserted:

```
§3.5 vault_get output example {value, approvalToken:null}   → PASS
§3.6 vault_set output example {stored, entryId}             → PASS
vault_get + {allowed_consumers, scope} alongside the secret → FAIL
   "Additional properties are not allowed ('allowed_consumers', 'scope' were unexpected)"
```
(`jsonschema` 4.26.0, `Draft202012Validator`, `RefResolver` over the 12-schema store, validator scope published per C163.)

Both vault schemas are **sound** — the gap is assertion-side, not schema-side. A daemon returning the secret plus the entry's `allowed_consumers` and `scope` violates §7 item 1 and the precedence clause, and **passes every conformance vector**, satisfying item 5. The `additionalProperties: false` closure that prevents credential-metadata leakage does real work that no vector ever invokes — and `README.md:71` tells the implementer it does.

**Severity MED, not LOW.** C127-1 was LOW because nothing bound broke. Here something demonstrably did: **the false universal has been consumed as a warrant.** `C378:274-278` (registries lineage, 2026-08-13) declines a finding on the ground that

> **The exclusion is DISCLOSED at the point of use.** … `:71-72` records that the tools bind via `shapeMatchesSchema` … Verified live: … carries **12** `shapeMatchesSchema` occurrences. The tree is not unvalidated; it is validated by a different, declared mechanism.

C378 verified the **operand** (12 occurrences) and never the **population** (8 tools) — v55 exactly. **Routed, not re-adjudicated:** C378 rests its decline on at least five independent grounds; that its argument #3 carries an overstated warrant does not disturb the decline, which is another lineage's disposition and scoped to its locus (v51). Recorded so C378's successor can re-weight one limb.

**Fix shape is ratified and cheap** — the same one C128 applied to C127-1: amend `:71` to state what is actually bound (6 of 8 tool outputs; `vault_get` bound only to the error envelope; `vault_set` unbound), and add the pair to the `:44` gap ledger or a §8 drift row. **Routed, not applied** — this pass mutates nothing.

### §B.3 — N2 (LOW, routed OUT — venue is the runner owners): the named mechanism has zero executors

`README.md:71` names `shapeMatchesSchema` as the binding mechanism. **Who executes it?** (v45/v50 — a mechanism's modality is only as strong as its enforcer's caller count.) There is no in-repo presence validator; the three known conformance runners live in `hestia/plugin-sdk/{typescript,python,rust}` and all three load *this repo's* vector file by path. Measured across all three:

| Runner | reads `shapeMatchesSchema`? | JSON-Schema dependency? | executes |
|---|---|---|---|
| `typescript/test/conformance/conformance.test.ts` | declares it at `:45` as an optional interface field; **read by nothing** | none | `fieldChecks`, `ordering` |
| `python/tests/conformance/test_conformance.py` | no occurrence | none | `fieldChecks` (`:329`), `ordering` (`:332`) |
| `rust/tests/conformance.rs` | no occurrence | none | `fieldChecks` (`:495`) |

**0 of 3.** The one runner that names the field declares its *type* and never reads it. So even for the 6 tools whose outputs *are* bound, passing the vectors asserts only `fieldChecks` — and P0-007's `fieldChecks` exercise three fields of a nine-property schema.

This is **not presence's to fix** and is not charged here: the runners are another repo's artifacts and the vector file is a legitimate declarative surface whose consumers may implement as much of it as they choose. It is filed because it sets N1's consequence — the sentence at `:71` describes a binding that, at present, nothing anywhere performs. **Routed to the plugin-SDK conformance-runner owners**, jointly with N1's addressee.

### §B.4 — I-1 (INFO): three sites overstate this tree's coverage, and the pattern is one-directional

| Site | Claim | Ground truth | Command |
|---|---|---|---|
| `C160:97` | *"all **14** vector `shapeMatchesSchema` `$ref`s"* | **12** occurrences; 14 is the **scenario** count. Scenarios **P0-009 and P0-010 carry zero** | `grep -c shapeMatchesSchema` |
| `C127:108` | *"all **13** schemas parse"* | **12** — already corrected by `C160:103`, recorded here only to show the pair | `git ls-files` over the tree |
| `web4-standard/testing/conformance/README.md:15` | the presence row's scenario count is **10** | **14** scenarios | `python3 -c "…len(…['scenarios'])"` |

The README row is **stale, and datable**: it last moved at `0405999d` (2026-05-16); `P1-004` entered the vector file at `ac9de279` (2026-05-18), and `git merge-base --is-ancestor 0405999d ac9de279` succeeds — the count was correct when written and was not updated when the v1 scenarios landed. It sits in one of the four **orphan** files §A.1 recovered; no filename sweep in ten passes could see it.

C160's "14" is not a bare typo and is worth stating precisely: substituting the scenario count for the shape-ref count **asserts a 1:1 scenario↔shape-ref coverage that does not hold**, and the two scenarios it silently covers for (P0-009, P0-010) are the `resources/read` pair — the very surface C127-1 had flagged as vector-less, in the audit whose job was to verify C127-1's remediation. Run your strictest rule on your own lineage first (v44): this lineage's own instrument absorbed the gap it had just charged.

### §B.5 — Negatives, published so the positives are interpretable

- **All 7 distinct `shapeMatchesSchema` targets resolve** by `$id` *and* by JSON-Pointer fragment. Ten passes of forward-direction checking remain correct.
- **`additionalProperties` is a consistent idiom, not a defect:** 8 of 8 tool `input` defs are `true`, 9 of 9 tool `output` defs are `false`. Permissive in, closed out — deliberate and uniform. Not charged.
- **C356-N1 re-confirmed on a new field, incidentally.** `hestia_vault_set`'s `entryId` carries `format: uuid`; executed, `{"stored": true, "entryId": "not-a-uuid"}` **PASSES**, because `format` is annotation-only under the Draft 2020-12 the README names. The two findings compose: even if a vector *did* assert `vault_set`'s output, the constraint on its only identifier would not bite. Evidence for C356-N1's live status, **not a new charge**.

---

## §E — Refuted / declined, with the reason each was killed

| Candidate | Verdict | Why |
|---|---|---|
| *"P0-007, a v0 scenario, asserts against the v1 `query_policy` schema"* | **REFUTED — ratified, do not resurrect** | Polarity inverted. `C88-3` charged the *opposite* (P0-007 bound the strict v0 schema a v1 daemon cannot satisfy); `C89` repointed it; `C127:44-50` mechanically confirmed the superset property; `C160:94` lists it as *"Intentional + self-documented."* The novelty matcher killed this before it reached policy review. |
| *"`v0/tools/hestia_query_policy` is an orphan schema"* | **DECLINED** | It is unreachable *because* of the ratified repoint above. Charging it re-charges C89's fix. |
| *"`approvalToken` is 'always null in v0/v1' but nothing asserts it"* | **DECLINED — ratified non-defect** | `C160:95`: *"Permissive schema; always-present-but-optional ≠ conflict."* Executed: output omitting `approvalToken` entirely validates (`required: ["value"]`). Already settled. |
| *"the two credential tools have no success-path vector"* (this pass's first headline) | **DEFLATED to evidence** | `C372:411-412` — *"coverage ≠ defect, per v43."* Survives only as the measurement under N1, never as the charge. Falsified by policy review, which is where the finding's real shape came from. |
| *"there is no in-repo validator"* | **CORRECTED, scoped** | `web4-standard/testing/validator/{README.md,validate_vectors.py}` **exists**; `grep -rn -i presence` over it = **0**. True only as *"no in-repo validator for the presence schemas."* |

---

## Findings

| # | Severity | Class | Disposition |
|---|---|---|---|
| **N1** | **MED** | **net-new, presence-venue** | `schemas/presence-protocol/README.md:69-71` asserts the vectors *"bind **each** tool's output … via `shapeMatchesSchema`"*; measured **6 of 8**. `hestia_vault_get` is bound only to `error_envelope`, `hestia_vault_set` to nothing; neither `$id` occurs in the vector file. The same document discloses vector-absence at `:63-65` and `:44-45`, so this is an internal contradiction in a §7-bound directory, not an undisclosed coverage gap. Consequence: §7 item 1 and item 5 diverge — a `vault_get` reply leaking `allowed_consumers`+`scope` alongside the secret fails the normative schema (executed) and passes every vector. Already consumed as a decline warrant by `C378:276`. **Routed — fix shape ratified by C128** |
| **N2** | LOW | routed OUT (runner owners) | `shapeMatchesSchema` has **0 of 3** executors among the conformance runners that consume this vector file; only the TS runner declares the field (`conformance.test.ts:45`) and nothing reads it. Sets N1's consequence; not presence's to fix |
| **I-1** | INFO | instrument | Three sites overstate this tree's coverage: `C160:97` "14" (12), `C127:108` "13" (12, already corrected), `testing/conformance/README.md:15` "10" (14) — the last stale since `ac9de279`, and invisible to every filename sweep this lineage has run |
| **I-2** | INFO | instrument | The filename denominator is a citation query: `grep -rl 'presence-protocol' web4-standard/ \| grep -v presence` recovers **4** orphan files, one of which carries I-1's third site. C356's empty artifact-token residue was true of the sweep it ran; the tree-crossing form is not empty |
| — | REFUTED/DECLINED | — | ×5 (§E), including this pass's own first headline |

**ZERO mutation of `web4-standard/`.** No spec, schema, vector, README or SDK file was edited. C316's routed N1 stays discharged by C342 and is not re-reported.

**No accountability self-audit block:** this pass creates no surface and performs no consequential act — it writes one document under `docs/audits/`.

---

## Guards for the next presence delta (C436)

1. **All C276 / C316 / C356 guards still bind and were honoured.** The no-verdict-posture flagship stays killed; `HestiaCallbackSigner`, `web4-policy`'s `Escalate`, the AAEP triple, the §7 conformance-vector gate, C316's REFUTED-GUARD 3(a)/(b) and its four venue-declined artifacts were **not** re-derived. **Add to the do-not-resurrect list:** P0-007→v1 (ratified, §E), the `approvalToken` probe (`C160:95`), and bare coverage-absence framings (`C372:411-412`).
2. **N1's regression set.** (a) `README.md:71` still reads *"bind each tool's output"* — re-resolve **by content, not by line**. (b) The per-tool table in §B: **6 of 8**, `vault_get`→`error_envelope` ×2, `vault_set`→none. (c) `grep -c 'schemas/presence-protocol.*vault' …conformance.json` = **0**. (d) Baseline: 17 tool-bearing nodes / 12 shape sites / 7 distinct targets / 9 of 12 schemas reachable. A move in the table **without** a change to `:71` is the regression; a change to `:71` alone may be the fix — check that the new text matches the table.
3. **N2's regression set.** `grep -rn shapeMatchesSchema` over the three `hestia/plugin-sdk` runners was **1 occurrence, 0 reads**, and none carries a JSON-Schema dependency. **If a runner ever executes it, that is the interesting event** — and the next question is *which vocabulary it selects* (C356 guard 3, same shape).
4. **C356-N1 is still open and now has a second demonstration** (`vault_set.entryId`, §B.5). Its guard-2 cells were 4-for-4 at this HEAD; re-run them.
5. **Live carries:** C127-1 cross-track facet STILL OPEN (do not re-charge the C128-closed half). C198 B.2 trigger NOT fired. Consumer gate NEGATIVE **9th** time.
6. **Method, born this pass — run the sweep BACKWARDS.** Ten passes asked *do the refs resolve* and got a correct answer every time; the defect was in the complement — *which normative artifact is never a target*, and *does anything execute the assertion*. A forward-only integrity check confirms the edges that exist and is structurally blind to the ones that do not.
7. **And check the tree-crossing residue even when the filename residue was empty** (I-2). C356 recorded an empty artifact-token sweep honestly; the orphan carrying a false count was in a *different tree* under the *domain's* word, which is where §A.1's four files came from.
8. **Proportionality:** the SHORT form again. The finding came from executing the artifacts backwards against each other and from policy review killing the first headline — not from re-reading the spec, which was not re-read.
