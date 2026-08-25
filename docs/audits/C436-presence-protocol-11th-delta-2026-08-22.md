# C436 — `presence-protocol.md`, 11th delta

**Date:** 2026-08-22
**Target:** `web4-standard/core-spec/presence-protocol.md` (blob `6414a7fe`, 722 L) and its bound artifact tree
**Slot:** C396 + 40 (rotation arithmetic)
**Form:** SHORT. The five obligations C396 pre-registered are the preamble, not the deliverable — they are near-certain HOLDs against a 60-day-frozen target with an empty window, and this pass does not present "5/5 HOLD" as its yield. The budget lands on §B.
**Lineage:** internal-consistency (2026-05-17) → C38 → C88 → C89 (remediation, `0beb1b93`) → C127 → C128 (remediation, `cf0d6cc5`) → C160 → C198 → C236 → C276 (#584) → C316 (#644) → C356 (#687) → C396 (#720) → **C436** (this 11th delta).

**Enumeration rule (stated per standing rule):** the inclusive rule. This lineage's non-C-numbered member is `docs/audits/presence-protocol-internal-consistency-2026-05-17.md`; it is counted in the 11 audit documents below.

**Mutation:** ZERO. Every finding is reported, not applied. Remediation is a separate reviewed PR.

---

## §A — Delta window

**Target byte-frozen 60 days.** `git hash-object web4-standard/core-spec/presence-protocol.md` = `6414a7feecf1ef7760bbed0ae2cc279317c4006e`, 722 L, last touched `0beb1b93` (C89, 2026-06-23). The conformance vector file is frozen at the **same commit** (`45b7bc20`). The schemas `README.md` is frozen at `cf0d6cc5` (C128, 2026-07-02).

**Window** `360c3660..HEAD` = **76 commits**, of which **0** touch any of the **19** non-audit presence artifacts (path-bound, `-- <the 19 files>`). This is the **8th consecutive fire with both delta halves empty**.

### §A.1 — Denominator, with its matcher (v40)

| Cell | Value | Matcher |
|---|---|---|
| presence artifacts | **30** | `git ls-files \| grep presence` — **case-sensitive** |
| — audit documents | **11** | `… \| grep '^docs/audits/'` |
| — non-audit artifacts | **19** | `… \| grep -v '^docs/audits/'` |
| case-insensitive variant | **31** | `grep -i` — adds `docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md` |

C396 published 29 / 10 / 19. The **+1 is C396's own audit document**; the non-audit population is unchanged at 19. Publishing the matcher rather than the count is what makes that decomposable — C396 pinned the `-i` caveat and this pass carries it forward rather than re-deriving a bare number.

### §A.2 — C396's four pre-registered NEXT-DELTA checks: 4 of 4 HOLD

| # | Check | Baseline | Measured | Verdict |
|---|---|---|---|---|
| 1 | `schemas/…/README.md` still asserts the vectors *"bind **each** tool's output … via `shapeMatchesSchema`"* — **resolved by content, not line** (v65) | present at `:71` | present, `:71`, byte-identical | **HOLD** — C396-N1 still open |
| 2 | backward-sweep table | 17 nodes / 12 sites / 7 targets / 6-of-8 tools / 9-of-12 reachable | **17 / 12 / 7 / 6-of-8 / 9-of-12** | **HOLD** — no move |
| 3 | `shapeMatchesSchema` executors across the 3 plugin-SDK runners | 1 occurrence, 0 reads | **1** (`plugin-sdk/typescript/test/conformance/conformance.test.ts:45`, an optional interface field), **0 reads**; all 3 runners load the vector file, none has a JSON-Schema dependency | **HOLD** — C396-N2 still open |
| 4 | C356 guard-2 regression set | `format`=14 (11 uuid + 3 date-time), `pattern`=6, `$vocabulary`=0, README non-conformance line corpus-sole | **14 (11+3) · 6 · 0 · corpus-sole** | **HOLD** 4/4 |

Check 2's decision rule was pre-registered by C396: *a move in the table without a change to `:71` is the regression; a change to `:71` alone may be the fix.* Neither moved. The rule did not fire.

**Obligation 4 was executed read-only against `dp-web4/hestia` and is route-out only** — no edit was made in that repo, and none is proposed from here.

### §A.3 — Carries

- **C127-1** — STILL OPEN. `v0/common/` = `error_envelope`, `trust_state`, `witness_entry` only (3 files, unchanged).
- **C198 B.2** — NOT fired (0).
- **C356-N1** — open, unchanged (`vault_set.entryId` `format: uuid` accepts `"not-a-uuid"`; no `$vocabulary`, no validator in-tree for these schemas).
- **C316's routed N1** — remains discharged by C342. Not re-reported.
- **C396-N1 / N2** — both open; N2's venue is the runner owners, not this lineage.
- **Consumer gate** — NEGATIVE, 10th consecutive.
- **`C374-N4` and `C390-N2`** — DISCHARGED at C434. Not re-routed.

---

## §B — The resource axis

C396 ran the sweep backwards on the **tool** axis: *which tool outputs are bound by a vector?* (6 of 8). The complement it did not run is the **resource** axis: *which of the spec's resources are exercised by a vector at all?*

**This section's heading in this pass's first draft was "the question no instrument has asked." That was wrong** — `C127:24` asked it and answered it (2-of-6, rated LOW). What no instrument has checked is narrower: whether any *index* asserts the contrary. The corrected framing is carried through §B.2.

The spec exposes **six** resources (§4, `:436-458`): 4 fixed + 2 parameterized. The vector file exercises **two**.

```
$ python3 -c "…json… collect steps with a 'resource' key"
scenarios          : 14
distinct tools     : 8   [begin_action, connect, query_history, query_policy,
                          record_outcome, request_witness, vault_get, vault_set]
   — assertion-bearing : 7   (vault_set appears only in P0-004 setup, no `expect`)
distinct resources : 2   ['hestia://society/state', 'hestia://witness/recent']

spec resources     : 6
ZERO conformance   : 4
   - hestia://context/shared
   - hestia://session/own
   - hestia://society/trust/{plugin_id}
   - hestia://vault/{name}
```

### §B.1 — Why the coverage gap is *not* the finding

Per `C372:411-412` (ratified: *"coverage ≠ defect, per v43"*), and exactly as C396 reasoned before charging its own N1: the 4-of-6 gap is **disclosed**. `schemas/presence-protocol/README.md:63-65` states that `Session` and `VaultEntry` *"also have no conformance vector. Authoring their schemas … and their `resources/read` vectors is pending."* `:44-45` ships the four-item known-gap ledger. Charging the gap would be charging the project's disclosure discipline, which this corpus does well.

**The finding is the opposite: an index file asserts coverage the corpus elsewhere admits it does not have.**

### §B.2 — N1 (LOW): the conformance index's `Coverage` cell overstates the presence suite — on the row whose other cell C396 already charged

**Locus:** `web4-standard/testing/conformance/README.md:15`

```
| File | Coverage | Vectors |
|------|----------|---------|
| `presence-protocol-conformance.json` | Presence Protocol v0: 8 tools + 6 resources + error envelope. … | 10 |
```

| Claim in the cell | Measured | Verdict |
|---|---|---|
| 8 tools | 8 distinct tools appear; **7** appear in an assertion-bearing step | **true only on the loose reading** |
| **6 resources** | **2** (`society/state` P0-009, `witness/recent` P0-010) | **FALSE on every reading** |
| error envelope | 2 sites bind `error_envelope.schema.json` | **TRUE** |
| Vectors = 10 | 14 scenarios | **FALSE** — already charged, C396 I-1 |

**The column header is `Coverage`, and the row's subject is the file.** The decisive evidence is authorship, not grammar: `git blame -L 15,15` dates the row to `0405999d` (2026-05-16, Dennis Palatov), and at that commit the vector file contained **exactly 10 scenarios**. The `Vectors` cell was file-accurate at birth and went stale; the row was written to describe the file.

**Withdrawn from this pass's own first draft — the "discriminating asymmetry" argument.** That draft held that *"8 tools"* is true under both the file and spec readings while *"6 resources"* is true only under the spec reading, so only the latter discriminates. **Adversarial verification refuted it.** `hestia_vault_set` occurs exactly once in the file — `P0-004 setup[0]`, `keys=['tool','input']`, **no `expect` clause** — so it asserts nothing. Assertion-bearing distinct tools = **7**, not 8. The draft was applying two strictness standards at once: counting a resource as exercised only when a step asserts (P0-009 and P0-010 both do), while counting tools loosely enough to include an unasserted setup fixture. Under one consistent strict reading **both** numerals are false and neither discriminates; under one consistent loose reading both are arguable. The cell is *worse* than the draft said, and the draft's supporting argument does not stand. It is replaced by the `git blame` evidence above.

**Novelty is per-LOCUS only (v56) — the measurement is C127's.** This pass's draft claimed the numerals were "never checked against the file the row describes." That is **false**, and the falsifier was in this lineage's own third pass: `C127:24` reports *"documentary completeness + **a 2-of-6-resource coverage gap**, not a wire contradiction"* and `C127:79` reasons that *"§7 item 5 binds only the vectors (**which don't cover them**)"* — C127 resolved resource coverage against the vector file, got 2-of-6, and rated the containing finding **LOW**. What is uncharged is narrower and exact: **the `README.md:15` cell**. The five certifications this pass cites — `C88:121`, `C127:104`, `C160:97`, `C198:85`, `C236:84` — do read *"counts (8 tools / 6 resources / …) internally consistent"* and do resolve those numerals against spec §4; but C127 held both readings in one document without reconciling them.

