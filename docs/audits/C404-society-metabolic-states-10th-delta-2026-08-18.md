# C404 — SOCIETY_METABOLIC_STATES.md, 10th delta

**Date**: 2026-08-18
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md`
**Prior pass**: C364 (2026-08-11, PR #692) · lineage: C21 → C54 → C96 → C133 → C168 → C206 → C244 → C284 → C324 → C364 → **C404**
**Corpus HEAD**: `269ac5b4`
**Verdict**: **2 net-new findings** — **N1 (LOW-MED)**, a constant table cites two spec sections as its source and one of them defines no numbers while the other backs 1 of its 8 rows; **N2 (LOW)**, an exported function's required argument is supplied by no type in the SDK. Plus **N3**, a sharpening of C364-N1 that measures C364's own routed fix and finds one of its three shapes insufficient; 1 INFO at no severity; 1 class routed; 8 guard checks closed; 6 negatives published; and 3 corrections to inherit, one of them to the prior pass. **Zero mutation.**

**Out of scope**: any mutation of spec, schema, SDK, crate, vector or governed state; self-answering any DESIGN-Q — **including `C360:508-509`'s open operator DESIGN-Q, which this pass explicitly does not answer (§B.4)**; adjudicating C360-N1 or C284-R1 on the merits (routed only); the C168-N1 `society.rs` rename (operator-gated); `entity-types.md` (C372's lineage); the `testing/conformance/` tree (web4-lct's first work item); the `protocols/` cluster (D0 gates it, operator-unanswered); mining `simulations/` and the `archive/` sprawl trees (declined by construction at C284, re-declined here as a pre-registered rule).

---

## 0. What this pass is

The target is byte-frozen and has been for **ten** windows. C364's guard opens with *"Target byte-frozen `5e3f7203` since `a504ea41`; 9 consecutive clean passes"*, and this window adds a tenth: **29 commits, 0 in `web4-standard/`**. An eleventh reading of the spec text was a guaranteed null before execution and is not attempted.

C364 ran two instruments nine passes had not: it **executed §10**, and it derived the mirror set by the **domain's word** instead of the target's filename. Both returned findings. This pass runs the rungs above them:

- **§B — it reads a constant table against the sections that table cites.** `metabolic.py:304` heads eight numbers with `# ── Witness Requirements by State (§2, §4.2) ──`. Ten passes have read §2 and §4.2. None has asked whether §2 and §4.2 *contain* those eight numbers.
- **§C — it asks whether an exported function's arguments can be supplied.** v45 asks who calls a function. The rung above is: *could* anyone, given the types that exist.
- **§D — it mutates the vector suite on one side of the harness's filter** (v66) and runs the result against **C364's own three routed fix shapes**, before a maintainer ships one.
- **§E — it executes §3.2**, the target's only block of numbered MUSTs, which three passes have cited as a premise and none has run.

The policy review **falsified this pass's proposed flagship on five independent grounds** (§J.1) — the sixteenth consecutive pass on this track whose drafted headline did not survive review — and supplied §B's question while attacking it. §B is therefore the reviewer's question, executed and verified row-by-row here rather than inherited.

---

## 1. §A — Target and mirror set (null by construction)

Target blob `5e3f7203`, unchanged since `a504ea41` (C55, 2026-06-14): **65 days, 10 consecutive frozen windows**, 444 lines.

All artifacts tracked by the C364 guard are byte-identical to the C364 snapshot, and the two artifacts C364 added to the tracked set are included:

| Artifact | Blob at `269ac5b4` | C364 |
|---|---|---|
| `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` | `5e3f7203` | `5e3f7203` |
| `web4-standard/implementation/sdk/web4/metabolic.py` | `d3d31446` | `d3d31446` |
| `web4-standard/test-vectors/metabolic/society-metabolic-states.json` | `855eedb5` | `855eedb5` |
| `web4-standard/implementation/sdk/tests/test_metabolic.py` | `bac4b18c` | `bac4b18c` |
| `web4-standard/METABOLIC_STATES_INTEGRATION_SUMMARY.md` | `1617db27` | `1617db27` |
| `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (B14 anchor) | `2ad453ba` | `2ad453ba` |
| `web4-standard/core-spec/web4-society-authority-law.md` (B15/C58-B10 anchor) | `0849ebbe` | `0849ebbe` |
| `web4-core/src/society.rs` (C168-N1 anchor) | `17112f05` | `17112f05` |
| `web4-standard/core-spec/atp-adp-cycle.md` (C96-E1 anchor) | `2d060579` | `2d060579` |
| `web4-standard/ontology/web4-core-ontology.ttl` (M7 anchor) | `fc4b4c36` | `fc4b4c36` |

**Window, with its anchor published** (the discipline C324 §F installed and C364 kept):

```
$ git merge-base --is-ancestor c23ce054 HEAD          →  YES   # C364's re-baseline is a true ancestor
$ git log --oneline c23ce054..HEAD | wc -l            →  29
$ git log --oneline c23ce054..HEAD -- web4-standard/  →  0
```

**Zero `web4-standard/` commits in 29. Tenth consecutive clean window against the spec text.** §A is a negative by blob identity; C364's 8-artifact table and C324's before it are carried by identity, not re-derived.

**Domain-word residue re-derived, not inherited** (C364 guard 6):

```
$ git grep -li "metabolic" -- web4-standard/ | grep -v docs/audits | sort  →  28
$ git grep -l  "SOCIETY_METABOLIC_STATES" -- web4-standard/ | sort         →   5
$ comm -23 <those two>                                                     →  23
```

**23, unchanged from C364, member-for-member.** The mirror set neither expanded nor contracted this window — and unlike C324's identical sentence, that is now said of the instrument that *can* see an orphan.

---

## 2. §B — N1 (LOW-MED, net-new) — a constant table cites two sections; one defines no numbers, the other backs one row of eight

### 2.1 The claim being tested

`web4-standard/implementation/sdk/web4/metabolic.py:302-315` (comment column realigned for legibility; text verbatim):

```python
# ── Witness Requirements by State (§2, §4.2) ──────────────────
# Each state specifies how many witnesses are required relative to total.
# Expressed as a fraction of total witnesses (0.0 = none needed, 1.0 = all needed).

