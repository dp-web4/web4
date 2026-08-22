# C430 — `t3-v3-tensors.md`, 11th delta audit

**Date**: 2026-08-21 · **Slot**: C430 (= C390 + 40) · **Target**:
`web4-standard/core-spec/t3-v3-tensors.md` · **Mutation**: **ZERO** · **PR**: this branch

**Lineage = 14 at HEAD** (inclusive rule; the non-C-numbered
`docs/audits/t3-v3-tensors-internal-consistency-2026-05-24.md` is a member). Ordinal chain:
C42(1) C82(2) C121(3) C154(4) C192(5) C230(6) C270(7) C310(8) C350(9) **C390(10) C430(11)** —
`C154` and `C192` both self-title "4th delta"; the chain is the authority.

---

## Headline

**§10 opens by claiming it "classifies *all* trust, value, and energy parameters by governance
tier". It classifies 25. The trust-query ATP stake minimum is not one of them — and the corpus
hard-codes it in three independent places while the standard's only other declaration of it
publishes a five-tier, role-varying schedule.**

Ten prior passes read this file for what it *declares*. This one asked the inverse question: what
does the corpus *implement* that §10's completeness claim never classifies? The answer was reachable
only from outside the lineage — the parameter's declaring document,
`web4-standard/T3V3_PRIVACY_GOVERNANCE.md`, is an **orphan with zero cross-citations in either
direction**, and no pass of this lineage has ever opened it.

