# C386 — `atp-adp-cycle.md` Ninth Delta Re-Audit
## (the conservation invariant is published in two correct forms and a third that is false under the only reading the corpus defines — and the runner that would have caught it asserts a JSON literal)

**Date**: 2026-08-14
**Target**: `web4-standard/core-spec/atp-adp-cycle.md`
**Slot**: C386 (rotation arithmetic: C346 + 40)
**HEAD**: `294cf283`
**Predecessor**: `docs/audits/C346-atp-adp-cycle-8th-delta-2026-08-09.md` (PR #681, doc commit `03b61ac2`)
**Lineage rule (inclusive, stated per the standing enumeration rule)**: every C-numbered
`atp-adp-cycle*` audit **plus** the non-C-numbered
`atp-adp-cycle-internal-consistency-2026-05-23.md`. That is **12 documents at base**
(`ls -1 docs/audits/ | grep -E '^(C[0-9]+-)?atp-adp-cycle'`), **13 with this pass**. C346 counted
**11 + itself**; the discrepancy is C346's own — it excluded one member. See §F.1.

---

## Headline

The target is **byte-frozen for the 38th day** and the corpus delta is **empty for the fourth
consecutive pass**. The yield is therefore entirely a *per-locus* novelty result (v56), and it is
executable.

`atp-adp-cycle.md:214` names a **transfer-conservation invariant** and states it as
`initial == final + fees`. Four further prose sites and one executable function state the same
thing compatibly. **Two sites state something else**:

> `sender_deducted == actual_credit + fee + overflow`

— `web4-standard/testing/conformance/atp-operations.json`, the `invariant` field of `xfer-001`,
and `web4-core/src/atp.rs:135`, the rustdoc on `pub fn transfer`, in a **released crate**
(`web4-core-rust-v0.3.0`).

That statement is not a variant spelling. Under the reading the corpus itself supplies for
`sender_deducted` — **net balance delta**, fixed by `atp.py:252` and written out in so many words by
this lineage's own `C190:84` (*"`transfer()` **net** `sender_deducted == …`"*) — it is **false for
`xfer-002`, a vector shipped in the same JSON file**: net deducted **10**, right-hand side **30**.
Under the only reading that rescues it — *gross* debit, `amount + fee` — it reduces to
`amount == actual_credit + overflow`, which is the **definition of `overflow` in the implementation
it documents**: a tautology, not a conservation statement. It is false or it is vacuous; there is no
third reading.

Nothing in the repository can detect this, and the reason is the finding's second half. The
conformance suite's `description` says *"Conservation invariant MUST hold across all operations."*
The one assertion in the suite that names it is `test_conformance.py:342`:

```python
        # Conservation invariant
        assert exp.get("conservation_holds", True)
```

It asserts the **vector's own JSON literal**, not a computed property of the result — and it is
**doubly** vacuous: deleting the `conservation_holds` key from the vector entirely still yields
`11 passed` (probe run and reverted, §C.1.5). It is the **only** self-satisfying assertion among
**101** asserts in an 892-line file. Meanwhile the SDK exports a **real computed checker** —
`check_conservation()`, `atp.py:310-323`, called from `test_atp.py`, `test_vectors.py:241`,
`test_integration.py:304` and `:512` — which `test_conformance.py` **never calls**. The conformance
runner had the instrument and used a literal instead.

The same wrong formula independently produced a **second** artifact. `atp-valid-007` in
`test-vectors/schema-validation/atp-jsonld-validation.json` — a **MUST-PASS** document — publishes
`{fee: 10, sender_balance: 0, receiver_balance: 900, actual_credit: 400, overflow: 590}`. Those five
numbers are formula A applied literally (`1000 − (400 + 10 + 590) = 0`). The implementation the
schema's own `description` names yields **`sender_balance = 590`**, and the balance the document
requires is provably **unreachable**: it needs a sender opening at `410` while `transfer()` refuses
any opening balance below `1000` for that input (§C.2, executed). **This is N2, and it discharges
`C372:383` deferral row **d4**, which routed the `atp` schema/vector sweep to this slot.**

**Prior art, named rather than absorbed** (v44): C166's standing GUARD, carried forward at
`C190:96`, is that this invariant *"has **no positive definition site**"* in the spec — it appears
only in exception framing. `C190:102` files INFO I-2 on the definite article at `:213`. **This pass
charges a different thing**: not the absence of a definition site, but the **non-equivalence of the
sites that do exist**, and the runner's structural inability to see it. C166/C190 asked *"is it
stated?"*; C386 asks *"do the statements agree, and does anything check?"*

**Findings: N1 MEDIUM · N2 MEDIUM · 1 INFO. 2 net-new. ZERO mutation. C387 = declared NO-OP.**

---

## Severity legend

| | |
|---|---|
| **MEDIUM** | A normative-facing artifact publishes something false or unachievable, and no gate can detect it. Routed; not auditor-applicable. |
| **LOW** | Doc-quality or process defect with bounded reach. |
| **INFO** | Recorded so a later pass does not re-derive it as new. Routed to nobody. |

---

## §A — Freeze and window

Collapsed to a blob table per the C344/C346 precedent: **do not re-resolve anchors on an unchanged
blob.**

| artifact | blob at HEAD | last commit | date |
|---|---|---|---|
| `web4-standard/core-spec/atp-adp-cycle.md` | `2d060579` | `256ab51d` | 2026-07-07 |
| `web4-standard/schemas/atp-jsonld.schema.json` | `a8e07c0f` | `639cdebd` | 2026-03-21 |
| `web4-standard/schemas/contexts/atp.jsonld` | `a78531a0` | `639cdebd` | 2026-03-21 |
| `web4-standard/test-vectors/atp/transfer-operations.json` | `3b89dffc` | `a3b93713` | 2026-02-27 |
| `web4-standard/test-vectors/schema-validation/atp-jsonld-validation.json` | `11485cec` | `3495e135` | 2026-03-22 |
| `web4-standard/testing/conformance/atp-operations.json` | `31cbd900` | `92454d65` | 2026-05-14 |
| `web4-standard/deployment/config/demurrage.example.json` | `699ad842` | `0e547127` | 2025-12-05 |
| `web4-core/src/atp.rs` | `f5b0efe0` | `8857ab09` | 2026-05-13 |
| `web4-standard/implementation/sdk/web4/atp.py` | `efa5de3c` | `62524cf8` | 2026-05-24 |
| `web4-standard/test-vectors/validate_vectors.py` | `5259d473` | `a3b93713` | 2026-02-27 |
| **`web4-standard/implementation/sdk/tests/test_conformance.py`** *(new member, §B.4)* | `79ce20d6` | `b6c243c2` | 2026-05-19 |

- Target **byte-frozen 38 days**, blob `2d060579`, **804 L**. **5th consecutive frozen delta.**
- **All 11 mirror artifacts frozen** — every last-commit date above predates this window.
- **Window pre-registered** (v26): span `03b61ac2..HEAD`; root = repo root; tree = all; filetypes =
  all.

| claim | command | result |
|---|---|---|
| window size | `git log --oneline 03b61ac2..HEAD \| wc -l` | **30** commits |
| window ∩ `web4-standard/` | `git log --oneline 03b61ac2..HEAD -- web4-standard/` | **1** — `afd04623` |
| what `afd04623` touched | `git diff --name-only … \| grep -v docs/audits/` | `errors.md`, `security-framework.md`, `submission/draft-web4-core-00.xml` — **no ATP artifact** |
| window ATP tokens | `git log -S'ATP' 03b61ac2..HEAD -- web4-standard/ \| wc -l` | **0** |

`afd04623` is the commit that broke the `security-framework.md` freeze at C376. It does not reach
this target.

---

## §B — Mirror set and the directions swept

### B.1 — v36 as a set difference, verb set pre-registered

Pre-registered before running (v26): verb set = `\b(atp|adp|demurrage)\b`, case-insensitive;
window = `docs/audits/` + `web4-standard/docs/audits/`; subtract the filename sweep
(`atp-adp-cycle`).

| | count |
|---|--:|
| domain-word hits (`git grep -lEi '\b(atp\|adp\|demurrage)\b'`) | **157** |
| filename hits (`git grep -l "atp-adp-cycle"`) | **94** |
| **residue** (`comm -23`) | **63** |
| residue rows **postdating C346** (2026-08-09) | **2** |

The two rows that postdate the predecessor — where this instrument's yield has lived on C344,
C346 and C348 — are:

1. **`C350:307`** (t3-v3 9th delta) — names `test-vectors/validate_vectors.py` and its
   `87 t3v3+atp` result. **Not an addressee row**; it is another lineage reading the same runner
   C346 characterised as gate 3. Recorded so C426 does not re-derive it.
2. **`C372:383`, deferral row `d4`** — *an addressee row, and this slot is its named receiver*:
   > *"Remaining: `acp`, **`atp`**, `attestation-envelope`, `capability`, `dictionary`,
   > `r7-action`, `t3v3` → **each to its own lineage slot**, one per pass."*

   The ask, in the C332/C328 shape, is: *does the schema ship MUST-PASS vectors that contradict its
   spec?* **RECEIVED and DISCHARGED this pass — see N2.** The answer is yes, one of three.

**Record the negative too** (v36): no other residue row addresses this lineage.

### B.2 — C346's own guard 2, honoured

C346's guard 2 forbids re-running a census over held labels and calling it a ledger check. The set
difference above is the instrument it prescribed. It returned one live addressee row (`C372-d4`),
and that row is discharged in this document rather than routed onward.

### B.3 — Novelty, per LOCUS (v56), enumerated in TWO passes (v57)

The finding lives in `test_conformance.py` and `atp-operations.json`. Both are cited artifacts, so
stage 1 does **not** dispose of them.

**`atp-operations.json` — cited 7 times across 3 documents**, and the naive "a fourth gate nobody
named" framing is **wrong**; it is true only of C346 §E's *table*:

| doc | line | what it is |
|---|--:|---|
| C306 | `:44` | a row in a mirror-set count table |
| C306 | `:167`, `:177` | **C306-N1 in full** — the `atp-001`–`atp-005` id collision |
| C308 | `:255` | INFO-1, an `ls` of `testing/conformance/` |
| C346 | `:84` | the freeze table |
| C346 | `:177` | prose — *"the suite that minted the colliding identifier block"* |
| C346 | `:645` | the C386 baseline |

**`test_conformance.py` — cited by 6 documents at 9 line loci**, enumerated in two passes:
(a) `git grep -ohE "test_conformance\.py:[0-9]+" -- docs/audits/` → `:115 :174 :213 :526 :575
:692-693 :807 :826 :887`; (b) grep the **path** and read each hit's surrounding line for a bare
`` `:N` `` detached from the filename (the v57 blind spot) → **nothing additional inside the ATP
block**. **None of the 9 loci falls in `:238-395`, the `TestATPConformance` block.**

**And the prior denominator that *did* contain the block, disclosed rather than hidden** (v46,
applied to my own novelty claim): `docs/audits/sprint-52-conformance-gap-consolidation-2026-05-15.md`
is the origin of **all nine** loci, and its **Source** line covers this suite by brace expansion —
`web4-standard/testing/conformance/{tensor,atp,r6-r7,society}-*.json`. It surveyed all **39** tests
and catalogued **8 xfails**, **none of them ATP**. Its instrument was the **xfail count**, which is
structurally blind to a *passing-but-vacuous* assert. `C306:161` went further and **executed** the
gate (`pytest tests/test_conformance.py tests/test_vectors.py` → `71 passed, 5 xfailed`) — and a
green count is likewise blind to it.

**So the honest novelty statement is not "nobody looked."** It is: *the suite was named 7 times and
executed at least once; its runner-side ATP block has never been read at a locus, and every
instrument previously pointed at it (xfail census, pass count) is incapable of seeing a vacuous
assertion.*

### B.4 — A member the mirror set was missing

`test_conformance.py` is the **executing consumer** of `testing/conformance/atp-operations.json` and
was absent from every prior baseline in this lineage (C266, C306, C346). Added to §G's baseline for
C426.

---

## §C — Findings

### N1 (MEDIUM, net-new) — the transfer-conservation invariant is published in a form that is false under the corpus's own reading and vacuous under the only reading that saves it, in a released crate, behind an assertion that cannot fail

**Route**: standard-editor / author ruling + SDK track + `web4-core` crate owner.
**Not auditor-applicable** — it is a ruling on which of the published forms is canonical, and the
fix touches an outward conformance artifact and a released Rust crate.

#### C.1.1 — The three forms, and where each is stated

| form | statement | sites | count |
|---|---|---|--:|
| **C** | `initial == final + fees` | spec `:214`; `atp.rs:11` (module "Key invariants"); `atp.py:10`; `atp.py:319` (docstring of `check_conservation`) — **plus the executable `check_conservation()` at `atp.py:310-323`** | 4 prose + 1 executable |
| **B** | `sender_deducted = amount + fee - overflow` | `atp.py:252` (docstring of `transfer`) | 1 |
| **A** | `sender_deducted == actual_credit + fee + overflow` | `atp-operations.json` `xfer-001.invariant`; **`atp.rs:135`** (rustdoc on `pub fn transfer`) | 2 |

C and B are per-system and per-account statements of the same fact and agree on every vector. **A is
the outlier at 2 sites against 5.**

#### C.1.2 — Executed: A is false for `xfer-002`

Both transfer vectors driven through the SDK's own `transfer()`, all three forms evaluated:

```
id         deducted  A: cr+fee+ovf  B: amt+fee-ovf  C: init==fin+fees
xfer-001      31.50     31.50    OK      31.50    OK   150.00==150.00    OK
xfer-002      10.00     30.00 FALSE      10.00    OK   190.00==190.00    OK
xfer-003   (error vector — no arithmetic)
```

`xfer-002` and `xfer-001` are **in the same JSON file**. `atp.rs::transfer()` is behaviourally
identical to `atp.py`'s (`available -= total_deduction; available += overflow`) — there is no
Rust/Python divergence; both bindings implement B/C and **document** A.

#### C.1.3 — The rescue reading, and why it does not rescue

`sender_deducted` could be read as the **gross** debit (`amount + fee`) rather than the net balance
delta. On that reading A is true on both vectors (`30 == 10 + 0 + 20`), and `xfer-001` cannot
disambiguate — with `overflow = 0`, gross and net coincide at `31.50`. `xfer-002` ships **no**
`invariant` field, so the JSON alone never fixes the reading.

**Two things close it.**

1. **The corpus defines the identifier, and defines it as net.** `atp.py:252` states
   `sender_deducted = amount + fee - overflow` for the same name. And this lineage's own
   **`C190:84` writes it out**: *"`transfer()` **net** `sender_deducted == actual_credit + fee +
   overflow`"* — the prior pass read it as net, which is precisely what makes its verdict
   chargeable (§C.1.4).
2. **Under the gross reading A is a tautology.** Substituting `sender_deducted = amount + fee` and
   cancelling `fee` gives `amount == actual_credit + overflow`, which is the *definition* of
   `overflow` at `atp.py:264` / `atp.rs:157-165` (`overflow = amount - actual_credit`). It states
   nothing about conservation, and it cannot fail for any input.

**A is false under the only reading its corpus defines, and vacuous under the only reading that
saves it.**

#### C.1.4 — The prior verdict, and the three lines it stopped short of (v41/v52)

`sender_deducted` and `actual_credit` occur in exactly **one** audit document corpus-wide —
`C190:84`, this lineage's own 4th delta — which certified the pair **"Concordant."** Per v57, one
prior citation is **materiality, not a tombstone**: it proves the formula is load-bearing in the
audit record. So the question is *which clause of the cited range C190 relied on*:

> `| 2 | Transfer conservation (§2.4 post-C151 / §6.3) | header `sum(initial)==sum(final)+total_fees`
> (L11); `transfer()` net `sender_deducted == actual_credit + fee + overflow` (L135, L143–176);
> `test_transfer_conservation` (**L228–243**) | **Concordant.** |`

`test_transfer_conservation` (`atp.rs:229-244`) calls `transfer(..., None)` — `max_balance = None`,
so **`overflow` is structurally `0.0`**, and its closing comment is `31.5 == 30 + 1.5 ✓`. It is the
one arm on which A and C agree.

The falsifier is **`test_transfer_with_max_balance`, `atp.rs:246-258`** — `overflow = 20.0`,
`assert_eq!(sender.available, 90.0); // 100 - 30 + 20 overflow`. It computes A's counterexample and
asserts it, without ever naming conservation. **It begins three lines below the end of C190's cited
range.** A verdict licenses only the range it was measured on (v41); C190's "Concordant" does not
reach `:246-258`, and C190 was right about everything it looked at.

#### C.1.5 — Why no gate can see it: the interlock

This is the half that makes it structural rather than clerical.

| | |
|---|---|
| the suite's own claim | `atp-operations.json` `description`: *"Conservation invariant MUST hold across all operations."* |
| the only assertion naming it | `test_conformance.py:342` — `assert exp.get("conservation_holds", True)` |
| what it asserts | the vector's own literal `true` at `atp-operations.json:84`. Not a property of `result`. |
| **doubly vacuous** | probe: delete `conservation_holds` from `xfer-001` → **`11 passed`**. `.get(…, True)` passes on absence too. *(Mutated in place, run, reverted; tree restored byte-identical, `md5 a965c69a…`, `git status` clean.)* |
| uniqueness | **1 of 101** asserts in 892 lines. Every other `.get(…)`-with-default in the file guards an `if` that then asserts a **computed** value (`:126 :128 :130 :132 :167 :201 :211 :553 :555 :557 :585 :587`). The three bare `assert False` at `:812 :830 :888` are unconditional xfail markers — a different class. |
| the instrument that existed | **`check_conservation()`**, `atp.py:310-323`, exported in `web4/__init__.py:579` and `atp.py:28`, called from `test_atp.py:357/367/377/387/398`, `test_vectors.py:241`, `test_integration.py:304`, `test_integration.py:512` — and from `test_conformance.py` **zero times**. |
| the inert prose | the `invariant` field itself. **3 of 5** conformance suites publish one; **1 of 3** (`r6-r7-actions.json`, at `test_conformance.py:641`) is consumed by the runner, and only as an assertion **message** on a computed assert. ATP's is the one that is both **formula-shaped** and **unconsumed**. |

**The vacuous assert is *why* the contradictory `invariant` string survived 92 days.** The runner
shipped with a real checker in the same package and reached for a literal instead.

#### C.1.6 — Direction, dated (not assumed)

| date | commit | event |
|---|---|---|
| 2026-03-13 | `b052beb8` | `atp.py:252` states **B** (correct) |
| **2026-05-13** | `8857ab09` | `atp.rs` lands with **C** at `:11` **and A at `:135`** — the two forms enter the same 289-line file together |
| 2026-05-14 | `92454d65` | `atp-operations.json` lands carrying **A** as `xfer-001.invariant` |
| 2026-05-14 | `381904a4` | pytest wiring lands with the self-satisfying assert (`test_conformance.py:342`) |
| **2026-06-06** | `f854ef0e` | **the spec first states the invariant, as C**, at `:214` — in a C34 remediation, **24 days after A had already propagated to two artifacts** |

So this is not "the outward artifact is stale." The standard settled on the correct form **after**
the wrong one had shipped downstream, and neither downstream site was reconciled in the **69 days**
since. Nearest named class (v44/v57): the **`remediation-incompleteness` family** (`C36` → `C38:144`
→ `C56:67` → `C60:110-116` → `C64:18` → `C166:90`) — a remediation that corrected one site and left
its siblings. **Filed as the Nth member of that family, not as a new class.**

#### C.1.7 — Severity: MEDIUM, and the concession that earns it

**Stated plainly: the vector DATA is correct and the harm is bounded to prose.** `xfer-002` asserts
`sender_balance == 90.0`; a binding that implemented A literally would produce `70.0` and **fail the
vector**. So the conformance suite does not actually license a wrong implementation.

On the flat claim "A is false" alone this would be a **LOW** — an unconsumed metadata field, correct
data, all 11 tests green. What lifts it to **MEDIUM** is the conjunction:

1. `atp.rs:135` is the **rustdoc on `pub fn transfer` in a released crate** —
   `git tag --contains 8857ab09` → `web4-core-rust-v0.2.0`, `web4-core-rust-v0.3.0`. Anyone reading
   the public API docs reads a false-or-vacuous invariant.
2. The **conformance suite is the artifact the standard publishes for other language bindings**, and
   its stated invariant contradicts the data it ships with.
3. **N2** shows the same formula already produced a second, independently authored artifact that is
   unreachable — so this is a propagating error, not an isolated typo.
4. No gate in the repository can detect any of it (§C.1.5).

---

### N2 (MEDIUM, net-new) — a MUST-PASS schema-validation document computed with formula A, unreachable by the implementation the schema names

**Route**: SDK track + standard-editor. **Discharges `C372:383` deferral row `d4` for `atp`.**

`test-vectors/schema-validation/atp-jsonld-validation.json` declares (`meta.description`):

> *"Each 'valid' document MUST pass validation."*

and `schemas/atp-jsonld.schema.json`'s own `description` names what it validates:

> *"Validates output from `ATPAccount.to_jsonld()`, `TransferResult.to_jsonld()`, and cross-language
> implementations."*

The suite holds **8 valid / 15 invalid** = the 23 C346 executed. **3 of the 8** valid documents are
`TransferResult`s:

| id | document | reachable? |
|---|---|---|
| `atp-valid-006` | `fee 5, sender 495, receiver 500, credit 495` | ✅ (`s0 = 995`, `amount = 495`) |
| `atp-valid-008` | `fee 0, sender 100, receiver 200, credit 100` | ✅ (`s0 = 200`, `amount = 100`) |
| **`atp-valid-007`** | `fee 10, sender_balance 0, receiver 900, credit 400, overflow 590` | ❌ **unreachable** |

**Executed proof.** `transfer()` fixes `amount = actual_credit + overflow = 990`. Then
`sender_balance = s0 − (amount + fee) + overflow`, so `sender_balance = 0` requires
**`s0 = 410`** — while the same call requires `s0 ≥ amount + fee = 1000` or it raises
`Insufficient balance`. **Unsatisfiable.** Driving the implementation with the opening balance the
document implies:

```
transfer(s0=1000, r0=500, amount=990, fee_rate=10/990, max_balance=900)
  → fee=10.0  sender=590.0  receiver=900.0  credit=400.0  overflow=590.0
doc claims sender_balance=0; implementation yields 590.0
```

Every other field matches exactly. **The one field that differs is exactly the overflow, `590`** —
i.e. the document's author computed `1000 − (400 + 10 + 590) = 0`: **formula A, applied literally.**

This is the **C332 shape** (*"the green IS the defect"* — MUST-PASS vectors that the function the
schema names cannot produce), reached independently here. The 23/23 green is honest about what it
tests — **shape** — and says nothing about whether the numbers are producible; `atp-jsonld.schema.json`
constrains no arithmetic. **C346's §E observation 3 stands unrevised** (the schema gate covers 0 of
§7.1's 6 MUSTs); N2 is the next rung down: the gate also does not notice that one of its MUST-PASS
documents is counterfactual.

---

### I-1 (INFO) — recorded so C426 does not re-derive it

`C350:307` (t3-v3 9th delta, 2026-08-10) independently reads
`test-vectors/validate_vectors.py` and reports its `87 t3v3+atp` result. That is C346's **gate 3**
seen from the other lineage. **Not an addressee row, not a defect, routed to nobody.**

---

## §D — C346's six guards and the carry ledger, executed

Every cell is a measurement taken this pass at `294cf283`, with the command that produced it.

| # | C346 guard | command | measured at HEAD | verdict |
|--:|---|---|---|---|
| 1 | was N1 reconciled — does `C62-B11` carry a disposition in the **ISP** ledger, and does B1's description name ISP §4.1 again? | `git grep -n "C62-B11\|ISP-B11" -- docs/audits/`; `ls docs/audits/*inter-society*` | `ISP-B11` still **1 doc** (`C78:68`, `:109`). Newest ISP-lineage doc is still **`C62-…-2026-06-16`** — ISP has not been re-audited, so nothing *could* have changed. | **UNCHANGED — C346-N1 stands** |
| 2 | do not census held labels; run the set difference | §B.1 | run; **63** residue, **2** postdating C346, **1** an addressee row (`C372-d4`) | **HONOURED** — and it yielded, again |
| 3 | was C306-N1 option (i) amended; did any runner become wired? | `git grep -rn "validate_vectors" -- . ':!docs/audits' ':!*validate_vectors.py'` | hits only in `forum/nova/**` copies and 2 READMEs. **0 invocations.** No duplicate-ID check appeared. | **UNCHANGED — C346-N2 stands** |
| 3b | is the `atp-001`–`atp-005` collision still live? | id-collect ∩ over both suites | conformance `{atp-001…005, xfer-001…003, scale-001…003}` ∩ vectors `{atp-001…015}` = **`atp-001`…`atp-005`**, still **5** | **UNCHANGED — C306-N1 stands** |
| 4 | check C346-N3's links and C306-N2's paths **as one class** | `grep -n` + file-existence | `README.md:229` and `ATP_INTEGRATION_SUMMARY.md:7` both still point at `implementation/ATP_ADP_IMPLEMENTATION_INSIGHTS.md` — **absent**. `deployment/README.md` L33-34 **and** L83-84 still `cp ../implementation/reference/{demurrage_service,atp_demurrage}.py` — **both absent**; file last touched `0e547127` **2025-12-05** | **UNCHANGED — C306-N2 + C346-N3 stand, still undecided together** |
| 5 | do not re-open the refuted rows | — | not re-opened: I-2 false mirrors (`lct.rs:585 slash()`, `ledger.rs mint()`), ontology term non-resolution, JSONC fences (C158-owned), the 23/23 suite *(N2 charges a **different predicate** — reachability, not shape; stated explicitly)*, the 3/3 `to_jsonld()`↔schema result, the `sdk-test.yml` path-filter candidate, the 25 outward files' non-citation | **RESPECTED** |
| 6 | build §G by capture; re-derive every scope, denominator and path root | §F | done; **1 correction** to C346's own lineage count (§F.1), **1** to my own novelty framing (§F.2) | **DONE** |

**Carry ledger.** No row lost a locus. No row gained one. All held by byte-freeze.

| Carry | loci | status | route |
|---|--:|---|---|
| **B1** (§5 abstract-FX vs mcp §7.7) + the absorbed **`C62-B11`** half | 1 + 1 | **OPEN, still mis-scoped** — guard 1 negative | operator + ISP lineage |
| **B2b** §5.3 exchange bypasses MUST #4/#5/#6 | 1 | HELD (DESIGN-Q, both sides in one frozen blob) | operator |
| **M2** §2.4 cap never references §6.1 `max_slash_per_event` | 3 (`:184`/`:194`/`:547`) | HELD by byte-freeze | operator |
| **ISP-B10** commitment-ATP charged-vs-allocated | 1 | HELD; ISP frozen since C62 | operator |
| **B3 / B4 / I2 / B6-SDK** | 4 | HELD; `atp.py` byte-frozen | SDK track |
| **X1** `lct:web4:` identifier | 1 | HELD (C33 corpus decision) | cross-track |
| **B8** (inbound, acp-owned) | 1 (`:621`) | STANDS | acp lineage |
| **C306-N1** vector-ID collision | 1 | HELD, unchanged (guard 3b) | operator/author |
| **C306-N2** deployment README paths | 2 | HELD, unchanged (guard 4) | operator/author |
| **C346-N1** absorbed carry never reported back | 2 | **OPEN**, guard 1 negative | operator + ISP |
| **C346-N2** `validate_vectors.py` has 0 invocations | 1 | HELD, unchanged (guard 3) | operator |
| **C346-N3** two pointers to an archived ATP doc | 2 | HELD, unchanged (guard 4) | operator/author |
| **C166 GUARD / C190 I-2** no positive definition site; definite article at `:213` | 2 | **HELD and cited, not re-charged** — N1 is a different predicate (§ Headline) | operator |
| **I-1…I-5** (C266/C306) | — | HELD as recorded | unchanged |
| **`C372-d4` (`atp` row)** | 1 | **RECEIVED and DISCHARGED this pass** → N2 | closed here |

---

## §E — The gate inventory, corrected to four

C346 published three gates over this target's vectors. There are **four**; the fourth is the one
that carries the finding.

| gate | wired to CI? | scope | reports | what the green answers |
|---|---|---|---|---|
| `test-vectors/validate_context_refs.py` | **yes** (`vector-context-refs.yml`) | 1 of 2 atp vector files | `atp.jsonld OK (21 refs, 1 files)` | cited `web4.io` context URIs resolve |
| `test-vectors/schema-validation/validate_schema_vectors.py` | no | the schema-validation suite | `atp: 23/23 passed` | **two dataclass SHAPES** match their schema — **not** that the documents are producible (**N2**) |
| `test-vectors/validate_vectors.py` | no — **0 invocations** | 2 of 35 files | `87 passed, 0 failed` | transfer arithmetic reproduces |
| **`implementation/sdk/tests/test_conformance.py::TestATPConformance`** *(the fourth)* | **yes** — under `sdk-test.yml`'s path filter | 11 vectors from `testing/conformance/atp-operations.json` | `11 passed` | the 11 vectors' **numeric expectations** reproduce — and **nothing about conservation**, despite one assert naming it (**N1**) |

Two observations worth carrying:

1. **The fourth gate is the only ATP gate actually wired to CI** — and its *data* lives at
   `web4-standard/testing/conformance/`, **outside** `sdk-test.yml`'s `implementation/sdk/**` path
   filter. C346 examined this shape for `test-vectors/` and **refuted** it as latent (1 of 3
   commits). **I did not re-derive it for `testing/conformance/`, and I am not charging it** — it is
   flagged as a C426 deferral row (§G d3) precisely because C346's refutation was measured on a
   different tree and does not license a skip here (v41).
2. **The vacuity is invisible to every instrument previously pointed at this block** — sprint-52's
   xfail census (8 xfails, none ATP) and C306's pass count (`71 passed, 5 xfailed`) both report
   green. That is v43/v47 one rung further on: **coverage is not execution; execution is not
   assertion.**

---

## §F — Own errors

Published because a pass that reports only its findings is reporting half its instrument.

1. **I inherited C346's lineage count and it is one short.** C346's header and its guard 6 both say
   *"11 docs at base + this pass."* The inclusive rule it states —
   `^(C[0-9]+-)?atp-adp-cycle` over `docs/audits/` — returns **12**: the 11 C346 counted **plus
   `C34-atp-adp-cycle-audit-2026-06-06.md`**, which sorts after `C306`/`C346` in `ls` order because
   `C34` is lexically later than `C306`. This is the standing enumeration hazard in a new dress —
   not a glob trap this time but a **sort-order** trap in a hand-transcribed list. Base is **12**,
   **13** with this pass. C346's guard 6 warned that a C-number-based count would reproduce its own
   error; it did — I caught it only by running the rule rather than copying the number.
2. **My first novelty framing was false and the policy review killed it.** I drafted *"a fourth gate
   C346 never named"* on a per-*table* reading, when `atp-operations.json` is cited **7 times across
   3 documents** and C306-N1 is *entirely about that file*. The claim survives only in the
   per-locus form (§B.3), and the honest version had to disclose **sprint-52's brace-expanded
   denominator** and **C306:161's execution** — both of which I had not found. **Ninth consecutive
   pass in which policy review falsified a load-bearing cell.**
3. **My headline was falsifiable as first written.** *"A is FALSE"* has a rescue reading (gross vs
   net) that `xfer-001` cannot disambiguate and that `xfer-002` does not carry an `invariant` field
   to settle. The reviewer supplied it; the corrected form (**false under the corpus's reading,
   vacuous under the rescue**) is strictly stronger and is not falsifiable. **Had I shipped the
   original, the first reader with the gross reading would have closed the finding.**
4. **Form C was undercounted 2 → 4 prose sites + 1 executable.** I missed `atp.py:10` and
   `atp.py:319`, and — materially — I missed `check_conservation()` entirely on the first pass. That
   omission would have cost the finding its interlock (§C.1.5), which is the half that makes it
   MEDIUM rather than LOW.
5. **A reviewer anchor was off by one, and I checked** (v52, fourth consecutive pass on which this
   rule paid): the reviewer's own correction #2 said the literal `initial == final + fees` is at
   `:214`, not the `:213` I had published. **Verified — `:214` is right, my `:213` was wrong.**
   `C190:96` cites the pair correctly as `L213–214`. Of the reviewer's **8** corrections, I verified
   all 8 and **rejected none** — the first pass in six with a zero rejection count. Recorded as a
   datapoint, not a policy change.
6. **`git status` clean after the mutation probe.** The `conservation_holds` deletion in §C.1.5 was
   made in place, run, and reverted from a backup; `md5sum` before and after both `a965c69a…`;
   `git status --porcelain` empty. Stated because a probe that mutates a tracked vector must publish
   its restoration.

---

## §G — Disposition, baseline, and guards for C426

**Findings: N1 MEDIUM · N2 MEDIUM · I-1 INFO. 2 net-new. ZERO mutation. 1 new file.**

- **C387 = declared NO-OP.** N1 is an author ruling on which published form is canonical and its fix
  touches a **released crate** (`web4-core-rust-v0.3.0`) plus an outward conformance artifact; N2 is
  an SDK/vector correction. Neither is an auditor's edit. Do **not** self-fix
  `atp-adp-cycle.md`, `atp.rs`, `atp.py`, `atp-operations.json`, `atp-jsonld-validation.json`,
  `test_conformance.py`, or any workflow.
- **Decide N1's two A-sites together.** Correcting the rustdoc without the conformance `invariant`
  field (or vice versa) leaves the divergence intact in the other direction — the exact failure mode
  C346-N1 documents one level up.
- **The cheapest correct fix, offered without applying it**: replace `test_conformance.py:342` with
  a call to the `check_conservation()` the package already exports, and let the resulting failure
  (or pass) decide which form is canonical. That is v45's *"the caller count is the conformance
  measurement"* turned into a one-line remedy.
- **`C372-d4`'s `atp` row is CLOSED here** — the receiving lineage acted and is recording the
  disposition where the sender will read it (v37). The remaining d4 members (`acp`,
  `attestation-envelope`, `capability`, `dictionary`, `r7-action`, `t3v3`) are untouched by this
  pass and remain routed to their own slots.
- **Rotation**: next atp delta ≈ **C426**.

**Baseline for C426.** All paths repo-relative and **verified to resolve as written**. Blobs in §A.

- target `web4-standard/core-spec/atp-adp-cycle.md` — `256ab51d` (*blob* `2d060579`, **804 L**;
  §7.1 heading `:615`, its **6 MUSTs** `:617-622`, MUST-#6-scope note `:624-633`, escrow note
  `:635-641`, §2.4 `:184`/`:194`, **the invariant literal `:214`** *(C386 §F.5 — C346's baseline did
  not carry this anchor)*, §6.1 `:547`, §5.3 `:511-512`, MUST #5 referent `:621`)
- the other **10** artifacts of the §A table, at the blobs recorded there
- **new baseline member**: `web4-standard/implementation/sdk/tests/test_conformance.py` — `b6c243c2`
  (*blob* `79ce20d6`, 892 L; `TestATPConformance` `:238-395`, the vacuous assert **`:342`**, the
  computed-invariant counter-example **`:641`**)
- **new baseline member**: `web4-standard/implementation/sdk/web4/atp.py` **`:310-323`**
  (`check_conservation`) — the unused instrument

**Guards for C426.**
1. **Re-run the executable check first, and identify WHICH form landed.** Evaluate A/B/C against
   `xfer-001`/`xfer-002` (§C.1.2's script). If A is gone from `atp.rs:135`, confirm it is also gone
   from `atp-operations.json` — **a one-sided fix is the C346-N1 shape recurring**, and this pass
   pre-registers that as the thing to look for.
2. **Check whether `test_conformance.py:342` still asserts a literal.** If it now calls
   `check_conservation`, **verify it is reached** (`git log -S` for the call expression) before
   recording it as enforcement — v45, and C346's guard 3 in its general form.
3. **NEW deferral row d3 — the path-filter question for `testing/conformance/`.** C346 measured the
   `sdk-test.yml` filter gap against `test-vectors/` and refuted it (1 of 3 commits). It was **not**
   measured against `web4-standard/testing/conformance/`, and a refutation licenses only the range
   it was measured on (v41). Measure: since `270a5715` (2026-03-27), how many commits touch
   `testing/conformance/` **without** touching `implementation/sdk/`? If that count is non-trivial
   the gap is demonstrated, not latent.
4. **d4 — `atp-valid-007`'s siblings.** N2 checked the **3** `TransferResult` documents. The **5**
   `ATPAccount` valid documents and all **15** `invalid` documents were **not** checked for
   reachability. Do them, and publish the denominator.
5. **d5 — `deployment/config/demurrage.example.json`** has been in this lineage's baseline since
   C266 and has **never been read against §3.3 / §7.2**. Nine passes.
6. **d6 — the other two `invariant`-bearing conformance suites.** `society-roles.json`'s `invariant`
   is prose (not formula-shaped) and unconsumed; `r6-r7-actions.json`'s is consumed as a message.
   Neither was checked for *truth*. Not this lineage's subject matter — **route, do not adjudicate.**
7. Do **not** re-open: I-2's false mirrors (`lct.rs:585 slash()`, `ledger.rs mint()`); ontology term
   non-resolution; JSONC fences (C158-owned); the 23/23 **shape** result (N2 charges reachability, a
   different predicate — do not read N2 as re-opening it); the 3/3 `to_jsonld()`↔schema result; the
   25 outward files' non-citation; C346's §E path-filter candidate **for `test-vectors/`** (guard 3
   above is a *different tree*, deliberately).
8. **Count the lineage by running the rule, not by copying the number** (§F.1). Base is **13** after
   this pass. `ls` sorts `C34` after `C306`.

**Instrument index.** Warranty: **results** re-run against the tree at `294cf283` after the findings
were written; **instruments, scopes, denominators and path roots** re-derived in a second separate
sweep. **Not mechanically reproducible — one row, named rather than absorbed**: the residue triage
in §B.1 is hand-read after the mechanical `comm -23`, though its verb set **was** pre-registered
this time (C346's could not say that).

| claim | instrument | scope | result |
|---|---|---|---|
| target frozen 38 d | `git log -1 --format=%h -- web4-standard/core-spec/atp-adp-cycle.md` | 1 file | `256ab51d`, 2026-07-07 |
| mirror set frozen | `git rev-parse HEAD:<path>` × 11 | 11 files | §A table |
| window | `git log --oneline 03b61ac2..HEAD` | repo | **30** commits |
| window ∩ standard | `git log --oneline 03b61ac2..HEAD -- web4-standard/` | tree | **1** (`afd04623`) |
| window ATP tokens | `git log -S'ATP' 03b61ac2..HEAD -- web4-standard/ \| wc -l` | window | **0** |
| v36 residue | `comm -23` of `git grep -lEi '\b(atp\|adp\|demurrage)\b'` minus `git grep -l atp-adp-cycle` | both audit trees | domain **157**, filename **94**, residue **63**, postdating C346 **2** |
| locus novelty (pass a) | `git grep -ohE "test_conformance\.py:[0-9]+" -- docs/audits/` | both audit trees | **9** loci, **0** in `:238-395` |
| locus novelty (pass b) | grep the path, read each hit's surrounding line for a bare `` `:N` `` | both audit trees | **0** additional |
| `conservation_holds` novelty | `git grep -lF conservation_holds -- docs/audits/ web4-standard/docs/audits/` | both audit trees | **0** |
| `atp-operations.json` citations | `git grep -n atp-operations -- docs/audits/` | both audit trees | **7** hits / **3** docs |
| the three forms | evaluated against both transfer vectors through `web4.atp.transfer` | 2 vectors × 3 forms | A **FALSE on xfer-002** (30 vs 10); B, C **OK on both** |
| A's rescue reading | algebraic substitution `sender_deducted := amount + fee` | 1 formula | collapses to `amount == credit + overflow` = `overflow`'s definition (`atp.py:264`) |
| assert census | `grep -c "assert " tests/test_conformance.py` | 1 file | **101** (the 102nd `assert` token is prose at `:190`) |
| self-satisfying uniqueness | `grep -nE "assert (exp\|vec\|inv\|v)\b[^=<>!]*$"` | 1 file | **1** — `:342` |
| vacuity probe | delete `conservation_holds`, re-run, revert | 1 vector | **`11 passed`**; tree restored, `md5 a965c69a…` |
| `check_conservation` callers | `git grep -n check_conservation -- . ':!docs/audits' ':!archive'` | repo | `test_atp.py` ×5, `test_vectors.py:241`, `test_integration.py:304`,`:512`, `test_package_api.py:411` — **`test_conformance.py` 0** |
| `invariant` field census | JSON walk × 5 suites + `grep -n '\["invariant"\]'` | 5 suites + 1 runner | **3 of 5** publish one; **1 of 3** consumed (`:641`, as a message) |
| C190's cited range | `sed -n '84p'` | 1 line | `L228–243`; falsifier at `atp.rs:246-258` |
| released crate | `git tag --contains 8857ab09` | repo tags | `web4-core-rust-v0.2.0`, `web4-core-rust-v0.3.0` |
| N2 reachability | solve `transfer()` for the document's five fields, then execute | 3 `TransferResult` docs | **1 of 3 unreachable** (`atp-valid-007`); impl yields `590.0` vs doc's `0` |
| guard 1 (ISP) | `git grep -n "C62-B11\|ISP-B11" -- docs/audits/` | both audit trees | `ISP-B11` **1** doc (C78); newest ISP doc still C62 |
| guard 3 (validator) | `git grep -rn validate_vectors -- . ':!docs/audits' ':!*validate_vectors.py'` | repo | **0** invocations |
| guard 3b (collision) | id-collect ∩ over both atp suites | 2 files | **5** ids |
| guard 4 (links) | `grep -n` + file existence × 4 paths | 3 files | **4 of 4** still broken |
| lineage size | `ls -1 docs/audits/ \| grep -E '^(C[0-9]+-)?atp-adp-cycle'` | 1 dir | **12** at base, **13** with this pass |

---

## Pattern (C386)

**An unexecutable statement drifts from the data it ships with, and the drift is invisible in
proportion to how confidently the artifact asserts it.**

C346's lesson was that a carry can fail *by being received*. This one is about a different kind of
receipt. The conformance suite says *"Conservation invariant MUST hold across all operations"* and
ships a line of prose stating the invariant — prose that no runner parses, in a file whose entire
purpose is to be machine-consumed by other language bindings. Because nothing evaluates it, nothing
notices when it stops matching the vectors two entries below it, or the spec that was corrected 24
days later, or the two other files that state it correctly. It then propagated: into a released
crate's public API documentation, and into a MUST-PASS validation document describing an account
state no implementation can reach.

The runner is the part worth keeping. It **had** the instrument — `check_conservation()`, exported,
computed, and called from four other test modules in the same package — and at the one place that
names the conservation invariant it wrote `assert exp.get("conservation_holds", True)`: an assertion
about the vector's opinion of itself. That is the single site in 892 lines and 101 asserts that opted
out of the file's own convention, and every instrument previously aimed at this block — an xfail
census, a pass count, two prior audits — reports green, correctly, because a vacuous assertion is
exactly as green as a true one.

**v58: a claim that no instrument consumes is not documentation, it is an unversioned fork.** When a
machine-readable artifact carries a human-readable statement of its own invariant, check first
whether *anything* evaluates it — and if nothing does, treat every copy of that statement as an
independent artifact that must be dated and diffed against the others, not as a restatement of one
fact. The corollary is where the yield was: **when you find a vacuous assertion, look for the real
checker.** Its existence is what turns "sloppy test" into a finding, and its call graph tells you the
convention the vacuous site departed from.

→ [[feedback_unit_green_is_not_system_green]] · [[feedback_coverage_is_not_execution]] ·
[[feedback_modality_needs_an_enforcer]] · [[feedback_decline_licenses_its_range]] ·
[[feedback_cited_locus_detached_from_filename]] · [[feedback_novelty_is_per_locus_not_per_artifact]]
