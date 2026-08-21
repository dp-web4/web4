# C426 — `atp-adp-cycle.md` 10th Delta Audit

**Date**: 2026-08-21 · **Track**: legion-web4 · **Slot**: `web4-20260821-060000` · **Protocol**: v2
**Target**: `web4-standard/core-spec/atp-adp-cycle.md` (blob `2d060579`, 804 L)
**Predecessor**: C386 (9th delta, PR #714, doc commit `cd39cfab`)
**Lineage**: **13 at base, 14 with C426.** Rule, run not copied (v33):
`ls -1 docs/audits/ | grep -E '^(C[0-9]+-)?atp-adp-cycle'` → 13. The unprefixed
`atp-adp-cycle-internal-consistency-2026-05-23.md` **is** a member (standing inclusive rule; C332
verified, not re-litigated). C346 published 11 and was two short because `ls` sorts `C34` after
`C306` **and** the unprefixed member sorts first; C386 corrected the first half.

**Result**: **ZERO mutation, 6th consecutive frozen delta.** 1 net-new MED, 1 net-new LOW-MED,
1 INFO widening. Two proposed headlines **killed by policy review** — the surviving MED came out of
attacking the second kill.

---

## §A — Delta (window, freeze, mirrors)

**Window pre-registered (v26)**: `cd39cfab..HEAD` (C386's doc commit → `c50364c3`), whole repo,
all filetypes; `web4-standard/` sub-window reported separately.

| measure | value | command |
|---|---|---|
| window, repo-wide | **26** commits | `git log --oneline cd39cfab..HEAD \| wc -l` |
| window, `web4-standard/` | **1** — `2462881f` (interface planes) | `git log --oneline cd39cfab..HEAD -- web4-standard/` |
| ATP tokens in that commit | **0 artifacts** | `git log -p … \| grep -ciE '\batp\b'` → 2, both prose |
| target freeze | **45 d** (`256ab51d`, 2026-07-07) | `git log -1 --format=%cs -- <target>` |

**Mirror blob table** — all 12 tracked artifacts **byte-identical to C386**. §A is a negative by blob
identity; anchors are NOT re-resolved on an unchanged blob (C344 precedent).

| artifact | blob | last touched |
|---|---|---|
| `core-spec/atp-adp-cycle.md` | `2d060579` | 2026-07-07 |
| `implementation/sdk/web4/atp.py` | `efa5de3c` | 2026-05-24 |
| `web4-core/src/atp.rs` | `f5b0efe0` | 2026-05-13 |
| `implementation/sdk/tests/test_atp.py` | `cb7ecff3` | 2026-05-24 |
| `implementation/sdk/tests/test_conformance.py` | `79ce20d6` | 2026-05-19 |
| `implementation/sdk/tests/test_vectors.py` | `eb163b0f` | 2026-04-17 |
| `testing/conformance/atp-operations.json` | `31cbd900` | 2026-05-14 |
| `test-vectors/atp/transfer-operations.json` | `3b89dffc` | 2026-02-27 |
| `test-vectors/schema-validation/atp-jsonld-validation.json` | `11485cec` | 2026-03-22 |
| `schemas/atp-jsonld.schema.json` | `a8e07c0f` | 2026-03-21 |
| `schemas/contexts/atp.jsonld` | `a78531a0` | 2026-03-21 |
| `deployment/config/demurrage.example.json` | `699ad842` | 2025-12-05 |

**v36 set difference, recorded including the negative.** Domain word `ATP` (word-bounded) over
`web4-standard/`, non-audit = **136** files; filename sweep `atp-adp-cycle` = **19**;
residue `comm -23` = **117**. **No residue member postdates C386** — the only in-window
`web4-standard/` commit is `2462881f`, which touches no ATP artifact. Residue yield: **none**,
published as a negative so a later fire's positive is interpretable.

---

## §B — C386 guard regression: **both guards fire NEGATIVE (nothing landed)**

**Guard 1 — re-run the A/B/C conservation evaluation first, and identify which form landed.**
**None did.** All three forms sit exactly where C386 left them:

| form | statement | sites at HEAD |
|---|---|---|
| **C** | `initial == final + fees` | spec `:214`, `atp.rs:11`, `atp.py:10`, `atp.py:319`, executable `check_conservation()` `atp.py:310-323` |
| **B** | `sender_deducted = amount + fee − overflow` | `atp.py:252` |
| **A** | `sender_deducted == actual_credit + fee + overflow` | `atp.rs:135` (rustdoc, **released crate**), `atp-operations.json` `xfer-001.invariant` |

C386-N1 stands **entirely open**. The one-sided-fix hazard C386 warned about has not been triggered
because no fix was attempted.

**Guard 2 — if `:342` now calls `check_conservation`, verify it is reached before recording
enforcement.** It does not. `test_conformance.py:342` is still
`assert exp.get("conservation_holds", True)`.

**Qualified, per v73** — the negative is about *one file*, not the corpus:
`check_conservation` **is** called from `test_atp.py:357-398`, `test_vectors.py:241`,
`test_integration.py:304`/`:512`, and is re-exported at `web4/__init__.py:109`/`:579`.
It is called from `test_conformance.py` **zero** times. That file-scoped zero is the finding;
an unqualified "nothing calls it" would be a false absence.

---

## §C — Deferral rows d3–d6 (C386 §H), all four discharged or routed

### d3 — the `sdk-test.yml` path-filter question, re-scoped to `testing/conformance/` — **CONFIRMED**

`.github/workflows/sdk-test.yml` `paths:` on **both** `push` and `pull_request` =
`web4-standard/implementation/sdk/**` and `.github/workflows/sdk-test.yml`.
`web4-standard/testing/conformance/atp-operations.json` — the data consumed by
`TestATPConformance`, the only CI-wired ATP gate (C386's corrected gate inventory, item 4) — is
**outside** that filter. Denominator: `grep -rln 'atp-operations\|testing/conformance' .github/workflows/`
= **0 of 0** workflows reference it.
C346 refuted this candidate **for `test-vectors/` only**; a refutation licenses only its range (v41),
and this is the other range. **ROUTED to the SDK/CI owner**, not charged here.

### d4 — reachability of the `ATPAccount` valid docs — **DISCHARGED, and it produced N1**

Two corrections to the row as written. (i) The suite has **8** valid docs, not 5: 5 `ATPAccount`
+ 3 `TransferResult` (C386-N2 already charged one of the latter). (ii) The row's `invalid` half is
**ill-posed**: a negative vector is unreachable *by construction*, so reachability is a
positive-vector predicate; the predicate that applies to the 15 `invalid` docs is *rejection*, and
C346's 23/23 shape result already settled it. d4 therefore reduces to the 5 `ATPAccount` docs.

**Executed** (SDK on `sys.path`, in-memory, disk `md5` unchanged):

| id | `available+locked+adp` | `initial_balance` | identity holds | `total` ok | `energy_ratio` exact |
|---|---|---|---|---|---|
| `atp-valid-001` | 0 | 0 | ✅ | ✅ | ✅ |
| **`atp-valid-002`** | **1100.0** | **1000.0** | **❌** | ✅ | **❌** (doc `0.909`, SDK `0.9090909090909091`) |
| `atp-valid-003` | 1000.0 | 1000.0 | ✅ | ✅ | ✅ |
| `atp-valid-004` | 1000.0 | 1000.0 | ✅ | ✅ | ✅ |
| `atp-valid-005` | 0.006 | 0.006 | ✅ | ✅ | ✅ |

**4 of 5 hold the accounting identity; `atp-valid-002` alone breaks it, and is alone in having an
inexact `energy_ratio`.** The two anomalies are the same anomaly: `0.909` is the rounded value of
the ratio computed from the non-conserving numbers. → **N1**.

### d6 — the other two `invariant`-bearing suites — **ROUTED, not adjudicated**

- `testing/conformance/r6-r7-actions.json:147` — *"ReputationDelta.role_lct MUST equal
  ActionRole.role_lct from the action that generated it"* → **reputation lineage** (next: C432).
- `testing/conformance/society-roles.json:72` — *"Authority binds to role_lct, not filling entity.
  Rotation preserves accountability chain."* → **society-roles / SOCIETY lineage**.

Both are declarative invariant strings of the same class as the ATP one C386 found vacuously
asserted. Whether anything asserts *them* is their lineage's measurement, not this one's.

### d5 — `deployment/config/demurrage.example.json` read against §3.3 / §7.2 — **DISCHARGED** → **N2 + I-2**

Reading the config against §3.3 forced enumerating §3.3's four-mechanism block, which 13 passes had
never done (v76). That is **N2**. The config's own orphaning is **I-2**.

---

## §D — Findings

### N1 — **A deflation that never retired its row: `B4` is carried OPEN under a description this lineage refuted four passes ago** — LOW-MED → SDK track + carry-table owner

**The row.** `C78:83` filed **B4**: *"SDK `recharge()` does rate-based **ADP→ATP** with no value
proof, contradicting §7.1 MUST #4"*, routed CROSS-TRACK with the remedy *"either the SDK gates
`recharge` (or renames it to a non-charging primitive), or the spec acknowledges a passive-recovery
model and scopes MUST #4"*.

**The deflation.** `C190:113`, in its own §D (INFO / deflated — anti-overcall record):

> ***`recharge()` is neither §2.1 minting nor §2.2 value-proof charging*** *— a rate-based
> replenishment toward `max_multiplier * initial_balance` (L97-106). A primitive-layer convenience
> (SAGE/IRP-style energy top-up); **does not contradict the spec**, simply not the spec's charging
> model. INFO.*

**The defect.** The deflation never reached the carry table. B4 is still carried as an **open
CROSS-TRACK row, under the original refuted description**, in every pass since:

| pass | locus | how B4 is carried |
|---|---|---|
| C118 | `:46` | *"**B4** (SDK `recharge()` rate-based **ADP→ATP** with no value proof — CROSS-TRACK): **STILL OPEN**"* |
| C190 | `:113` | **substance deflated to INFO — table not updated** |
| C306 | `:182` | `atp.py` blob unchanged ⇒ *"B3/B4/I2/…"* HELD |
| C346 | `:416`, `:277` | `B3 / B4 / I2 / B6-SDK \| 4 \| **4** \| HELD` — and B4 is one of *"the nine labels the ledger holds"* |
| C386 | `:412` | `B3 / B4 / I2 / B6-SDK \| 4 \| HELD; atp.py byte-frozen \| SDK track` |

**Why it matters, concretely.** Both mirrors were executed this pass. `self.adp` has exactly **one**
mutation site per mirror — `atp.py:104` and `atp.rs:82`, both `+=`, both inside `commit()`.
**Nothing anywhere decrements `adp`.** There is no ADP→ATP conversion in the code at all. A
remediator working the carry table would set out to *gate a conversion that does not exist*, and the
remedy as written ("gate or rename") cannot be evaluated against a description that is false.

**Disposition.** Not a re-adjudication — C190's ruling stands and is not reopened. The ask is a
**ledger correction**: retire B4 per C190 §D, or re-describe it to whatever residual survives the
deflation. Precedent for the class: `C322-N1` / `C324-N1` (rows that stopped being typed).
**v42 applied**: a deflation retires the row; here it retired the *substance* and left the *label*.

**Severity capped LOW-MED** (v45): `recharge` has **12** `.recharge(` call sites across
`web4-standard/` + `web4-core/`, **all tests**, and is **not** exported from `web4/__init__.py`.
It does ship in released crates (`git tag --contains 8857ab09` → `web4-core-rust-v0.3.0`,
`web4-core-py-v0.3.0`, `web4-sdk-py-v0.27.0`). The defect charged here is in the **ledger**, not the
code.

### N2 — **Two enumerations of "Anti-Hoarding Mechanisms" with different cardinality; and §7.1 MUST #2's antecedent has no normative referent** — LOW-MED → standard-editor

**Filed as a challenge to `C150:52` / `C190:57` and a rung below `C78:140` — not as net-new.**

`atp-adp-cycle.md:293-298` §3.3 enumerates **four** mechanisms:

1. Demurrage · 2. Velocity Requirements · 3. Stake Limits · 4. Use-or-Lose

`ATP_INTEGRATION_SUMMARY.md:75-92`, under the **same section name**, enumerates **three** —
Demurrage, Velocity Requirements, Stake Limits. **Use-or-Lose is absent.**

**The polarity is inverted from what you would expect.** The spec gives each mechanism one line; the
non-normative summary gives each three bullets. For mechanisms 2 and 3, the **summary is the only
document in the corpus with definitional content** — *"Minimum circulation rates enforced / Stagnant
pools penalized / Active use rewarded"* and *"Maximum stakeable amounts / **Excess returns to pool** /
Prevents concentration"*.

**§7.1 MUST #2 (`:618`)** — *"Entities MUST NOT accumulate tokens beyond stake limits"* — binds on
`stake limits`. Matcher published: `grep -rni 'stake[ _-]*limit\|stakeable' web4-standard/` = **4
hits in 2 files**: `:297` (the §3.3 name), `:618` (the MUST), and
`ATP_INTEGRATION_SUMMARY.md:89-90`. There is no schema field, no SDK constant, no test vector and no
numeric anywhere. **The MUST's antecedent's only expansion is non-normative summary prose.**

**Capped at VACUOUS, not violated (v74)** — publishing the vacuity is the finding. Severity does not
rise past LOW-MED.

**Near-misses named in the same sentence (v73), so the successor does not re-derive them:**
`atp.py:238-262` / `atp.rs:136` `max_balance` + overflow-to-sender is a caller-supplied **receiver**
cap inside `transfer()`, CI-wired via `xfer-002` — semantically close to *"Maximum stakeable amounts
/ Excess returns to pool"* but it is not a society-declared accumulation limit;
`T3V3_PRIVACY_GOVERNANCE.md:104` `max_stake_per_query` is per-query, a different object;
`society.py:225 reclaim()` is an explicit-amount treasury reclaim called at termination (`:541-549`),
not a time-triggered sweep of unutilized allocations.

**Prior art cited, not re-charged.** `C78:140` raised the pairing *"'Non-accumulative … cannot be
hoarded' (§1.2 L24) is absolute, while §3.3/§7.1#2 permit holding up to stake limits"* and deflated
it to INFO on the ground that §1.2 qualifies *"by entities"*. That deflation **presupposes that
stake limits have content**. C426 drops a rung (v61): C78 asked whether two claims conflict; this
asks whether one of them names anything. `C150:52` and `C190:57` both map *"MUST #2 (§3.3)"* in a
§7.1 normative-summary blindspot re-check whose predicate is *"no new cross-section contradiction"* —
a different question from *"is the antecedent defined"*. Neither mapping is contradicted; both are
challenged on scope.

**Implementation status of the block, honestly qualified.** Three of the four mechanisms have an
implementation, and **all three are in `archive/`**: `atp_demurrage.py:454`
`check_velocity_requirement` + `:473` `min_velocity_per_month` (mechanism 2), `:243-247`
`max_holding_days` → *"forcing ADP conversion"* (mechanism 4), and the demurrage engine itself
(mechanism 1). Mechanism 3 has none anywhere. **Not charged** — the corpus archives deliberately.
Recorded because the first draft of this cell said *"1 of 4"*, which was an artifact of excluding
`archive/` from the sweep (v75: a filter is a guess about where the subject matter lives).
**False-mirror guard for the next pass:** `mcp-servers/web4-trust/server.ts` `*Velocity` is
**V3-tensor** velocity, not ATP circulation velocity — do not count it for mechanism 2.

### I-1 — **Widening of the standing I2 row: the two mirrors' `recharge` docstrings disagree, and only the Python one makes a false claim** — INFO-LOW, Python-only

`atp.py:119`: *"Recharge ATP **from ADP pool**"*. The body never reads `self.adp`, and under the
settled `I2` / `C34-M6` reading there is no ADP pool to draw from.
`atp.rs:97`: *"Recharge: add ATP up to `max_multiplier * initial_balance`"* — **makes no ADP claim.**

One mirror's docstring is wrong and the other's is right: a genuine discrimination, and the natural
fix is to copy the Rust wording. **Filed under the existing I2 / C11-M6 row (SDK docstring wording),
not as net-new.** Note the row it widens is the same row that killed this pass's second headline.

### I-2 — **The demurrage deployment surface is orphaned as a block, not as two pointers** — INFO, widening input to the OPEN operator row C306-N2

**No adjudication** — C306-N2 is operator-owned and this pass's scope bar excludes re-adjudication.

`0e547127` (2025-12-05) shipped, together: `deployment/config/demurrage.example.json`,
`demurrage.dev.json`, `systemd/web4-demurrage.service`, `cron/web4-demurrage.cron`,
the `deployment/README.md` section, and `implementation/reference/demurrage_service.py` +
`atp_demurrage.py`. `12ee197c` (2026-05-12) archived the two Python files and left the other five in
place. C306-N2 / C346-N3 charge **two broken `cp` source paths** in `README.md` L33-34/L83-84;
the **consumer-orphaning of the whole block** is the same commit under a different predicate.

**Denominator published (v40), and the first draft of this cell was wrong.** Of **14** substantive
config keys, **6** have zero readers outside `archive/`
(`min_velocity_per_month`, `velocity_penalty_rate`, `decay_calculation_interval_hours`,
`metrics_file`, `pid_file`, `log_file`); **7** more appear outside `archive/` only in the live
`deployment/README.md`, which documents them rather than reading them. An earlier draft published
*"11 of 11 keys read by exactly one file"* — false; the pass's own measurement table showed
`atp_demurrage.py` reading 8 of them. Corrected here rather than silently dropped.

This bears directly on `C306:252` option (b) — *"restore the two files because the shipped deployment
surface depends on them"*. Per `C346:660` the class is to be decided as one; this is input to that
decision, and `C306:281` already named the class (*"deployment configs, service units, cron entries,
install guides — which no C-series lineage has ever gated"*).

---

## §E — Two headlines proposed, two headlines killed. The instrument story is the yield.

Both of this pass's proposed headlines were killed by policy review, and **both were killed by a
disclaimer written within three lines of the code under test, on a line this lineage had already
adjudicated and I did not read before measuring.**

**Headline 1 — "§3.3 declares four anti-hoarding mechanisms and only one is implemented."**
Killed by this pass's *own other finding*. The `archive/` exclusion in my implementation sweep was a
guess about where the subject matter lives (v75); `atp_demurrage.py` implements mechanisms 2 and 4,
and I had read the file that names them (`demurrage.example.json`) ten minutes earlier for I-2
without reading what its keys *mean*. Also wrong in that draft: *"`stake limits` occurs exactly
twice"* (it is 4 — my own sweep returned `ATP_INTEGRATION_SUMMARY.md:89-90` and my sentence dropped
it), and *"every §3.3 citation in the lineage is about text consistency"* (`C78:140` is a
substantive normative-conflict candidate).

**Headline 2 — "`recharge()` breaks the two-state invariant; `atp-valid-002` is the canonized
result."** The arithmetic was right and reproducible: `ATPAccount(1000) → lock(350) → commit(100) →
recharge()` yields exactly `(750.0, 250.0, 100.0, init 1000.0)`, `available+locked+adp = 1100`,
matching `atp-valid-002` field-for-field; 4 of the other 5 `ATPAccount` valid docs hold the identity
and `atp-valid-002` is alone in having an inexact `energy_ratio`. **The predicate was wrong.**
`atp.py:54` declares *"Invariant: total = available + locked (**ADP is separate tracking**)"* and
`atp.rs:43` declares *"Total active ATP (available + locked). **ADP is separate.**"* — I imported the
**spec's** identity onto a class that disclaims it, in both mirrors, three lines above the field.
Disclosure at the point of use, polarity against me (v45/v57). And `C78:51` had opened that exact
line and ruled *"the line-54 invariant `total = available + locked` **is itself correct**"* — my
headline reached the opposite verdict on the same line without citing the pass that settled it.
`adp` is monotonic by construction (one `+=` site per mirror, no decrement anywhere), so the 100
units are counted once as spent plus a historical record; there is no double-count.
The mutation in §D of my draft (`recharge` debits `self.adp` → 7 failed) was **not v59-plausible**:
plausibility is judged against the *declared* design, and the declared design says `adp` is not a
pool. The suite was pinning the designed semantics, not requiring a defect.

**`atp-valid-002` is recorded as a DEFLATED CANDIDATE with its predicate named**, so a successor
neither re-derives it nor mistakes it for a live row: the artifact **never claims arithmetic**.
`test_schema_validation_vectors.py:25` validates **shape** only — it never sums the fields and never
recomputes `energy_ratio`; `C346:440` records the predicate verbatim (*"two dataclass shapes match
their schema"*). "Valid" there means *conforms to the atp schema*. The hand-authored `0.909`
three-decimal literal is evidence for the shape-fixture reading, and there is **no `recharge` token
anywhere in that vector file** — the state merely *coincides* with the executed sequence.
Coincidence is not provenance.

**What this cost and what it bought.** Both kills were cheap because the premise was submitted
**measured** rather than as a plan; the reviewer could run the falsifier instead of arguing about a
proposal. Headline 2 only existed because the reviewer killed headline 1 and left d4 as the pass's
remaining work — and N1 as filed exists only because the reviewer killed headline 2. **The pass's
findings are all downstream of its own refutations.**

**Reviewer cell corrected back (v52).** The review's first pass held that the lineage is **12** docs,
excluding the unprefixed `atp-adp-cycle-internal-consistency-2026-05-23.md`. That is the exclusive
rule. `C386:457` names the standing inclusive rule and `C386:555` states the base verbatim; running
it (`ls -1 docs/audits/ | grep -E '^(C[0-9]+-)?atp-adp-cycle'`) returns **13**. Accepted on
re-review. Two different mis-enumerations of the same lineage in three passes — C346 mis-**sorted**,
the reviewer mis-**scoped** — which is why the rule says *run it, never copy the number*.

---

## §F — Novelty (matchers published)

| claim | matcher | result |
|---|---|---|
| `atp-valid-002` never named | `git grep -n "atp-valid-002" -- docs/audits/` | **0 of 255** docs |
| `web4-economy/server.ts` unseen by this lineage | `git grep -c web4-economy -- docs/audits/` | **2 of 255** (C384, C424 — both *mcp-protocol*), **0 of 13** atp docs |
| §3.3 never enumerated as a block | `grep -ci 'anti-hoard\|hoarding'` over the 13 | **`anti-hoard*` = 0 in all 13**; `hoard` = C78 only |
| §3.3 citation base rate | `grep -c '§3\.3'` over the 13 | **31**: C190 7, C78 5, C150 4, C34 3, C118 3, C119 2, C151 2, C228 2, C266 1, C306 1, C386 1, C346 0, internal-consistency 0 |
| the config pair never read for content | `git grep -n "demurrage.example\|demurrage.dev" -- docs/audits/` | 4 hits, **all blob-table rows** (C306:45, C346:85/:646, C386:102/:545) |

---

## §G — Deferral row for C466 (the next `atp-adp` delta) — pre-registered

1. **C386-N1 (the A/B/C conservation split) is UNFIXED after two full windows.** Re-run the A/B/C
   evaluation **first** and identify which form landed; a one-sided fix is the C346-N1 shape
   recurring. If `test_conformance.py:342` now calls `check_conservation`, verify it is *reached*
   (`git log -S`) before recording enforcement. **Third consecutive no-motion ⇒ escalate as a stall,
   do not re-file.**
2. **N1's ask is a ledger edit, so check the LEDGER, not the code.** `atp.py`/`atp.rs` are frozen;
   B4 will look "HELD" by blob identity in any pass that measures the code. Regression instrument:
   `grep -n "B4" docs/audits/C466-*.md` — if B4 is still carried with the token `ADP→ATP`, it is
   unretired. Do **not** re-adjudicate C190 §D.
3. **N2 regression:** `grep -rni 'stake[ _-]*limit\|stakeable' web4-standard/` — still 4 in 2 files?
   And has `ATP_INTEGRATION_SUMMARY.md:75-92` gained a fourth member, or §3.3 lost one?
4. **DO NOT RE-RUN, all executed and settled this pass:** d3 (CI path filter — **CONFIRMED and
   ROUTED**, it is the SDK/CI owner's, not a finding to re-file); d4 (**DISCHARGED**; its `invalid`
   half is ill-posed — reachability is a positive-vector predicate and C346's 23/23 covers
   rejection); the 5 `ATPAccount` valid docs' arithmetic (table in §C); the `available+locked+adp`
   identity (**disclaimed at `atp.py:54` / `atp.rs:43`, ruled correct at `C78:51`** — a third pass
   at this line is a rediscovery); `atp-009`/`atp-010`'s missing ADP term (ratified by C190 §D).
5. **d6 was ROUTED, not adjudicated** — `r6-r7-actions.json:147` → reputation (C432);
   `society-roles.json:72` → society-roles. Do not adjudicate them here; check only whether the
   receivers took them.
6. **I-2 is operator input, not a row to charge.** If C306-N2 is still unanswered at C466, idle it —
   do not re-audit or self-decide.
7. **Still open, unchanged, do NOT re-file:** C386-N1, C386-N2, C346-N1 (`ISP-B11` absorption, ISP
   not re-audited since C62), C306-N1 (`validate_vectors.py` 0 invocations), C306-N2 / C346-N3
   (broken paths), B1/B2b/M2/ISP-B10/B3/I2/B6-SDK/X1/B8, the I-2 false-mirror guard
   (`lct.rs:585 slash()`, `ledger.rs mint()`), ontology term non-resolution, JSONC fences (C158),
   3/3 `to_jsonld()`.
8. **New false-mirror guard:** `mcp-servers/web4-trust/server.ts` `*Velocity` = V3-tensor velocity,
   **not** ATP circulation velocity.

---

## §H — Method carry proposed: **v78 — read the implementation's own declared invariant before testing one against it**

An invariant you bring from the spec is a hypothesis about the code, not a property of it. Before
charging an implementation with breaking an identity, **read the class's own declared invariant** —
it is usually within three lines of the field you are summing, and if it disclaims your identity the
polarity is against you (v45/v57), not merely neutral. Then **grep the lineage for the line number
you are about to charge**: `C78:51` had already opened `atp.py:54` and ruled it correct, and a
headline that reaches the opposite verdict on an adjudicated line without citing the adjudication is
a rediscovery at best.

Two corollaries earned the same way:

- **v59's "plausible" is judged against the DECLARED design, not against the spec.** A mutation that
  contradicts the class's own stated invariant does not measure whether the suite is blind; the
  resulting failures are the suite correctly pinning the design.
- **When two findings in one pass touch the same artifact, cross-execute them before drafting.**
  Headline 1's falsifier was sitting inside I-2's evidence set — the same two files, read ten
  minutes apart, for different predicates. An auditor's own section boundary is a filter, and a
  filter is where the false absence lives (v75).

And the shape of the pass is itself the lesson: **submit the premise MEASURED, not as a plan.** Both
kills were adjudicated on re-run commands rather than argued, and each kill handed the pass its next
piece of work.