**Disclosure — narrowed.** The draft asserted the gap is "not disclosed." Refuted as worded: `schemas/presence-protocol/README.md:60-65` states that `Session` and `VaultEntry` *"also have no conformance vector,"* and `:44-45` ships the known-gap ledger. What is true is only the narrow claim: **neither the vector file (`description` + 3 `notes`) nor the conformance README itself says anything about resource coverage.** The README's harness prose — runners *"exercise every scenario"* — is true and irrelevant: all 14 run, 2 touch a resource. So this is **two artifacts disagreeing**, not an undisclosed gap, and §B.1 already scoped it that way.

**Harm — mechanism holds; attribution corrected.** §4.2 (`:455`) requires `hestia://vault/{name}` to return a VaultEntry *"with `secret` redacted"*; §5.7 (`:576`) repeats it. Against that requirement: **0** vectors read the resource, **0** VaultEntry schema exists, `web4-standard/testing/validator/` has 0 presence hits, and the only two vault scenarios (P0-004, P0-005) assert solely `_hestia_error.code` against `error_envelope`. `hestia_vault_get` cannot cross-check it — the tool is *designed* to return the secret. So a daemon serving that resource un-redacted **passes 14 of 14 scenarios**.

Three corrections to how the draft charged this: (1) such a daemon is still **non-conforming** under §7 items 1–2 (*"Implement all 6 resource URIs in §4"*) — the true statement is only that the *vector suite* cannot detect it; (2) the gap itself is **C127-1**, a standing routed carry re-verified open at C160/C198/C236/C276, so the harm is **borrowed, not caused by this cell**; (3) C396-N1 already used a near-identical consequence framing. The cell's contribution is that it is the artifact telling an implementer the surface is covered.

