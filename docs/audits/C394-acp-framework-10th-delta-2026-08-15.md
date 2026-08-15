# C394 — `acp-framework` 10th delta

**Date**: 2026-08-15 · **Target**: `web4-standard/core-spec/acp-framework.md` and its swept set
**Predecessor**: `C354-acp-framework-9th-delta-2026-08-10.md` (PR #686) · **Window**: `9958fc6a..0f4ebd93`
**Verdict**: **1 method finding (INFO), 1 recovered carry re-entered at LOW with a measured increment, 1 cross-lineage re-confirmation (INFO), 3 recorded negatives. ZERO mutation.**

**Revision 1 (2026-08-15, PR #719 review cycle)** — §C.2's `A \ B` cell and its stated mechanism were
false; corrected here, with the lct control's convention now published and the next-delta baseline
re-stated by domain. **Findings, severities, the UNION figure and §C.1/§C.3/§D/§F.1–F.4 are unchanged.**
Full account of what was wrong and in which direction: **§F.5**.

**Enumeration rule (stated, per the standing rule):** this lineage's members are the ten
`C{n}-acp-framework-*` documents plus the non-C-numbered
`acp-framework-internal-consistency-2026-05-28.md`. The inclusive rule is used throughout and is
applied to this pass as well as to the passes it charges.

---

## Proportionality — what this pass did and did not do

C354 §5 item 7 pre-registered: *"An empty window at C394 with no inbound residue ⇒ genuinely short
record. **The inbound sweep is not covered by that ruling** and should be run at full every pass — it
has been the entire yield six fires running."*

The window **is** empty. The inbound sweep was run at full, and it is again the entire yield — this
time not as an outside citation but as a **row this lineage lost about itself**. So: short on
re-derivation, full on the sweep.

- **NOT re-published:** C314 §C.2's 8-row corpus baseline table. It is re-derivable in one command
  against unmoved blobs; cited at `C314:170-180`, delta only published below.
- **NOT re-derived:** the `forum/nova/ACP-bundle/` declination (`C314 §C.1`) and the `forum/`+`archive/`
  exclusion (`§C.0`). Both cited, per C314 guard 1.
- **PRE-DECLARED OUT OF SCOPE before any validator ran:** `@context` / `@type` absence in the §2.x
  examples is **REFUTED-GUARD 2(b)** (`C37:264-266`, applied by C87). Declared first so the instrument
  could not argue for the finding. **REFUTED-GUARD-2(b) HELD** — no failure on other grounds was found,
  and none is reported.
- **NOT escalated:** N2's severity. See §C.2's severity note — the escalation was available and is
  declined on the record.

**Swept set — published as an enumeration, not a count word** (`git ls-files web4-standard | grep -i acp`,
9 canonical artifacts, unchanged from C354, named in full so the set cannot contract silently per C314
guard 1): `core-spec/acp-framework.md`, `ACP_INTEGRATION_SUMMARY.md`, `schemas/acp-jsonld.schema.json`,
`schemas/contexts/acp.jsonld`, `test-vectors/acp/plan-operations.json`,
`test-vectors/schema-validation/acp-jsonld-validation.json`, `implementation/sdk/web4/acp.py`,
`implementation/sdk/tests/test_acp.py`, `implementation/sdk/tests/test_acp_jsonld.py` — plus the
**declined** `forum/nova/ACP-bundle/` (21 files) and the **excluded**
`archive/reference-implementations/acp_{framework,executor,hardbound_e2e}.py` (3). All three named.

---

## §B — Window: empty on both halves

Pre-registered before measuring: span `9958fc6a..HEAD` (C354's commit → `0f4ebd93`), root = repo root,
glob = the 9 enumerated artifacts, filetypes = all.

| Measurement | Command | Result |
|---|---|---|
| Window size | `git log --oneline 9958fc6a..HEAD \| wc -l` | **28** |
| Touching the 9 acp artifacts | `git log --oneline 9958fc6a..HEAD -- <the 9>` | **0** |
| Touching `web4-standard/` at all | `git log --oneline 9958fc6a..HEAD -- web4-standard/` | **0** |
| Spec blob | `git rev-parse HEAD:web4-standard/core-spec/acp-framework.md` | `f8d7ccda`, **38 d frozen** (last touched `fb0075fc`, 2026-07-08) |
| Schema blob | `git rev-parse HEAD:web4-standard/schemas/acp-jsonld.schema.json` | `fbe09135` — unmoved since C314 |
| Context blob | `git rev-parse HEAD:web4-standard/schemas/contexts/acp.jsonld` | `08b09ffb` — unmoved since C314 |

**7th consecutive fire with both delta halves empty.**

**Instrument note, small and worth fixing at the source.** This track's memory guard records the acp
spec as *"byte-frozen 33 d at `f8d7ccda`."* `git cat-file -t f8d7ccda` returns **`blob`**, not `commit` —
`f8d7ccda` is the spec's *content* hash, and the phrasing "frozen **at** `<hash>`" reads as a commit. The
freeze identity is correct and the guard is materially right (33 d at C354 + 5 = 38 d here); only the
noun is ambiguous. Recorded so the next pass does not try to `git show` it.

---

## §A — Carry ledger: **11 rows + I-3 = 12**

Re-derived from C354 §A's table **and from C314 §C's findings** — the second half is new this pass and
is the subject of §C.1.

| Carry | C354 | C394 | Live evidence at HEAD |
|---|---|---|---|
| **M7** — int `witnessLevel` vs structured `witness_requirement` | STILL-OPEN | **STILL-OPEN** | `acp-framework.md` `f8d7ccda`, unmoved |
| **B-LEDGERPROOF / C37-5** | STILL-OPEN | **STILL-OPEN** | blob-identical |
| **N2** — `maxAtp` cumulative vs per-intent | STILL-OPEN | **STILL-OPEN** | blob-identical |
| **JSONC fences** (3 of 7) | STILL-OPEN | **STILL-OPEN** | blob-identical |
| **I-3** — `ACP_INTEGRATION_SUMMARY.md:101` `ledgerInclusion` in prose, in no ledger | STILL-OPEN | **STILL-OPEN**, now **69 days** | `3283d330`, unmoved |
| **M6** — `acp:` predicates in no TTL | STILL-OPEN | **STILL-OPEN** | `grep -c "acp:" web4-standard/ontology/*.ttl` = **0**; `web4-core-ontology.ttl` holds **zero** ACP terms |
| **B-AGENCY / L1** | STILL-OPEN | **STILL-OPEN** | MEDIUM CROSS-TRACK, unchanged |
| **B8** — ACP discharge not routed through R6 | STILL-OPEN (dispositioned inbound by `C346:418`) | **STILL-OPEN** | unchanged |
| **N4** — hub write tools carry no proof-of-agency | INFO (UNTRIPPED) | **STILL INFO (UNTRIPPED)** | `git grep -ciE "proofOfAgency\|proof_of_agency\|agency_grant" -- hub/` = **0** |
| **B11 / B12 / B13 / B14 / B15** | STILL-OPEN | **STILL-OPEN** | `errors.md` did not move this window |
| **B1-3** | re-entered by C354 N2 as row 11 | **STILL IN THE LEDGER** — C354's guard 2 answered | Not retired. C354 pre-registered "if a future pass reports 10 rows it retired it again"; this pass reports **11 + I-3** |
| **`C314-N1`** — 22 of 62 acp schema properties undefined in `contexts/acp.jsonld` | **ABSENT** | **RE-ENTERED at LOW, C314's own severity** | See §C.1 (why it was absent) and §C.2 (what it measures at HEAD) |

**Row survival 11/11; 0 closed; 1 recovered.** Ledger arithmetic changes this pass: C354 §5 item 5
pre-registered *"10 rows + I-3 = 11."* Re-entering C314-N1 makes it **11 + I-3 = 12**. Stated
explicitly so a future pass reading C354's line sees a *recovery*, not a mismatch.

**C314 guard 4 / C274-N1 — both pre-registered greps re-run, both unmoved:** `acp-jsonld.schema.json`
`witnesses` still `"items": {"type": "string"}` at **`:189`** and **`:229`**; acp↔r7 cross-references
still **0 in both directions** (`git grep -in "\br7\b"` over the 4 acp artifacts = 0; `git grep -in "\bacp\b"`
over the 4 r7 artifacts = 0).

**C314 guard 3 — the schema/context coverage re-measurement — was NOT run by C354.** It is run here.
That is §C.1.

---

## §C.1 — **N1 (INFO / method, net-new): a routed finding was lost because the carry ledger is re-derived from the predecessor's *table*, and a pass's own new findings are never written into its own table**

**The fact.** `C314 §C.2` opened a finding — *"The published ACP JSON-LD context defines none of the 22
properties belonging to the six nested value objects the standard's own schema declares"* — and
classified it **"Classification: net-new"**, **"Routed, not applied"** (`C314:205-207`). At C394 it
appears in **no carry ledger in the corpus**.

**The mechanism, which is structural and not a C354 mistake.** The ledger is a chain of
table-to-table re-derivations, and each pass's own net-new findings are born in **§C**, never written
back into its own **§A**:

| Document | What §A says about its own provenance |
|---|---|
| `C314:86` | "§A.4 — Carry ledger: **9 rows**, re-derived from **C274 §A.3's table**" |
| `C354:34` | "§A — Carry ledger: 9 rows + I-3 … Re-derived from **C314 §A.4's table**, not its prose" |

C314's §A.4 table holds the rows C314 *inherited from C274*. C314's own N1 was born two sections later
in §C.2. So when C354 re-derived from C314 §A.4's table — correctly, per
`[[feedback_prose_is_not_ledger]]` — **the table it read could not contain the row.** C354 hand-promoted
I-3 across the same gap and did not promote N1. The discipline that protects the ledger from prose is
the same discipline that drops each pass's own yield.

**A second, independent loss channel — the guard was carried forward as its own footnote.** C314's
guard 3 (`C314:258`) *is* the N1 regression check: *"**N1 regression check:** re-run the schema/context
coverage measurement over **all 11 pairings** … If `contexts/acp.jsonld` has gained terms, say which."*
C354's next-delta list item 3 reads, in full: *"**Guard 3 correction stands**: enumerate schema trees
with `git ls-files`, **never** `schemas/*.json` (12 of 24)."* That is guard 3's **instrument footnote**.
Its **substance** — re-run the coverage measurement — is gone. The guard survived as the correction to
how it should be enumerated, with nothing left to enumerate.

**Why "Discharged by freeze" is not the defect, and what is.** C354's CUT list (`C354:17`) cuts *"the
11-pairing schema↔context coverage **baseline**"* — the *measurement* — and discharges **that** by
freeze. That is correct: unmoved blobs cannot yield a different table, and C354 explicitly wrote the
cuts down *"so a later pass can see they were discharged, not dropped."* C354 never claimed to
discharge the finding. **The defect is not a mis-disposition; it is that the row had no ledger entry to
be dispositioned from.** A cut is scoped to the object it names, and the object it named was a table.

For completeness, the inversion is worth stating once, because it is what makes the row's absence
consequential rather than clerical: for a finding whose remedy was **routed to an author**, freeze is
affirmative evidence the remedy has **not landed**. The same fact that licenses cutting the
re-measurement is the fact that keeps the row open.

**Proof of loss, machine-checked, not inferred.**

1. **The row is absent from every ledger.** `git grep -nIF "C314-N1" -- docs/audits/ web4-standard/`
   returns **3 hits outside its origin, none of them a ledger row**: `C322:136` (uses it as a measured
   control), `C354:17` (the CUT list), `C390:199` (posture citation).
2. **It is live posture in a sibling lineage.** `C390:199` — **2026-08-14, one day before this pass** —
   reads *"the same posture `C314-N1` established and this pass re-verifies rather than inherits."* A
   sibling lineage treats it as live precedent while it is dead in its own lineage's ledger and guard.
3. **The downstream instrument lost it.** This track's per-file memory guard for `acp-framework` — built
   from C354 — carries `schemas/contexts/acp.jsonld` only as a swept-set member and inside the
   `grep -F` matcher guard; the phrase "schema→context pairings" appears once, dismissively, as
   "C314's OTHER 11". None of its four pre-registered C394 checks is the coverage re-measurement.
4. **The decisive one: this pass re-derived the identical defect from scratch.** §C.2's instrument
   (emitter-produced key names vs context terms) was built and run *before* the novelty matcher was
   applied, with no knowledge that C314 had measured it. The predecessor was located only by the
   novelty sweep. **A finding that a later pass in the same lineage can rediscover cold is a finding
   its ledger is not carrying** — this is `[[feedback_novelty_is_an_absence_claim]]` used as a
   detector rather than a filter.

**Classification — filed as INFO/method, not as this pass's net-new finding.** C354 set the precedent
five days ago and it binds here: `C354:125-141` (its N2 ⇒ v42) is the structurally identical act — B1-3
had fallen out of the ledger, C354 recovered it, filed **the recovery** as INFO/method, and re-entered
**the underlying row at its own severity**. Filing this pass's composite as "N1, MED, net-new" would
claim C314's finding as this pass's yield. It does not. **C314-N1 is re-entered at LOW, C314's own
rating**; the *loss* is this pass's contribution and it is INFO.

**Remedy — routed, and one part self-applied.**
- **Self-applied here (doc-only, in the audit record):** C314-N1 re-entered as ledger row 12; guard 3's
  substance restored and re-run in §C.2.
- **Routed to this lineage's convention, not applied:** §A should be re-derived from the predecessor's
  **§A table ∪ the predecessor's §C findings**. One clause. Every pass in this rotation inherits the
  same gap, so this is not an acp-local fix and is not applied unilaterally.
- **Latent naming hazard, one line, not a leg of this finding:** the acp lineage now holds two rows
  named `N1` (C314's context coverage, C354's `W4_ERR_ACP`). Zero mis-resolutions have occurred — every
  live citation uses the C-prefixed form — and `C354:241` self-disambiguates in its own sentence. Noted
  for the next pass; not charged.

---

## §C.2 — **N2 (LOW — C314-N1's severity, re-entered with a measured increment): the two instruments do not subsume each other, and the honest figure is 26**

Guard 3's substance, run. Both artifacts are byte-identical to C314, so C314's cells reproduce by
construction — **the increment is the only thing published.**

**Reproduced, not inherited.** C314's Instrument B (schema-declared properties across all `$defs`, on
its stated non-`@` convention) gives **22 of 62** at HEAD, unchanged. The four nested names the context
*does* define are `lawHash`, `grantId`, `planId`, `intentId`.

**The increment.** This pass built a second instrument — **Instrument A: the key names the SDK's four
public `to_jsonld()` methods actually emit** (`acp.py:469/:691/:821/:958`, each emitting
`"@context": [ACP_JSONLD_CONTEXT]` at `:486/:699/:829/:972`) — measured against the same 36 context
terms. **Neither instrument subsumes the other.**

**Domain, stated before the counts (v40/v49).** Instrument B walks **`$defs/X/properties` at depth 1
only** — the convention C314 used and the one every figure in this table is on. Instrument A walks the
emitted document to full depth. The two domains are not the same shape, which is exactly why the
difference set below needs a domain label rather than the word "never".

| | distinct undefined key names |
|---|---|
| **Instrument B** — schema-declared properties, **depth-1 `$defs/X/properties`** | **21** of 49 distinct names |
| **Instrument A** — emitter-produced key names, in the canonical example | **20** of 44 distinct names |
| **A \ B** — emitted, **outside Instrument B's depth-1 `$defs` domain** | **5**: `output`, `q`, `rows`, `status`, `tool` — of which only **3** (`tool`, `q`, `rows`) are undeclared at *any* depth |
| **B \ A** — schema-declared, never emitted in the canonical example | **6**: `audience`, `authorized`, `dependsOn`, `expr`, `kind`, `requiresApproval` |
| **UNION** | **26** — invariant under both conventions; a **floor**, see the tail note |

**Why A sees five things B cannot — two mechanisms, not one.** The first draft of this paragraph gave
one mechanism and it was wrong; corrected in review (§F.5).

1. **Depth-1 truncation → `output`, `status`.** These *are* schema-declared, at depth 2:
   `$defs/ExecutionRecord/properties/result` is a fully modelled object with
   `properties {status, output, resourcesConsumed}` and `"additionalProperties": false`. B misses them
   because it does not descend past depth 1, **not** because `result` is opaque. A full recursive walk
   gives **52 distinct / 23 undefined**, and the only three names recursion adds are `output`,
   `resourcesConsumed`, `status`. That `result` is closed and fully modelled *strengthens* the
   no-disclosure-defense argument below, rather than weakening it.
2. **Bare `{"type": "object"}` parents → `tool`, `q`, `rows`.** `ExecutionRecord.mcpCall` and
   `result.output` are declared `{"type": "object"}` with no `properties`, so **no walk of any depth**
   can reach their children. (The earlier draft wrote `mcpCall.args`; that is not a path in this schema
   — `mcpCall` is `$defs/ExecutionRecord/properties/mcpCall` and `args` is
   `$defs/PlanStep/properties/args`, two different `$defs`, and `PlanStep` has no `mcpCall` property.)

A JSON-LD processor expands all five against the active context exactly as it does any other key. B's
domain is *what the schema declares*; A's is *what the wire carries*. **A context must cover the union.**

**UNION 26 is a floor, and the 3-name tail is example-dependent.** The arithmetic is invariant under
both conventions — `21 + |A\B_depth1| = 21 + 5 = 26` and `23 + |A\B_full| = 23 + 3 = 26` — so the
headline does not move. But `tool`, `q`, `rows` are not emitter literals: `acp.py:978` and `acp.py:967`
pass `self.mcp_call` and `self.result_output` through as **caller-supplied free dicts**, so those names
are whatever the canonical example's author happened to write. A different payload yields a different
tail. **26 is therefore a floor with a 3-name example-dependent tail, not a settled total** — the same
canonical-example-is-a-floor caution this pass records in F.1, applied to its own table.

**Two counts for one concept — the conventions, published side by side (v61).** C314's **22** counts
**per-`$def` occurrences** over a 62-property total (36 top-level + 26 nested); this pass's **21**
counts **distinct property names** over 49. The gap is exactly one: `expiresAt` is declared in both
`Guards` and `ProofOfAgency`, counted twice by C314's convention and once by this one. **Both are
correct on their own convention and C314's stated convention is not retired** — the union figure of 26
is stated in distinct names and labelled as such.

**A control in the opposite direction, which is why this is a method result and not an acp artifact.**
`lct` fails the *other* way. **The control's convention, stated (this was the review's ask):** the **6**
is a **per-occurrence** count over the two `$defs` tensor blocks — `sub_dimensions`, `last_computed`,
`computation_witnesses` × 2 (`lct-jsonld.schema.json:303/311/315/343/351/355`), `grep -c` over
`contexts/lct.jsonld` = **0**. That is **C314:196's convention exactly** (2 `$defs` / 14 properties / 6
undefined / 57.1%), reproduced so the row is comparable to C314's table. **On the table's own domain
above — depth-1 `$defs`, distinct names — lct is 3, not 6.** Three figures for one artifact, published
side by side rather than picked between (v61):

