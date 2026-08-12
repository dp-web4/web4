# C364 — SOCIETY_METABOLIC_STATES.md, 9th delta

**Date**: 2026-08-11
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md`
**Prior pass**: C324 (2026-08-06, PR #649) · lineage: C21 → C54 → C96 → C133 → C168 → C206 → C244 → C284 → C324 → **C364**
**Corpus HEAD**: `c23ce054`
**Verdict**: **2 net-new findings** — **N1 (MED)**, the conformance harness enforcing §10 has no denominator; **N2 (LOW-MED)**, the standard's only unindexed integration summary contradicts the spec it summarizes. Plus 2 INFO, 1 routed to another lineage, 3 guard checks closed, and four negatives published. **Zero mutation.**

**Out of scope**: any mutation of spec, schema, SDK, crate, vector or governed state; self-answering any DESIGN-Q; the C168-N1 `society.rs` rename (breaking public API across two WASM faces and a committed `.d.ts` — operator-gated); adjudicating findings owned by the entity-types (C372) or society-specification (C400) lineages — those are **routed only**; the `protocols/` cluster (D0 gates it, operator-unanswered); mining `simulations/` and the `archive/` sprawl trees (declined by construction at C284, re-declined here as a pre-registered rule — see §C.1).

---

## 0. What this pass is

The target is byte-frozen and has been for nine windows. Seven consecutive passes returned zero net-new against it. A tenth reading was a **guaranteed null before execution**, and the proposed scope said so and did not propose one.

Instead this pass runs the two things nine passes never did:

- **§B — it executes the spec.** §10 is a Conformance section that names a canonical vector suite and places a MUST on cross-language reimplementations. Nine passes cited that section. None ever ran it.
- **§C — it derives the mirror set by the domain's word instead of the target's filename.** Every prior derivation grepped the path token `SOCIETY_METABOLIC_STATES`. That instrument is structurally blind to any artifact that discusses metabolic states without citing the spec's path — which is most of them.

Both arms returned findings. The policy review corrected this pass's own scoping denominator before execution (185 → 28, §G.1) and supplied the sharper form of §B's question, which became N1.

---

## 1. §A — Target and mirror set (null by construction)

Target blob `5e3f7203`, unchanged since `a504ea41` (C55, 2026-06-14): **58 days, 9 consecutive frozen windows**, 444 lines.

All eight artifacts tracked by the C324 guard are byte-identical to the C324 snapshot:

| Artifact | Blob at `c23ce054` | C324 |
|---|---|---|
| `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` | `5e3f7203` | `5e3f7203` |
| `web4-standard/implementation/sdk/web4/metabolic.py` | `d3d31446` | `d3d31446` |
| `web4-standard/test-vectors/metabolic/society-metabolic-states.json` | `855eedb5` | `855eedb5` |
| `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (B14 anchor) | `2ad453ba` | `2ad453ba` |
| `web4-standard/core-spec/web4-society-authority-law.md` (B15/C58-B10 anchor) | `0849ebbe` | `0849ebbe` |
| `web4-core/src/society.rs` (C168-N1 anchor) | `17112f05` | `17112f05` |
| `web4-standard/core-spec/atp-adp-cycle.md` (C96-E1 anchor) | `2d060579` | `2d060579` |
| `web4-standard/ontology/web4-core-ontology.ttl` (M7 anchor) | `fc4b4c36` | `fc4b4c36` |

**Window, with its anchor published** (the discipline C324 §F installed after finding its own guard anchor was 20 commits stale):

```
$ git merge-base --is-ancestor 36602276 HEAD          →  YES   # C324's re-baseline is a true ancestor
$ git log --oneline 36602276..HEAD | wc -l            →  52
$ git log --oneline 36602276..HEAD -- web4-standard/  →  1
```

One `web4-standard/` commit in 52, and it is not on the target or any mirror. **Ninth consecutive clean window against the spec text.**

---

## 2. §B — The machine check: executing §10 (the flagship)

### 2.1 What §10 publishes

§10 (`:428-441`) is the target's Conformance section. It makes four checkable claims and one normative requirement:

| §10 claim | Line | Measured at `855eedb5` | Verdict |
|---|---|---|---|
| suite contains **12 vectors** | `:434` | `len(json["vectors"])` → **12** | **TRUE** |
| **four categories**, 3 / 3 / 4 / 2 | `:436-439` | `Counter(id.split('-')[1])` → `{energy: 3, wake: 3, transition: 4, reliability: 2}` | **TRUE** |
| coverage is **6 of 8** states as *driven* states | `:441` | union of `state`/`from_state`/`to_state` → **6**: `active, dreaming, hibernation, rest, sleep, torpor` | **TRUE** |
| estivation and molting not exercised, though `molt_success_rate` is a §5.2 input | `:441` | both absent from the driven set; `molt_success_rate` present in both reliability vectors | **TRUE** |
| **MUST** match every deterministic case — numeric equality for §6.1/§6.2/§5.2, exact boolean for §3.1 membership | `:441` | see §2.2 | — |

Every descriptive claim in §10 is accurate. That is worth publishing as a negative: nine passes read this section and none verified its arithmetic; it holds.

**The suite is executed, and it is green:**

```
$ python3 -m pytest tests/test_metabolic.py -q     →  71 passed in 0.13s
```