| # | severity | finding | routed to |
|---|---|---|---|
| **N1** | **LOW-MED** | §10's "all" is false by ≥1 parameter: the trust-query ATP stake minimum is hard-coded three times (schema `minimum: 10`, SDK `TRUST_QUERY_MIN_STAKE = 10`, CLI default `10`) and classified in none of §10.2/§10.3/§10.4; its only other declaration is a **five-tier role-sensitivity schedule** (10/50/100/500/1000) that nothing reads. **Severity capped**: no MUST violated | standard-editor / operator (author ruling, two mutually exclusive remedies) |
| **N2** | **LOW** | `T3V3_PRIVACY_GOVERNANCE.md` is a titled *Specification* inside `web4-standard/` with **0** inbound and **0** outbound cross-citations, **2** RFC2119 keywords in 292 lines, and a §5 "Implementation Requirements" whose need-to-know gate, engagement/forfeit resolution and three decorators have **0** implementation. Its sole implementation was **archived as sprawl** at `65cd5488` (Sprint 32 T1, #151) | standard-editor / operator |
| **N3** | **INFO** | `commitment` is free text with **three** spellings across four artifacts and **0** consumers | recorded, not charged |
| **N4** | **INFO** | the **pre-registered NULLs**, published as the answer: guards 1, 2 and 3 all unchanged for an 11th pass; guard 4's operator fork is unanswered at the **5th** check ⇒ **ESCALATED as a routing failure**, not re-probed | operator |

**Pre-registered before §B was measured** (session log Step 5, change 3): *zero net-new findings is a
PASS on this pass.* An 11th consecutive frozen pass with both delta halves empty is expected to yield
nothing, and no finding would be manufactured to avoid that outcome. The NULL was the expected
result; N1 is what the inbound sweep actually returned.

---

## §A — Window, freeze, denominator

**Target byte-frozen.** Blob `32d3368e`, 689 L, last content commit `d89595e8` (#531, 2026-07-16) —
**36 d**, **11th consecutive frozen pass**.

```
git rev-parse HEAD:web4-standard/core-spec/t3-v3-tensors.md   →  32d3368e…
git log -1 --format="%h %ad" --date=short -- <target>          →  d89595e8  2026-07-16
```

**Window pre-registered** (v26): span = `b20d5aa3..HEAD` (`b20d5aa3` = the commit that added
`docs/audits/C390-t3-v3-tensors-10th-delta-2026-08-14.md`); root = repo; filetypes = all; tree =
whole repo, `archive/` excluded from every subject-matter denominator and stated per-cell.

| layer | probe | result |
|---|---|---|
| whole window | `git log --oneline b20d5aa3..HEAD \| wc -l` | **33** commits |
| target | same, `-- core-spec/t3-v3-tensors.md` | **0** |
| mirror layer (8 paths: `ontology/t3v3-ontology.ttl`, `ontology/t3v3.jsonld`, `schemas/t3v3.schema.json`, `schemas/t3v3-jsonld.schema.json`, `test-vectors/t3v3/`, `test-vectors/schema-validation/t3v3-jsonld-validation.json`, `implementation/sdk/web4/trust.py`) | same, `--` those paths | **0** |

**Both halves of the corpus delta are empty for the second consecutive fire.** §B is therefore
entirely the inbound sweep's yield — as it was at C390, now for the 6th consecutive pass.

---

## §B — The inbound sweep, run before §A per C390 guard 5

### B.1 — by-number channel: **non-zero for the first time in three passes**

`git grep -ln "C390" -- . ':!docs/audits/C390-*'` → **8 files**, 7 of them audits:
`C350`, `C392:213`, `C394:155,156,297,387`, `C400:420`, `C406:355`, `C410:322`, `C414:360,409`, and
`whitepaper/PUBLISHER_CONTEXT.md`.

**Every one of them is outbound or citational; none routes a row *into* this lineage.** `C390-N2`
travels with `C374-N4` as a standing re-route to acp `C434` (`C406:355`, `C410:322`, `C414:409`) —
still unserved, now **5 passes old**, and **not this pass's to take**. Recording the negative is what
makes B.2's positive interpretable (v36).

**One inbound corroboration, by role rather than by number.** `C406:35` (2026-08-18) re-ran
`C366-N1`'s class-wide denominator over `git ls-files web4-standard/` and published **15** referenced
context names / **10** backed / **5** unbacked — `law.jsonld`, `mrh.jsonld`, `sal.jsonld`,
`t3v3.jsonld`, **`trust-query.jsonld`**. `C390-N1` is therefore now carried by **two** lineages
independently, and `C406:A.2` had already answered this pass's guard 2 three days early ("did the
gate's domain widen? **No**"). **`C390-N1` is HELD, corroborated, and unmoved — not re-derived here.**

### B.2 — the residue: an orphan in this lineage's own subject matter

`C392:174` published an orphan census naming 13 residue members never cited by any audit. One of them
is **`web4-standard/T3V3_PRIVACY_GOVERNANCE.md`** — a 292-line document titled *"T3/V3 Privacy and
Governance Specification"*, living in this lineage's subject matter, which **no pass of this lineage
has ever opened in 10 passes**.

It is invisible to every instrument this lineage runs:

| instrument | why it cannot see the file |
|---|---|
| filename-token sweep `git grep -l "t3-v3-tensors"` | the file never writes the target's name (v36: a file is invisible to a sweep keyed on another file's name) |
| the target's own outbound links | `grep -n "PRIVACY_GOVERNANCE\|privacy" core-spec/t3-v3-tensors.md` → **0** for the filename |
| any index / README / manifest | `git grep -rn "T3V3_PRIVACY" web4-standard/` → **1 hit, the file's own heading**. Nothing in `web4-standard/` links to it |
| `validate_context_refs.py` | domain is `test-vectors/`; the file is markdown |

**Cross-citation is 0 in BOTH directions** — the same shape `C412-N1` charged for the LCT termination
vocabulary, here one rung further out: not a term with no consumer, a *document* with no edge.

---

## §C — N1 (LOW-MED): §10 classifies 25 parameters and claims to classify all of them

### C.1 — the claim

`t3-v3-tensors.md:600-607` (§10 preamble):

> This section classifies **all** trust, value, and energy parameters by governance tier: who decides
> the value, and what latitude implementers have. It synthesizes normative decisions from §2.3 and
> §3.3 of this document, `atp-adp-cycle.md` §6.3/§7, and `multi-device-lct-binding.md` §4.4.

**Denominator, counted from the file** (header and separator rows excluded, script in §F):
§10.2 Protocol-invariant = **12** rows · §10.3 Society-configurable = **8** · §10.4 Simulation-only =
**5** ⇒ **25 parameters classified**, under **3** tiers (§10.1).

### C.2 — the parameter that is in none of them

| site | value | kind |
|---|---|---|
| `web4-standard/schemas/trust-query.schema.json` `properties.query.properties.atp_stake` | `{"type":"integer","minimum":10}` | schema-enforced floor |
| `web4-standard/implementation/sdk/web4/trust.py:616` | `TRUST_QUERY_MIN_STAKE = 10` | constant, re-exported at `web4/__init__.py:77,555` |
| `web4-standard/implementation/sdk/web4/trust.py:653-654` | `if self.atp_stake < TRUST_QUERY_MIN_STAKE: raise ValueError` | constructor gate |
| `web4-standard/implementation/sdk/web4/__main__.py:602` | `--stake` `default=10`, help `"(default: 10, minimum allowed)"` | shipped CLI default |
| `web4-standard/test-vectors/trust-query/invalid-no-stake.json:21` | `"minimum_required": 10` | published negative vector |

**Denominator for the competing declaration** — every declaration of a trust-query stake minimum
repo-wide (`archive/`, `simulations/` and `docs/audits/` excluded; matcher
`git grep -rniE "min[_ ]?(atp[_ ])?stake|minimum.*stake|stake.*minimum"`): the `min_atp_stake` family
(`reputation-computation.md:293`, `sdk/web4/reputation.py:110-112`, 2 tests) is a **reputation *rule*
trigger field — a different object**, as `C426:208` ruled for `max_stake_per_query`. Excluding it,
**exactly one** other declaration exists:

`web4-standard/T3V3_PRIVACY_GOVERNANCE.md:183-191` — **§4.2 Stake Requirements by Role Sensitivity**:

| Role Category | Example Roles | Min ATP Stake |
|---|---|---|
| Public Service | Citizen, Participant | **10** |
| Professional | Developer, Designer | **50** |
| Specialist | Surgeon, Auditor | **100** |
| Critical | Nuclear Operator, Judge | **500** |
| Governance | Protocol Admin, Oracle | **1000** |

The corpus hard-codes the **lowest tier as a flat, role-blind floor**.

### C.3 — executed, with a backed control

```python
sch = json.load(open('schemas/trust-query.schema.json'))
v   = Draft202012Validator(sch)          # jsonschema, iter_errors read directly
base = json.load(open('test-vectors/trust-query/valid-staked-query.json'))['input']['query']
```

| document | §4.2 tier | stake | verdict |
|---|---|---|---|
| `requested_role="web4:Surgeon"` | Specialist / 100 | 10 | **VALID** |
| `requested_role="web4:Judge"` | Critical / 500 | 10 | **VALID** |
| `requested_role="web4:Oracle"` | Governance / 1000 | 10 | **VALID** |
| **backed control** `web4:Surgeon` | — | **9** | **FAILS** — `9 is less than the minimum of 10` |

The control fires, so the validator is live and discriminating: there is a **value guard on the flat
floor and no guard at all keyed to the role** (v79). `requested_role` is read **6** times in
`trust.py` (`:643 :666 :695 :861 :879 :912`) — serialization, audit-log, and `profile.get_t3()`
lookup. **Never for a floor.** `evaluate_trust_query`'s Step 1 (`:868`, `requester_atp.lock(float(query.atp_stake))`) is a *balance* check
(`requester_atp.lock(...)`), not a floor check.

### C.4 — the discriminating artifact is the negative vector, and it is wrong for its own role

Both published trust-query vectors query **`web4:Surgeon`** — a §4.2 **Specialist**, minimum **100**.

- `valid-staked-query.json` stakes **100**. Consistent with §4.2 — and therefore *non-discriminating*.
- `invalid-no-stake.json`, whose entire job is to pin the floor, stakes `0` and publishes
  `"error": {"code": "INSUFFICIENT_STAKE", …, "minimum_required": 10}` — the **Public Service** figure,
  for a **Specialist** query. Under §4.2 the minimum required for `web4:Surgeon` is **100**.

The one artifact in the corpus that exists to state the floor states the wrong one for the role it
uses, and it agrees with the schema and the SDK, so nothing can see the disagreement.

### C.5 — direction: born divergent, not drifted (standing rule: date the defect)

```
git log --diff-filter=A --format='%h %ad' --date=short -- <path>
  c66792fd  2025-09-14   T3V3_PRIVACY_GOVERNANCE.md
  c66792fd  2025-09-14   schemas/trust-query.schema.json
  c66792fd  2025-09-14   test-vectors/trust-query/valid-staked-query.json
  c66792fd  2025-09-14   test-vectors/trust-query/invalid-no-stake.json
  b052beb8  2026-03-13   implementation/sdk/web4/trust.py
```

**All four spec-side artifacts were added in the same commit.** The tier table and the flat floor
that ignores it were authored together, 341 days ago. This is a birth divergence; no later change can
be blamed for it, and the SDK (6 months younger) is **faithful to its declared source** — its
docstring `:633` cites `trust-query.schema.json`, not the spec, and it matches it exactly. **The
charge is not against the SDK.**

### C.6 — v59 mutation probe: a value guard, no gate guard

`TRUST_QUERY_MIN_STAKE` → **100** (a *plausible* wrong value — the Specialist tier, not a sentinel):

```
10 failed, 2740 passed, 5 xfailed
```

| the 10 failures | what they prove |
|---|---|
| **9** × `tests/test_cli.py::TestTrust::*` | collateral — they fail because `__main__.py:602` hard-codes `--stake` default `10`; none asserts a floor |
| **1** × `test_trust_query_eval.py::TestATPAccounting::test_minimum_stake_query` (`:351-352`, docstring *"Minimum stake (10 ATP) works."*) | **restates the constant** |
| **0** | assert a role-dependent floor |

**Backed control on a neighbouring behavioural line** (v79's required tell): mutating the RANGE
disclosure branch (`trust.py:890`, `temperament=c` → `temperament=c*0.9`) fails **2** tests
(`test_trust_query_eval.py::TestDisclosureLevels::test_range_returns_uniform_composite`,
`test_mcp_server.py::TestWeb4EvaluateTrust::test_approved_range_disclosure`). The suite **is** capable
of catching behaviour in this module — the absence of a tier assertion is real, not a dead suite.
Both mutations reverted; `git diff --stat` on the SDK is empty.

### C.7 — why it is unclassifiable as shipped, and where severity caps

Against §10.1's own tier definitions:

| tier | test | trust-query stake floor |
|---|---|---|
| **Protocol-invariant** | *"Cross-language test vectors enforce them"* (§10.2 preamble names `test-vectors/t3v3/tensor-operations.json`) | hard-coded like an invariant, but `grep -c stake tensor-operations.json` = **0** across all **15** vectors ⇒ **no vector enforces it** |
| **Society-configurable** | *"Societies set these via published economic or governance laws"* | role-varying like a configurable, but there is **no law hook**: `ROLE_SENSITIVITY` occurs **once repo-wide**, inside `T3V3_PRIVACY_GOVERNANCE.md:169` itself |
| **Simulation-only** | *"Implementations MUST NOT hard-code them as canonical"* | if it belongs here, the schema, the SDK constant and the CLI default are three MUST NOT violations — **but it is not listed there**, so the antecedent has no referent |

**Severity capped at LOW-MED, deliberately.** No MUST is violated: §10.4's `MUST NOT` reaches only
parameters it lists, and §4.2 is a table with **0** RFC2119 keywords in a document carrying **2**
(`:13` *"Every trust query MUST include:"*, `:129` *"This is REQUIRED in Web4"*) — neither of which is
the stake schedule. **The bite is the completeness claim in §10's opening sentence**, which is the
target's own normative-adjacent framing, and the fact that the corpus ships a governed-looking
economic parameter that no tier owns.

**The honest counter-reading, stated rather than suppressed**: §10's second sentence names its three
sources (§2.3/§3.3, `atp-adp-cycle.md` §6.3/§7, `multi-device-lct-binding.md` §4.4), and
`T3V3_PRIVACY_GOVERNANCE.md` is not among them. That narrows the charge — the omission may be
*scoped* rather than *wrong* — but it does not dissolve it: the claim word is **"all … parameters"**,
the "synthesizes" sentence describes where the *decisions* came from, not the extent of the
classification, and the parameter is hard-coded in three shipped artifacts either way.

### C.8 — remedies (author ruling; mutually exclusive)

1. **Classify it.** Add a §10.3 row (society-configurable, role-keyed), give `trust-query.schema.json`
   a role→floor map or a `law`-sourced minimum, and add a cross-language vector. This makes §4.2
   normative and makes the negative vector's `minimum_required` role-dependent.
2. **Retire the schedule.** Mark `T3V3_PRIVACY_GOVERNANCE.md` non-normative/exploratory (or move it to
   `archive/`, where its implementation already went at `65cd5488`), and add a §10.4 row recording the
   tier figures as simulation-only. This makes the flat floor correct by construction.

**Not this ledger's to decide.** Both remedies are cheap; leaving it is the expensive option, because
the corpus currently ships the appearance of tiered trust-query economics with none of the mechanism.

---

## §D — N2 (LOW): the orphan specification

`web4-standard/T3V3_PRIVACY_GOVERNANCE.md`, 292 L, added `c66792fd` (2025-09-14), **never modified
since — 341 d**.

| property | measurement | command |
|---|---|---|
| inbound cross-citations inside `web4-standard/` | **0** | `git grep -rn "T3V3_PRIVACY" web4-standard/` → 1 hit, its own §4.2 heading |
| outbound cross-citations | **0** | `grep -n "t3-v3-tensors\|core-spec" T3V3_PRIVACY_GOVERNANCE.md` |
| RFC2119 keywords | **2** in 292 L (`:13`, `:129`) | `grep -nE '\b(MUST\|SHOULD\|MAY\|SHALL\|REQUIRED)\b'` |
| audit citations, lifetime | **2**, both incidental | `C392:174` (names it *as* an orphan), `C426:208` (cites `:104` for a different object) |
| its sole implementation | **archived** | `archive/reference-implementations/t3v3_privacy_governance.py`, moved at `65cd5488` "Sprint 32 T1: Archive reference implementation sprawl" (#151, 2026-04-11) |

**§5 "Implementation Requirements" against the shipped SDK** (`grep -ric <token> sdk/web4/trust.py`):

| §5.1 declares | in `trust.py` |
|---|---|
| `@requires_atp_stake` / `@role_contextual` / `@audit_logged` decorators | **0 / 0 / 0** |
| `verify_need_to_know(request)` gate + 95% stake-return rejection path | `need_to_know` **0**, `legitimate` **0** — `evaluate_trust_query` has no need-to-know step |
| `set_engagement_expectation(...)` + §1.3's four-outcome stake resolution | `engage` **1**, `forfeit` **1** — both inside one f-string, `trust.py:907` |
| `log_trust_query(...)` audit trail (§2.2) | `audit_log` **8** — **implemented** |

So one of four declared mechanisms exists. `t3-v3-tensors.md` **§7.2 Privacy Protection** covers the
same subject in four `MAY` bullets and never references the document that specifies it.

**Note the overlap with N1's remedy 2** — these are one decision, not two. N2 is charged separately
because it stands even if §10's "all" is read narrowly: a titled Specification with no edge in either
direction is a corpus-integrity fact independent of any completeness claim.

---

## §E — N3 (INFO): `commitment` is free text with three spellings

| site | value |
|---|---|
| `T3V3_PRIVACY_GOVERNANCE.md:52` | `"Must engage or forfeit stake"` |
| `core-spec/r6-framework.md:405` | `"must_engage_or_forfeit"` |
| `core-spec/r7-framework.md:642` | `"must_engage_or_forfeit"` |
| `sdk/web4/trust.py:907` | `f"Must engage within {query.validity_period} seconds or forfeit stake"` |

Two core-spec documents agree on a snake_case token; the SDK emits an English sentence with an
interpolated number. **Nothing consumes the field** — `git grep` for either spelling returns only the
four declaration sites, and `TrustQueryResponse.commitment` is `Optional[str]` with no enumeration in
any schema. **INFO, not charged**: with zero consumers there is no failure mode today, and the class
(free-text status strings) is `C412-N1`'s, already open with the operator.

---

## §F — Guards: the pre-registered NULLs (C390 §G, **5 actionable + 1 fence**)

| guard | probe | result |
|---|---|---|
| **1** — N1 backing-file census, and *which of 3 shapes landed* | `grep -o "web4\.io/contexts/[a-z0-9._-]*" sdk/web4/*.py \| sort -u` vs `ls schemas/contexts/` | **11 constants, 10 backed, `trust-query.jsonld` still unbacked.** **NONE of the three shapes landed** — no context file created, `to_jsonld()` not removed, no `KNOWN_MISSING` entry added. `C390-N1` **HELD, 1 window, ZERO motion** — and independently corroborated by `C406:35` (§B.1) |
| **2** — did `validate_context_refs.py`'s domain widen? | `:39` `VECTORS_DIR`, `:83` `rglob`; gate executed | **No.** `KNOWN_MISSING` = **1** entry (`t3v3.jsonld`), citation and disposition text byte-identical. Gate: **283 refs, 9 names, 8 `OK`, 1 `KNOWN`, exit 0** — every figure identical to C390. `C406:A.2` reached the same answer 3 d earlier (v49 holding for a third pass) |
| **3** — re-run the five-row `DimensionScore` table | `rdfs:domain web4:DimensionScore` in `ontology/t3v3-ontology.ttl`; `$defs.DimensionScore` in `schemas/t3v3-jsonld.schema.json`; `@context` keys of both context files | **identical to C390 and C350.** 5 ttl properties, declared at `:87 :92 :97 :102 :107` with their `rdfs:domain` lines at `:88 :93 :98 :103 :108`; schema keys `dimension, score, observed_at, witnessed_by`, `required: [dimension, score]`, `additionalProperties: false`; both contexts define `observedAt`/`witnessedBy` (camelCase), **no `@vocab`**. **3 of 5 rows still ❌ — immobile for 11 passes.** No row became ✅, so the "check the other two moved with it" follow-up does not arm |
| **4** — `C310-N1`'s A/B fork, **5th check** | **read the vector, not the note** (guard 4 is explicit that the read is the escalation's precondition) | `grep -rn "v3-valid-003" web4-standard/` → `test-vectors/schema-validation/t3v3-jsonld-validation.json:167`, **present** ⇒ **option B not executed**. Target `:429-435` verbatim under a frozen blob ⇒ **option A not executed**. ⇒ **ESCALATED per guard 4**, see §F.1 |
| **5** — inbound sweep before §A, by subject matter as well as filename token; **record the negative** | §B | **run first.** by-number **non-zero but entirely outbound/citational** (negative recorded, §B.1); the yield was the subject-matter residue (§B.2) |
| **6 — FENCE (not actionable)** | do not re-open | **honoured, each locus named**: C310's and C350's do-not-raise lists (composite-weights #2/#3, decay-model #5 Training/Temperament, C238-N1/D2 NUMERIC facet, vectors-as-authority, the C230 "+2 shift", the `ns/`-vs-`ontology#` split, C278-N2); **N1 refutation 2** (the gate's `schemas/contexts/` resolution — ratified convention, docstring `:5-8`, `:40`, `:107`); **`r7-action`'s d4 member** (r7's slot); **`C318-I-1`** (closed at C350); `C192-N3`. **None re-opened.** |

### F.1 — Guard 4: the fork itself is now the row

`C310-N1` asked the operator to choose between two mutually exclusive readings of the V3 entity-role
binding note (`t3-v3-tensors.md:429-435`). It has now gone unanswered across **C278 → C310 → C350 →
C390 → C430 — five checks, 19 days since C390 and 12 days since C310 raised it**. Both options remain
unexecuted, measured this pass, not assumed.

**Per guard 4, this ledger escalates the *unanswered fork* rather than re-probing a sixth time.** The
row for the operator is no longer "which reading is right" but "a fork explicitly marked
*do-not-self-decide* has survived five audit passes of the file it lives in". **C470 must not probe it
a sixth time**; it should read this section's disposition and, if still open, treat it as a channel
failure — the disposition `C428-N3` reached for `C348-N2` after three misses.

**Inherited-error correction (v79: re-resolve every anchor you inherit).** `C390:58` records the fork
as *"unanswered at the 5th pass"*; `C390:295` and `C390:337` record it as *"the 4th pass"* with the
chain `C278 → C310 → C350 → C390`. **The chain enumeration is the authority: C390 was the 4th check
and C430 is the 5th.** `C390:58` is off by one against its own body. Corrected here, under a frozen
blob, exactly as `C428` corrected `C388`'s `test_integration.py` anchor.

---

## §G — Instrument index (built by capture)

All paths repo-relative. Basenames checked for collision with
`git ls-tree -r --name-only HEAD | grep -c "/<basename>$"`; ⚠ = collides, always written rooted.

| instrument | command / method | denominator | result |
|---|---|---|---|
| window | `git log --oneline b20d5aa3..HEAD` (+ `-- <target>`, `-- <8 mirrors>`) | 33 commits | **33 / 0 / 0** |
| freeze | `git rev-parse HEAD:<target>`; `git log -1 --date=short -- <target>` | 1 file | `32d3368e`, `d89595e8` 2026-07-16, **36 d** |
| by-number channel | `git grep -ln "C390" -- . ':!docs/audits/C390-*'` | whole repo | 8 files, **0 inbound routes** |
| §10 row count | python: lines starting `\|`, minus separator and header rows, per section | 3 tables | **12 / 8 / 5 = 25** |
| stake-minimum denominator | `git grep -rniE "min[_ ]?(atp[_ ])?stake\|minimum.*stake\|stake.*minimum" -- . ':!archive' ':!docs/audits' ':!simulations'` | whole repo | 2 object classes; `min_atp_stake` excluded per `C426:208` |
| schema execution | `jsonschema` `Draft202012Validator.iter_errors` read directly (**not** the non-raising `validate()`) | 3 roles + 1 control | 3 VALID @10, control FAILS @9 |
| v59 mutation | `TRUST_QUERY_MIN_STAKE` `10`→`100`, full `pytest tests/` | 2750 tests | 10 failed — **9 CLI-default collateral, 1 restating the constant, 0 behavioural** |
| backed control | `trust.py:890` `temperament=c` → `c*0.9`, full `pytest tests/` | 2750 tests | **2 failed** ⇒ suite is capable |
| §5.1 gap | `grep -ric <token> sdk/web4/trust.py` for 8 tokens | 1 file | 3 decorators 0, need-to-know 0, engage/forfeit 1 (one f-string), audit_log 8 |
| direction | `git log --diff-filter=A --format='%h %ad' --date=short -- <path>` | 5 paths | 4 spec-side artifacts share `c66792fd` 2025-09-14 |
| gate | `python3 test-vectors/validate_context_refs.py` | `test-vectors/**` | 283 refs, 9 names, exit 0 — identical to C390 |
| G1 five-row table | `grep -n "rdfs:domain web4:DimensionScore" ontology/t3v3-ontology.ttl`; `$defs.DimensionScore`; `@context` keys of both contexts | 4 files | 5 props, 4 schema keys, no `@vocab` ⇒ **3 of 5 ❌** |
| trust suite baseline | `python3 -m pytest tests/test_trust.py tests/test_trust_query_eval.py -q` | 121 tests | **121 passed** — green, and green *because* nothing tests the tiering |
| vector census | `grep -c stake test-vectors/t3v3/tensor-operations.json`; `grep -o '"id": "t3v3-[0-9]*"' \| wc -l` | 15 vectors | **0 / 15** mention stake |

**Not mechanically reproducible: none.** `rdflib`/`pyld` remain absent on this host (re-confirmed);
**no finding in this pass depends on a hand-derived row** — N1 rests on an executed validator with a
backed control plus two mutation runs, N2 on file existence and greps, N3 on four literal sites.

**Basename collisions checked**: `trust.py` (⚠ 2 — `implementation/sdk/web4/trust.py` and
`web4-core/src/…` is `.rs`, no collision after filetype; written rooted throughout),
`acp.jsonld` (⚠ 2, not relied on this pass), `t3v3.jsonld` (⚠ 2 — `ontology/` and the retired
reference; written rooted).

---

## §H — Own errors

1. **Step 1 of the session log recorded "Sprint plan: no `docs/SPRINT.md`". The file exists** — 2084
   lines, last touched `11d79d20` (2026-05-19, 94 d). It surfaced *by accident*, as a hit in the
   `DimensionScore` domain-word sweep, not from any check I ran. The claim I should have made is the
   narrower true one: *a sprint plan exists but has been stale for 94 days, and the C-series rotation
   is the de-facto sprint.* **An unqualified negative is a claim about my instrument** (v73) — and I
   made it in the document whose whole purpose is to record what I checked.
2. **The first draft charged the SDK.** `TRUST_QUERY_MIN_STAKE = 10` looks like the defect until you
   read the class docstring (`trust.py:631-635`), which declares `trust-query.schema.json` as its
   source — and the SDK matches that source exactly. **Read the implementation's own declared
   invariant before testing one against it** (v78, C426, on this same failure). The charge moved to
   the spec/schema divergence, where it belongs, and the finding got *smaller and correct* rather
   than bigger and wrong.
3. **The first draft's headline was N2 (the orphan document).** That is the weaker finding: an orphan
   is a corpus-hygiene fact, and this lineage has charged orphan-shaped rows before. N1 — a
   completeness claim in the **frozen target itself** — is the stronger and more novel one, and it
   only became visible after asking which *tier* the parameter belongs to. **The orphan was the
   route; it was not the finding.**
4. **I nearly published the §10.2 row count as 13.** `grep -c "^| "` over the section returns 13
   because it counts the header row. Counted properly (script in §G) it is **12**, and the total is
   **25**, not 26. A denominator published from a `grep -c` without excluding table furniture is the
   same class of error as an unrooted `git log` (v39).

5. **Three of my own anchors were wrong on first write, and all three were caught by re-resolving
   rather than by review.** `trust.py:889` (the backed-control mutation site) is `c = t3.composite`;
   the mutated line is **`:890`**. The `DimensionScore` ttl properties are *declared* at
   `:87 :92 :97 :102 :107` — `:88` and its siblings are the `rdfs:domain` lines, which is what my
   grep matched; citing the match line as "the property" would have been a silent off-by-one against
   a byte-frozen file. And `C310-N2`'s `observationCount` anchor is `:107`, not `:108`, for the same
   reason. **Every anchor in this document was re-resolved against HEAD after drafting**; 3 of ~40
   were wrong, all in the same direction — the line the tool printed, not the line the claim is about.

---

## §I — Carry table (disposition, not re-derivation)

Sound because §A shows the target byte-frozen and the mirror layer at **0** commits: no carry anchors
into changed text.

| carry | probe | status |
|---|---|---|
| **C390-N1** (`trust-query.jsonld` referenced live, never backed) | guard 1 | **HELD, 1 window, ZERO motion.** Corroborated independently by `C406:35` (5 unbacked, class-wide). Adjudicate jointly with `C366-N1` item (3) |
| **C390-N2** (instrument divergence, routed to acp `C434`) | `C406:355`, `C410:322`, `C414:409` | **STILL ROUTED, 5 passes old, unserved.** Travels with `C374-N4`. **Not this pass's to take** |
| **C390-N3** (the pre-registered null) | guards 1–4 | **RE-CONFIRMED** — nothing in the class moved |
| **C390-N4** (`C366:426` decomposed) | namespace half fenced, case half subsumed | **CLOSED at C390.** Not re-opened |
| **C350-N1** (all 3 `DimensionScore` evidence properties fail the round trip) | guard 3 | **STILL-OPEN, unchanged, 11th pass** |
| **C350-N2** | corrected and closed at C390 | **CLOSED** |
| **C350-N3** / **C318-I-1** | closed at C350 | **CLOSED**, fenced |
| **C350-N4** (`C310-N3` consumed; gate cites it by id+path) | gate executed, exit 0 | **STILL OPEN-AND-GATED**, unchanged |
| **C310-N1** (V3 entity-role note, operator fork) | guard 4 | **ESCALATED — the fork itself is the row** (§F.1). 5th check |
| **C310-N2** (`observationCount` in `.ttl`, schema forbids) | `ontology/t3v3-ontology.ttl:107` (`web4:observationCount`); **0** hits in the schema | **STILL-OPEN**, subsumed in the five-row class |
| **C310-N3** (36 refs to a non-existent context) | guard 2 | **OPEN-AND-GATED**, unchanged |
| **C310-N4** (header `:4` names the retired context) | frozen blob ⇒ verbatim | **STILL-OPEN, UNCHANGED** |
| **C270-N1** (successor gate anchored to the crate) | no window commit touches `web4-trust-core/` | **STILL-OPEN**, disposition-checked |
| **C270-N2** (Rust cross-language vectors unbacked) | `grep -rn tensor-operations --include=*.rs . \| grep -v target` → **0** | **STILL-OPEN**, untouched |
| **C270-N3** (pre-C-series alignment audit never entered the ledger) | inclusive rule admits it; lineage = **14** | **STILL-OPEN as a status row** |
| **C192-N3** | fenced | **STANDS. Not re-raised** |

---

## §J — Refuted this pass, do NOT resurrect

1. **"The SDK's flat `TRUST_QUERY_MIN_STAKE` is the defect."** Refuted — the SDK is faithful to its
   declared source (`trust.py:633`, `trust-query.schema.json`), which it matches exactly. The
   divergence is spec-vs-schema, born in one commit (§C.5).
2. **"`min_atp_stake` is a competing declaration of the same floor."** Refuted — it is a
   **reputation-rule trigger field** (`reputation-computation.md:293`,
   `sdk/web4/reputation.py:110-112`), matched against an *action's* staked ATP, not a query floor.
   Same token family, different object; `C426:208` made the identical ruling for `max_stake_per_query`.
3. **"The valid trust-query vector proves the tiering is honoured."** Refuted as evidence — it stakes
   100 for a Specialist role, which is *consistent* with §4.2 and therefore **non-discriminating**
   (v77). The discriminating artifact is the negative vector, and it publishes 10 (§C.4).
4. **"§10's 'all' is scoped to this document, so nothing is omitted."** **Not refuted — recorded as
   the live counter-reading** and stated in §C.7. It narrows the charge; it does not dissolve it.

---

## §K — Deferral row pre-registered for **C470** (next t3-v3 slot = C430 + 40)

**Do NOT re-run** (rediscovery under a frozen blob):

1. the §10 row count (**25**) and the three-table denominator — re-count only if `git log -- <target>`
   is non-empty;
2. the stake-minimum denominator sweep and the `min_atp_stake` exclusion (**settled**, §J.2);
3. the direction test on `c66792fd` (four artifacts, one commit — a fact, not a measurement);
4. the v59 mutation on `TRUST_QUERY_MIN_STAKE` — **spend the probe on an unprobed branch**; the
   result (9 CLI-default collateral + 1 constant-restating) will not change while the CLI default is
   hard-coded;
5. the `T3V3_PRIVACY_GOVERNANCE.md` §5.1 gap census — **8 tokens, settled**; re-run only the
   *inbound-citation* cell, which is the one that can move;
6. guard 4's fork — **do not probe a sixth time**; read §F.1's disposition. If still open, treat it as
   a **channel** failure (the `C428-N3` disposition), not a finding to re-file;
7. `C390-N2` at acp `C434` — **6 passes old** by C470. If `C434` still has not served it, that is the
   routing row, and it is **acp's**, not this lineage's.

**DO run, in this order:**

- **I1.** Did either N1 remedy land? Check §10.2/§10.3/§10.4 row counts **first** — if the total moved
  off 25, read *which* tier gained the row before re-deriving anything. A §10.4 row means remedy 2;
  a §10.3 row means remedy 1 and the schema should have gained a role→floor map.
- **I2.** Did `T3V3_PRIVACY_GOVERNANCE.md` move at all? It has been frozen 341 d. Any motion — an
  archive move, a non-normative banner, a first inbound link — re-opens both N1 and N2.
- **I3.** `C390-N1` third window. **ZERO motion for two windows now.** A third no-motion ⇒ **STALL**,
  escalate as a channel problem rather than routing it a fourth time.
- **I4.** Guard 3's five-row table, 12th run. **If any row became ✅, check the other two moved with
  it** — `additionalProperties: false` means a half-fix breaks published vectors.
- **I5.** Re-run the **inbound residue** sweep (§B.2's method), not the filename sweep. It is what
  produced this pass's entire yield, and `C392:174`'s orphan census has **12 other members** this
  pass did not open — at least one more is in this lineage's subject matter.
- **I6.** Re-resolve every anchor **inherited** from this document before citing it. This pass carried
  21 anchors forward from C390 and found **one wrong** (`C390:58`'s ordinal, §F.1) under a
  byte-frozen blob.

---

## §L — Lineage-continuation recommendation (policy-review condition 3)

The reviewer required this pass to answer the make-work question directly rather than leave it
implicit. Precedent: `C422 §H.8`, where the operator was asked the same of a comparably frozen
lineage.

**Measured basis:**

| measure | value |
|---|---|
| target freeze | **36 d**, 11th consecutive frozen pass |
| mirror-layer commits, this window | **0** (2nd consecutive empty) |
| by-number inbound routes | **0** for the 3rd consecutive pass (by-role delivered again, §B.1) |
| net-new findings per pass | C310 **4** · C350 **4** · C390 **4** · **C430 3** |
| where the yield came from | C310–C390: mixed; **C390 and C430: 100% inbound sweep**, 0% from re-reading the target |
| open rows never closed by any pass | **9** (C270-N1/N2/N3, C310-N1/N2/N3/N4, C350-N1, C390-N1) |

**Recommendation: CONTINUE, but widen the domain — do not retire.** The argument for retiring
(nothing moves) is real and is the same one raised for `web4-lct` at `C422 §H.8`. It does not hold
here, for one measured reason: **this pass's headline is a defect in the frozen target itself**,
reached by asking a question about the *corpus* rather than the *document*. A frozen file is not an
exhausted file (v69) as long as the corpus around it keeps declaring things the file claims to
classify.

What should change is the **domain**, not the cadence: the target-plus-8-mirrors window has returned
zero twice running and is no longer informative. C470 should pre-register its window as **the subject
matter** — every artifact declaring a T3/V3 trust, value or economic parameter, `archive/` excluded —
with the target-and-mirror window kept only as a freeze check. **§K's I5 is that widening's first
step.**

**Counter-argument, recorded so the operator can weigh it**: 9 rows have never been closed by any
pass, and 2 of them (`C310-N1`, `C390-N1`) are blocked on decisions only the operator can make. If
those stay unanswered, a 12th pass will re-publish 9 HELD rows and the ledger's value degrades
regardless of what the sweep finds. **The rows, not the cadence, are what needs the operator.**
