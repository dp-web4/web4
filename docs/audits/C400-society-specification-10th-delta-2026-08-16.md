# C400 — `SOCIETY_SPECIFICATION.md` 10th delta

**Date**: 2026-08-16
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (498 lines)
**Predecessor**: C360 (9th delta, PR #690, `75f7f5a2`, 2026-08-11)
**Slot arithmetic**: C360 + 40 = **C400**. Next SOCIETY_SPEC delta ≈ **C440**.
**Lineage enumeration rule (inclusive, stated per standing rule)**: every `docs/audits/*society-specification*`
member, C-numbered or not. Measured: `git ls-files 'docs/audits/*society-specification*'` → **10** members
(C22, C50, C92, C131, C164, C202, C240, C280, C320, C360). **This lineage has no non-C-numbered
`…-internal-consistency-…` member** (`society-roles-internal-consistency-2026-05-21.md` belongs to the
`society-roles` lineage, `inter-society-protocol-internal-consistency-2026-05-21.md` to ISP). C400 is the
**10th** pass.

**Verdict**: **1 LOW-MED routed (widening, not net-new) · 1 MED process/ledger recovery (per-arm) · 3 INFO ·
2 candidates killed by policy review · 6 negatives published · ZERO mutation · 1 new file (this one).**

**Nothing in this pass was applied in-tree.** Every mutation reported below was run in a throw-away
`mktemp -d` copy and discarded; the working tree is byte-identical to `HEAD` except for this file.

---

## §0 — Pre-registered window and matchers

Every gate cell below carries the command that produced it (C360's own-error rule). All commands were run
from the **repository root**; see §E-1 for why that sentence is load-bearing in this pass.

| Item | Value | Command |
|---|---|---|
| Baseline | C360 `75f7f5a2` | per `per_file_guards.md` |
| Window, repo-wide | **28** commits | `git log --oneline 75f7f5a2..HEAD \| wc -l` |
| Window, `web4-standard/` | **0** | `git log --oneline 75f7f5a2..HEAD -- web4-standard/ \| wc -l` |
| Window, target | **0** | `git log --oneline 75f7f5a2..HEAD -- web4-standard/core-spec/SOCIETY_SPECIFICATION.md` |
| Target byte-frozen at | `87377c38`, **2026-07-14** (33 d) | `git log -1 --format=%H%n%ci -- <target>` |
| SDK tree | `sdk/web4/` unmoved since 2026-05-24 (`62524cf8`) | inherited from C360, re-checked by window |

**8th consecutive empty window on this rotation.** With 0 commits in `web4-standard/`, §A is a
*movement* check, not a re-resolution (see §A).

---

## §A — Cross-reference sweep: NEGATIVE, by the guard's own instruction

C360 resolved **all 37** cross-reference sites at HEAD, 37/37 EXACT, and published that as a negative with
the instruction: *"Do NOT re-run in full at C400; check only whether the 7 MOVED siblings moved again."*

`for f in <sibling>; do git log --oneline 75f7f5a2..HEAD -- "$f" | wc -l; done`

| sibling | commits in window |
|---|---|
| `web4-society-authority-law.md` | 0 |
| `society-roles.md` | 0 |
| `atp-adp-cycle.md` | 0 |
| `mcp-protocol.md` | 0 |
| `reputation-computation.md` | 0 |
| `hub-law-schema.md` | 0 |
| `t3-v3-tensors.md` | 0 |
| `inter-society-protocol.md` | 0 |
| `SOCIETY_METABOLIC_STATES.md` | 0 |
| `did-web4-method.md` | 0 |

**10 of 10 unmoved. §A = NEGATIVE, inherited-by-measurement rather than re-derived.** The 37/37 result
holds by blob identity on both ends of every edge.

---

## §B — Machine checks (run FIRST, v43)

### §B-1 — Fenced-block execution — and a **denominator correction to C360**

```
python3: re.findall(r'```(\w*)\n(.*?)```', body, re.S); json.loads each json-tagged block
grep -n '```' <target>            # 34 fence lines → 17 blocks
grep -n '^```json' <target>       # 4   ← misses the 8 list-indented ones
```

| measure | C360 published | C400 measured |
|---|---|---|
| fenced blocks | 17 | **17** ✓ |
| tagged `json` | 13 | **12** ✗ |
| parse OK | 9 / 13 | **8 / 12** |
| parse FAIL | 4 | **4** ✓ |

The **four failures are identical** and are the `{...}` elision convention (§4.2.1 block 2 `voting_record`;
§4.2.2 blocks 1–3 `original_data`, `new_data`, `voting_record`) — kept, not discarded (C356's rule), and
benign. **C360's `json`-tagged denominator is one too high**, so both its numerator and denominator are off
by one. Enumerated exhaustively: `json`-tagged opening fences are at `:138, :218, :233, :248, :268, :284,
:302, :320, :334, :354, :364, :376` = **12**. The verdict is unchanged; the cell is corrected.
*(v40: a metric's denominator is a domain, and it must be re-derived, not inherited — including from your
own lineage.)*

### §B-2 — The backwards sweep (v64): which artifacts DECLARE this spec as their target?

`for f in $(git ls-files 'web4-standard/test-vectors/**/*.json'); do python3 -c "print(json.load(...).get('spec'))"; done`

**35 test-vector files in `web4-standard/`; exactly ONE declares this target**
(`test-vectors/society/society-vectors.json:4`). 15 of the 35 carry **no `spec` key at all**. Published as a
negative: the mirror set on the vector side is 1, and it is the file C320 §B-5 already adjudicated.

`git grep -n "SOCIETY_SPECIFICATION" -- web4-standard/test-vectors web4-standard/schemas web4-standard/implementation`
→ 6 hits in `sdk/web4/federation.py` + `sdk/web4/society.py`, 1 in the vector file, **0 in `schemas/`**.

### §B-3 — d1 (C360 deferral 1): `hub/hub-lib/src/ledger.rs` against §4.1's three ledger classes — **COMPLETED, NEGATIVE**

```
git grep -il "confined"       -- hub/   → 0
git grep -il "participatory"  -- hub/   → 0
sed -n '49,80p' hub/hub-lib/src/ledger.rs
```

`hub/hub-lib/src/ledger.rs`'s `LedgerEntry` is
`{index, timestamp, prev_hash, actor_lct_id, event, signature, entry_hash, proposal_ref}` — no ledger-class
field, and no `witnesses` field. §4.1's Confined / Witnessed / Participatory classification has **zero
surface in `hub/`**.

**Absence matcher for reason 3 below, published beside the claim (v44).** "No document claims `hub/`
implements §4.1's three classes" is itself an absence claim, so here is the instrument:
`git grep -rn "§4.1\|confined\|participatory" -- hub/ ':!hub/target'` → **1 hit**, and it is a false
positive: `hub/docs/PAIRED-CHANNELS.md:451` cites a *different* spec's §4.1 (X25519/ChaCha20-Poly1305
primitives). **True count of coverage claims: 0.**

**Not charged, for three stated reasons** — the row is published as a completed negative so the 11th pass
does not re-walk it:

1. **C22:145 already charged** the participatory-validators schema asymmetry, and target `:257` (*"The
   absence of an explicit `validators` field in this JSON is intentional"*) is its **ratified remediation**.
2. **C22:184 already recorded** *"only CONFINED default is exercised; WITNESSED + PARTICIPATORY untested"* —
   partially remediated since (`test_federation.py:107` WITNESSED, `:519` PARTICIPATORY), so re-asking is
   the prior rung (v43: stay on the next rung).
3. **A coverage gap is not chargeable — the document that CLAIMS the coverage is** (v64/`C372:411-412`).
   I looked for a claim that `hub/` implements §4.1 and **found none**. `federation.py:197`
   (`# ── Ledger Types (SOCIETY_SPECIFICATION §4.1) ──`) claims only the enum, and the enum is faithful.

**Standing note for the SDK track, not charged here:** `LedgerType` is *written* (`federation.py:524`,
`society.py:336`) and **never branched on** — `git grep -n "ledger_type" -- ':!docs/audits'` returns 23
hits, all construction, defaulting, or test assertion; no site reads it to vary access or validation. This
is C22:145's own observation (*"just an enum, not a struct, so no canonical rule exists in code either"*),
re-verified at HEAD, **not re-charged**.

---

## §C — Findings

### C400-N1 (LOW-MED) — §3.2.3's named economic capability is **not reachable via the `incorporate_child` path alone**. **ROUTED to C50-B18 as a WIDENING, not filed net-new.**

**Novelty denominator, published with its matcher (v44) — case-INSENSITIVE and widened past my first
draft**, because case-sensitivity is exactly what bit C396:

```
git grep -n  "3\.2\.3\|Economic Fractal"                  -- docs/audits   → 0
git grep -ci "economic fractal\|atp_flow\|3\.2\.3"        -- docs/audits   → 0
```

**§3.2.3 has never been named by any pass in ten, under either matcher.** C50-B18's own title names
**§3.1/§3.2.2** only.

**Target text (`:186-189`, §3.2.3 Economic Fractals):**
> - Parent societies can allocate ATP to child societies
> - Child societies manage their own sub-allocations
> - Energy flows follow citizenship paths

**Executed at HEAD** (two founders per society, because C92-N1's `<2` guard blocks the solo path):

```
incorporate_child(parent, child):                 True
society_ancestry(child):                          ['lct:society:parent', 'lct:society:child']
parent.society.is_citizen('lct:society:child'):   False
§3.2.3 allocate_treasury(parent, child, 100.0):   False
parent.treasury.balance:                          1000.0   (unchanged)

workaround — admit_citizen(parent, child):        True
  parent.society.is_citizen(child):               True
  allocate_treasury(parent, child, 100.0):        True    balance 900.0
```

**Mechanism.** `allocate_treasury` gates on `state.society.is_citizen(entity_lct)` (`society.py:644`).
`incorporate_child` (`society.py:773-815`) sets `child.society.parent` / `parent.society.children` and
appends two `FORMATION` entries (`incorporate_child`, `incorporated_by`) — and creates **no**
`CitizenshipRecord`. So the fractal tree and the citizenship machinery are disjoint, which **is** C50-B18.

**What is new, and why it is a rung rather than a re-file.** B18 charges a *missing record*
(*"incorporation creates parent/child links but never a CitizenshipRecord; child societies are never
citizens"*). What B18's text does **not** state is the **consequence**: the missing record makes a
**named normative capability of the target** return `False` on the incorporation path.

**The gate is correct; do not charge the gate.** §3.2.3's third bullet (`:189`) is *"Energy flows follow
citizenship paths"* — so `allocate_treasury`'s `is_citizen` check is **faithful to the spec**.

**THE SPEC IS COHERENT AND EXONERATED; THE SDK IS THE SOLE DEVIATOR.** My first draft wrote *"bullets 1
and 3 are jointly satisfiable only if incorporation implies citizenship"* — that puts the tension in the
target, and it is **wrong**. `:162` reads *"Societies **can** be citizens of other societies"* and §3.2.2
is conditional throughout (*"**If** Society A is citizen of Society B"*). **Nothing in §3 says
incorporation implies citizenship.** The spec's two acts — incorporate (§3.2.1) *and* admit (§3.1) — are
jointly satisfiable with no tension at all, and that two-act sequence is **exactly what the workaround
above executes**. Publishing the tension as spec-internal would be the same inverted-target error that
killed §D-1.

**The residue that IS a legitimate widening of B18 is the §3.1 DIAGRAM, not bullets 1/3.** The target's own
illustration at `:164-171` labels every child *"(citizen of Regional)"*, *"(citizen of City)"*,
*"(citizen of Universe)"* — i.e. the spec's picture treats hierarchy membership **as** citizenship, while
§3.2.1 makes incorporation the constitutive act and §3.1's prose keeps citizenship optional (*"can"*). A
reader who builds from the diagram builds the SDK's model; a reader who builds from §3.1's prose builds the
correct two-act one. **That is the rung on B18.**

**Severity: LOW-MED, with three stated discounts.**
1. Bullet 1 reads *"can allocate"*, not MUST — a capability, not an obligation.
2. **A working, spec-plausible workaround exists and was executed** (`admit_citizen` then allocate), so this
   is *not reachable via `incorporate_child` alone*, **not** "unreachable". Publishing "unreachable" beside
   an executed reachability proof would be a self-contradiction of the exact class C396 charged elsewhere.
3. The spec licenses the two-act reading (above), so no spec defect is implied.

**Executed fix shape handed to the SDK track (a HAND-OFF, not a proposal this pass owns; not applied
in-tree).** The workaround transcript above *is* B18's fix: one `admit_citizen`-equivalent inside
`incorporate_child`, creating the `CitizenshipRecord` that B18 says is missing, makes the §3.2.3 path work
end-to-end. The archived reference implementation already does the whole flow
(`archive/reference-implementations/society_specification.py:467-473`, in a method whose docstring reads
*"Economic fractal: parent allocates ATP to child (§3.2.3)"*).

**Guard run against the fix (v53), with the flip side published.** Applied in a tmpdir copy at correct
depth (see the hazard note in N2), one line inside `incorporate_child`:

```python
    child_state.society.parent = parent_state.society
    parent_state.society.children.append(child_state.society)
+   admit_citizen(parent_state, child_state.society_id, timestamp, [])
```
```
pytest tests/test_society.py                         → 86 passed
incorporate_child(parent, child)                     → True
parent.society.is_citizen('lct:society:child')       → True
§3.2.3 allocate_treasury(parent, child, 100.0)       → True     balance 900.0
```

**But the file was 86 passed BEFORE the change too** — so **no test in the suite observes the difference in
either direction**. The fix shape is *unconstrained by the suite*, which is itself part of B18's story: the
disjunction B18 charges is invisible to every test that exists.

*First attempt, published because it constrains the fix:* patching `parent_state.society.add_citizen(...)`
fails — `Society` has `is_citizen` / `issue_citizenship` / `suspend_citizen` / `reinstate_citizen` /
`terminate_citizen` but **no** `add_citizen` (`federation.py:555-631`), and the attempt broke 6 tests with
`AttributeError`. The fix must route through the module-level **citizenship-lifecycle** function
`admit_citizen`, not a raw setter — which is the correct shape anyway, since that is the path that emits
the `citizenship/grant` ledger entry §4.2.1 item 1 requires.

**Disposition: written into C50-B18's row as a widening (v37 — a subsumption/widening is a disposition).
No spec edit. No SDK edit. Route only.**

### C400-N2 (MED, process/ledger) — C50-B16(c)'s row was occupied by **B16(b)'s** predicate at C360; B16(c)'s own three arms, executed cold, split **2 false / 1 true**

**The label collision.** C50 defines three sub-rows at `:158`:

- **(a)** SDK never records §4.2.1's MUST minimum fields
- **(b)** §4.2.2's amendment wire-shape (`amendment_type`, `reason`, `law_authorization`, `status:"superseded"`) has no SDK counterpart; `amend()` is not law-driven
- **(c)** `create_society` bypasses three MUST-record categories — founder citizenship grants, initial-law ratification, and seed deposit never hit the ledger (`society.py:332-414`)

C320 keeps them apart correctly (`:121` = (a), `:122` = (b)) and restores **(a), (c), B18, B19** to the SDK
bundle at `:136`/`:235`/`:261`, routing **(b)** to the operator with C320-N3.

**C360:448 then reads:**

> \| **C50-B16(c)** amendment wire-shape \| SDK track (restored C320) \| `amendment_type` 0, `law_authorization` 0; `amend()` takes no law ref \| **OPEN** \|

That is **(b)'s title and (b)'s evidence under (c)'s id.** C360's §C header asserts *"each was re-resolved
by **content** at HEAD"* — and for this row the content re-resolved was a different row's. **C50-B16(c)'s
own predicate was not re-verified at C360**, while the table reported 12/12 OPEN.

**Re-derived COLD this pass, by execution — the proof the row was lost.** I reached B16(c)'s predicate not
by reading the carry table (which does not contain it) but by running the artifact.

**B16(c) charges THREE arms, and it must be dispositioned PER ARM.** My first draft filed a whole-row
deflation off **two** measured arms — which is v60 recurring inside my own correction (*a fact printed in a
baseline is not carried; charge or explicitly carry the other N−1*). Policy review caught it and measured
the third. All three transcripts:

```
create_society(founders=['lct:alice','lct:bob'], initial_treasury=1000.0) →
  formation | genesis     | {'founders': ['lct:alice','lct:bob'], 'name': 'S'} | witnesses [alice, bob]
  formation | bootstrap   | {'citizen_count': 2, 'treasury': 1000.0}           | witnesses [alice, bob]
  formation | operational | {}                                                  | witnesses [alice, bob]

create_society(..., initial_law=LawDataset(law_id='citizenship_law_v1', version='1', society_id='s')) →
  entries 3    (identical three FORMATION entries; treasury 0.0)
  law_change entries: []
  society.py:332-333 →  if initial_law is not None: fed_society.set_law(initial_law)
  docstring :308     →  "initial_law: Optional law dataset to publish at genesis."
```

| arm | original wording | verdict | surviving claim |
|---|---|---|---|
| **1 — founder citizenship grants** | *"never hit the ledger"* | **FALSE as stated** — founders ARE on the ledger, in `genesis.data.founders`, which is **§4.2.1 item 5's own declared formation payload** | not recorded as a `citizenship/grant` **event class** |
| **2 — seed deposit** | *"never hits the ledger"* | **FALSE as stated** — the seed treasury IS on the ledger, in `bootstrap.data.treasury == 1000.0` | not recorded as an `economic/deposit` **event class** |
| **3 — initial-law ratification** | *"never hit the ledger"* | **TRUE, unmodified, and strictly stronger than the other two** | the law is `set_law()`-ed onto the society object and **published to no ledger at all** — not as a `law_change/ratify` event and **not even as a payload field**, while the docstring at `:308` says *"publish at genesis"* and §1.3 Bootstrap says *"First law ratified"* |

§1.3 assigns arms 1–2's duties to the Bootstrap Phase in prose (*"Initial citizens recorded"*, *"Treasury
allocated (if any)"*) and the SDK discharges them **there**; §2.3's own *"Rejection produces no event"*
shows the spec already tolerates a status change with no event, so the strong reading of arms 1–2 is not
free. **No such defence exists for arm 3**: §1.3's third bootstrap duty is *"First law ratified"*, §4.2.1
item 2 enumerates `action: propose|ratify|amend|repeal`, and nothing is recorded anywhere.

**Disposition — per arm, not per row:**
- **arm 1** — wording withdrawn; re-stated as *"recorded as a `formation` payload field, not as the
  `citizenship` event class"* — **LOW-MED**, SDK track.
- **arm 2** — same, on `economic` — **LOW-MED**, SDK track.
- **arm 3** — **UNMODIFIED, re-verified TRUE at MED.** Do not deflate. This is the arm that holds the row up,
  and it had not been executed by any pass in ten.

**C50-B16(c) therefore stays OPEN at MED on the strength of arm 3**, with arms 1–2 re-stated downward. The
label collision is filed as the mechanism that let all three go un-executed.

**Attached LOW note (the residue of a killed headline — see §D-2).** `society-vectors.json`'s
`minimal_society` vector pins `expected.ledger_entry_count = 3`, and it is the **only** vector of six with a
ledger key and the **only** assert (`test_society.py:829`). Executed (v53, *run the guard against the FIX*,
in two throw-away `mktemp -d` copies — **nothing was applied in-tree**):

| mutation applied to the tmpdir copy | `pytest tests/test_society.py -k TestVectors` |
|---|---|
| B16(c) **citizenship** arm — emit a `citizenship/grant` per founder | **1 failed**, 6 passed — `test_minimal_society`: `AssertionError: assert 5 == 3` |
| B16(c) **seed-deposit** arm — emit an `economic/deposit` when `initial_treasury` set | **7 passed** |
| baseline, unmutated | 7 passed |

So **B16(c) cannot be closed on its citizenship arm without also amending the vector**, and its deposit arm
is unpinned. Denominator stated honestly: **1 of 6 vectors**, not 2. *(The `7 passed` control is a
measurement, not an endorsement of applying the arm.)*

**Method hazard, published because this pass leans on tmpdir runs and already owns one path-resolution
own-error (§E-1).** `TestVectors` resolves its fixture by a **relative** path,
`tests/../../../test-vectors/society/society-vectors.json` (`test_society.py:799-810`). Copy the SDK
directory alone into `/tmp` and that path escapes the copy: the fixture fails to load and pytest reports
**7 ERRORS** — which a careless reader can mistake for the **`7 passed`** control above. The copy used here
was `cp -r <repo>/web4-standard "$TMP/web4-standard"` and the runs were made from
`$TMP/web4-standard/implementation/sdk`, so the relative path resolves inside the copy. **State the copy
depth whenever this instrument is used.** (The `assert 5 == 3` in the row above is itself proof the vector
loaded — an error would not have produced a comparison.)

### C400-I1 (INFO, observation — deliberately NOT charged) — `law_reference` has no consumer anywhere

`git grep -c "law_reference" -- ':!docs/audits'` → **`web4-standard/core-spec/SOCIETY_SPECIFICATION.md:3`
and nothing else in the repository.** The three sites are `:147` (§2.4 citizenship record), `:274` (§4.2.1
block 1), `:371` (§4.2.2 amendment block). Not the SDK, not `hub/`, not `schemas/`, not the archived
reference implementations — which **do** implement its siblings: `voting_record` (`society_lifecycle.py:3` +
`society_specification.py:1` = **4** in `archive/reference-implementations/`), `effective_date`
(`society_lifecycle.py:6`, plus 1 in `archive/implementation-sprawl/` = **7** in `archive/` by the wider
matcher). *Matchers travel with their denominators (v64): "4" is `archive/reference-implementations/`; "7"
is all of `archive/`.*

Own-lineage note: C50-B23 charged the `law_reference` vs `law_authorization` synonym pair, and **C92:63
verified the remediation** — which **created the third `law_reference` site** by renaming §4.2.2's key. So
this lineage's own remediation propagated a key that no instrument reads.

**Not charged.** "Implemented nowhere" is a **coverage gap**, and per v64 the chargeable thing would be a
document *claiming* the coverage. I looked; nothing claims it. Filed as an observation so the 11th pass has
the measurement without inheriting a charge.

### C400-I2 (INFO) — d5 correction to C360's deferral text

C360:547 defers *"`archive/reference-implementations/society_specification.py` **and the two `docs/reference/`
referrers**"*. Measured:

- `git grep -n "society_specification" -- ':!docs/audits'` → **0 referrers to the archive file**, repo-wide.
- The two `docs/reference/` files are referrers to the **spec**, not to the archive file:
  `CANONICAL_TERMS_v1.md:122` and `GLOSSARY.md:87`. C360's phrasing conflates the two populations.
- The archive file's own docstring claims it implements *"SOCIETY_SPECIFICATION.md (**392 lines**)"*; the
  target is **498**. Last touched `65cd5488` (2026-04-11, "Archive reference implementation sprawl").

Archived tree, zero referrers, stale by construction — **not charged**; recorded so the 11th pass does not
re-open it as a lead.

### C400-I3 (INFO) — `recipient_lct` in `web4-standard/`: **1**

`git grep -c "recipient_lct" -- web4-standard` → `core-spec/SOCIETY_SPECIFICATION.md:1`. The §4.2.1:309
declaration is the only occurrence in the entire standard tree. `entity_lct` occurs in **16**
`web4-standard/` files. Published as a **negative measurement**, not a finding — see §D-1 for why the
finding it looked like is dead.

---

## §D — Candidates killed (published so the 11th pass does not re-walk them)

### §D-1 — KILLED by policy review: *"`recipient_lct` vs `entity_lct` is a spec-internal key fork"*

**Drafted claim:** §4.2.1 block 3 names the allocation recipient `recipient_lct`, block 1 and §2.4 name the
same slot `entity_lct`, the SDK's implementation of block 3 (`allocate_treasury`, `society.py:652-661`)
emits `entity_lct`, and `recipient_lct` occurs once in all of `web4-standard/` — so C50-B23's synonym-pair
block was never enumerated (standing rule: *when a prior pass charged ONE member of a structured block,
enumerate the whole block*).

**FALSIFIED — they are two slots, and two independent implementations of this spec prove it.**

- `archive/reference-implementations/society_specification.py:467-473` emits `recipient_lct` inside an
  `ECONOMIC/allocate` record, in a method docstringed *"Economic fractal: parent allocates ATP to child
  (§3.2.3)"* — a 5-for-5 field match with §4.2.1 block 3 — while the **same file** uses `entity_lct` for
  citizenship at `:236`/`:284`.
- `archive/reference-implementations/society_lifecycle.py` makes them **two dataclasses**:
  `TreasuryAllocation.recipient_lct` (`:216-218`) and `CitizenRecord.entity_lct` (`:290-292`).
- Counts: `git grep -c "recipient_lct" -- archive/reference-implementations` → `society_lifecycle.py:9`,
  `society_specification.py:1`.

**The direction is inverted.** The spec is not forked; two implementers read §4.2.1 exactly as written and
built two distinct types. The only artifact that conflates the names is the SDK's `allocate_treasury` — and
that is **already C50-B16(a)**, which cites `society.py:656-661`, *the emitting lines themselves*. Withdrawn.

### §D-2 — KILLED by policy review: *"the conformance vectors pin non-conformance in 2 of 6 vectors"*

**Drafted claim:** `society-vectors.json` declares this spec and asserts field-by-field, and two of its six
`expected` sets encode states §4.2.1's MUST clauses forbid, so a conformant second implementation fails
cross-language parity.

**FALSIFIED on the denominator and on the class.** `ledger_entry_count` appears in **exactly one** vector
and **one** assert. `society_with_treasury.expected` asserts only `treasury_balance` and `total_deposited`
— both **correct**; it merely *omits* a ledger claim. **Absence of a key is not an assertion**, so vector 2
is a **coverage gap** — precisely the predicate `C320 §B-5` and `C360:412` refuted with *"do not re-walk"*,
citing C22-I3 and C318's *"a coverage census is not a finding."* My own control (`7 passed`) was the
counter-evidence and I walked past it.

**Also falsified:** the "is 3 the spec-wrong number" question is B16(c), which I had declined to
re-litigate — and B16(c) turns out to be false as stated (§C/N2). What survives is the LOW note attached to
B16(c), not a headline. **Both drafted headlines died; the residue is in N2, and the falsification is what
produced N1.**

*Policy review has now falsified a central premise or headline on C354, C356, C364, C366, C372, C378, C382,
C386, C388, C390, C392, C394, C396 and **C400** — 14 consecutive.*

---

## §E — Own-error log (all caught pre-ship)

### §E-1 — I ran three gate greps from a **stale cwd** and got `0 hits repo-wide` for tokens that exist

`git grep -n "recipient_lct"`, `"law_reference"` and `"change_description"` each returned **empty**. All
three were run after an earlier `cd web4-standard/implementation/sdk` had persisted in the shell — so the
pathspec `-- . ':!docs/audits'` was rooted at the **SDK subdirectory**, not the repo root. Re-run from root
they return 89+ / 3 / 4 hits.

Had I published them, **§D-1 would have been inverted**: "`recipient_lct` occurs nowhere, including in the
spec that declares it" is a much *louder* finding than the true one, and it is false. Caught by a sanity
re-read (the token I had just read at `:309` cannot be absent from the file I read it in).

This is C360's own-error class recurring one pass later, in a new mechanism: C360 published a `0` that was a
**relabelled** number; C400 nearly published three `0`s that were **correctly computed over the wrong
domain**. The rule generalises: *a gate cell must carry the command **and the root** that produced it.*
Every table in this document states the root.

### §E-2 — I inherited a carry's disposition instead of its predicate

I planned to route around C50-B16(c) rather than re-litigate it (v51: route, do not re-adjudicate). Policy
review called that a cop-out, and it was: v51 protects **another lineage's** rows. B16(c) is **this
lineage's own**, and its three arms had not been executed by anyone in ten passes. Executing them produced
§C/N2 — the label collision, the two false arms, and the third arm that holds the row up. **v51 does not
license inheriting your own lineage's unexecuted claims.**

### §E-3 — I drafted a whole-row deflation from 2 of 3 arms

Having falsified B16(c) arms 1 and 2, I wrote *"C50-B16(c) is DEFLATED and RE-STATED … LOW-MED"* without
measuring **arm 3**. Policy review measured it: the initial-law arm is **true, unqualified, and stronger
than the two I had measured** — so the row survives at MED, and my correction would have *weakened a row on
evidence that did not cover it*. Filed as method carry **v65b** (§H). The failure is exactly the one this
lineage already names in v60 (*charge or explicitly carry the other N−1*), committed inside a **correction**,
which is the place it is hardest to see.

---

## §F — Deferral ledger for C440

| # | row | state after C400 |
|---|---|---|
| d1 | `hub/hub-lib/src/ledger.rs` vs §4.1's three classes | **COMPLETED — NEGATIVE** (§B-3). Do not re-open. |
| d2 | `web4-policy`'s §7.3 faithfulness | **NOT completed.** `web4-policy` had **0** commits in this window (`git log --oneline 75f7f5a2..HEAD -- web4-policy` → 0), so the C320 measurement holds by blob identity — but the *predicate* is now three passes old. Re-test at C440. |
| d3 | SDK emitted `data` keys vs §4.2.1 minimums, row by row | **COMPLETED in the direction that mattered, and the result is §D-1 + §D-2.** The token-absence half is C50-B16(a) and was not re-charged. |
| d4 | `test-vectors/metabolic/society-metabolic-states.json` vs §1.4 | **NOT completed.** Opened; it declares `"spec": SOCIETY_METABOLIC_STATES.md` (not this target) and its 4 vector families are energy/wake/transition/reliability — none of which §1.4 constrains beyond naming the 8 states. Reason for deferring rather than closing: the diff belongs to the **C364 lineage**, which owns that file. |
| d5 | archive reference impl + the "two `docs/reference/` referrers" | **COMPLETED — see C400-I2**, including the correction to C360's phrasing. |
| **d6 (new)** | **Audit the other sub-row labels for the same collision §C/N2 found.** B16(a)–(c), B17–B20 are a structured block; only (c) was checked this pass. | **OPEN for C440.** |

---

## §G — Carry re-verification

**Derived from C360's §C table ∪ C360's §C findings** (v62: a pass's own findings are born in its §C and
structurally cannot be in the table its successor reads).

| Carry | Owner | State at HEAD | Status |
|---|---|---|---|
| C50-B13 Law Oracle name collision | operator DESIGN-Q | target `:24` ✓, `society-roles.md` §2.2 ✓ | OPEN |
| C50-B14 citizenship revocability vs SAL §5.1 | operator DESIGN-Q | SAL §5.1 ✓ | OPEN |
| C50-B15 law inheritance model | operator DESIGN-Q | target `:178` ✓ | OPEN |
| C92-N1 solo-founder guard (half-closed) | SDK track | `society.py:317-318` `if len(founders) < 2: raise` — **hit live this pass**, blocked the first §3.2.3 execution attempt | **OPEN, re-verified by execution** |
| C164-N1 enum-comment stale vocab | SDK track | `society.py:92/:94` still pre-C51 | OPEN |
| C22-M3 `type` ↔ `event_type` | SDK track | `society.py:111` | OPEN |
| C92-N3 / C50-B20 id-scheme examples | C33 bundle | frozen body | OPEN |
| C50-B16(a) §4.2.1 MUST minimum fields | SDK track | 0 of 5 tokens SDK-wide — **not re-charged**; see §D-1 for why its `recipient_lct` arm is subtler than the token count suggests | OPEN |
| **C50-B16(b)** amendment wire-shape | operator, w/ C320-N3 | `amendment_type` 0, `law_authorization` 0 | **OPEN — and this is the row C360:448 filed under (c)'s id (§C/N2)** |
| **C50-B16(c)** `create_society` bypass | SDK track | **PER-ARM (§C/N2)**: arm 1 (founder citizenship) + arm 2 (seed deposit) wording FALSE, re-stated as event-class omissions at LOW-MED; **arm 3 (initial-law ratification) TRUE and UNMODIFIED — no `law_change` entry and no payload field** | **OPEN at MED, on arm 3** |
| C50-B18 fractal tree ⟂ citizenship | SDK track | `CitizenshipRecord` 0 in `society.py:773-815` | **OPEN — WIDENED by C400-N1 (the §3.1 diagram), LOW-MED** |
| C50-B19 `merge_law` no contradiction check | SDK track | `federation.py:389-403` | OPEN |
| C320-N3 §4.2.2 zero conformant implementers | operator, w/ B16(b) | target `:351` ✓ | OPEN |
| C360-N1 `QuorumPolicy.check` 0 production callers | SDK track + operator | window empty; holds by blob identity | OPEN |
| C360-N2 / N2b 4 of 13 emission sites ship `witnesses: []` | SDK track | re-confirmed incidentally: `:620` deposit and `:652` allocate emit no `witnesses` (see §C/N2 transcript) | OPEN |
| C360-N3 received rows | process | see below | OPEN |

**RECEIVED rows — carried, NOT adjudicated** (owned by other lineages; typed here so they cannot be lost):

| id | owner lineage | anchor here | state |
|---|---|---|---|
| C54-B14 | society-metabolic-states (C133→C364) | `SOCIETY_SPECIFICATION.md:89` | OPEN, unmoved (window 0) |
| L1-residual | society-authority-law (C58→C366) | §1.4 `:85-89` → SAL §3.6 back-link absent | OPEN, unmoved (window 0) |

**Row count: 16 lineage rows + 2 received = 18.** C360 published 12 + 2. The rise is accounted for
explicitly (v62: account for a rising count as explicitly as a falling one): **+3** are C360's own findings
(N1, N2/N2b, N3), which by construction were not in the table C360 handed forward; **+1** is **C50-B16(b)**,
recovered by §C/N2 from under (c)'s label.

**SDK-track bundle after this pass — twelve rows:** C92-N1, C164-N1, C22-M3, C92-N3/C50-B20, C50-B16(a),
C50-B16(c) *(re-stated)*, C50-B18 *(widened by C400-N1)*, C50-B19, C360-N1, C360-N2, C360-N2b, **+ the
C400-N1 fix shape**.
**Operator DESIGN-Q bundle:** C50-B13, C50-B14, C50-B15, C50-B16(b), C280-N1 (adjudicate with B-D1), C320-N3.

---

## §H — Method carry

**v65 — a carry id and its predicate can decouple; re-resolve by PREDICATE, not by id.** C360's §C
asserted every row was *"re-resolved by content at HEAD"* and 12 of 12 were — but one row's content
belonged to a **different sub-row of the same structured block**. A sub-lettered id (`B16(a)/(b)/(c)`) is
exactly the shape that invites the collision: the ids are one character apart and the titles are
paraphrasable into each other. The check that catches it is cheap and was never run: **paste the
predicate's own words from the ORIGINATING pass into the row, then re-verify against those words** — not
against the title the previous pass wrote. C400 reached B16(c)'s real predicate only by *executing the
artifact*, which is the same detector v62 named: **rediscovering a charged row cold proves the ledger lost
it.**

**v65b — a multi-arm row must be dispositioned PER ARM.** I measured 2 of B16(c)'s 3 arms, found both
false, and drafted a whole-row deflation. The unmeasured arm — initial-law ratification — is **true,
unqualified, and stronger than the two I measured**. A row-level verdict computed from a proper subset of
its arms is v60 recurring one level up: *charge or explicitly carry the other N−1*, and that applies to a
**correction** exactly as it applies to a charge. **A deflation needs full coverage of the row's arms
before it is allowed to touch the row.**

Corollaries this pass paid for:

- **v51 does not license inheriting your OWN lineage's unexecuted claims.** "Route, do not re-adjudicate"
  protects other lineages' rows. On your own, an unexecuted predicate is a liability, and executing it here
  falsified it in two of three arms — and the third, unexecuted, is the one that holds the row up
  (§E-2, §E-3).
- **A gate cell must carry the command AND THE ROOT.** Three greps returned honest `0`s computed over the
  wrong domain (§E-1). C360 published a relabelled `0`; C400 nearly published a mis-rooted one. Same class,
  new mechanism.
- **Absence of a key is not an assertion.** A vector that omits a claim under-covers; it does not encode a
  false one. Conflating the two re-walks a refuted coverage census with your own control as counter-evidence
  (§D-2).
- **When a coverage gap really is not chargeable, say so with its three reasons and publish it as a
  completed negative** (§B-3), so the next pass inherits a closed row rather than a promising-looking lead.
- **Chase the killed headline's mechanism.** Both drafted headlines died; the falsification of §D-1 is what
  led to §3.2.3, the section no pass in ten had named. *(v64's "chase the reviewer's falsifier", again.)*
- **Publish the matcher CASE-INSENSITIVELY, and publish the wider one too.** The first novelty matcher
  returned 0; so did the widened, case-insensitive one — and only the second is worth anything as an absence
  claim, because case-sensitivity is what bit C396. The same applies to an absence claim about *documents*:
  §B-3's "no document claims `hub/` implements §4.1" ships its matcher and its one false positive.
- **A guard that is green on BOTH sides of a fix is reporting on the suite, not the fix.** `86 passed`
  before and after the C400-N1 fix shape means no test observes the change — which is itself the coverage
  story of the row being widened.

---

*C400 verdict: target byte-frozen 33 days, window 0 of 28 in `web4-standard/`, §A negative by measurement.
Both drafted headlines killed by policy review (14th consecutive). What survives is one LOW-MED widening
routed to C50-B18 — §3.2.3, unnamed in ten passes under either matcher, has a capability not reachable via
the `incorporate_child` path alone, and the real widening is the §3.1 **diagram**, which labels hierarchy
membership as citizenship while §3.1's prose keeps it optional; the spec is coherent and the SDK is the sole
deviator — plus an executed, guard-run fix shape handed to the SDK track. And one MED process recovery:
C50-B16(c) had been carrying C50-B16(b)'s predicate since C360, and its own three arms, executed cold for
the first time in ten passes, split 2 false / 1 true — the true one, initial-law ratification, holds the row
at MED and had never been run. Ledger 12 + 2 → 16 + 2, every increment accounted. Zero mutation; nothing was
applied in-tree. Next SOCIETY_SPEC delta ≈ C440.*