| lct, by domain | undefined |
|---|---|
| depth-1 `$defs`, **distinct names** — the domain of the acp table above | **3** |
| depth-1 `$defs`, **per-occurrence** — C314:196's convention, the figure this control uses | **6** |
| **full recursive walk incl. top-level `mrh` `oneOf` branches**, distinct names | **7** — adds `binding_context`, `role`, `last_attestation`, `witness_count` (`lct-jsonld.schema.json:123/157/158/159`) |

**The 7 is real and is not the figure to put beside acp's 21.** On that same full-recursive domain acp's
Instrument B is **23 of 52**, not 21 of 49; quoting lct-7 against acp-21 would compare two domains, the
defect class this lineage already carries (v40/v49). The control stays on C314's convention and names it.

**Instrument A for lct — corrected, and the correction is the interesting part.** The draft said A gives
**0**. That is true **only on the canonical all-strings example**. `lct.py:576/:586` pass MRH entries
through *verbatim* (`{"lct_id": b} if isinstance(b, str) else b`), so when a caller supplies the
schema's own modelled dict form the emitter returns those keys unchanged. Executed both ways:

| `LCT.to_jsonld()` input | undefined names emitted |
|---|---|
| canonical all-strings `witnesses=[...]` | **0** |
| schema's modelled dict form, as `test_lct_jsonld.py:429/:486` supplies it | **4**: `binding_context`, `last_attestation`, `role`, `witness_count` |