**Severity LOW, not MED** — the draft said MED and that is not defensible:
- Nothing binds `testing/conformance/README.md`. §7's Precedence clause binds the JSON Schemas and the vectors JSON — **not** this index. C396-N1 earned MED inside the §7-bound schemas directory with an executed schema-validation demo; this is the same shape in an unbound index.
- C396 rated an equally false numeral **in the identical row** (`10` vs 14) at **INFO**.
- C127 rated the analogous documentary-completeness + 2-of-6 finding at **LOW**, and its steelman applies here verbatim.

### §B.3 — The block was the table, not the row (v76, one level up)

The draft applied *enumerate the whole block* to the row — C396 charged the `Vectors` cell, so the row is the block — and then stopped. Verification pushed it one level further, to the table. Every `Vectors` cell, re-counted from each file's own structure:

| Row | Claimed | Actual | |
|---|---|---|---|
| `tensor-operations.json` | 8 | **9** (`t3_vectors` 6 + `v3_vectors` 2 + `sub_dimension_vectors` 1) | **WRONG** |
| `atp-operations.json` | 11 | 11 (5+3+3) | ok |
| `r6-r7-actions.json` | 8 | 8 (4+3+1; `role_contextualization` is a prose object, not a vector list) | ok |
| `society-roles.json` | 8 | **9** (2+4+1+2) | **WRONG** |
| `presence-protocol-conformance.json` | 10 | **14** | **WRONG** (C396 I-1) |