**Received, not re-derived (carry #4).** Whether `metabolic.py:21`'s `Validated against:` claim is backed by an actual loader is **not** this pass's question to re-answer — **C362 discharged it four commits ago**, naming `test_metabolic.py:442` as one of the 15 backed sites of 17, and explicitly instructing *"Do not batch the 15 backed / 2 unbacked `Validated against:` claims into a corpus sweep"* (`C362:110`, `C362:287`). The claim is **BACKED**. Re-filing it here would inflate this pass's yield with another lineage's work. Cited, closed.

Likewise **v45's caller question returns non-zero here**, which is the complement of C360-N1: `web4/society.py:39,46` imports `valid_transition` and `MetabolicState` from `web4.metabolic` in production, not only in tests. The module is not inert.

### 2.2 N1 (MED, net-new) — §10's MUST is enforced by a harness with no denominator

The suite is loaded and the twelve vectors do pass. The defect is one level up: **nothing asserts that there are twelve.**

`test_metabolic.py:430-500` is the entire enforcement of §10. Its structure:

```python
def test_vectors_exist(self, vectors):
    assert len(vectors) >= 5                          # :447-448 — the ONLY cardinality guard

def test_energy_cost_vectors(self, vectors):
    for v in vectors:
        if v["id"].startswith("metabolic-energy-"):   # :452 — no per-category floor
            ...assert...
```

All four category methods have that shape (`:450`, `:464`, `:477`, `:487`). A category whose vectors are all absent iterates zero times and **passes vacuously**. The single floor is `>= 5`, against a §10 that publishes 12 in a 3/3/4/2 breakdown.

**Demonstrated, not argued.** Feeding truncated vector lists directly to the four test methods (zero mutation — the repository's vector file was never touched):

| Vector set | `vectors_exist` | `energy` | `wake` | `transition` | `reliability` | Suite |
|---|---|---|---|---|---|---|
| canonical, all 12 | PASS | PASS | PASS | PASS | PASS | **GREEN** |
| **3 energy + 2 wake (5)** | PASS | PASS | PASS | **PASS (0 iterations)** | **PASS (0 iterations)** | **GREEN** |
| first 5 | PASS | PASS | PASS | PASS | PASS | **GREEN** |
| first 4 | **FAIL** | PASS | PASS | PASS | PASS | RED |

**Seven of the twelve vectors can be deleted with the suite fully green** — `metabolic-wake-dreaming-interrupted`, all four `metabolic-transition-*`, and both `metabolic-reliability-*`. That set includes:

- **the entire §3.1 transition arm** — the only place in the suite where §10's *"exact boolean match for transition-matrix membership"* MUST is checked, and the only arm that exercises the invalid-transition and self-transition rejections; and
- **the entire §5.2 reliability arm** — the only arm exercising `molt_success_rate`, which §10 explicitly cites as the reason molting is not wholly uncovered.

The suite would still report green at 5 vectors, and §10's coverage sentence would silently become false: driven-state coverage falls from **6 of 8** to **5 of 8** — `dreaming` leaves the set with the wake-dreaming vector, and `active, rest, torpor, sleep, hibernation` remain. Measured, not estimated:

```
$ driven(full) → 6  {active, dreaming, hibernation, rest, sleep, torpor}
$ driven(cut)  → 5  {active, hibernation, rest, sleep, torpor}
```

**Why this is not C362's finding.** C362 asked *does anything load the vector file* and answered yes for metabolic. This asks *does the loader have a denominator*, and the answer is no. C362's own instruction — do not batch the claims — is what forces the question to be asked per-file rather than corpus-wide, and this is the per-file answer for metabolic.

**Novelty (v44 — the matcher is published beside the claim).** Over all 90 documents in `docs/audits/`:

```
$ grep -rliE "<token>" docs/audits/ | wc -l
  test_vectors_exist  → 0     len(vectors)  → 0     ">= 5"        → 0
  "vacuously"         → 0     "no assertion" → 0    "empty loop"  → 0
  "vacuous"           → 9     "cardinality"  → 9    "per-category" → 1
```

The nine `vacuous` hits were read: all concern a **gate walking the wrong tree or a pathspec matching nothing** (C316-I3, C318, C348, C352, C344, C314's empty `$defs`, C90's absent citation, C156's edge case). None concerns a test harness with an under-specified vector count. And `test_metabolic.py` has been named in a C-series document exactly twice, both times by **other lineages** — C326 at `:396` (`DORMANT_STATES` length) and C362 at `:442` (the loader). Its own lineage has never opened it. **Net-new.**

**Severity MED, and the honest limits.** Latent: the vector file is byte-frozen 58 days, so no vector has ever been silently dropped, and nothing is currently wrong in the repository. What is wrong is that the mechanism §10 relies on to keep a *cross-language reimplementation* honest would also report green to a partial port that shipped five vectors. §10's MUST is addressed to reimplementers; the harness that would catch them cannot count.

**Disposition: ROUTED to the SDK track, not applied.** Mutation is out of scope for this pass, and the fix has more than one legitimate shape (assert `len(vectors) == 12`; assert per-category counts against §10's 3/3/4/2; or drive the categories from a manifest so §10 and the harness cannot diverge). Choosing among them is the SDK owner's call. **Fix-shape precedent** for whoever takes it: hub #670 `law.rs:390 is_known_law_action` — *"is this a value the gate can ever actually see?"* — the same question asked of a denominator instead of a domain.

---

## 3. §C — v40 domain-word inbound sweep (the derivation nine passes could not run)

### 3.1 The instrument, and its pre-registered bound

Every prior mirror derivation in this lineage used the **path token**:

```
$ git grep -l "SOCIETY_METABOLIC_STATES"                     →  39 files
$ git grep -l "SOCIETY_METABOLIC_STATES" -- web4-standard/   →   5 files
```

That instrument can only see artifacts that cite the spec **by path**. The **domain word** sees the rest:

```
$ git grep -li "metabolic"                                            →  202
$ git grep -li "metabolic" | grep -v "^docs/audits/"                  →  147
$ git grep -li "metabolic" -- web4-standard/ | grep -v docs/audits/   →   28
```

**Pre-registered exclusion rule, stated as a rule rather than performed silently**: the sweep is bounded to `web4-standard/`. The 119-file difference between 147 and 28 is almost entirely the sprawl trees the primer prohibits mining — `archive/reference-implementations/` (42), `archive/implementation-sessions/` (13), `archive/game-prototype/` (6), `archive/` (5), `archive/implementation-sprawl/` (2), `simulations/` (11) — plus `docs/`, `forum/`, `whitepaper/` and `hub/`. Widening into them is the drift C284 declined by construction; the bound is the same one, applied to a new instrument.

**Residue = 23** (`comm -23` of the two in-standard lists), of which one is the target itself, leaving **22 in-standard artifacts carrying metabolic content that no derivation in nine passes could reach.**

> **Instrument note, recorded because it is counter-intuitive**: the target appears in its own residue. `SOCIETY_METABOLIC_STATES.md` does not contain the string `SOCIETY_METABOLIC_STATES` — §10 cites the *vector* path in lowercase (`:432`), not its own. A file is invisible to a sweep keyed on its own name.

### 3.2 Rulings

Admission criteria pre-registered before the rulings were written, unchanged from C324 §C: **M1** discusses the target's subject matter · **M2** product-bearing/normative rather than a process log or archive · **M3** has **reach** — a divergence in it can propagate a defect to a consumer.

| Residue file | M1 | M2 | M3 | Ruling |
|---|---|---|---|---|
| `METABOLIC_STATES_INTEGRATION_SUMMARY.md` | ✓ | ✓ | **✗** | **NON-MIRROR by reach — but FILED as N2.** Zero consumers, and *that is the finding*. §C.3 |
| `core-spec/entity-types.md` | ✓ | ✓ | ✓ | **ROUTED to C372** — third metabolic vocabulary. §C.4. Not adjudicated here |
| `implementation/sdk/web4/role.py` | ✓ | ✓ | ✓ | **DISCLOSED divergence → evidence, not charge (v45).** §C.5, filed I-1 |
| `test-vectors/society/society-vectors.json` | ✓ | ✓ | ✓ | **SECOND SUITE** — filed I-2. §C.6 |
| `ontology/web4-core-ontology.ttl` | ✓ | ✓ | ✓ | **C21-M7 CONFIRMED by a second matcher** — §C.7 |
| `core-spec/ALIGNMENT_PHILOSOPHY.md` | ✓ | ✗ | — | **NON-MIRROR** — 3 hits (`:36`, `:86`, `:146`), all philosophy-track prose asserting metabolic states are "necessary"/"confirmed alignment". No normative content, no divergence |
| `proposals/ATP_INSURANCE_PROTOCOL.md` | ✓ | ✗ | — | **NON-MIRROR** — 1 hit (`:537`), a bibliography line naming the ATP/ADP cycle spec, not this one |
| `schemas/entity-jsonld.schema.json`, `sdk/web4/entity.py`, `sdk/web4/schema_registry.json` | ✓ | ✓ | ✓ | **NON-FINDING, measured** — all three carry the identical string *"Behavioral and metabolic metadata for an entity type"*. That is entity-type metadata, a different sense of the word; none references the eight states |
| `sdk/CHANGELOG.md`, `sdk/README.md`, `sdk/web4/__init__.py`, `sdk/web4/__main__.py`, `sdk/web4/mcp_server.py`, `sdk/web4/society.py` | ✓ | ✓ | ✓ | **NON-FINDING, measured** — SDK surface. `CHANGELOG:671` publishes "17 valid transitions"; §3.1 has **17** edges and `_TRANSITIONS` has **17** entries (§C.8). Consistent |
| `sdk/tests/{test_cli,test_conformance,test_integration,test_metabolic,test_package_api,test_society}.py` | ✓ | ✓ | ✓ | **HARNESS** — `test_metabolic.py` is N1's subject; `test_conformance.py` noted at §C.9; remainder exercise the SDK surface without asserting spec content |

**Result: the mirror set expands by one filed finding and one routed row — the first expansion in this lineage since C54.** C324 recorded "the mirror set neither expanded nor contracted" and was correct *for its instrument*. The instrument was the limit.

### 3.3 N2 (LOW-MED, net-new) — the standard's only unindexed integration summary, and it contradicts the spec it summarizes

`web4-standard/METABOLIC_STATES_INTEGRATION_SUMMARY.md` — 136 lines, sitting in the root of the published standard. **One commit in its entire history** (`c53b4f8f`, the commit that first added the spec). Never named in any of the 90 documents in `docs/audits/`; never opened by any of the nine passes in this lineage.

**It has zero inbound references anywhere in the repository:**

```
$ git grep -l "METABOLIC_STATES_INTEGRATION_SUMMARY"   →  0
```

**The denominator is what makes this a defect rather than an idiom (v46).** The standard's root contains **seven** `*_INTEGRATION_SUMMARY.md` files. `web4-standard/README.md:49-54` indexes them as a labelled block — and indexes **six**:

| File | Indexed in `README.md` | Inbound refs within `web4-standard/` |
|---|---|---|
| `SOCIETY_INTEGRATION_SUMMARY.md` | ✓ `:49` | 1 |
| `SAL_INTEGRATION_SUMMARY.md` | ✓ `:50` | 3 |
| `AGY_INTEGRATION_SUMMARY.md` | ✓ `:51` | 2 |
| `ACP_INTEGRATION_SUMMARY.md` | ✓ `:52` | 1 |
| `ATP_INTEGRATION_SUMMARY.md` | ✓ `:53` | 1 |
| `DICTIONARY_INTEGRATION_SUMMARY.md` | ✓ `:54` | 1 |
| **`METABOLIC_STATES_INTEGRATION_SUMMARY.md`** | **✗** | **0** |

**Six of seven, not zero of seven.** A 0-of-7 result would have made unindexed summaries a corpus property and the correct action would have been to route it, not charge it — that is C362's rule applied to its own precedent. At 6 of 7 the omission is a defect in the index, and it explains the orphan: the one place in the corpus that references this file class does not reference this file. (The README also names the *spec* at `:60`, which is how the path-token sweep reaches the README while never reaching the summary.)

**And the orphan is not benign, because its content has drifted from the spec it summarizes.** Divergences, measured against the frozen `5e3f7203`:

| Locus | Summary says | Spec says | Assessment |
|---|---|---|---|
| `:53` | `Any → Active: Transaction or wake trigger` | §3.1 gives **seven distinct** wake triggers: Hibernation requires external witness / `new_citizen` / 90-day timeout (`:184`); Torpor requires energy-producer recharge (`:186`); Estivation requires `threat_score < 20` (`:189`); Dreaming requires consolidation complete; Molting requires renewal complete | **Materially wrong, and on the hardened surface.** §7.2(1) *"Wake-Trigger Flooding"* exists precisely to rate-limit and ATP-bond cheap external wake triggers. "Transaction or wake trigger, from any state" is the unhardened rule §7.2 is written against |
| `:50` | `Active → Rest: 1 hour no activity` | `:171` `1 hour no transactions` | Divergent — "activity" is the broader predicate; §2.2 distinguishes them |
| `:51` | `Rest → Sleep: Scheduled or 6 hours idle` | `:179` `6 hours no activity` | Divergent — adds a scheduled trigger the matrix does not carry |
| `:83-86` | `### With MRH` — "Reduced horizon during sleep / Frozen boundaries in hibernation / Expansion during molting" | The target contains **0** occurrences of `MRH` or "Markov Relevancy" | **Unreciprocated on both sides**: `core-spec/mrh-tensors.md` contains **0** occurrences of "metabolic", and so does `MRH_RDF_SPECIFICATION.md`. A three-claim coupling between two specifications, asserted in a third document that neither cites |
| `:109` | "Sleep deprivation attacks prevented" | §7.2(1) states prevention as a mitigation **to be applied** ("Prevent by rate-limiting and/or ATP-bonding") | States an obligation as an accomplished fact |
| `:7` | `## Date Added: January 17, 2025` | Spec header: `## Date: 2026-05-30` | A 2025 date on a document in the published standard |
| `:32` | "95% energy reduction in hibernation" | §2.4: hibernation = 5% of baseline | **Correct** — recorded so the table is not read as uniformly negative |

**Severity LOW-MED.** LOW-ward because reach is genuinely zero — nothing imports it, nothing cites it, no code path consults it, and its transition block is explicitly a summary rather than a normative matrix. MED-ward because it is *inside the published standard*, is indistinguishable from the six indexed summaries to a human reader browsing the repository, and its one materially wrong line is on the surface §7.2 hardens. The reach is to a reader, not to a consumer — which is exactly why an M3-keyed mirror derivation would never have filed it, and why it needed a different instrument to find at all.

**Disposition: ROUTED, not applied.** Two independent fixes exist (index it in `README.md`; or reconcile `:50-53`, `:83-86`, `:109` against the spec) and they are not the same decision — one is an index repair, the other could reasonably end in deleting or archiving the file instead. That choice is the standard-owner's.

### 3.4 N3 (INFO, ROUTED to C372 — not adjudicated here) — a third metabolic vocabulary, in a core-spec file

`web4-standard/core-spec/entity-types.md:779-783` publishes a table under the heading **"Metabolic States"**:

| Frame | Metabolic States | Meaning |
|---|---|---|
| Normal | WAKE, FOCUS | Standard accountability |
| Degraded | REST, DREAM | Reduced capabilities acknowledged |
| Duress | CRISIS | Fight-or-flight |

Five names. **One** — REST — is a state of this specification. WAKE, FOCUS, DREAM and CRISIS are not among the eight (`ACTIVE, REST, SLEEP, HIBERNATION, TORPOR, ESTIVATION, DREAMING, MOLTING`); `DREAM` is one character from `DREAMING` and is not it.

With `web4-core/src/society.rs`'s `Genesis / Bootstrap / Operational` (the C168-N1 carry), the corpus therefore carries **three mutually incompatible `MetabolicState` vocabularies**, two of them in `web4-standard/core-spec/`. The path-token instrument could not see this one: `entity-types.md` does not cite the target by path.

**Not adjudicated.** `entity-types.md` is the C372 lineage's file and its §13 is SOIA-SAGE PolicyGate material with its own design history. This lineage's obligation is to **type it and route it** so it cannot be lost the way C320 lost rows.

### 3.5 I-1 (INFO) — the SDK works around the divergence by citing an audit item this lineage closed as stale

`web4-standard/implementation/sdk/web4/role.py:357-360`:

> *The Rust implementation gates differentiation and witnessing checks on `MetabolicState::Operational`. Since the Python SDK's MetabolicState model is pending reconciliation (**audit P4**), we accept a simple boolean `is_operational` flag instead of importing MetabolicState directly.*

**The pointer resolves** (path tokens are their own class — every one gets checked): P4 is `docs/audits/cross-language-society-role-atp-r6-alignment-2026-05-14.md:252` — *HIGH, "Reconcile MetabolicState models (5-state vs 7-state)", Operator decision*.

But **C21 §4 closed P4 as `RESOLVED-AS-STALE` on 2026-05-29**, on the ground that spec, SDK and vectors are all at **8** states and the "5-state vs 7-state" framing was factually wrong. So a live workaround in shipped SDK code, disclosed in its own docstring, is justified by an item this lineage declared stale 74 days ago — while the divergence it actually works around is real and is tracked under a different id, **C168-N1**.

**INFO, and deliberately not charged as a defect.** Per v45, disclosed inertness is discipline, not drift: `role.py` says exactly what it is doing and why, which is why this is legible at all. The observation is about **traceability** — the code's pointer and the ledger's pointer name different rows for the same problem, so neither one leads a maintainer to the other. Recorded for the SDK track; no change proposed.

### 3.6 I-2 (INFO) — §10 says "the canonical suite", singular; there are two

`web4-standard/test-vectors/society/society-vectors.json:76-80` carries a vector named `metabolic_transition` — *"Valid metabolic state transition from ACTIVE to REST"* — plus a `metabolic_state: "active"` field at `:19`. It is loaded independently, by `test_society.py:808`, and is declared canonical for its own spec by `society.py:21`.

§10 (`:430-432`) says *"the canonical test vector suite"* and names one file. A second file drives a §3.1 transition. Nothing is contradictory — the ACTIVE→REST edge is valid in both — and nine passes tracked one vector file because one is what §10 names. Recorded so that the next pass's mirror set has two vector files in it, and so that a §3.1 change is known to require edits in two places.

**This also discharges the metabolic half of C360's deferral d4** (`C360:545-546`: *"opened only far enough to confirm the 8 state names. Never read against §1.4 or against `SOCIETY_METABOLIC_STATES.md` from this lineage"*). The vector file has now been read in full and executed against this lineage's spec (§B). The §1.4 half belongs to C400 and is untouched.

### 3.7 C21-M7 confirmed by a second, independent matcher

M7 (ontology lacks `web4:MetabolicState`) has been carried by blob identity for eight passes. The domain-word sweep re-derives it by content: `web4-core-ontology.ttl` contains exactly **two** occurrences of "metabolic", `:85` and `:179`, both `rdfs:comment` prose about the **ATP/ADP metabolic cycle**, and neither declares a class or an individual. **M7 HOLDS**, now on two independent instruments rather than one.

*Instrument correction to C21, recorded not charged*: C21's citation reads `grep -i metabolic web4-core-ontology.ttl → no class`. Run as written, that command returns **two lines**, not nothing. C21's finding is right; the shorthand for it would mislead a next auditor into thinking the grep is empty.

### 3.8 Negatives measured and published

- **§3.1 ↔ SDK ↔ CHANGELOG transition parity.** Spec §3.1 has **17** edges; `_TRANSITIONS` has **17** entries; `CHANGELOG.md:671` publishes "17 valid transitions". Three independent statements, all 17.
- **§10's descriptive arithmetic is correct in all four claims** (§B.1).
- **The SDK conformance suite is green**: 71 passed.
- **`Validated against:` at `metabolic.py:21` is BACKED** — received from C362, not re-derived.
- **The module has production callers** — `society.py:39,46` (v45 non-zero).

### 3.9 `test_conformance.py` — ruled on the file, not expanded into the tree

`test_conformance.py:692-693` describes societies as having "(genesis, bootstrap, operational) and 8 MetabolicStates", mapping "dormant/sunset phases … to metabolic states rather than phase". This is the *fourth* place the two vocabularies are reconciled in prose rather than in code. It exercises `web4-standard/testing/conformance/`, a second vector tree whose seven files include **no metabolic suite**.

**Ruled on the single file; the tree is not gated here.** `testing/` is recorded in this track's standing carry as one of six `web4-standard/` trees that has never had a gate row, and it is the **web4-lct** lineage's pre-registered first work item. Gating it from this slot would take that lineage's work. Routed, not taken.

---

## 4. §D — C324's guard checks, re-run

| Guard item | Instrument, re-run at `c23ce054` | Result |
|---|---|---|
| 3 — did `ledgers/reference/python/heartbeat_ledger.py` change or get promoted? | `git log --oneline -- <path>` → still **one commit in its entire history** (`7fb0284f`); blob `f61f3bc2` | **UNCHANGED.** M2-fail stands; do not re-file its §5.1 divergence |
| 4 — hot-tree anchors re-resolved **by content**, using the form that actually returns 4 | `git grep -nE 'society\.state\|inner\.state' -- '*.rs' \| grep -v assert` → **4** | **4 non-test consumers, all display/serialization.** C168-N1 / C284-N1 at **unchanged reach** |
| 5 — `web4-standard/README.md` `**NEW**` badges | `grep -c '\*\*NEW\*\*'` → **7** | Unchanged whole-README property. **Not re-filed**, per C324's ruling |

**v22 fires a third time, and the per-file prediction was wrong while the tree-level one was right.** C324 published `admin.rs:295` and `main.rs:1159` and predicted both would drift. At HEAD, `admin.rs:295` **held exactly**; `main.rs` moved to **`:1224`** (+65). `wasm.rs:628`/`:673` held. Six commits touched those two files in the 52-commit window while the spec took zero. The carry is confirmed at the level it was stated — *anchor half-life is a property of the anchored tree* — and refined: within a hot tree, which file moves is not predictable, so **every** hot anchor must be re-resolved by content each pass, not just the ones that moved last time.

**v36 inbound set difference.** `grep -rln` over `docs/audits/` for the target, filtered to documents postdating C324 (2026-08-06), returns exactly one: **C360** (2026-08-11). It routes `C54-B14` to this lineage as a RECEIVED row, **re-verified TRUE at HEAD** against `SOCIETY_SPECIFICATION.md:89` (`C360:462`), with the instruction not to adjudicate it from that lineage. **Received and carried below — not re-derived**, and C360's re-verification is cited rather than repeated.

---

## 5. §E — Carries ledger, full rows

**Design-Q total: 14** — C21 ×8 (H1, H3, M3, M5, M7, L4, L5, L7) + C54 ×6 (B5, B6, B7, B8, B9, B14-normative-strength). Published per C324's rule: *a ledger may collapse its narration but must publish its row count.*

| Carry | Class | Anchor | Anchor blob | State at `c23ce054` |
|---|---|---|---|---|
| **C21-H1** §2.3/§5.1 silent on Sleep `update_rate` | DESIGN-Q | spec §5.1 `:297` | `5e3f7203` | OPEN — demonstrated at C284 §3.1; cite, do not re-derive |
| **C21-H3** §5.1 single column mixes incommensurable axes | DESIGN-Q | spec `:293-302` | `5e3f7203` | OPEN — as above |
| **C21-M3** emergency-state entry only from Active | DESIGN-Q | spec §3.1 | `5e3f7203` | OPEN, held by freeze |
| **C21-M5** define "dormant" | DESIGN-Q | spec | `5e3f7203` | OPEN — couples to B15/C58-B10 |
| **C21-M7** `web4:MetabolicState` absent from ontology | DESIGN-Q | `web4-core-ontology.ttl` | `fc4b4c36` | OPEN — **re-confirmed on a second matcher this pass (§C.7)** |
| **C21-L4** Estivation 10% < Sleep 15% ordering | DESIGN-Q | spec §6.1 | `5e3f7203` | OPEN, held by freeze |
| **C21-L5** Rest queued-vs-refuse | DESIGN-Q | spec §2.2 | `5e3f7203` | OPEN, held by freeze |
| **C21-L7** §6.2 wake-penalty state coverage | DESIGN-Q | spec §6.2 | `5e3f7203` | OPEN, held by freeze |
| **C54-B5** §4.3 sentinel monitored-set — Estivation exit unfireable | DESIGN-Q | spec `:280` vs `:189` | `5e3f7203` | OPEN — re-verified TRUE at C324 §B.2; cite |
| **C54-B6** §6.1 `Society_Size` undefined + baseline units | DESIGN-Q | spec `:341` | `5e3f7203` | OPEN — re-verified TRUE at C324 |
| **C54-B7** §6.2 penalty constants 10/100/50 ungrounded | DESIGN-Q | spec `:352-356` | `5e3f7203` | OPEN — re-verified TRUE at C324 |
| **C54-B8** §7 omits Estivation + `threat_score` provenance | DESIGN-Q | spec `:366-388` | `5e3f7203` | OPEN — re-verified TRUE at C324 |
| **C54-B9** §6.2 prices a Dreaming premature-wake with no §3.1 transition | DESIGN-Q | spec §6.2 vs §3.1 | `5e3f7203` | OPEN — re-verified TRUE at C324 |
| **C54-B14** §1.4 MUST-conform vs "Proposed Standard" + §10 SHOULD | DESIGN-Q + cross-track | `SOCIETY_SPECIFICATION.md:89` | `2ad453ba` | OPEN — **re-verified TRUE by C360 this window (§D); received, not re-derived** |
| **C54-B1** SDK hibernation-wake omits `new_citizen`/90-day | CROSS-TRACK (SDK) | `metabolic.py:147` | `d3d31446` | STILL STALE by freeze |
| **C54-B3** SDK "Daily ATP Cost" vs spec §6.1 "Hourly" | CROSS-TRACK (SDK) | `metabolic.py:207` | `d3d31446` | STILL STALE — re-confirmed at `:207` this pass |
| **C54-B4** SDK Torpor `"Frozen + alert bonus"` vs spec `"Frozen"` | CROSS-TRACK (SDK) | `metabolic.py:110` | `d3d31446` | STILL STALE — re-confirmed at `:110` |
| **C54-B11** SDK comment "Rest: queued" vs `return state == ACTIVE` | CROSS-TRACK (SDK) | `metabolic.py:410-413` | `d3d31446` | STILL STALE — re-confirmed at `:410-413` |
| **C54-B15 / C58-B10** SAL §3.6 dormant list omits Rest | DESIGN-Q, two-sided | `web4-society-authority-law.md:138-141` | `0849ebbe` | OPEN, HELD — composes with C168-N1 |
| **C96-E1** ATP conservation cross-ref | CROSS-TRACK | `atp-adp-cycle.md` §3.3 | `2d060579` | HELD |
| **C168-N1 / C284-N1** `society.rs` phase enum mis-cites the 8-state spec | DESIGN-Q + publish-track | `web4-core/src/society.rs:33-48` | `17112f05` | OPEN — reach **unchanged** (§D). Now known to be one of **three** vocabularies (§C.4) |
| **C284-N2** §5.2 as absence-never-grants precedent | INFO → #580 survey | spec §5.2 | `5e3f7203` | ROUTED, awaiting #580 |
| **C324-N1** C54-B5…B9 restored to the ledger | LOW, ledger-integrity | — | — | **DISCHARGED** — all five carried as full rows above, count published |
| **C324-N2** anchor half-life (v22) | INFO, method | — | — | **CONFIRMED a third time and refined (§D)** |
| **C364-N1** §10's MUST enforced by a harness with no denominator | **MED, net-new** | `test_metabolic.py:447-448` | `bac4b18c` | **OPEN — routed to SDK track** |
| **C364-N2** unindexed integration summary contradicting the spec | **LOW-MED, net-new** | `METABOLIC_STATES_INTEGRATION_SUMMARY.md`, `README.md:49-54` | `1617db27` | **OPEN — routed to standard-owner** |
| **C364-N3** third metabolic vocabulary | INFO, routed | `entity-types.md:779-783` | — | **ROUTED to C372** — do not adjudicate here |
| **C364-I-1** `role.py` cites P4, closed stale at C21; live successor C168-N1 | INFO, traceability | `role.py:357-360` | — | Recorded for SDK track |
| **C364-I-2** second vector suite drives a §3.1 transition | INFO | `society-vectors.json:76-80` | — | Recorded; mirror set now holds two vector files |
| **C244** LCT §1.2-vs-§5 charge · **C284-N3** H1/H3 demonstration | — | — | — | **CONSUMED — do NOT re-open** |

**Refuted — do NOT resurrect**: C284-R1 (#580-vs-§5.1 dormancy-freeze); C284-R2 (2026-05-11 triage basename collision); C324's `README.md` `**NEW**`-badge charge (whole-README property, 7 instances).

---

## 6. §F — Method notes

- **v47 (proposed): a green conformance suite proves the vectors it *ran*, never the vectors it was *supposed to* run.** v45 established that a green unit test is evidence about a function, not a system. N1 is the next term: a green *suite* is evidence about its actual input, not about the input its specification publishes. The bridge between them is a **denominator assertion**, and it is a distinct artifact from both the vectors and the tests — `test_metabolic.py` loads the right file, computes the right values, compares against the right expectations, and still cannot notice that seven twelfths of its subject matter is missing. **Where a spec publishes a vector count, that count is a normative claim and needs an assertion of its own.** The general instrument: feed the harness a truncated input and see whether it still passes. It costs one script and it is the only way to measure a filter that fails open.
- **v40 has a second edge: the domain word finds artifacts the filename cannot, and the residue is where the un-audited corpus lives.** Nine passes derived this mirror set correctly and it was still incomplete, because a path-token grep is a citation-graph query and an orphan has no citations. Both of this pass's findings are in that residue, and N2 *is* the orphan — the instrument's blind spot and the defect turned out to be the same object. Corollary worth carrying: **run the sweep on the domain's word, then subtract the filename sweep, and read what is left**; and bound it by tree with a stated rule, because the domain word also reaches every sprawl tree.
- **The sibling ratio is what licenses the charge (v46, applied to itself).** N2 is filed because **6 of 7** integration summaries are indexed. At 0 of 7 the correct action would have been to route it as a corpus property, exactly as C324 did with the `**NEW**` badges and C362 did with `@context`. The ratio was measured before the finding was written, not after.
- **Received rows are cheaper than re-derived ones, and this pass took three.** C362 gave the `Validated against:` verdict; C360 gave B14's re-verification; C324 gave B5–B9's. All three are cited, none re-derived. The lineage's yield is not diminished by that — the two findings it *did* produce came from instruments no other pass had run.

**Guard for the next metabolic delta (~C404) — do NOT re-open as net-new:**

1. Target byte-frozen `5e3f7203` since `a504ea41`; **9 consecutive clean passes**. Re-baseline from **`c23ce054`** (this pass's HEAD, a verified ancestor-to-be). Publish the anchor beside the window count.
2. **Design-Q row count is 14.** A future table with fewer rows is a defect in the table.
3. **§10's four descriptive claims were verified TRUE at `855eedb5` and the suite was executed green (71 passed). Do not re-run unless the vector blob or `test_metabolic.py` (`bac4b18c`) moves — but if either moves, re-run the truncation test, not just the suite.**
4. **N1 regression check**: `grep -n "len(vectors)" test_metabolic.py`. If it still reads `>= 5`, N1 is open. If a count assertion appeared, verify it against §10's *current* 3/3/4/2 — the failure mode after a fix is the assertion and §10 drifting apart.
5. **N2 regression check**: `git grep -l "METABOLIC_STATES_INTEGRATION_SUMMARY"` — 0 means still orphaned. Re-measure the 7-file denominator with `git ls-files "web4-standard/*_INTEGRATION_SUMMARY.md"`; the ratio, not the absence, is what licenses the finding.
6. **The mirror set now holds TWO vector files** (`test-vectors/metabolic/` and `test-vectors/society/`) and the domain-word residue (23 in-standard files, `comm -23` of the two sweeps). Re-derive the residue; do not inherit this list.
7. **Every hot anchor is re-resolved by content each pass, not only the ones that moved last time** — `admin.rs:295` held while `main.rs` moved `:1159`→`:1224`. Instrument: `git grep -nE 'society\.state|inner\.state' -- '*.rs' | grep -v assert` (returns 4; a `':!*test*'` pathspec returns 7 and is wrong).
8. **Do not re-file**: `README.md`'s 7 `**NEW**` badges; the `ledgers/` §5.1 divergence; the `Validated against:` loader predicate (C362's); `entity-types.md`'s vocabulary (C372's); the `testing/conformance/` tree gate (web4-lct's).

---

## 7. §G — Post-write instrument re-run and own-error log

Every count above was re-run after this document was written, at a different scope than it was first taken.

| Claim | Re-run instrument | Result |
|---|---|---|
| residue = 23 in-standard files | `comm -23` of the two sorted sweeps | **23** ✓ (22 excluding the target) |
| 7 integration summaries, 6 indexed | `git ls-files "web4-standard/*_INTEGRATION_SUMMARY.md"` + per-file `grep -c` | **7 / 6** ✓ |
| summary is an orphan | `git grep -l METABOLIC_STATES_INTEGRATION_SUMMARY` | **0** ✓ |
| §10 arithmetic | JSON re-parse, `Counter` on id segment | 12 · 3/3/4/2 · 6 states ✓ |
| suite green | `pytest -q` | **71 passed** ✓ |
| truncation demo | direct invocation of the four test methods on cut lists | GREEN at 5, RED at 4 ✓ |
| §3.1 edge parity | parse the fenced block; `count("Transition(MetabolicState.")` | **17 / 17** ✓ |
| 4 non-test `society.state` consumers | published instrument, verbatim | **4** ✓ |

### Own-error log — 5 items, all caught before ship

1. **The scoping denominator was wrong, and the correction is what made the scope approvable.** The proposal published **"185 non-audit files"** for the domain-word sweep. It reproduces under no measurement: `git grep -li` gives 202 tracked, 147 non-audit, **28** in-standard non-audit. 185 was a `grep -rl` over the working tree carrying untracked and excluded paths, reported as if it were the sweep's denominator. **This is the C360 failure exactly** — a real number from a neighbouring query, relabelled — and it was caught by the policy reviewer, not by me. It also cuts the way v41 predicts: the corrected number *strengthened* the proposal (28 is one session's work; 185 would have been sprawl and a correct REJECT), which is the tell that the original was guessed rather than measured. **Every count in this document now carries the command that produced it.**
2. **Two sub-checks were proposed that another lineage had already discharged.** The `Validated against:` loader predicate was closed by C362 *four commits before this session started*, with an explicit instruction not to re-batch it. I proposed re-deriving it. Caught at policy review; cited as RECEIVED instead. Carry #4 — check whether your carry was discharged by someone else — fired on the pass that has it written in its own opening sequence.
3. **The sharper form of §B's question was not mine.** The proposal asked *"is §10's claim backed?"* — which C362 had answered. The policy review supplied *"does the backing enforce what §10 publishes?"*, which is N1. Recorded because the review is repeatedly the step that turns a null into a finding: C324's reviewer forced the ledger reframe that produced its whole yield, and this one did the same thing one pass later.
4. **Line-count and phrasing cells written from expectation.** The proposal said the summary was **137 lines** (`wc -l` → **136**) and that a repo-wide grep for it "returns only its own H1 line" — the filename token returns **0**; my grep had matched the *title* string via an alternation I then described as if it were the filename result. Both corrected above. Same shape as C324's §G: the numbers a finding rests on were re-measured and held, while the numbers *describing the measurement* were written from memory.
5. **The truncation's coverage consequence was stated as 4 of 8; it is 5 of 8** — caught by the post-write re-run, which recomputed the driven-state union on the cut list instead of re-reading the sentence. The first draft also carried a parenthetical that listed the same five states on both sides of a "minus", which is what an unrun derivation looks like. The finding is unaffected — N1 rests on the seven deleted vectors and the vacuous passes, both demonstrated by execution — but this is the fourth consecutive pass in this corpus where the *consequence* prose was written from expectation while the *evidence* was measured. **The rule that keeps catching it: if a number appears in a sentence, it must have been produced by a command, including numbers that merely describe a finding rather than establish it.**

---

## 8. Conclusion

Ninth consecutive frozen window on the target, and the first pass in this lineage since C54 to expand the mirror set — because it is the first to derive the mirror set with an instrument that can see an orphan.

The result worth carrying is that both findings were invisible to correct method. Nine passes ran a citation-graph query to find the target's mirrors, and a citation-graph query cannot return a document nothing cites; the standard's only unindexed integration summary was therefore guaranteed to be missed by every pass, and it is the one that drifted. And nine passes cited §10's conformance requirement without executing it; executed, its every descriptive claim is true and its enforcement mechanism cannot count — seven of twelve vectors, including the entire arm carrying the specification's only boolean MUST, can be deleted with the suite reporting green.

Neither finding is a defect in a prior pass. Both are defects in instruments that prior passes used correctly.

**Zero mutation.** 2 net-new findings routed and not applied, 2 INFO recorded, 1 row routed to another lineage, 3 guard checks closed, 3 rows received from sibling lineages rather than re-derived, 5 negatives published, and 4 of this pass's own cells corrected — one of them the denominator its entire scope rested on.

---

*Accountability self-audit: **n/a**. This pass creates no surface and causes no consequential act — it adds one document under `docs/audits/` and mutates no spec, schema, code, vector or governed state. The truncation demonstration in §B.2 was executed by passing in-memory lists to test methods; the repository's vector file was never modified. Every defect named is routed, not applied; the two items that would be consequential acts (the C168-N1 enum rename, and any edit to `entity-types.md` or `README.md`) are operator- or lineage-gated and were held out of scope before execution. Confirmed with the policy reviewer at Step 4.*

*Audit produced under Autonomous Session Protocol v2 by `legion-web4-20260811-180000`. Policy review: **REVISE** → six changes required and accepted (re-publish the denominator with its command and a pre-registered sprawl-tree exclusion rule; delete the sub-check C362 already discharged and cite it as received; adopt the harness-denominator question as the headline; rule on the two-suites question; rule on `test_conformance.py` as a single file without gating its tree; hold the routing line on other lineages' files).*