WITNESS_REQUIREMENTS: Dict[MetabolicState, float] = {
    MetabolicState.ACTIVE: 1.0,        # All witnesses active
    MetabolicState.REST: 0.3,          # 3 of 10 (duty rotation)
    MetabolicState.SLEEP: 0.2,         # Minimal quorum (2 of 10)
    MetabolicState.HIBERNATION: 0.0,   # Single sentinel (handled externally)
    MetabolicState.TORPOR: 0.0,        # Reactive only
    MetabolicState.ESTIVATION: 0.0,    # Defensive — internal only
    MetabolicState.DREAMING: 0.0,      # No new transactions
    MetabolicState.MOLTING: 1.0,       # Heightened security
}
```

The header is a **provenance claim**: these eight numbers come from §2 and §4.2 of the target. That claim is checkable, and it has never been checked.

### 2.2 §4.2 first, because it is the shorter half

§4.2 "Witness Rotation" (`:253-263`) is one fenced Python block:

```python
def select_active_witnesses(witnesses, required_count, block_height):
    """Select witnesses for current duty cycle."""
    cycle = block_height // CYCLE_LENGTH
    seed = hash(f"{cycle}:{society_lct}")
    shuffled = deterministic_shuffle(witnesses, seed)
    return shuffled[:required_count]
```

```
$ sed -n '253,265p' <target> | grep -nE "[0-9]"   →  1 line: "### 4.2 Witness Rotation"
```

**§4.2 contains no numeric literal.** `required_count` is an *input parameter* and `CYCLE_LENGTH` is an undefined symbol. §4.2 is a selection procedure that consumes a witness requirement; it cannot be the source of one. Half the citation supplies nothing.

### 2.3 §2, row by row — each cell measured against §2's own text

Instrument, run per section rather than as one grep, so that an absence is distinguishable from a miss:

```
$ awk -v s="### 2.N" 'index($0,s)==1{f=1;next} /^### |^## /{f=0} f' <target> | grep -i witness
```

| State | SDK | §2 line the header points at | Verdict |
|---|---|---|---|
| ACTIVE | `1.0` | `:39` — *"All witnesses actively monitoring"* | **BACKED.** "All" → 1.0 |
| REST | `0.3` | `:56` — *"Witnesses rotate duty cycles (**e.g.**, 3 of 10 active)"* | **An illustration promoted to a constant.** The spec marks the number as an example |
| SLEEP | `0.2` | `:70` — *"Minimal witness quorum (**e.g.**, 2 of 10)"* | Same |
| HIBERNATION | `0.0` | `:86` — *"**Single** sentinel witness maintains heartbeat"* | **Numerically contradicts** — spec says one, table says none. **Disclosed** by the inline comment *"handled externally"* |
| TORPOR | `0.0` | `:103` — *"Witnesses wake only on triggers"* | No count in the spec; `0.0` is an interpretation |
| ESTIVATION | `0.0` | §2.6 `:113-127` — **no witness line at all** | **No basis in the cited section** |
| DREAMING | `0.0` | `:138` — *"**Witness testimony consolidation**"* | **Directionally opposed** — witnesses are performing work in this state, and the requirement is zero |
| MOLTING | `1.0` | `:151` — *"Witness rotation (old retiring, new training)"* | No count. *"Heightened security"* is the **SDK comment's own gloss**, not §2.8 |

**One of eight rows is cleanly backed by the section the table cites.** Two promote an explicit `e.g.` to a shipped constant; one contradicts a stated count; one has no line to rest on; two carry no count either way; one is directionally opposed to its source.

### 2.4 Why this is LOW-MED and not MED, said explicitly

**MED-ward.** `WITNESS_REQUIREMENTS` and `required_witnesses` are **public exported API** of the standard's reference SDK (`__init__.py:332`, `:774`), and `MetabolicProfile.witness_fraction` (`metabolic.py:353`, `:362`) surfaces the same eight constants a second time. The two `e.g.` values are the failure mode §10's MUST is written to prevent: a cross-language reimplementer reading §2 sees *"e.g., 3 of 10"* and **cannot derive `0.3`** — the number is only obtainable by reading the Python. And the defect is in the one line that *asserts* the provenance, which is the shape v64 names: a coverage gap is not chargeable, the document that claims the coverage is. Here the claim and the code are the same artifact.

**LOW-ward, and these deflations are real.** Nothing consumes the values in production (§C). §10's conformance suite covers §6.1, §6.2, §5.2 and §3.1 only — the witness table is not in the vectors, so no reimplementer is currently being held to it. The HIBERNATION deviation is **disclosed at the point of use**, which per v45 is discipline rather than drift. And the table is plainly a good-faith reading of §2 — every row is *defensible*; what is wrong is that the header says these numbers came from somewhere they did not.

**Not charged as a spec defect.** §2's `e.g.`s are honest — the spec is describing states, not publishing a constant table, and it says so. The defect is in the citation, not the cited text.

### 2.5 Novelty (v44 — matcher published, both audit trees)

```
                                 docs/audits/ (245 docs)   web4-standard/docs/audits/ (2 docs)
required_witnesses                     0                              0
WITNESS_REQUIREMENTS                   1                              0
witness_fraction                       0                              0
"Witness Requirements by State"        0                              0
"e.g., 3 of 10"                        0                              0
```

The single `WITNESS_REQUIREMENTS` hit is **`C54:100`** — C54-B5's recommendation to *"define the monitored-state set once … and reconcile §2.4/§2.5/§3.1/§4.3/§7.1 + SDK `WITNESS_REQUIREMENTS`"*. That is the **sentinel monitored-set** question (which low-energy sentinel evaluates triggers in which states), a different predicate: it asks what the sentinel watches, not whether the table's numbers come from the sections it cites. **Named as the nearest prior mention rather than claimed absent.** Net-new.

### 2.6 Disposition: ROUTED to the SDK track, not applied

Three legitimate fix shapes and they are not the same decision: correct the header to cite only what it uses; or promote §2's two `e.g.`s to normative constants in the spec so the citation becomes true; or drop the table to the four rows that have a basis. The middle one is a **spec** change and is the standard-owner's, not the SDK's. Choosing is not this pass's call.

---

## 3. §C — N2 (LOW, net-new) — an exported function whose required argument no type can supply

`metabolic.py:318`:

```python
def required_witnesses(state: MetabolicState, total_witnesses: int) -> int:
```

v45 asks who calls it. The answer is **nobody in production**:

```
$ git grep -n "required_witnesses(" -- web4-standard/ | grep -v "def required_witnesses"   →  8
    tests/test_integration.py:1648        total_witnesses=10
    tests/test_metabolic.py:344,347,350,354,357   10, 10, 10, 10, 10
    tests/test_metabolic.py:361                   1
    tests/test_metabolic.py:364                   0