**3 of 5 `Vectors` cells are wrong**, and a second `Coverage` cell overstates: `tensor-operations.json`'s cell claims *"construction, update, decay, levels, sub-dimensions"* for T3/V3, but the V3 side has only `v3-001` (*Neutral V3 tensor*) and `v3-002` (*V3 with explicit values*) — no update, decay, or level vector.

This is the finding's real shape and the reason LOW is right: **`testing/conformance/README.md` is an uncared-for index**, not a presence-specific defect. It also widens the fix — amending only the presence row would leave two wrong cells in the same table, and C396's I-1 missed the same two.

### §B.4 — I-2 (INFO): a published negative carries two different denominators inside one cell

C396 published, as a negative, that `additionalProperties` *"is a uniform idiom — **8/8** tool inputs `true`, **9/9** outputs `false`"*. Re-measured per file:

- tool schemas in tree: **9** (`v0/tools/` 8 + `v1/tools/` 1)
- `$defs.input.additionalProperties: true` — **9 of 9**
- `$defs.output.additionalProperties: false` — **9 of 9**
- plus **1 nested** `true` inside `query_history`'s input (`:18`), which a flat `grep -c` folds into the input tally

The idiom claim is **correct and strengthened** — 9/9 on both halves. The defect is that one published cell used a **v0-only denominator for inputs and an all-versions denominator for outputs**. That is the v40 class (*a metric's denominator is a domain*) occurring inside a single sentence, where the mismatch is hardest to see. Corrected here; no artifact changes.

### §B.5 — Negatives, published so the positives are interpretable

- **The spec is clean on the resource axis.** §4 declares six resources and §3 (`:115-128`) and the §5 intro (`:461-473`) **each** partition all six by casing class — `society/state` ad-hoc snake_case, `context/shared` opaque, the other four §5-typed camelCase. Stated twice, complete both times. N1 is an index defect, not a spec defect.
- **`shapeMatchesSchema` targets:** 7 distinct, 7 of 7 resolve ($id **and** fragment). Unchanged.
- **Scenario IDs:** P0-001…P0-010, P1-001…P1-004 = 14. Contiguous, no gaps.
- **No resource is reachable by a hidden mechanism.** A full recursive walk of every key at every depth — including `setup`, `capture`, `input`, `path`, `target`, and `{{…}}` interpolations — finds resource steps at exactly `/scenarios/8/steps/0` and `/scenarios/9/steps/0`. A raw regex over the file text returns the same 2 distinct URIs. The 2-of-6 count is not a naive-matcher artifact.
- **The 4 orphan files** C396 recovered still carry `presence-protocol` references invisible to filename sweeps. **N1 lives in one of them** — the orphan set has yielded a charged finding in two consecutive passes, which is the argument for keeping it in the guard list. (C396's *"invisible to every sweep"* was scoped to **filename** sweeps: `C316:37` did list this file in an inbound-citation set.)

---

## §E — Refuted / declined, with the reason each was killed

C396 carried five. This pass adds a **sixth**, killed by the novelty matcher **before** drafting:

**(f) `hestia://context/shared` is missing from the known-gap ledger — REFUTED, do not resurrect.**
The ledger (`schemas/…/README.md:44-45`) claims *"**four** spec-referenced artifacts have no JSON Schema in this tree yet."* `context/shared` is spec-referenced (§4.1, first row) and has no schema, no vector, and **zero** mentions in the schemas README — the only one of the six resources scoring 0 on every instrument. The literal count therefore reads 5, not 4.

**It was already adjudicated.** `C160:58` ruled it *"n/a — spec declares it opaque (no shape to author) — **defensibly excluded**"*, and `C160:40` re-derived the complete schema-less set over 7 §5 structs + 6 §4 resource bodies as exactly `{society/state, R6Action, Session, VaultEntry}`. C198, C236 and C276 each re-ratified that derivation byte-stably. The charitable reading — *artifacts pending a schema* — is the one C160 adopted on the merits, four times over. Re-charging it on the literal reading would be a wording technicality against a 4×-ratified adjudication.

Matcher published so the kill is reproducible: `grep -rn 'context/shared' docs/audits/` → **5 hits in 3 files** (C38, C88, C160). The candidate died on step 3 of the opening sequence (*novelty is an absence claim*), which is what that step is for — its cost was one grep, not a draft.

The five C396 carried (**P0-007→v1 ratified** · `v0 query_policy` orphan · `approvalToken` always-null · bare coverage-absence framing · *"no in-repo validator"* false as written) are unchanged and still refuted.

---

## Findings

| # | Sev | Class | Locus | Statement |
|---|---|---|---|---|
| **N1** | **LOW** | instrument | `web4-standard/testing/conformance/README.md:15` | The `Coverage` cell asserts the presence suite covers *"8 tools + **6 resources** + error envelope."* Measured: **2 of 6** resources, and 7 of 8 tools appear in an assertion-bearing step. The row's subject is the file (`git blame` → authored when `Vectors=10` was exact). The **cell is the defect** — the underlying coverage gap is C127-1 and is disclosed in the schemas README, so it is two artifacts disagreeing, not an undisclosed gap. **ROUTED, not applied.** |
| **N1b** | **LOW** | instrument | same file, `:11` and `:14` | The same table's `Vectors` cells are wrong for `tensor-operations.json` (8, actual **9**) and `society-roles.json` (8, actual **9**); `tensor`'s `Coverage` cell also claims V3 *update / decay / levels* vectors that do not exist. **3 of 5 `Vectors` cells wrong** ⇒ the defect is the index, not the presence row. |
| **I-2** | INFO | method | C396 §B.5 | The published `additionalProperties` negative used a v0-only denominator for inputs (8/8) and an all-versions denominator for outputs (9/9). True value is **9/9 on both**; the idiom claim strengthens. |

**Fix shape — C128's ratified shape, one amendment covering all three rows:** correct the three `Vectors` cells (`8`→`9`, `8`→`9`, `10`→`14`), amend the presence `Coverage` cell to what is actually covered (*"8 tools + 2 of 6 resources + error envelope"*), and drop the non-existent V3 verbs from the `tensor` cell. **This discharges C396's I-1 third site in the same edit.** ROUTED, NOT APPLIED — this pass mutates nothing.

---

## §H — Retirement ledger, and routing

**Consecutive frozen-target passes yielding zero net-new charged finding: 0.**

Opened at policy review's requirement this pass, to make this loop capable of failing. The rule, pre-registered:

- This pass charged net-new findings (N1, N1b) ⇒ the counter **stays at 0**.
- Had it landed on the measured-negative branch, the counter would read 1 and this section would be **required** to route an explicit retirement question to the operator at C476.
- **Two consecutive** zero-yield passes ⇒ the pass recommends retiring the lineage.

Sanctioned precedent: the operator asked at **C422** that the `web4-lct` lineage be considered for retirement, so lineage retirement is a live option in this rotation, not an escalation.

**Honest note on this pass's yield.** Both findings are LOW and live in an **unbound** index file; the strongest thing this pass produced is arguably not N1 but the correction record in §B.2 — a draft that claimed MED, a novel measurement, and an undisclosed gap, all three of which adversarial verification cut down. The measured case against ritual still holds (four consecutive passes against this frozen blob have each charged something and yielded a method carry), but the severity trend on this lineage is **MED → LOW**, and C476 should weigh that when it reads the ledger.

**Routed, not taken:** `pr_standing_blocks.py` reports **web4 #757 BLOCKED** (2 standing CHANGES REQUESTED, branch `hub/anchor-ceiling-two-sites`). That is the **HUB track's** PR, not this lineage's. This fire's branch was verified **not stacked** on it (`git merge-base --is-ancestor` fails; `origin/main..HEAD` = 0 commits before this audit). Routed to the HUB track rather than cleared from here — same reasoning as SESSION_FOCUS item 0f.

**Instrument note (a reviewer correction, corrected back — v52).** Policy review reported `tools/pr_standing_blocks.py` absent from the tree and proposed charging it. It is present and executable at `/home/dp/ai-workspace/private-context/tools/pr_standing_blocks.py`; it is absent only **relative to the web4 worktree**, which is the wrong denominator — private-context is a separate repository and the primer's path is written relative to it. A **false absence** of the v73 class. Not charged.

---

## Guards for the next presence delta (C476)

1. **N1/N1b fix check — by content, not line.** Does the presence row still read *"6 resources"*? Are the three `Vectors` cells still `8 / 8 / 10`? A fix touching **only** the presence row leaves two wrong cells in the same table and leaves N1b open — the three cells discharge together.
2. **Baseline census to re-run:** 14 scenarios / 8 distinct tools (**7** assertion-bearing) / **2** distinct resources / 6 spec resources / 4 zero-coverage. Suite counts: tensor **9**, atp **11**, r6-r7 **8**, society-roles **9**, presence **14**.
3. **Do NOT re-probe the six refuted items** (a–f in §E). Item (f), `context/shared`, is newly added and killed by `C160:58` + `C160:40`, re-ratified 3×. Run the published matcher before spending a draft on any candidate touching the gap ledger.
4. **Do NOT re-charge the 2-of-6 resource coverage gap as a measurement.** `C127:24` measured it and rated it LOW; `C127-1` owns it as a standing routed carry. Only a *new locus asserting the contrary* is chargeable.
5. **C396's four checks all HOLD** — re-run them cheaply, but they are the preamble.
6. **The unrun axis is the `error_envelope` axis.** C396 swept tools backwards, C436 swept resources backwards. Remaining: which of the spec's 10 error codes are exercised by a vector, and does any index assert otherwise? Pre-registered so C476 inherits a question rather than a re-derivation.
7. **Retirement ledger stands at 0.** If C476 charges nothing net-new, set it to 1 and route the retirement question to the operator. Weigh the MED→LOW severity trend noted in §H.
8. **Obligation on hestia is read-only, route-out only.** If a runner has begun executing `shapeMatchesSchema`, ask **which vocabulary it selects** (C356 guard-3 shape) and route it — do not fix runners from this worktree.

→ method carry **v83**: *a count in a table is predicated on its **column header**, not on the domain it names* — five passes certified "6 resources" by resolving it against the spec section where it is true, never against the file the row describes. Two corollaries, both earned by this pass's own draft being cut down: **(i) when a prior pass charges one cell of a row, the block is the row — and then the table** (C396 charged one cell; this pass charged the row and still missed two wrong cells one row up, until verification pushed it); **(ii) a "discriminating asymmetry" between two numerals is only evidence if both are measured under the *same* strictness** — counting resources strictly and tools loosely manufactured a discriminator that did not exist.
