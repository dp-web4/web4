# C326: `web4-society-authority-law.md` (SAL) — 8th delta re-audit

**Date**: 2026-08-06
**Auditor**: Autonomous session (legion-web4-20260806-180032), v2 protocol
**Document**: `web4-standard/core-spec/web4-society-authority-law.md` — blob `0849ebbe`, 419 L
**Window**: `70381838..HEAD` (C286's merge 2026-07-30 → `6b160f68`) = **59 commits**
**Lineage**: **C16** → C23 → C58 → C98 → C134 → C170 → C208 → C246 → C286 → **C326** (9 prior passes)
**Prior remediation**: C16-rem `3e152e02` (#240, 5 of 12); C59 `0d756773` (#330, 10/10 HELD since C98)

---

## Verdict

| | |
|---|---|
| **Spec mutation** | **ZERO** — SAL byte-frozen at `0849ebbe` since `1354e4c2` (2026-07-14), **23 days**; 0 commits in window |
| **Net-new defects on the spec** | **0** — 7th consecutive fully-clean SAL delta (C98·C134·C170·C208·C246·C286·C326) |
| **Net-new findings** | **1 MED** (N1, ledger-integrity — this lineage's own carry ledger) |
| **Swept clean** | **1** (I-1 — `sal-governance.json`, executed for the first time in the corpus's history, **6/6 pass**) |
| **C286 forward checks** | both answered — **`KNOWN_ROLES` unchanged; no fidelity test appeared** ⇒ **C286-N1 STANDS** |
| **Carry rows restored** | **13 ids** across 10 rows, each with a live-HEAD binary re-verification |
| **Method carry born** | **v24** (member-naming dispositions) — filed as an extension of **v18**, distinguished from v23 |
| **Own cells corrected post-write** | **5** (§G) — incl. one that would have been the pass's headline, and one violating a method carry this pass applies elsewhere |

**§C ledger row count: 19 rows** (13 restored + 6 continuous survivors). Published per **v23**.

---

## §A — Carry-row reconstruction (spine of this pass)

### A.0 — The lineage is 9 documents, not 8, and the origin is invisible to its own naming convention

The rotation locates a lineage by globbing `docs/audits/C*-society-authority-law*`. That returns 8
files. The lineage's **origin pass is not among them**: it is
`docs/audits/sal-internal-consistency-2026-05-27.md`, which self-identifies as `# C16:` on line 1,
predates the `C{n}-{slug}` convention, and is named for the slug alone. C23:6 names it *"Prior
audit"*. It published **12 findings** (2 HIGH / 8 MEDIUM / 2 LOW = H1, H2, M1–M8, L1, L2).

Every prior delta in this lineage inherited its starting row set from a successor document rather
than from C16. This pass reconstructed from C16 forward. **Denominators restated** (all `grep -rlF`,
both audit trees, at `6b160f68`):

| artifact | passes that ever read it |
|---|---|
| `web4-standard/ontology/hub-law.ttl` | 5 of 9 (C134 C170 C208 C246 C286) |
| `web4-standard/core-spec/hub-law-schema.md` | 4 of 9 (C134 C208 C246 C286) |
| **`web4-standard/test-vectors/federation/sal-governance.json`** | **0 of 9** → §B |

### A.1 — C59 remediation and the frozen-target checks

SAL is byte-identical to the blob C208/C246/C286 verified (`git diff 1354e4c2 HEAD -- <SAL>` =
empty). C59-rem 10/10 HELD trivially. Encoding sweep `grep -nE '&#|&amp;|â€' <SAL>` → empty.
Per the C286 §A collapse warrant (cite C208+C246), the C59 sites are not re-derived.

### A.2 — Anchor re-resolution by content (v11 / v22)

The cheap v22 screening test (`git log --oneline 70381838..HEAD -- <file> | wc -l`) and the actual
drift **point opposite ways**, which is worth recording:

| anchor (C286-published) | commits in window | live | result |
|---|---|---|---|
| `main.rs:720` / `:724` (`parse_role`) | **9** | `:720` / `:724` | **HELD exactly** |
| `init.rs:585` (`law_oracle`/`policy_entity` unfilled) | 0 | `:585` | HELD |
| `law.rs:35/39/43/49/57` (`KNOWN_ROLES` + `is_known_role`) | 1 | unchanged | HELD |
| `law.rs:263/275/287/307` (the four hard-`Err` sites) | 1 | unchanged | HELD |
| **`law.rs:447`** (the non-overlap test) | **1** | **`:452`–`:458`** | **DRIFTED +5** |
| SAL spec anchors | 0 | — | HELD |

**v22 refinement (publish, do not treat the count as a predictor):** the file with **9** commits
drifted **0** anchors; the file with **1** commit drifted the only anchor that moved. `main.rs`'s
nine commits all landed below `:724`; `law.rs`'s single commit was a test-module insertion *above*
`:447`. The commit count is a **screening** test — it correctly said "re-resolve `law.rs`" — but its
*magnitude* carries no information about drift. A pass that re-resolves only the hottest file by
commit count would have re-resolved `main.rs` (which held) and skipped `law.rs` (which moved).

### A.3 — C286's two forward checks, answered

C286's guard: *"FIRST CHECK AT C326: did `KNOWN_ROLES` change, and did a fidelity test appear."*

1. **`KNOWN_ROLES` is unchanged.** `law.rs:39-47` still holds exactly 7 entries in the same order:
   `sovereign, administrator, treasurer, archivist, witness, citizen, applicant`. It still rejects
   `law_oracle`, `policy_entity` and `auditor`, and still admits `applicant` (grep = 0 in the
   standard). The four hard-`Err` sites are byte-unchanged.
2. **No fidelity test appeared.** The only `KNOWN_ROLES` test is still the **non-overlap** assertion
   (now `law.rs:452-458`): it asserts society roles ∌ constellation roles and vice-versa. It never
   asserts that `KNOWN_ROLES` **matches** `society-roles.md`. The one in-window `law.rs` commit
   (`5a1d9fa3`, #597) is entirely inside `#[cfg(test)] mod tests` — it vendored the hub-law interop
   fixtures in-repo because a public repo's tests cannot `include_str!` a private sibling.

   **Side finding, recorded not filed:** that commit's own message establishes that
   `cargo test (hub)` in `.github/workflows/ci.yml` *"has been red every run since the workflow was
   armed … that job has never once been green."* C286 cited that workflow (`206dd004`) as the
   mechanism by which a future role-vocabulary drift would be caught. **The gate C286 named as its
   backstop could not compile at the moment C286 named it** — and was fixed four minutes after C286
   merged (C286 `70381838` 04:08:57; `5a1d9fa3` 04:12:08, same day). No action: the gate is green
   now, and the observation is about C286's forward guard, not about SAL. Recorded so the next pass
   does not re-derive it.

⇒ **C286-N1 (MED, routed to HUB track) STANDS, undischarged.** Not re-argued here; not self-applied.

---

### A.4 — **N1 (MED): the carry ledger's dispositions stopped naming their members, and 13 ids went with them**

**Class**: ledger integrity (this lineage's own record). **Not a spec defect. Zero spec mutation.**

#### The census

`grep -oF '<id>' <doc> | wc -l` over all 8 post-C16 passes. Bare-label rows use `grep -oE '\b<id>\b'`
with the collider baselined (below).

| id | C23 | C58 | C98 | C134 | C170 | **C208** | C246 | C286 |
|---|---|---|---|---|---|---|---|---|
| `C16-M8` | 8 | 7 | 3 | 6 | 6 | 5 | 3 | 4 |
| `C23-H1` | 6 | 11 | 8 | 4 | 3 | 2 | 14 | 2 |
| `\bB7` | 0 | 2 | 4 | 3 | 5 | 10 | 0 | 10 |
| `\bB15` | 0 | 2 | 3 | 2 | 6 | 6 | 4 | 7 |
| `\bB6` | 0 | 5 | 4 | 6 | 6 | 5 | 3 | 5 |
| `\bB10` | 0 | 2 | 5 | 5 | 2 | 3 | 2 | 3 |
| **`C16-H1`** | 1 | 3 | 2 | 3 | 1 | **0** | 0 | 0 |
| **`C16-M1`** | 1 | 8 | 2 | 2 | 6 | **0** | **0** | 3 |
| **`C16-M3`** | 1 | 2 | 2 | 2 | 1 | **0** | 0 | 0 |
| **`C16-M4`** | 1 | 2 | 2 | 2 | 5 | **0** | 0 | 0 |
| **`C16-M5`** | 2 | 2 | 1 | 1 | **0** | 0 | 0 | 0 |
| **`C16-M6`** | 1 | 5 | 2 | 2 | 1 | **0** | 0 | 0 |
| **`C23-M3`** | 0 | 4 | 2 | 2 | 1 | **0** | 0 | 0 |
| **`C23-L2`** | 1 | 6 | 2 | 2 | 1 | **0** | 0 | 0 |
| **`\bB1`** | 0 | 3 | 3 | 3 | 1 | **0** | 0 | 0 |
| **`\bB8`** | 0 | 2 | 3 | 2 | 1 | **0** | 0 | 0 |
| **`\bB9`** | 0 | 2 | 5 | 4 | 1 | **0** | 0 | 0 |
| **`\bB11`** | 0 | 2 | 3 | 3 | 2 | **0** | 0 | 0 |
| **`L1-residual`** | 0 | 1 | 2 | 3 | 2 | **0** | 0 | 0 |
| `C16-L1` | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `L1-revised` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**Collider baselines** (v10 rule 2 — a label's count is meaningless until its collider is subtracted):
`\bB1` vs the compound `H1+B1` = 0/0/0/0/**1**/0/0/0, so C170's single `\bB1` **is** the compound
hit ⇒ `B1` has no independent occurrence after C134. `grep -rlF 'C58-B15'` over both audit trees =
**0 files**: `C58-B15` has never once been typed as an id — it exists only as the `/B15` suffix
inside `C58-B10/B15` (4 files). `\bB15`'s healthy-looking counts are the *law-composition* B15
(C50-B15), a **different item** from `C58-B15`.

#### What happened, in the documents' own words

C170:48 enumerates the carry set by id:

> *"All other C58/C23/C16 design-Q and cross-track items (C23-H1+B1, C23-M3, C23-L2, C16-M1+B7,
> C16-M3, C16-M4/M5, C16-M6, B8, B9, B11, L1-residual): referent files all frozen; carries STAND
> verbatim per the C134 §A.3 table."*

C208:43 replaces that with one row:

> `| all other C16/C23/C58 design-Q + cross-track | frozen | referents frozen | **STAND** per the C170 §A.3 table |`

C246 and C286 inherit the collapsed form. **The row was never dropped.** C208 has a row; the row
records a disposition; the disposition says STAND — and it is *true*. What the ledger lost is the
**membership**.

#### Three distinct mechanisms, not one

| # | mechanism | instance | effect |
|---|---|---|---|
| **i** | **compound-token fold** | `C16-M4/M5`; `C58-B10/B15` | the id is greppable only as a substring of another token — `C16-M5` reads 0 at C170 *while still being carried*, and `C58-B15` has never been typed at all |
| **ii** | **rename off the origin prefix** | `C16-L1` → `L1-revised` (C23) → `L1-residual` (C58–C170) | three names for one item; none after the first traces back to the pass that owns it |
| **iii** | **catch-all row** | C208:43 | count preserved, membership lost |

#### Why this is v24 and not a re-file

- **It is not v23.** v23's remedy is *publish the row count*. Here the count never fell — C208 has a
  row for exactly the thing C170 had a row for. Publishing the count is a true statement that
  conceals 13 ids. **v23 is blind to this by construction.**
- **It is not v19 either.** v19 requires that an id absent from a newer pass show *a recorded
  disposition*. C208 **has** one. v19 is satisfied and the ids are still gone.
- **v18 is the prior art and is named here deliberately.** v18 (C318) already holds that *"a carry
  FOLDED INTO another (incl. a RANGE like `B15–B18`) loses its row"* — that is mechanism (i), and a
  catch-all is arguably a degenerate fold. **The genuinely new content is narrower**: the
  disposition's *forwarding pointer decays*. "STAND per the C170 §A.3 table" points into a document
  no later pass re-opens, so the disposition is **present and unrecoverable at the same time**. That,
  and only that, is claimed as new.

> **v24 — a disposition must name its members.** Every carry row must enumerate ids that survive an
> individual `grep -F`. Three failure modes to test each pass: **catch-all** (row names no ids),
> **compound** (id greppable only as a suffix), **rename** (id no longer traces to its origin pass).
> A forwarding pointer to a prior table is not a disposition — the table it points at is a document
> the rotation does not re-open. Extends **v18**; **v23's remedy cannot detect it.**

#### The measured consequence, inside this lineage's own most recent finding

`C16-M1` is the row that proves the swallow was not harmless. It reads 6 at C170 → **0 at C208** →
**0 at C246** → **3 at C286**. It did not survive; it was swallowed and then **independently
re-derived two passes later**, because C286-N1 rediscovered the same subject matter (society-role
vocabulary conflict) from the `hub/` side and reconnected to it only by luck of topic. C286 paid a
full pass to re-derive a taxonomy conflict C16 had recorded **63 days** earlier.

And `C16-H1` closes the loop. C286-N1's own text (`:218`) routes its victim to *"the remedy SAL §9
prescribes for `W4_ERR_LAW_CONFLICT`"* — while `C16-H1-remainder`, dropped at C208, is precisely the
finding that **`W4_ERR_LAW_CONFLICT` does not exist in the canonical error taxonomy.** The 7th
delta's flagship prescribes a remedy that a dropped HIGH from the origin pass says is undefined.

#### Severity: MEDIUM

Higher than the LOW this track assigned at C322/C324, because those drops were **backstopped**
(`carries.md` retained the ids "nowhere else in the repository" being the load-bearing clause).
This one is not: `C16-H1` is a **HIGH**, is typed **cross-track**, is still true at live HEAD, and
`grep -rlF 'C16-H1'` over both audit trees returns files **none of which are after C170**. Not
HIGH: nothing is mis-stated, no spec text is wrong, and every dropped item re-verified as still
true — the defect is recoverability, not correctness.

### A.5 — Binary re-verification of the 13 dropped ids at live HEAD

Per **v10 rule 5**: binary status only, citing the owning pass. **No fresh severity, no
re-argument of merits, no recommended fix.** Definitions taken from C134 §A.3 (`:52-64`), the last
table that defines each id.

| id | owner | definition (C134 §A.3) | live-HEAD instrument | status |
|---|---|---|---|---|
| `C16-H1-remainder` | C16 (**HIGH**, cross-track) | `W4_ERR_LEDGER_WRITE` / `_AUDIT_EVIDENCE` / `_LAW_CONFLICT` absent from `errors.md` + `errors.py` | each `grep -cF` → `errors.md` **0**, `errors.py` **0**; each **1** in SAL | **TRUE** |
| `C16-M1` | C16 | 5-role SAL taxonomy vs 7-base+2-context | re-derived independently as C286-N1 | **TRUE** (re-derived) |
| `C16-M3` | C16 | `r6Bindings` absent from SDK | SAL **1**, `sdk/` **0** | **TRUE** |
| `C16-M4` | C16 | SAL §3.4 ledger ops not mirrored in SDK | `sal.birth\|sal.role.bind\|sal.law.update\|sal.audit.adjust` in `sdk/` = **0** (SAL `:111`) | **TRUE** |
| `C16-M5` | C16 | event-topic + AUDIT `LedgerEventType` | `LedgerEventType` = CITIZENSHIP, LAW_CHANGE, ECONOMIC, METABOLIC, FORMATION — **no AUDIT** | **TRUE** |
| `C16-M6` | C16 | §5.5 cool-down unrepresented in `federation.py` | SAL `grep -ciE 'cool.?down'` **2**, `federation.py` **0** | **TRUE** |
| `C23-M3` | C23 | Rest queue-vs-refuse (SAL §3.6 `:141` "MAY queue") | `metabolic.py:410 accepts_new_citizens()` returns **bool**; SAL is 3-valued (accept / queue / defer) | **TRUE** |
| `C23-L2` | C23 | SDK half — no AUDIT `LedgerEventType` | same instrument as `C16-M5` (overlap noted at C134`:53`) | **TRUE** |
| `B1` | C23 (digest facet of C23-H1) | birth-cert digest | no independent occurrence after C134; rides `C23-H1`, which survives | **FOLDED** — mechanism (i) |
| `B8` | C58 | genesis-citizen terminability (SAL §5.1 vs SOCIETY_SPEC §4.2.1) | both sides frozen since C170 | **TRUE (frozen)** |
| `B9` | C58 | SDK `DORMANT_STATES` ⊇ REST vs SAL §3.6 | `DORMANT_STATES` present, `len == 5` asserted at `test_metabolic.py:396` | **TRUE** |
| `B11` | C58 | §6 `citizen`-binding — `r6-framework.md` has no carrier field | SAL §6 `:256` makes `lawHash` + `society` + `citizen` a **MUST**-bind triple; in `r6-framework.md` `lawHash` = **4** and `society` = **4** (both carried in the `rules` object, `:34-35`, `:381`, `:435`, `:455`), **`citizen` = 0** | **TRUE** |
| `L1-residual` | C16→C23→C58 | SOCIETY_SPEC §1.4 back-link | `SOCIETY_SPECIFICATION.md:39/:59/:299` cite SAL §3.4/§3.1/§5.4 | **TRUE (frozen)** |

**12 TRUE, 1 folded-and-riding. Zero were closed. Zero were remediated.**

**Routing status of the dropped HIGH** (measurement, not adjudication): `C16-H1-remainder` is
typed **cross-track to `errors.md` / `errors.py`**. It is tracked by **no open issue or PR**, and no
audit document after C170 names it. The natural consumer is the **`errors.md` rotation slot — C334**
in the standing order. Named as the route; **no severity assigned by this pass, and neither
`errors.md` nor `errors.py` is touched.**

---

## §B — The artifact 9 passes never read

### B.1 — Inbound derivation (v20)

`git grep -lF 'web4-society-authority-law.md'` = **101 tracked files** (three other spellings of the
same sweep return 100 — see §G correction 6; the two files in the gap are whitepaper *build outputs*
and change nothing here). Filtering to the
standard's own machine-readable artifacts surfaced three, of which two were already in the lineage's
read set (A.0) and one was not: **`web4-standard/test-vectors/federation/sal-governance.json`**.

It declares SAL as its specification in its own header —
`"spec": "web4-standard/core-spec/web4-society-authority-law.md"` — has existed since `f00c35f1`
(2026-03-16, #22), carries **6** vector groups, and `grep -rlF 'sal-governance.json'` over **both**
audit trees returns **0 files**. Not 0 of the SAL lineage: **0 of the entire C-series corpus.**

### B.2 — Refuting my own lead first (the C318 precedent)

This lead has the same shape as C318's flagship — *"the cross-language validator certifies 2 of 22
suites"* — which was **REFUTED under adversarial verification**. That refutation was read in full
**before** this section was written, and all three of its attacks were applied here:

1. **"Not the standard's conformance harness."** Conceded and not contested. **No claim is made in
   this pass about `validate_vectors.py`'s coverage, or about any denominator over suite
   directories.** I built a per-directory consumer table while investigating and **withheld it**:
   it greps the literal string `test-vectors/<dir>`, but `test_r6.py:47` builds
   `VECTORS_DIR = …/test-vectors` and joins the suite name separately, so the instrument
   under-counts by construction and matched `r6` only via a docstring. Publishing a "N of 22"
   contradiction from it would have re-run C318's refuted flagship on a worse instrument. → §G.
2. **"The claim was true when written."** Applied: `git log -S` on the exact docstring line returns
   **one** commit — `f00c35f1`, the same commit that created the vector file. The claim and its
   subject shipped together. It is not an accretion artifact, but neither is it evidence of a
   removed test: **no test has ever referenced this file** (below).
3. **"Different artifact class / it does have a consumer."** This is the one that had to be measured
   rather than argued, and it is why the finding below is an INFO.

### B.3 — Result: **executed for the first time, and it PASSES 6/6**

`grep -lniE 'sal.governance'` across `*.py *.rs *.ts *.js *.yml *.yaml` returns **2** files:
`archive/reference-implementations/governance_simulation_engine.py` (archived) and
`web4-standard/implementation/sdk/web4/federation.py:26` — a **module docstring**:
*"Validated against: web4-standard/test-vectors/federation/sal-governance.json"*.
`test_federation.py` is 639 lines and loads **zero** vector files.

So this pass executed the vectors against `federation.py` directly (throwaway script, run outside
the repo tree; **nothing written to the repo**, per the review's measure-don't-write tripwire):

| vector group | mechanism exercised | result |
|---|---|---|
| `citizenship-lifecycle` | `valid_citizenship_transition` | **PASS** |
| `citizenship-invalid-transitions` | `valid_citizenship_transition` ×8 | **PASS** |
| `quorum-policy-threshold` | `QuorumPolicy.check` | **PASS** `[False,True,True]` |
| `quorum-policy-majority` | `QuorumPolicy.check` | **PASS** `[False,True,False,False]` |
| `law-merge-inheritance` | `merge_law` + `Norm.check` | **PASS** (merged 2; child `SHARED` 100→50 overrides parent) |
| `audit-adjustment-validation` | `AuditAdjustment.has_negative_adjustment` / `.is_valid` | **PASS** both arrays |

**6 of 6.** The `federation.py:26` claim is **TRUE**. **Swept CLEAN.**

### B.4 — I-1 (INFO → test-vector owner / SDK track): the claim is true and unguarded

What survives is narrow and is stated as such: the only test-vector file in the standard whose
`spec` field names SAL has **no executing consumer**, so its agreement with `federation.py` is
maintained by nothing. The contrast that makes this measurable is **inside the same suite family**:
`test-vectors/society/society-vectors.json` carries a structurally identical docstring claim in
`society.py` **and** a real pytest fixture (`test_society.py:797-814` opens it and asserts
`len(vectors["vectors"]) >= 6`). `sal-governance.json` has only the docstring.

**This is not C322-N2** (declared-but-unverified `error_kind`/`error_path` *fields* inside suites
that do execute) and it is **not** C318's refuted flagship (a *denominator* over suite directories).
It is one file, named for this lineage's own spec, with no executor.

**Severity INFO, and the 6/6 pass is why** — the deflation is published rather than the headline.
A second, smaller cell for the same owner: the vector's `input` keys (`t3_deltas`, `v3_deltas`)
do not match the dataclass fields (`applied_t3_deltas`, `applied_v3_deltas`), and
`AuditAdjustment` additionally requires `audit_id` and `witnesses` that the vector does not supply —
so a naive field-mapping harness cannot round-trip this file without the manual mapping this pass
had to write. Recorded for whoever wires the consumer; **not filed as a defect** (the vector is a
cross-language contract, not a constructor spec).

**Entered as EXAMINED.** Per the C322 rev1 lesson, the point of a swept set is that it cannot be
re-discovered as novel: this file is now read, executed, and clean at `6b160f68`.

---

## §C — Carry ledger (**19 rows**; every row names its own ids, per v24)

**Restored — dropped at C208 (12) or C170 (1), all re-verified §A.5:**

| # | id | class | status |
|---|---|---|---|
| 1 | `C16-H1-remainder` | cross-track → **C334** (`errors.md` slot) | TRUE, routed nowhere |
| 2 | `C16-M1` | DESIGN-Q | TRUE — re-derived as C286-N1 |
| 3 | `C16-M3` | DESIGN-Q | TRUE |
| 4 | `C16-M4` | DESIGN-Q / cross-track | TRUE |
| 5 | `C16-M5` | DESIGN-Q / cross-track | TRUE |
| 6 | `C16-M6` | cross-track | TRUE |
| 7 | `C23-M3` | DESIGN-Q | TRUE |
| 8 | `C23-L2` | DESIGN-Q (overlaps `C16-M5`) | TRUE |
| 9 | `B1` | facet of `C23-H1` | FOLDED — rides a surviving row |
| 10 | `B8` | DESIGN-Q | TRUE (frozen) |
| 11 | `B9` | DESIGN-Q / cross-track | TRUE |
| 12 | `B11` | cross-track → `r6-framework.md` | TRUE |
| 13 | `L1-residual` | SPEC-side | TRUE (frozen) |

**Continuous survivors (6):**

| # | id | status |
|---|---|---|
| 14 | `C16-M8` / `B6` | STANDS — SAL §7.1/§7.1.1 triple family 100% absent from canonical `ontology/`; no `sal-ontology.ttl` there (one exists at `forum/nova/web4-sal-bundle/`, M2-declined — wording nit per the C286 guard, not a defect) |
| 15 | `C23-H1` | STANDS — birth-certificate N-way shape drift (**distinct from `C16-H1`**, see below) |
| 16 | `B7` | STANDS — SAL conformance-MUSTs vs `society-roles.md` Optional tier; adjudicate **with** `C16-M1` and #579 |
| 17 | `C50-B15` | STANDS — law-composition, 3 models (**distinct from `C58-B15`**, see below) |
| 18 | `C58-B10` | STANDS — dormant-defer vs `new_citizen` wake, two-sided |
| 19 | `C286-N1` | STANDS — routed to HUB track, undischarged (§A.3) |

**Two name collisions this ledger must keep visible** (both would otherwise read as renames):

- **`C16-H1` ≠ `C23-H1`.** `C16-H1` is the §9 error-code finding, carried as `C16-H1-remainder` and
  typed cross-track. `C23-H1` is filed at C23`:44` as `HIGH (new)` — birth-certificate three-way
  shape drift, which *"C16 missed … entirely."* `C23-H1` surviving does **not** rescue `C16-H1`.
- **`C58-B15` ≠ `C50-B15`.** The former is §9 expired-delegation and has **never** been typed as an
  id anywhere (0 files, both trees); the latter is law-composition and is healthy.

**Still with the operator, unchanged, not re-argued here:** `C50-B13` / `B14` / `B15`, `C16-M8`/`B6`,
`C58-B10`, `C33`. Route to the standing operator memo. **The CADENCE design-Q now has its 10th
consecutive datapoint.**

---

## §D — Forward guards for C366

Phrased as behaviours, not paths (v9 / [[feedback_guard_names_a_path_not_a_behaviour]]):

1. **Re-run the census, do not re-use this table.** The instrument is in §G. If any of the 19 rows
   reads 0 in the next pass, that is the finding — including if *this* document is the pass that
   dropped it.
2. **Apply v24 to your own §C before you apply it to anyone else's.** C320's own lesson is that the
   pass most likely to drop a row is the one congratulating itself for restoring one. This pass
   restored 13; treat that as the risk factor it is.
3. **`C16-H1-remainder` is the one to watch.** If C334 (`errors.md`) runs before the next SAL delta,
   check whether it consumed the row. If it did not, the routing failed twice and that is escalable.
4. **`KNOWN_ROLES` + fidelity test**: unchanged as of `6b160f68`. Re-check both; C286-N1 is still
   open and `cargo test (hub)` is green now, so a fidelity test is *possible* for the first time.
5. **Do not re-file:** I-1 (swept clean, 6/6 — check only whether the file or `federation.py`
   **changed**); C286's R1/R2/R3 refutations; C318's suite-coverage flagship; C322-N2.
6. **The lineage is 9 documents.** Do not locate it by globbing `C*-society-authority-law*` — that
   misses C16 (`sal-internal-consistency-2026-05-27.md`).

---

## §G — Instrument publication, and three of this pass's own cells corrected after writing

Every count below was **re-run after the findings were drafted, at a different scope than drafted
with** (v17). Three cells changed. All three are published rather than silently fixed.

**Instruments** (all at `6b160f68`):

```bash
# census (§A.4) — prefixed ids
grep -oF '<id>' docs/audits/<pass>.md | wc -l
# census — bare labels, collider baselined separately
grep -oE '\b<id>\b' docs/audits/<pass>.md | wc -l
# both audit trees, always (v17)
grep -rlF '<token>' docs/audits/ web4-standard/docs/audits/
# inbound derivation (v20) — use the tracked-file matcher; see correction 6
git grep -lF 'web4-society-authority-law.md' | wc -l                    # = 101 (tracked)
```

**Corrections:**

1. **`hub-law-schema.md` read-count: drafted 26, correct is 22.** 26 came from the bare token
   `hub-law-schema`; 22 from `grep -rlF 'hub-law-schema.md'`. The adjacent row (`hub-law.ttl` = 16)
   *was* the `-F` full-filename count (bare `hub-law` = 38) — so the drafted table **mixed two
   instruments across two adjacent rows.** This is the C314 loose-matcher class committed inside the
   table that motivates §B. Caught by the policy reviewer's independent re-measurement.
2. **Inbound sweep: drafted 101, "corrected" to 99 on review, and 101 was right.** See correction 6 —
   I accepted a reviewer's re-measurement over my own without reconciling the two instruments, which
   is the [[feedback_publish_the_instrument]] failure in its politest form: both numbers were
   *measured*, neither was *named*, so the disagreement looked like my error rather than a property
   of the two commands.
3. **My own quorum instrument returned the wrong answer and I nearly filed on it.** Drafting §B.3 I
   ran `[n for n in dir(F) if 'quorum' in n.lower() and callable(...)]`, got four names, saw no
   evaluator, and wrote *"federation.py has no quorum-check function"* — i.e. **2 of 6 vector groups
   unimplementable.** False. `check` is a **method on the `QuorumPolicy` dataclass**, not a
   module-level callable; a module-level scan cannot see it. Both quorum groups then passed. **A
   NO-IMPL result from a scan that cannot see the API shape is indistinguishable from a real gap** —
   and it would have been the pass's headline. It was caught only because the run that produced it
   also printed `dir(F.QuorumPolicy)`, which contained `check`.
4. **One instrument built and deliberately withheld** (see §B.2): the per-suite-directory consumer
   table. It greps the literal `test-vectors/<dir>` and therefore misses tests that join the suite
   name at runtime (`test_r6.py:47`). It would have produced a "N of 22 directories have no executing
   consumer" cell contradicting a **merged** C318 result, on an instrument that under-counts by
   construction. Withheld, and the reason recorded so the next pass does not rebuild it.

5. **My `B11` instrument was a casing failure, and the standing carry naming that defect is one I
   was applying elsewhere in this pass.** I published `grep -cF citizen r6-framework.md` → **0**.
   Case-insensitively it is **2** (`:52`, `:352`) — [[feedback_zero_as_wide_as_its_casing]], the
   C302 rev1 rider, committed inside a table whose whole purpose is re-verification. **B11's status
   is unchanged (TRUE)** and the re-derivation is *stronger* than what it replaced: the two hits are
   `Citizen` the **role name** in prose, not a field, and the right instrument is the one SAL §6
   actually specifies — of the three tokens it MUST-binds, `lawHash` and `society` both have carrier
   fields in R6's `rules` object and `citizen` has none. One word, two properties
   ([[feedback_one_word_two_properties]]): the role name is present, the carrier field is absent, and
   a case-blind zero conflates them in the direction that happens to flatter the finding.
6. **Three instruments, one question, three answers — and it is not binary-ness, `--exclude-dir`, or
   my own new file.** `git grep -lF` = **101** (tracked); `grep -rlF . --exclude-dir=.git` = **100**
   (99 before this document existed); `grep -rlFa` (binary-as-text) = **100**; `grep -RlF` (follow
   symlinks) = **100**. The two files in the gap are `whitepaper/build/WEB4_Whitepaper_Complete.md`
   and `whitepaper/build/web/index.html`. Both are tracked, both are on disk, both contain the
   string — and **whether `grep -r` finds them depends on where the recursion starts**:

   | probe | hits under `whitepaper/build` |
   |---|---|
   | `grep -rlF <pat> . --exclude-dir=.git` | **0** |
   | `grep -rlF <pat> .` (no exclude) | **0** |
   | `grep -rlF <pat> whitepaper/` | **2** |
   | `grep -rlF <pat> ./whitepaper/build` | **2** |

   Reproducible. **I am not claiming a mechanism I have not established** — binary classification,
   `--exclude-dir`, and symlink-following are each ruled out by the probes above, and I did not
   isolate the actual cause. What matters for the corpus is the consequence: this track's standing
   remedy is *name your matcher*, and here **the matcher is named and identical** — only the
   recursion root differs. A named matcher is not yet a reproducible one. **Adopting `git grep -lF`
   (tracked files, root-independent) as the citable instrument for inbound sweeps**, and publishing
   all four numbers rather than picking the one that agrees with the draft.

**Post-write re-runs that AGREED** (v10 corollary — an agreeing verifier confirms nothing until you
confirm it ran; these were re-run at a different scope and the scopes disagreed on nothing):
`sal-governance.json` = 0 files in both trees (re-run repo-wide: 0 outside `docs/`);
`KNOWN_ROLES` = 7 entries (re-run against `git show HEAD:hub/hub-lib/src/law.rs`);
window = 59 commits (re-run as `git rev-list --count`).

---

## §E — Method notes

1. **The rotation's own file-naming convention hid the lineage's origin pass for 9 deltas.** C16 is
   found by reading C23's header, not by globbing. Every membership-loss mechanism in §A.4 is a
   variant of the same thing: **an identifier that can no longer be reached from the outside.** The
   glob blindness is that defect one level up, committed by the process rather than by a document.
2. **A true disposition can destroy more information than a missing one.** C208's catch-all row is
   accurate — the referents *were* frozen and the carries *did* stand. A pass auditing for
   correctness finds nothing wrong with it. v19 asks for a recorded disposition and gets one; v23
   asks for a row count and it never fell. **The check that catches it is membership, and no prior
   carry required it.**
3. **The policy review earned its keep three times and reversed my spine twice.** It rejected my
   starting point (C98 → C23), I found its correction was itself under-derived (C23 → C16), and it
   then corrected three of my census cells — including that `C16-M1` does **not** survive to C286
   but is swallowed-then-re-derived, which is now the finding's strongest evidence rather than a
   footnote. It also pre-empted the refutation that would have killed the flagship: printing
   "`C16-H1` → 0 at C208" beside "`C23-H1` alive at C208" without stating they are different
   findings reads as rename-not-drop.
4. **Refuting the flagship first worked, and it worked by shrinking the finding.** §B started as a
   candidate MEDIUM (an unexecuted vector file). Reading C318's refutation first, then *executing*
   the vectors, turned it into a 6/6 pass and an INFO. The corpus's own precedent killed the
   interesting version of the finding before it was written, which is the cheapest possible place
   for that to happen.
5. **Commit count screens for anchor drift; it does not predict it** (§A.2). 9 commits → 0 drift;
   1 commit → the only drift. Use it to decide *whether* to re-resolve, never *which*.

---

## §F — Accountability self-audit

```
surface: none — this pass produces one audit document under docs/audits/
act: none — no consequential act; zero mutation of web4-standard/**, hub/**, or any SDK file
S: low/reversible [construct: docs/audits/C326-society-authority-law-8th-delta-2026-08-06.md, additive]
R: n/a   W: n/a
O: n/a   A: n/a   V: n/a
verdict: PASS (no caller-drivable surface; a record, not an enactment)
```

Findings route to their owners and none is self-applied: **N1** is this lineage's own ledger and is
corrected *in this document's §C* (the corrective act is a ledger, not a spec edit — v10 rule 6);
**C286-N1** stays with the HUB track; **`C16-H1-remainder`** routes to the `errors.md` slot (C334)
with no severity assigned here; **I-1** routes to the test-vector owner / SDK track. `errors.md`,
`errors.py`, `federation.py`, `law.rs` and SAL itself are untouched.