So **A for lct is 0 on the canonical example and 4 on the schema's own dict form.** This is F.1's lesson
recurring one section later, in this document's own control — recorded rather than quietly fixed.

**The direction claim survives, and is restated precisely.** What carries it is not A's absolute count
but the *difference sets*, **both taken on the full-recursive domain so the comparison is same-domain**:
for lct, **A \ B = 0** (every name the emitter produces, dict form included, is schema-declared at some
depth) while **B \ A = 3** (`sub_dimensions`, `last_computed`, `computation_witnesses` are declared and
emitted by no code path — `git grep -nI` over `web4-standard/implementation/sdk/` returns hits only in
`web4/schema_registry.json`, the bundled *copy of the schema*, and **zero in any `.py` module**). acp is
the mirror on the same domain: **A \ B = 3**, **B \ A = 6**. **acp declares less than it emits; lct
emits less than it declares.** Neither
instrument alone can rank the corpus.

**Severity — LOW, and the available escalation is declined on the record.** `C314:205` bounded this
LOW *"by the consumption mechanism (v13): nothing in the repo expands ACP JSON-LD to RDF … **Latent,
not a live failure**."* Re-verified at HEAD: `git grep -lIE "pyld|jsonld\.expand|rdflib" -- web4-standard/`
returns only the two MRH scripts, neither touching acp; canonical `.rq` count under `web4-standard/`
is **0**. `C390:196-203`'s two-count escalation template (live emission path + unwatched) was available
and is **declined**: the emission-path leg is real (§C.2's four `to_jsonld()` sites) but C314 knew it and
still rated LOW, and the *unwatched* leg is **cured by this pass re-entering the row** — escalating on a
condition this document removes would be circular. **Breadth is not consumption.** LOW stands.

**Remedy — routed to the standard author, unchanged from C314, not applied here.** The fix forks three
ways (add the terms / add scoped `@context` blocks to `steps`/`guards`/`proofOfAgency`/`mcpCall`/`result` /
ratify that nested value objects are deliberately opaque and say so), and C314 already ruled it
corpus-shaped — `lct.jsonld` (6) and `r7-action.jsonld` (2) carry the same class, so a per-file fix at
acp's slot would leave the pattern half-addressed. **No disclosure defense is available:**
`git grep -nIiE '"@json"|opaque|free-?form|not modell?ed'` over the spec, the schema and the context
returns **0** — the corpus discloses deliberate inertness elsewhere (v45/v57) and does not here; and the
schema sets `"additionalProperties": false` on `Guards`, `PlanStep` and the rest, i.e. it treats them as
**closed, fully-modelled** objects the context does not define at all.

---

## §C.3 — **N3 (INFO, explicitly NOT net-new): `C322-N3` re-confirmed at HEAD by a third lineage, with the mutation run**

Surfaced independently by this pass's v36 residue and identified as a predecessor by the novelty
matcher. **`C322-N3`** (`C322:307`, dictionary lineage) charged `web4-standard/implementation/sdk/web4/validation.py`
for resolving the bundled registry *ahead of* both documented overrides; **`C362:179`** re-verified it
HOLDS. This is the **third** confirmation and the first from a lineage that reached it by a different
route.

**Mutation run — a plausible wrong value, not a sentinel (v59).** A temp directory was populated with
all 12 canonical schemas and `AgentPlan.required` was extended with `expiresAt` — a real ACP guard
field, a change a genuine schema revision could make:

| probe | result |
|---|---|
| `get_schema_dir()` with `WEB4_SCHEMA_DIR=<tmp>` | returns **`<tmp>`** — the override is honoured |
| `get_schema("acp")` with the same env var | `AgentPlan.required` **without** `expiresAt` — bundled copy |
| `get_schema("acp", schema_dir=Path("<tmp>"))` — the **explicit argument** | `AgentPlan.required` **without** `expiresAt` — bundled copy |

`validation.py:220-224` consults the registry before the directory branch; `:8-12` documents
`WEB4_SCHEMA_DIR` as priority **1**; `:283` documents `schema_dir` as *"Override schema directory."*
**The severity multiplier this pass adds, in one line:** `get_schema_dir()` *does* return the override,
so the diagnostic function confirms an override the validator is not using. **Not re-charged — the row
belongs to the dictionary lineage.** Reported so C322-N3's disposition record shows a third
independent confirmation and an SDK-track routing that has now been open 9 days.

---

## §D — Negatives, recorded

A negative is publishable evidence; recording them is what makes the positives interpretable (v36).

| Check | Command / method | Result |
|---|---|---|
| acp SDK suite | `pytest tests/test_acp.py tests/test_acp_jsonld.py -q` | **139 passed** — C354's baseline, unchanged |
| Full SDK suite | `pytest -q` | **2750 passed, 5 xfailed** |
| acp schema-validation vectors, **executed** against the canonical schema | 12 `valid` + 24 `invalid` through `Draft202012Validator` | **12/12 pass, 24/24 fail as specified. 0 anomalies** |
| Can that harness count? (v47) | read `test_schema_validation_vectors.py:57-58` — `if not os.path.exists(path): continue` **fails open** | **Guarded in aggregate**: `TestVectorCoverage` asserts 92 / 186 / **278** and `test_all_schemas_covered` requires every mapped schema to contribute both arms. A *rebalance* between files would survive; a *deletion* would not. Recorded as a negative — the guard-can-count question has a real answer here |
| SDK bundled registry vs canonical schemas | all 12 keys `json.load`-compared, **executed not read** | **12/12 byte-equal.** The registry bundles exactly the 12 top-level schemas |
| Schema tree enumeration (C354 guard 3, footnote half) | `git ls-files 'web4-standard/schemas/*.json'` = **24** vs `ls web4-standard/schemas/*.json` = **12** | **Correction holds** — git's `*` crosses `/`; the 12 extra are the `presence-protocol/` tree |
| `W4_ERR_ACP` (C354's N1 regression check) | `git grep -nE 'W4_ERR_ACP"' -- web4-standard/` | **1 hit** — `acp.py:80`, the baseline. **No change ⇒ C354-N1 STILL-OPEN**, spec §10.1 has not gained it and the SDK has not dropped it |
| ACP terms in the canonical ontology (M6) | `grep -i "ACP_\|AgentPlan\|ExecutionRecord\|proofOfAgency" web4-standard/ontology/web4-core-ontology.ttl` | **0** — M6 unchanged |

---

## §E — Evidence, built by capture

**v36 inbound sweep as a set difference, verb set pre-registered before running, searched by the
domain's word rather than the target's filename** (a path-token sweep is a citation-graph query and
cannot return an orphan).

- **Domain tokens (pre-registered):** `Agentic Context Protocol` (30 files), `AgentPlan` (44),
  `ExecutionRecord` (44). Union = **68**.
- **Filename sweep:** `git ls-files | grep -i acp` = **45**.
- **Residue** (`comm -23`, domain \ filename) = **34 rows**. Reverse difference = **0**.
- **What the residue yielded.** Two rows carried this pass entirely, and neither is reachable by a
  filename sweep: `web4-standard/implementation/sdk/web4/{generate,deserialize,validation,mcp_server}.py`
  and `schema_registry.json` — the SDK's **generic** layer, which produces and validates every ACP
  document while containing the string "acp" only as a lowercase schema key. **Nine acp passes swept
  nine filename-matched artifacts; the emitter has never been in the set.** §C.2's Instrument A and
  §C.3 both live there.
- **Row postdating the predecessor:** `docs/audits/C376-security-framework-9th-delta-2026-08-13.md:207`
  cites `core-spec/acp-framework.md:43` and `schemas/acp-jsonld.schema.json $defs/AgentPlan` as a
  *worked control* for a `principal`+`agent` requirement. **Inbound, verified, no defect** — it uses acp
  correctly and asks nothing of this lineage. Recorded because "residue rows that postdate the prior
  pass are where the yield is," and this time the answer is a clean citation.

**Novelty matcher, published beside the claim** (v44 — and it fired twice this pass, which is the
point): tokens `WEB4_SCHEMA_DIR`, `schema_registry`, `get_schema_dir`, `@vocab`, `dropped on expansion`,
`undefined term`, `acp.jsonld` (**`grep -F`**, per this lineage's standing matcher guard — the regex form
matches `acp-jsonld` and returns 11 instead of 0), scoped to `docs/audits/` at HEAD.

- `WEB4_SCHEMA_DIR` → **2 audits** → `C322-N3`, `C362:179`. **Killed a drafted net-new finding.**
- `dropped on expansion` → **1 audit** → `C350:159`. Class precedent, sibling lineage.
- `acp.jsonld` (`-F`) → **3 audits** → C314, C354, C390. **Killed a second drafted net-new finding** and
  turned it into §C.1.

**Both of this pass's initial "net-new" candidates were falsified by its own novelty matcher.** What
survived is a smaller, truer thing: the *loss* of one of them, and a 5-name increment to the other.

**Not mechanically reproducible: one row, labelled in place.** §C.2's expansion claim is stated as a
*term-coverage* measurement (emitted/declared key names vs context terms), which is fully machine-checked.
The consequence — that a conformant JSON-LD 1.1 processor **drops** the undefined keys — is
**hand-derived from the context files' `@`-level keys** (no `@vocab`; `git grep -nIF '"@vocab"' -- web4-standard/`
= 9, all in the MRH tree, none in `schemas/contexts/`). **`pyld` is `ModuleNotFoundError` on this host**,
so the expansion half is labelled non-machine-checked, per C310 method note 3 and C350's precedent.

---

## §F — Instrument corrections

**F.1 — this pass's own published denominator was falsified in policy review, and the correction is
load-bearing.** The proposed scope published: *"23 SDK-generatable JSON-LD types measured against their
contexts — **17 at zero undefined** … so this is not the corpus idiom."* The reviewer produced `lct` as
a **7th** exception. Re-derived: the headline was measured on
`web4.generate.generate(<type>)` — the SDK's **canonical example** for each type — and
`generate("LinkedContextToken")` emits **`trust_tensor: null`**, omitting the tensor block entirely. So
the instrument **could not detect the standard's second-worst row by construction**, and its domain rule
was never published. **The corpus-idiom inference has been re-derived on C314's Instrument B and the
Instrument A figure is demoted to a corroborating floor with its domain rule stated in §C.2.** A
generator's canonical example is a floor, not a type's emission surface.

**F.2 — the reviewer's own correction is half wrong, and the half that is wrong is the same conflation
it warned against.** The review asserted *"`web4/lct.py` has `to_jsonld` … the names `sub_dimensions`,
`last_computed`, `computation_witnesses` are all three undefined … = **6 undefined**"* — attributing them
to the SDK **emitter**. `git grep -nI "sub_dimensions\|last_computed\|computation_witnesses" -- web4-standard/implementation/sdk/`
returns hits **only** in `web4/schema_registry.json`, the bundled *copy of the schema* — **zero in any
`.py` module**. The names are schema-declared (`lct-jsonld.schema.json:303/311/315/343/351/355`) and
never emitted. The reviewer read them out of Instrument B and attributed them to Instrument A: the
precise conflation its own point 5 asked this pass to avoid. **The reviewer's conclusion survives its
faulty evidence** — `lct` *is* a 7th exception under B, F.1 stands — and the error is what produced
§C.2's opposite-direction control. Verified rather than accepted (v52).

**F.2 scope note, added in the correction cycle.** F.2 is measured on the **3-name set**
(`sub_dimensions`, `last_computed`, `computation_witnesses`) and on that set it stands unchanged: those
three are schema-only and no `.py` module emits them. It does **not** generalize to the 7-name
full-recursive set — 4 of those 7 *are* emitter-reachable (§C.2, F.5). F.2's claim is that the reviewer
attributed *those three* to Instrument A; that remains true and the correction remains correct.

**F.3 — the memory guard's freeze citation.** See §B: `f8d7ccda` is a **blob**, not a commit. Noun
corrected at the source; no measurement changes.

**F.4 — C354's ledger-count line will read as a mismatch.** `C354:247` pre-registered "10 rows + I-3 =
11." This pass reports **11 + I-3 = 12**. The delta is the C314-N1 recovery, not an inflation. Stated in
§A and repeated here because C354's own guard 2 instructs the next pass to treat a *falling* count as a
retirement — a *rising* count needs the same explicit accounting.

**F.5 — the correction cycle, and what the false cell actually was.** PR #719 was returned CHANGES
REQUESTED on one cell of §C.2's table. The block is accepted in full and every claim in it was
re-derived from the artifacts before being applied (v52). What was wrong:

| draft claim | corrected | how |
|---|---|---|
| A\B = "emitted, **never schema-declared**", 5 names | 5 names outside B's **depth-1 `$defs` domain**; only 3 undeclared at any depth | `result` = `{status, output, resourcesConsumed}`, `additionalProperties: false` |
| B is blind because `result.output` is a bare object | B is blind by **depth-1 truncation**; the bare-object mechanism is real but explains only `tool`/`q`/`rows` | recursive walk = 52/23, adding exactly `output`, `resourcesConsumed`, `status` |
| `mcpCall.args` | not a path — `mcpCall` ∈ `ExecutionRecord`, `args` ∈ `PlanStep` | `PlanStep` has no `mcpCall` property |
| lct control "6", convention unstated | convention stated; 3 / 6 / 7 published by domain | see §C.2 |
| lct "Instrument A gives **0**" | **0** on the canonical example, **4** on the schema's dict form | executed both ways; `lct.py:576/:586` pass MRH dicts through verbatim |

**Direction of the error, stated because it is the part that propagates:** "never schema-declared" made
the schema↔context gap look **wider** than it is, and made Instrument B look **better characterized**
than it was. Both read as *more* verified, not less — the direction that survives a skim.

**Unchanged, and stated so the next pass reads a correction and not a re-measurement:** **UNION = 26**
(invariant under both conventions, now labelled a floor), **severity LOW**, the **declined escalation**,
**N1**, **N3**, **§D**, **§F.1–F.4**. Nothing in §C.1 is touched.

**Why the fix took a cycle rather than a note.** §C.2 is the table that re-enters `C314-N1` as ledger
row 12, and this document's thesis is that the next pass re-derives from its predecessor's *table* and
inherits whatever the cell says. A false cell **in this table** is the document's own failure mode,
propagating through the channel it exists to document.

**Policy review falsified a published number for the 13th consecutive pass.** The scope submitted was a
measured premise, not a plan; the review killed the headline denominator (F.1), convicted the
"MED / net-new" label (§C.1's classification), and demoted the label-collision claim to one line. All
three corrections are applied. The review's own factual error is recorded in F.2.

**14th, on the correction cycle itself.** The correction scope was submitted as six measured premises.
Five confirmed; **premise (f) — "Instrument A for lct = 0" — was falsified by execution**, and the
falsifier is F.1's own lesson: the 0 was read off the all-strings canonical example while the emitter
passes caller-supplied dicts straight through. The review also caught that swapping the lct control
6→7 without moving acp's B to 23/52 would have manufactured a fresh cross-domain comparison, and that
"§F needs no change" was itself false (hence the F.2 scope note). **A method note worth carrying: when a
reviewer's COUNT does not reproduce, check their ITEMS, not your count.** This pass's own verification
walker returned 3 against the reviewer's 7 and would have returned 3 forever — it did not descend
`oneOf`/`anyOf`/`allOf`, the same truncation-shaped blind spot as the instrument it was checking. One
line — *is `binding_context` in the context? no* — inverted the verdict. An item is checkable against
the artifact atomically; a count is only ever as good as the walker behind it.

---

## Next-delta (C434) checks — pre-registered

1. **Is `C314-N1` still in the ledger?** It is re-entered here as row **12** at LOW. **If a future pass
   reports 11 rows or fewer, it has been retired a second time — check the deflation, not the count**
   ([[feedback_ledger_emptied_not_closed]]). One grep: `grep -c "C314-N1" <that pass's doc>`.
2. **Guard 3, substance not footnote.** Re-run the coverage measurement on **both** instruments and
   publish the union — **and state the walk domain before the number** (§C.2, F.5). Baseline at HEAD,
   blobs `fbe09135` / `08b09ffb`:
   - **B, depth-1 `$defs/X/properties`** (C314's convention): **21 distinct / 22 per-`$def` occurrences**, of 49
   - **B, full recursive walk** (incl. `oneOf`/`anyOf`/`allOf`): **23** of 52 — the 2 extra are `output`, `status`
   - **A**, canonical example: **20** of 44 · **UNION = 26 under either convention**, a floor
   - **lct control**: **3** (depth-1 distinct) / **6** (depth-1 per-occurrence, C314:196) / **7** (full recursive); A = **0** canonical, **4** on the dict form

   If either blob has moved, the gap may have widened without anyone touching the context. **Carrying
   only the enumeration footnote is what lost this row once already** — and carrying a count without its
   domain is what cost this pass a review cycle.
3. **C354-N1** (`W4_ERR_ACP`): `git grep -nE 'W4_ERR_ACP"' -- web4-standard/` — **1 hit at HEAD is the
   baseline; any change is the answer.** Still open.
4. **C274-N1's two greps** — schema `witnesses` widening (`:189`/`:229`) and acp↔r7 cross-refs. Both
   still **NO**. One-liners, keep them.
5. **Sweep the SDK's generic layer, not just the filename set.** `generate.py`, `deserialize.py`,
   `validation.py`, `mcp_server.py`, `__main__.py`, `schema_registry.json` are now **in acp's swept set**
   and may not contract back out silently (C314 guard 1 form). They are invisible to
   `git ls-files | grep -i acp` and they carried this pass.
6. **REFUTED-GUARDS all still standing, none re-opened:** (a) C37's `ledgerInclusion` count → `C286:115`;
   (b) `@context` absence in §2.x examples → `C37:264-266`, applied by C87 — **pre-declare it out of
   scope BEFORE running any example validator**; (c) `ns/` vs `ontology#` → declined at `C310:163`.
   C274's bare-string `witnesses` guard likewise.
7. **Matcher guard, still live:** `grep -F` for `acp.jsonld`; the regex form matches `acp-jsonld` and
   returns 11 instead of 0. And exclude this pass's own document from any coverage grep.
8. **Two rows named `N1`** in this lineage (C314's, C354's). Not charged; disambiguate by C-prefix.
9. **Proportionality:** the window has now been empty **7 fires running**. The inbound sweep remains
   uncovered by any no-op ruling and should be run at full — it has been the entire yield **seven** fires
   running, and this pass is the first time it returned a row about *this lineage's own bookkeeping*.

---

## Accountability self-audit

```
surface: C394 audit document   act: publish an audit record; re-enter a ledger row; route two remedies
S: low/reversible [construct: doc-only; docs/audits/ is append-only record, no governed state mutated]
R: n/a [construct: no caller-driven path created]   W: n/a [construct: no identity/authority asserted]
O: pass [construct: policy review (Step 4) completed and REVISE applied before the document was written; rev1's corrections were policy-reviewed before any edit, and premise (f) was falsified there — see F.5]
A: pass [construct: every count carries its command; §F records this pass's own falsified number and the reviewer's]
V: n/a [construct: reversible, low-consequence; both substantive remedies ROUTED, not applied]
verdict: PASS
```

**ZERO mutation outside `docs/audits/`. 1 new file.**