```

Eight call sites, **all in tests, all passing an integer literal**. But the rung above "who calls it" is *could anyone*, and that answer is sharper: **no SDK type carries a witness total to pass.**

```
SocietyState  = [society, phase, metabolic_state, treasury, ledger, citizen_trust, founded_at]   (society.py:245-260)
Society       = [society_id, name, parent, citizens: Set[str], citizenship_records,
                 delegations, law, quorum_policy, witness_quorum: int]                            (federation.py)
```

`Society.citizens` is a set of **citizens**, not witnesses. `witness_quorum: int` is a *requirement*, not a total. Every other `witnesses` in the SDK is a per-call `List[str]` supplied by the caller. There is no registered-witness roster anywhere, so `total_witnesses` has no source — which is why all eight call sites invent one.

**Severity LOW, and the deflations are published with it.** The function is correct (7 assertions verify it, and they hold). Nothing is wrong in the repository today. And crucially — **this is not "the SDK cannot check witnesses."** It can and does: `federation.py:574-577` enforces a witness quorum, law-driven via `Procedure.requires_witnesses`, raising `ValueError("Insufficient witnesses: need N, got M")`. **`C360:515` already published that site**; the SDK's witness mechanism is law-driven rather than table-driven, and that is a design choice, not an absence. N2 is only the narrow observation that the *table-driven* function's argument is unsuppliable — which is a consistent consequence of that choice, and is why it reads as dead API rather than as a bug.

**This is what survived of this pass's proposed flagship** (§J.1). The killed version charged `transition_metabolic_state` for accepting `witnesses=[]` on a transition into MOLTING. Every step of that framing failed, and the narrowing is recorded because it is the lesson: each correction made the claim smaller and made it true.

---

## 4. §D — N3 (LOW, **sharpening of C364-N1, not net-new**) — the harness's routing key is an unvalidated substring, and one of C364's three routed fixes cannot see it

### 4.1 The mutation map (v66 — mutate on ONE side of the guard, publish the map not the verdict)

Fourteen single-field mutations to **plausible wrong values, not sentinels** (v59), applied to in-memory copies. **The repository's vector file was never modified** — `git status --porcelain` is empty.

| Mutation | Result |
|---|---|
| `v0.baseline` 100→90 · `v0.society_size` 10→9 · `v0.hours` 1→2 · `v0.expected.cost` 1000→900 · `v0.state` active→rest | **RED** ×5 |
| `v3.planned_hours` 8→10 · `v6.expected.valid` true→false | **RED** ×2 |
| `v10.factors.energy_efficiency` 0.85→0.75 · `v10.expected.score` 1.0→0.7 | **RED** ×2 |
| `v0.description` → wrong prose | GREEN — documentation, benign |
| `v0.id` **suffix** typo (still routed) | GREEN — the suffix is not read |
| `v6.to_state` rest→sleep | **GREEN** — Active→Sleep is also valid, so the boolean is preserved |
| `v6.id` **prefix** → `metabolic-transitions-` | **GREEN** |
| **all four** transition ids → `metabolic-transitions-` | **GREEN** |

**Ten of fourteen caught.** Two of the four silent ones are benign. The `to_state` case is recorded, not charged: a boolean assertion carries one bit and a mutation preserving that bit is invisible by construction — that is a property of the check, not a defect in it.

### 4.2 The prefix, and why it matters

`test_metabolic.py:450-500` routes every vector to its assertion by `v["id"].startswith("metabolic-<category>-")`. The category is a **substring convention of another field**. The JSON carries no `category` key, §10 names the four categories only in prose, and nothing validates that a vector's id prefix matches its payload. Rename all four transition ids and:

- the whole **§3.1 arm** — the only place §10's *"exact boolean match for transition-matrix membership"* MUST is checked — stops executing;
- `len(vectors)` is **still 12**;
- the suite is **GREEN, 5 of 5 test methods passing**.

Executed: `unrouted vectors` = **4** after the mutation, **0** on the control.

### 4.3 Running the guard against the fix (v53/v66) — before a maintainer ships one

C364 routed N1 with three fix shapes and left the choice to the SDK owner. Measured against this mutation:

| C364's routed fix shape | Under a prefix rename | |
|---|---|---|
| **A** — `assert len(vectors) == 12` | count is still 12 | **MISSES** |
| **B** — assert per-category counts against §10's 3/3/4/2 | measures `{energy:3, wake:3, reliability:2}`, transition absent | **CATCHES** |
| **C** — drive categories from a manifest | unrouted set is non-empty | **CATCHES** |

**Fix A is the one a maintainer is most likely to reach for** — it is a one-line change and it restates the sentence §10 already publishes. It is also the only one of the three that a rename walks straight through. **This is the routed-fix check C402 installed** (*"C362-N1's routed fix measured insufficient"*), fired one pass later on this lineage's own carry.

### 4.4 Disposition: **sharpening, not net-new**

Same defect class as C364-N1 (category filters that fail open), same anchor (`test_metabolic.py:450-500`), reached by renaming instead of deleting. It does not increment this pass's net-new count. What it adds is the discrimination among the three fix shapes, which C364 could not have made because it had not yet proposed them.

---

## 5. §E — §3.2 executed for the first time in ten passes (I-1, INFO, no severity), and the class it belongs to (I-2, routed)

### 5.1 Why this was worth running

§3.2 "Transition Requirements" is the target's **only block of numbered MUSTs**. Novelty, both trees:

```
"Transition Requirement"        → 1 file  (the spec itself)
"Notify all active witnesses"   → 1 file  (the spec itself)
"transition safety"             → 1 file  (the spec itself)
```

Zero audit documents. But §3.2 has been **cited three times** — `C96:84`, `C284:165`, `C324:215` — always as a **premise supporting a refutation**, never executed. A premise carried three times and never run is exactly what v52 means by *your predecessor holds the falsifier*.

### 5.2 Executed, per arm (v65b — a multi-arm row is dispositioned per arm)

Subject: `society.py:576 transition_metabolic_state`, the SDK's only metabolic-state mutator.

| §3.2 MUST | Site | Verdict |
|---|---|---|
| 1. Be recorded on the ledger | `society.py:593-602` — `LedgerEntry(event_type=METABOLIC, action="transition", data={"from":…,"to":…})` | **IMPLEMENTED** (executed) |
| 2. Notify all active witnesses | `grep -rci notify web4/*.py` → **0** | **ABSENT** |
| 3. Checkpoint current state | `grep -rci checkpoint web4/*.py` → **0** | **ABSENT** |
| 4. Verify transition safety | `society.py:587` `valid_metabolic_transition(…)` | **IMPLEMENTED** |
| 5. Update society LCT metadata | `SocietyState` has no LCT field | **ABSENT** |

**2 implemented, 3 absent.** Arm 4 is graded IMPLEMENTED, not "arguable": `"transition safety"` returns **exactly one hit in the entire repository** — `:203`, the MUST itself, with no definition anywhere — and §3.1 is the spec's own normative safety criterion for a transition, which `valid_transition` implements exactly (§G.1). Grading it partial would have manufactured an absence to inflate the table; the policy review caught that and it is corrected here.

### 5.3 Why this is INFO at no severity

The docstring names **exactly the two arms it implements**:

> *"Validates transition legality per metabolic module rules. Records the transition on the ledger."*

It claims nothing it does not do. Per v45, disclosed inertness is discipline, not drift. And `society.py:19` scopes the module: *"This module provides DATA STRUCTURES and pure-function operations. Persistence, networking, and **consensus** are out of scope."* Witness notification is networking; checkpointing is persistence. Three of the five arms are out of the module's declared scope by its own header.

No document in the corpus falsely claims otherwise — swept: `METABOLIC_STATES_INTEGRATION_SUMMARY.md:70` claims only *"State transitions recorded on ledger"*, which is arm 1 and is true.

### 5.4 The C284-R1 routing, drafted and **dropped** — and why the drop needed checking anyway

This pass drafted a note routing "§3.2's premise is 2-of-5 implemented" to **#580's precedent survey**, on the ground that `C284:165` refuted R1 using arms **(1) and (5)** and arm 5 is absent. The review's ground for dropping it: **arm 1 alone carries R1's conclusion** — the state *is* published on the ledger, executed and shown above — so arm 5 is redundant and there is no premise to weaken.

**Verified, and it holds only partly** (v52 — the reviewer's corrections get checked too). `federation.py:203` defines `CONFINED = "confined"  # Citizens only; internal consensus`, and `create_society` **defaults to `LedgerType.CONFINED`**. For a confined-ledger society the ledger record is citizens-only, so arm 1 does not publish the state to an *external* relying party; arm 5 would have been the ledger-class-independent channel.

**The routing is still dropped, and R1 is not re-opened.** R1 was a charge against the **spec**, and the spec does require arm 5 — so R1's refutation stands on the spec's text regardless of what any implementation does (v51: a REFUTED verdict is scoped to its locus). The ledger-class caveat is published because the *reason* for dropping was checkable and was not quite right, not because the drop was wrong.

### 5.5 I-2 (ROUTED as a class, not charged) — the `witnesses` ledger-attestation idiom

The killed flagship singled out `transition_metabolic_state` for accepting an ungated `witnesses` list. The denominator refutes the singling-out:

```
$ grep -n "witnesses: List\[str\]" web4/society.py
  400, 424, 476, 505, 536, 580, 676        (7 functions)   + :115 (the LedgerEntry field)
$ grep -n "len(witnesses)\|requires_witnesses" web4/society.py   →  0
```

**Seven functions take it; zero gate on it.** Each passes it straight to `LedgerEntry(witnesses=…)` as an attestation record. At 0 of 7 this is a module property, and C364's own §F states the rule it falls under: *"At 0 of 7 the correct action would have been to route it as a corpus property."* **Routed to the SDK track as a class. Not charged, and no member of it is charged.**

Note the adjacency and do **not** confuse the two: **C360-N2** charged *4 of 13 emission sites shipping `witnesses: []`* — a different predicate (what the emitter passes), on a different set (`deposit`, `allocate`, `incorporate_child`, `incorporated_by`), and `transition_metabolic_state` is **not** among them: it accepts and records witnesses. I-2 is about **gating**, C360-N2 about **supplying**.

---

## 6. §F — C364's guard checks, all 8 re-run

| Guard item | Instrument, re-run at `269ac5b4` | Result |
|---|---|---|
| 1 — freeze + re-baseline from `c23ce054` | `merge-base --is-ancestor` → YES; window 29 / **0** in `web4-standard/` | **10th consecutive clean window; 65 d frozen** |
| 2 — Design-Q row count is 14 | §H table enumerates 14 | **14** ✓ |
| 3 — do not re-run §10 unless vector `855eedb5` or `test_metabolic.py` `bac4b18c` moved | both unmoved | **NOT re-run.** §10's four descriptive claims and the 71-passing suite are C364's, carried by blob identity |
| 4 — N1 regression `grep -n "len(vectors)"` | `448: assert len(vectors) >= 5` | **UNCHANGED — C364-N1 OPEN.** No count assertion appeared, so the post-fix drift check does not apply yet |
| 5 — N2 regression `git grep -l METABOLIC_STATES_INTEGRATION_SUMMARY` | **2 hits, both `docs/audits/`** (C364 itself; C372:105) | **Orphan HOLDS.** The matcher travels with the number (v64): 0 outside the audit tree. Denominator re-measured: `git ls-files "web4-standard/*_INTEGRATION_SUMMARY.md"` → **7**, indexed at `README.md:49-54` → **6**. Ratio unchanged |
| 6 — re-derive the domain-word residue, do not inherit | `comm -23` → **23**, member-for-member identical | **UNCHANGED** |
| 7 — re-resolve **every** hot anchor by content | `git grep -nE 'society\.state\|inner\.state' -- '*.rs' \| grep -v assert` → **4** | **v22 fires a 4th time**: `admin.rs:295`→**`:389`** (+94) and `main.rs:1224`→**`:1240`** (+16) both moved; `wasm.rs:628`/`:673` held a third window. C364 predicted `admin.rs` would hold and it did not — **the tree-level carry is right, the per-file prediction is not predictable, which is the refinement C364 already made** |
| 8 — do-not-re-file list | none re-filed: README `**NEW**` badges, `ledgers/` §5.1, the `Validated against:` predicate (C362's), `entity-types.md` (C372's), `testing/conformance/` (web4-lct's) | **HELD** |

---

## 7. §G — Negatives measured and published

### 7.1 §3.1 ↔ `_TRANSITIONS` as a **SET**, not a count

C364 published *"Spec §3.1 has 17 edges; `_TRANSITIONS` has 17 entries; `CHANGELOG.md:671` publishes '17 valid transitions'. Three independent statements, all 17."* **Three agreeing counts are invariant under a swap** — that is the v66 lesson applied to this lineage's own negative. Taken as a set: §3.1's fence parsed to 17 ordered pairs, `valid_transition` enumerated over all 8×8:

```
spec − sdk  →  []        sdk − spec  →  []
```

**Exact set identity, both directions.** The negative is now stronger than the one it replaces, and the count parity is a consequence of it rather than evidence for it.

### 7.2 The vector expectations reproduce from the **spec's own formulas** — 8 of 12, and the denominator is stated

Hypothesis tested: the vectors were generated from `metabolic.py`, making the vector↔SDK loop closed and self-confirming, so a spec-to-SDK deviation would be invisible to a green suite.

**Refuted, at denominator 8.** Recomputed by hand from the spec text alone — §6.1's `Baseline * State_Multiplier * Society_Size × hours` with multipliers read from §2's per-state *"Energy Cost"* lines; §6.2's `penalties` dict; §5.2's four thresholds:

| Vector | Hand computation from spec | Expected | |
|---|---|---|---|
| energy-active-baseline | `100.0 × 1.00 × 10 × 1` | 1000.0 | ✓ |
| energy-rest-24h | `50.0 × 0.40 × 5 × 24` | 2400.0 | ✓ |
| energy-torpor-minimal | `100.0 × 0.02 × 20 × 1` | 40.0 | ✓ |
| wake-sleep-early | `10 × (1 − 4/8)` | 5.0 | ✓ |
| wake-hibernation-premature | `100 × (1 − 100/1000)` | 90.0 | ✓ |
| wake-dreaming-interrupted | `50 × (1 − 0/2)` | 50.0 | ✓ |
| reliability-perfect | `0.3 + 0.2 + 0.3 + 0.2` (0.95>0.9, 0.85>0.8, 0.96>0.95) | 1.0 | ✓ |
| reliability-none | all four thresholds unmet | 0.0 | ✓ |

**The denominator is 8, not 12** (own-error, §J.2). The four `metabolic-transition-*` vectors carry **booleans from §3.1's matrix, not values from any formula** — they are covered by §G.1's set check, which is the same instrument, so counting them here would have double-counted one arm as two.

**Honest limit, recorded**: §5.2's thresholds are strict `>`, and the two reliability vectors use 0.95/0.85/0.96 and 0.5/0.5/0.5 — neither sits on a boundary, so the pair **cannot distinguish `>` from `>=`**. That is coverage, not a defect (v43), and is not charged.

### 7.3 Other negatives

- **No document falsely claims §3.2 is implemented** (§E.3). Swept across `web4-standard/`.
- **§10 not re-run**, correctly: guard 3's two blobs are unmoved (§F).
- **`QuorumPolicy.check` guards its zero case** — `federation.py:186-193` returns `False` when `total_registered == 0` for both MAJORITY and UNANIMOUS. Read while routing N2; **no correction to C360/C400's account of it is needed**, and none is made.
- **The vector file has no schema**: `git ls-files 'web4-standard/schemas/'` holds 12 JSON-LD schemas and the presence-protocol tree, none covering `test-vectors/`. Recorded as the structural reason N3's routing key is unvalidated; not charged (the whole `test-vectors/` tree is unschema'd, a corpus property).

---

## 8. §H — Carries ledger, full rows

**Design-Q total: 14** — C21 ×8 (H1, H3, M3, M5, M7, L4, L5, L7) + C54 ×6 (B5, B6, B7, B8, B9, B14-normative-strength). Published per C324's rule: *a ledger may collapse its narration but must publish its row count.* **A future table with fewer rows is a defect in the table.**

| Carry | Class | Anchor | State at `269ac5b4` |
|---|---|---|---|
| **C21-H1** §2.3/§5.1 silent on Sleep `update_rate` | DESIGN-Q | spec §5.1 `:297` | OPEN — demonstrated at C284 §3.1; cite, do not re-derive |
| **C21-H3** §5.1 single column mixes incommensurable axes | DESIGN-Q | spec `:293-302` | OPEN — as above |
| **C21-M3** emergency-state entry only from Active | DESIGN-Q | spec §3.1 | OPEN, held by freeze — **re-confirmed structurally by §G.1's set enumeration** |
| **C21-M5** define "dormant" | DESIGN-Q | spec | OPEN — couples to B15/C58-B10 |
| **C21-M7** `web4:MetabolicState` absent from ontology | DESIGN-Q | `web4-core-ontology.ttl` `fc4b4c36` | OPEN — held by blob identity; C364 re-confirmed on a 2nd matcher, not re-run |
| **C21-L4** Estivation 10% < Sleep 15% ordering | DESIGN-Q | spec §6.1 | OPEN, held by freeze |
| **C21-L5** Rest queued-vs-refuse | DESIGN-Q | spec §2.2 | OPEN, held by freeze |
| **C21-L7** §6.2 wake-penalty state coverage | DESIGN-Q | spec §6.2 | OPEN, held by freeze |
| **C54-B5** §4.3 sentinel monitored-set — Estivation exit unfireable | DESIGN-Q | spec `:280` vs `:189` | OPEN — **named as N1's nearest prior mention (§B.5); different predicate, not discharged** |
| **C54-B6** §6.1 `Society_Size` undefined + baseline units | DESIGN-Q | spec `:341` | OPEN — re-verified TRUE at C324; cite |
| **C54-B7** §6.2 penalty constants 10/100/50 ungrounded | DESIGN-Q | spec `:352-356` | OPEN — **and §G.2 shows the vectors reproduce them, so the constants are consistently applied while remaining ungrounded** |
| **C54-B8** §7 omits Estivation + `threat_score` provenance | DESIGN-Q | spec `:366-388` | OPEN — re-verified TRUE at C324 |
| **C54-B9** §6.2 prices a Dreaming premature-wake with no §3.1 transition | DESIGN-Q | spec §6.2 vs §3.1 | OPEN — re-verified TRUE at C324 |
| **C54-B14** §1.4 MUST-conform vs "Proposed Standard" + §10 SHOULD | DESIGN-Q + cross-track | `SOCIETY_SPECIFICATION.md:89` `2ad453ba` | OPEN — RECEIVED from C360, carried by blob identity, **not re-derived** |
| **C54-B1** SDK hibernation-wake omits `new_citizen`/90-day | CROSS-TRACK (SDK) | `metabolic.py:147` `d3d31446` | STILL STALE by freeze |
| **C54-B3** SDK "Daily ATP Cost" vs spec §6.1 "Hourly" | CROSS-TRACK (SDK) | `metabolic.py:207` | STILL STALE by freeze |
| **C54-B4** SDK Torpor `"Frozen + alert bonus"` vs spec `"Frozen"` | CROSS-TRACK (SDK) | `metabolic.py:110` | STILL STALE by freeze |
| **C54-B11** SDK comment "Rest: queued" vs `return state == ACTIVE` | CROSS-TRACK (SDK) | `metabolic.py:410-413` | STILL STALE by freeze |
| **C54-B15 / C58-B10** SAL §3.6 dormant list omits Rest | DESIGN-Q, two-sided | `web4-society-authority-law.md:138-141` `0849ebbe` | OPEN, HELD — composes with C168-N1 |
| **C96-E1** ATP conservation cross-ref | CROSS-TRACK | `atp-adp-cycle.md` §3.3 `2d060579` | HELD |
| **C168-N1 / C284-N1** `society.rs` phase enum mis-cites the 8-state spec | DESIGN-Q + publish-track | `web4-core/src/society.rs:33-48` `17112f05` | OPEN — reach unchanged (4 consumers, all display/serialization) |
| **C284-N2** §5.2 as absence-never-grants precedent | INFO → #580 survey | spec §5.2 | ROUTED, awaiting #580. **§E.4's premise-strength note was drafted and DROPPED — do not re-draft it; the reason is recorded** |
| **C324-N1** C54-B5…B9 restored to the ledger | LOW, ledger-integrity | — | DISCHARGED at C364; count re-published above |
| **C324-N2 / v22** anchor half-life | INFO, method | — | **CONFIRMED a 4th time (§F guard 7)** — and C364's per-file prediction inverted, which is the refinement it already published |
| **C364-N1** §10's MUST enforced by a harness with no denominator | MED | `test_metabolic.py:447-448` `bac4b18c` | **OPEN — unchanged. SHARPENED by N3: of its 3 routed fix shapes, A is insufficient (§D.3)** |
| **C364-N2** unindexed integration summary contradicting the spec | LOW-MED | `METABOLIC_STATES_INTEGRATION_SUMMARY.md` `1617db27`, `README.md:49-54` | **OPEN — orphan holds, 7/6 ratio unchanged (§F guard 5)** |
| **C364-N3** third metabolic vocabulary | INFO, routed | `entity-types.md:779-783` | **ROUTED to C372, which ADJUDICATED it as C372-N2** — credited, closed here, do not re-route |
| **C364-I-1** `role.py` cites P4, closed stale at C21 | INFO, traceability | `role.py:357-360` | Recorded for SDK track; unchanged |
| **C364-I-2** second vector suite drives a §3.1 transition | INFO | `society-vectors.json:76-80` | Carried; mirror set holds two vector files |
| **C404-N1** `WITNESS_REQUIREMENTS` cites §2/§4.2; §4.2 has no numbers, §2 backs 1 of 8 | **LOW-MED, net-new** | `metabolic.py:302-315` `d3d31446` | **OPEN — routed to SDK track + standard-owner** |
| **C404-N2** `required_witnesses`' `total_witnesses` supplied by no SDK type | **LOW, net-new** | `metabolic.py:318` | **OPEN — routed to SDK track** |
| **C404-N3** harness routing key is an unvalidated id substring | LOW, **sharpening of C364-N1** | `test_metabolic.py:450-500` | **OPEN — routed with C364-N1; fix A insufficient** |
| **C404-I-1** §3.2 executed per arm: 2 implemented / 3 absent, disclosed | INFO, no severity | `society.py:576-604`, `:19` | Recorded. **Do not re-charge — `C360:508-509`'s operator DESIGN-Q owns the scoping question** |
| **C404-I-2** the 0-of-7 `witnesses` ledger-attestation idiom | **ROUTED as a class** | `society.py:400,424,476,505,536,580,676` | **Routed to SDK track. Do NOT charge a member.** Distinct from C360-N2 (gating vs supplying) |
| **C244** LCT §1.2-vs-§5 charge · **C284-N3** H1/H3 demonstration | — | — | CONSUMED — do NOT re-open |

**Refuted — do NOT resurrect**: C284-R1 (#580-vs-§5.1 dormancy-freeze — see §E.4, which checked the drop and did **not** re-open it); C284-R2 (2026-05-11 triage basename collision); C324's `README.md` `**NEW**`-badge charge (whole-README property); **and this pass's own killed flagship (§J.1) — `transition_metabolic_state` accepting `witnesses=[]` into MOLTING is NOT a finding; five grounds are recorded so it is not re-derived.**

---

## 9. §I — Method notes

- **v66 has a second edge: a count is invariant under a swap, so a count-parity negative is weaker than it reads.** This lineage published "17 / 17 / 17" as a strong negative for two passes. Three agreeing counts do not establish that three artifacts describe the same seventeen edges; only the set difference does. It cost one enumeration and it upgraded the negative rather than overturning it — which is the good case, and is why the check is worth running on negatives you already believe.
- **The rung above "who calls it" is "could anyone".** v45 measures a caller count. N2's question is whether the *type system* can supply the arguments — and when the answer is no, the zero caller count stops being an oversight and becomes a consequence. That reframing is what demoted this pass's flagship from a charge to an observation, correctly.
- **A citation in code is a checkable claim, and nothing in this corpus checks one.** `# ── Witness Requirements by State (§2, §4.2) ──` is eleven words asserting the provenance of eight constants. Ten passes read both cited sections and neither the header nor the sections had ever been read *against each other*. The general instrument: **wherever shipped code cites a spec section, open that section and count how many of the code's values it contains.** Half of N1's citation supplies no numbers at all, and that half was the cheapest thing in the pass to measure.
- **Test the routed fix before someone ships it (v66, C402's carry), and the cheapest fix is the one to test first.** C364 routed three fix shapes without ranking them. Fix A is the shortest, most obvious, and restates §10's own sentence — and it is the only one a rename walks through. A pass that routes N alternatives owes the next pass a measurement over them, because the maintainer will pick by cost.
- **A killed headline is worth more written down than deleted.** Five grounds killed this pass's flagship and every one of them is a reusable rule: test the disclosure on the *module you are charging*; check whether the question is an open DESIGN-Q someone else owns; check whether the constant you are shocked by is the **spec's** or the **SDK's gloss**; measure the denominator before singling out a member; and before claiming something is uncomputable, grep for the place it is already computed. §J.1 keeps them; the finding is gone.

---

## 10. §J — Post-write instrument re-run, and own-error log

Every count above was re-run after this document was written, at a different scope than it was first taken. **`git status --porcelain` empty throughout — zero mutation on both the proposal and the write.**

| Claim | Re-run instrument | Result |
|---|---|---|
| window 29 / 0 | `git log --oneline c23ce054..HEAD` and `… -- web4-standard/` | **29 / 0** ✓ |
| 10 blobs frozen | `git rev-parse HEAD:<path>` ×10 | all match C364 ✓ |
| residue 23 | `comm -23` of the two sorted in-standard sweeps | **23** ✓ |
| §4.2 has no numeric literal | `sed -n '253,265p' \| grep -nE "[0-9]"` | 1 line, the heading ✓ |
| §2 rows | per-section `awk` + `grep -i witness`, 8 sections | 1 backed / 2 `e.g.` / 1 contradicts / 1 absent / 3 no-count ✓ |
| `required_witnesses` call sites | `git grep -n "required_witnesses(" -- web4-standard/` | **8, all tests, all integer literals** ✓ |
| novelty, both trees | `git grep -lie <token> -- docs/audits/` and `-- web4-standard/docs/audits/` | 0 / 1(C54:100) / 0 / 0 / 0 ✓ |
| 17/17 as a set | fence parse vs `valid_transition` over 8×8 | `[] / []` ✓ |
| 8 vectors from spec formulas | hand recomputation, §G.2 table | 8/8 ✓ |
| mutation map | 14 mutations against all 5 test methods | 10 RED / 4 GREEN ✓ |
| fix shapes A/B/C | count, per-category counts, unrouted set | MISS / CATCH / CATCH ✓ |
| §3.2 arms | `grep -rci notify\|checkpoint web4/*.py`; `SocietyState` fields | 0 / 0 / no LCT field ✓ |
| 0-of-7 idiom | `grep -n "witnesses: List\[str\]"` + `grep -n "len(witnesses)\|requires_witnesses"` | **7 / 0** ✓ |

### Own-error log — 5 items

1. **The proposed flagship was falsified on five independent grounds, and the replacement headline came from the reviewer attacking it.** Recorded in full at §C and §E.5. The five: (a) I tested `metabolic.py:19`'s disclosure while charging `society.py`, whose own `:19` says *"consensus … out of scope"* and is the load-bearing one; (b) `C360:508-509` records that exact scoping question as an **open operator DESIGN-Q**, *"not self-resolved"* — charging it would have self-answered another lineage's DESIGN-Q, which my own out-of-bounds line forbids; (c) §2.8 Molting carries **no witness count**, so *"`witnesses=[]` while MOLTING = 1.0"* rested half on the SDK's own gloss — I had read §2.8 and still wrote the juxtaposition; (d) the `witnesses` parameter is **0-gated across 7 functions**, so singling out one charges a member of an idiom, against C364's own §F rule; (e) *"NOT COMPUTABLE"* is false — `federation.py:574-577` computes it law-driven and **`C360:515` had already published the site**. This is the **16th consecutive** pass here whose drafted headline did not survive review. Ground (e) is the sharpest: I wrote an absence claim without grepping for the thing I said was absent, one pass after v66b's *"narrow the absence to a weak presence before publishing"* entered the carry.
2. **A denominator relabelled from a neighbouring query — the C364 §G.1 shape, in the pass that inherited that lesson.** I proposed *"all 12 vector expectations reproduce from the spec"*. The three formula sources I named (§6.1, §6.2, §5.2) cover **8** vectors; the other 4 are §3.1 booleans, already covered by §G.1's set check. `12` was the suite total, relabelled as this instrument's denominator. Corrected to 8 with the non-covered members named — and the conclusion is unaffected, which is exactly what makes the error easy to ship.
3. **A partial absence manufactured by grading.** §3.2 arm 4 was written "ARGUABLE". `"transition safety"` has one hit in the whole repository — the MUST itself — and §3.1 is the spec's own safety criterion, which `valid_transition` implements exactly. The honest grade is IMPLEMENTED, giving 2/3, which is precisely what the docstring already claims. Grading it down inflated the table by one row.
4. **An inherited correction — C364's novelty denominator is wrong.** C364 twice publishes *"all 90 documents in `docs/audits/`"* (`:122`, `:185`). The tree held **227** tracked `.md` at C364's own anchor `c23ce054` (198 C-numbered), and 245 at HEAD; no filter yields 90. C364's novelty *conclusions* are unaffected — a `git grep -l` over the tree returns the same hits whatever denominator is stated — but the published figure is off by 137, and a successor re-deriving from it would under-scope its own sweep. **Inherit the correction, not the number.**
5. **The reviewer's own ground for one instruction was checked and found partly wrong** (v52). The drop of the C284-R1 routing rested on *"arm 1 alone carries R1's conclusion"*. `federation.py:203` defines `CONFINED` as *"Citizens only; internal consensus"* and `create_society` defaults to it, so on the default ledger class arm 1 does not publish to an external relying party. **The instruction was still followed** — R1 is a charge against the spec and the spec requires arm 5 — but the caveat is published rather than the ground taken on trust.

---

## 11. Guard for the next metabolic delta (**C444** = C404 + 40) — do NOT re-open as net-new

1. Target byte-frozen `5e3f7203` since `a504ea41`; **10 consecutive clean passes, 65 days**. **Re-baseline from `269ac5b4`** (this pass's HEAD, a verified ancestor-to-be). Publish the anchor beside the window count. §A is a negative by blob identity — check identity, do not re-derive C364's 8-artifact table or C324's.
2. **Design-Q row count is 14.** A future table with fewer rows is a defect in the table.
3. **§10 was NOT re-run this pass** and correctly so — C364's guard 3 gates it on vector blob `855eedb5` and `test_metabolic.py` `bac4b18c`. Both unmoved. **If either moves, re-run the truncation test AND the §B.1 mutation map, not just the suite.**
4. **N1 (C404) regression**: `sed -n '302,315p' metabolic.py`. If the header still reads `(§2, §4.2)` with 8 rows, N1 is open. If the spec grew normative witness constants, re-run the row-by-row table against the **new** §2 — the post-fix failure mode is the table and §2 drifting apart, the same shape C364 predicted for its own N1.
5. **N2 (C404) regression**: `git grep -n "required_witnesses(" -- web4-standard/`. Eight sites, all tests, all integer literals. A production call site appearing means either a roster type was added (check `SocietyState` and `Society` fields) or someone invented a total — the second is worse than the current state.
6. **N3 / C364-N1 regression**: `grep -n "len(vectors)" test_metabolic.py` → still `>= 5` at `:448`. **If a fix landed, identify WHICH of the three shapes** — shape A (`== 12`) does not close it, and the rename mutation in §D.2 is the test that tells them apart. Re-run it.
7. **C364-N2 regression**: `git grep -l METABOLIC_STATES_INTEGRATION_SUMMARY` — **count only hits OUTSIDE `docs/audits/`**; the audit tree now self-cites twice and a bare count reads 2, not 0. Re-measure the 7-file denominator with `git ls-files "web4-standard/*_INTEGRATION_SUMMARY.md"`; the **ratio**, not the absence, licenses the finding.
8. **Every hot anchor re-resolved by content, every pass** — `admin.rs` and `main.rs` both moved this window after C364 predicted `admin.rs` would hold. Instrument: `git grep -nE 'society\.state|inner\.state' -- '*.rs' | grep -v assert` (returns 4; a `':!*test*'` pathspec returns 7 and is wrong).
9. **Mirror set holds TWO vector files** (`test-vectors/metabolic/`, `test-vectors/society/`) plus the 23-file domain-word residue. **Re-derive the residue with `comm -23`; do not inherit the list.**
10. **Do NOT re-file**: `README.md`'s 7 `**NEW**` badges; the `ledgers/` §5.1 divergence; the `Validated against:` loader predicate (C362's); `entity-types.md`'s vocabulary (C372's — **adjudicated as C372-N2, now closed**); the `testing/conformance/` tree gate (web4-lct's); **any member of the 0-of-7 `witnesses` idiom (§E.5)**; **`transition_metabolic_state` accepting `witnesses=[]`** (killed, five grounds at §J.1); **the C284-R1 premise-strength note** (drafted and dropped, §E.4).
11. **Corrections to inherit**: C364's novelty denominator is **227 at its own anchor / 245 at HEAD**, not 90 (§J.4). The §3.1↔SDK parity negative is a **set** identity, not a count agreement (§G.1). The spec-formula reproduction denominator is **8 of 12**, not 12 (§G.2).
12. **Open questions this pass did not answer, by design**: `C360:508-509`'s operator DESIGN-Q on whether `society.py`'s *"consensus out of scope"* docstring exempts it from a MUST; whether §2's two `e.g.` witness fractions should become normative constants (standard-owner's, N1's third fix shape); the `>` vs `>=` boundary coverage in §5.2's two reliability vectors (coverage, not a defect — v43).

---

## 12. Conclusion

Tenth consecutive frozen window on the target. Zero net-new against the spec text, and none was sought.

What this pass adds is three checks the lineage had the materials for all along. A constant table in shipped SDK code names two specification sections as its source; one of them contains no numbers and the other supports one of its eight values, two of them explicitly marked as illustrations. An exported function takes an argument no type in the SDK can supply. And a suite whose category filter C364 showed fails open turns out to route by an unvalidated substring of another field — so the cheapest of the three fixes C364 routed cannot see the failure, which is worth knowing before a maintainer picks by cost.

The pass's own proposed flagship was none of these. It was killed on five grounds, and the headline that replaced it was found by the reviewer while attacking it — the second pass in a row where the yield came out of the falsification rather than the proposal. What survived of the killed finding is one narrow true sentence, and the five grounds are written into the guard so the next pass does not re-derive it.

**Zero mutation.** 2 net-new findings and 1 sharpening, all routed and none applied; 1 INFO at no severity; 1 class routed rather than charged; 8 guard checks closed; 6 negatives published, one of them an upgrade of a negative this lineage already believed; and 5 own-errors logged, including a correction to the prior pass and a check of the reviewer's own reasoning.

---

*Accountability self-audit: **n/a**. This pass creates no surface and causes no consequential act — it adds one document under `docs/audits/` and mutates no spec, schema, code, vector or governed state. The mutation map in §D.1 and the §3.2 execution in §E.2 were run by passing in-memory copies to library functions and to a re-implementation of the five test methods; `git status --porcelain` was empty before, during and after. Every defect named is routed, not applied; the items that would be consequential acts (the C168-N1 enum rename, any edit to `metabolic.py`, `test_metabolic.py`, `README.md` or the spec) are operator- or owner-gated and were held out of scope before execution. `C360:508-509`'s open operator DESIGN-Q is cited and explicitly not answered. Confirmed with the policy reviewer at Step 4.*

*Audit produced under Autonomous Session Protocol v2 by `legion-web4-20260818-060000`. Policy review: **REVISE** → 11 changes required, all accepted and independently re-verified before adoption (demote the flagship to LOW and delete the MOLTING framing; publish `society.py:19` as the tested disclosure; cite C360's open DESIGN-Q; publish the 0-of-7 denominator and route the class; delete "NOT COMPUTABLE" and credit `C360:515`; take the `WITNESS_REQUIREMENTS`-vs-citation table as the headline, verified row-by-row here rather than inherited; correct the vector negative to 8 of 12; restate §3.2 as 2 implemented / 3 absent; drop the C284-R1 routing and record why; publish both audit trees in every novelty matcher; keep the deliverable at one file with an own-error log).*
