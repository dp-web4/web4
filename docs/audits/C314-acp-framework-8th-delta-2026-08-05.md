# C314 — ACP Framework Eighth-Delta Re-Audit

**Date:** 2026-08-05
**Auditor:** Autonomous session `legion-web4-20260805-000032`
**Document audited:** `web4-standard/core-spec/acp-framework.md` (710 lines, blob `f8d7ccda`, last moved `fb0075fc` 2026-07-08 — **28 days byte-frozen**)
**Window:** `git rev-list 83467c36..HEAD` = **61 commits**, HEAD `e8005332`
**Method:** §A hand-verification at live HEAD, every anchor re-grepped rather than inherited. §B refute-by-default finder pass over the window. §C the artifact-tree sweep the previous eight passes did not run.
**Lineage:** C18 (#244) → C37 (#283) → C86 → C87 (#378) → C125 → C126 (#437) → C158 (#485) → C159 (remediation, #487 `fb0075fc`) → C196 (5th, 0 net-new) → C234 (6th, 0 net-new) → C274 (7th, #583) → **C314** (this 8th delta).

---

## Result

**1 LOW net-new · 3 INFO · 3 REFUTED · ZERO mutation of `web4-standard/`.**

**The flagship was refuted**, and refuted by a ruling the corpus had already made on an identically-shaped claim ten passes earlier. It is written up in full in §C.4 because a candidate that had to be killed by corpus precedent is the most useful thing this pass produced.

---

## Instrument note — the window is not the yield surface

| Artifact | Last commit (all time) | Commits since `fb0075fc` |
|---|---|---|
| `web4-standard/core-spec/acp-framework.md` | `fb0075fc` 2026-07-08 | **0** |
| `web4-standard/schemas/acp-jsonld.schema.json` | `6300d34a` 2026-03-21 | **0** |
| `web4-standard/schemas/contexts/acp.jsonld` | `6300d34a` 2026-03-21 | **0** |
| `web4-standard/test-vectors/acp/` | `4cbb66ce` 2026-03-14 | **0** |
| `web4-standard/test-vectors/schema-validation/acp-jsonld-validation.json` | `3495e135` 2026-03-22 | **0** |
| `web4-standard/implementation/sdk/web4/acp.py` + `tests/test_acp*.py` | `759eaefa` 2026-04-17 | **0** |
| `web4-standard/ACP_INTEGRATION_SUMMARY.md` | `99eaf021` 2025-09-15 | **0** |
| `forum/nova/ACP-bundle/` (9 files) | `3041e7aa` 2025-09-15 | **0** |
| `archive/reference-implementations/acp_{framework,executor,hardbound_e2e}.py` | `65cd5488` 2026-04-11 | **0** |

Of the window's 61 commits, **2 touch `web4-standard/`** (`8d3808db` #637, `01f410db` #581) and **0 touch any acp artifact**
(`git log --oneline 83467c36..HEAD -- <the 9 paths above>` = 0).

This is the exact configuration method carry **v13** names as the one in which a false clean is most likely. So the pass was pointed at the artifact tree, and the entry question was **coverage**, measured before anything else:

| Artifact | Named in how many of `docs/audits/**` | Matcher (all `grep -rlF … docs/audits/ \| grep -v C314`) |
|---|---|---|
| `ACP_INTEGRATION_SUMMARY` | **5 files** | `-F "ACP_INTEGRATION_SUMMARY"` |
| `acp.jsonld` (the published context) | **0 files, ever** | `-F "acp.jsonld"` — bare string, not just the `contexts/` path |
| `ACP-bundle` | **0 files, ever** | `-F "ACP-bundle"` |
| `acp-spec` (the bundle's own spec doc) | **0 files, ever** | `-F "acp-spec"` |

Scope `docs/audits/` at HEAD `e8005332`; all four re-run **after** this document was written, with two corrections forced by that re-run:

- **Self-collision.** This document is itself in `docs/audits/`, so the unfiltered counts became 6/12/1/1 the moment it was written. The figures above exclude it ([[feedback_ledger_emptied_not_closed]] — baseline every label grep against its collider).
- **The matcher had to change from regex to fixed-string, and this is the more useful correction.** `grep -rl "acp.jsonld"` returns **11** files, not 0 — the `.` is a regex wildcard, so it also matches **`acp-jsonld`**, i.e. `schemas/acp-jsonld.schema.json`, which 11 audit docs do discuss. The context and the schema differ by a single character, and the careless matcher silently reports the schema's well-covered history as the context's. `grep -rlF "acp.jsonld"` = **0**. Per [[feedback_enumeration_and_grep_hypotheses]] a tight grep is a hypothesis that fails silently; here a *loose* one would have certified coverage that does not exist and closed this pass clean.

**Two acp artifacts had never been read in eight passes**, one of them a complete parallel ACP specification. That, not the window, is what justified a full pass rather than the short NO-OP record C274's proportionality ruling would otherwise have required.

## Authority Hierarchy

Unchanged from C125/C158/C196/C234/C274: vectors → schema → SDK → spec prose; canonical neighbor owns its primitive. `forum/` and `archive/` excluded — see §C.0.

---

## §A — Delta Re-Verification

### §A.1 — C159's three applied edits: all **HELD**, 0 regressions

Spec byte-frozen, but every locus re-grepped at live HEAD per [[feedback_prior_finding_path_provenance]]:

| Edit | Locus | Live state at HEAD | Cross-anchor re-verified |
|---|---|---|---|
| **C156-5** softened trust-gaming cell | `:418` | `Audit adjustments (reputation staking is a future mechanism — see reputation-computation.md §10)` | `reputation-computation.md` `## 10. Future Evolution` **L835**, `### Reputation Staking` **L845** — unmoved since C274. Section-cite, line-shift-immune. **HELD** |
| **N1** WitnessDeficit re-cite | `:568` | `#   - runtime-count deficit (approval-gate phase, §3.2/§5.2): too few` | acp §3.2/§5.2 live. **HELD** |
| **N3** grant-path correction | `:254` | `if exceeds_caps(intent, grant.scope.r6Caps.resourceCaps):` | `entity-types.md` `"r6Caps"` **L377** / `"resourceCaps": {"max_atp": 25}` **L379** — byte-identical to what C274 recorded. **HELD** |

**[[feedback_remediation_introduced_regression]] check: CLEAN.** Spec byte-frozen; nothing to introduce. **No recorded-path drift this pass** — all three C274 anchors resolved on the first grep.

### §A.2 — C87's 8 fixes / 13-transition count

Byte-frozen since verified HELD at C158; SDK `VALID_TRANSITIONS` frozen. Not re-litigated (unchanged input).

### §A.3 — C274-N1's two pre-registered regression greps: **both answered, no movement**

C274 filed N1 (the AAEP non-join) to the author and pre-registered two one-grep regression checks for this pass. Both run at HEAD:

1. **Did the schema's `witnesses` widen?** **NO.** `acp-jsonld.schema.json` `:189-192` (Decision) and `:229-232` (ExecutionRecord) both still `"items": { "type": "string" }`. Unchanged.
2. **Did acp gain an r7 §1.7 cross-reference?** **NO — still 0 in both directions.** `grep -c "r7-framework\|r7 " web4-standard/core-spec/acp-framework.md` = **0**; `grep -c "acp-framework" web4-standard/core-spec/r7-framework.md` = **0**.

C274-N1 therefore **STANDS UNCHANGED**, still routed to the author, not re-litigated here.

### §A.4 — Carry ledger: **9 rows**, re-derived from C274 §A.3's table

Re-derived from the table, not from prose ([[feedback_prose_is_not_ledger]]).

| Carry | C274 state | C314 state | Live evidence at HEAD |
|---|---|---|---|
| **M6 / B-M6** — `acp:` predicates in no TTL | STILL-OPEN | **STILL-OPEN — premise survives, two counts corrected (see I-2)** | `grep -c "acp:" web4-standard/ontology/*.ttl` = **0**, unchanged |
| **M7** — integer `witnessLevel` vs structured `witness_requirement` | STILL-OPEN | **STILL-OPEN** | Split live: int at `:81`/`:316`/`:605`, structured object at `:329`. SDK integer-only. SDK bridge |
| **B-AGENCY / L1** — `web4_context` proofOfAgency casing/field-set | STILL-OPEN | **STILL-OPEN** | mcp-owned envelope; mcp byte-frozen. MEDIUM CROSS-TRACK |
| **B-LEDGERPROOF / C37-5** — §4.2 `ledgerProof` | STILL-OPEN | **STILL-OPEN, reach UNCHANGED** | Sole in-doc ledger object (`:281-285`); SDK `ProofOfAgency` has none; schema `additionalProperties:false`. **Explicitly did NOT gain reach this pass — see §C.4 R-C** |
| **B8** — ACP discharge not routed through R6 | STILL-OPEN | **STILL-OPEN** | atp-adp §7.1 #5 live; acp §9.1 MUST list has no R6-discharge item. CROSS-TRACK |
| **N2** — `maxAtp` "budget"/cumulative vs SDK per-intent-only | STILL-OPEN | **STILL-OPEN (unchanged)** | acp `:174` "against the plan's `resourceCaps.maxAtp` budget"; SDK `check_atp` **acp.py L213-217** still `return atp_amount <= self.max_atp`. SDK frozen ⇒ divergence unchanged |
| **N4** — hub MCP write tools carry no ACP proof-of-agency | INFO (UNTRIPPED) | **STILL INFO (UNTRIPPED)** | The hub moved heavily this window (~25 commits: atomic-write sweep, plane split, ledger integrity, XSS fix, A2 receipt v3). **No mover admitted a non-operator agentic caller to a write tool.** Re-checked, not inherited |
| **B11 / B12 / B13 / B14 / B15** | STILL-OPEN | **STILL-OPEN** | No mover touched errors §10.1 envelope, SAL witness vocab, or the D0 cluster |
| **JSONC fences** | INFO-corpus | **INFO-corpus, unchanged** | **3 of 7** `json` fences fail strict parse — **re-measured, not inherited** (`json.loads` over each ```` ```json ```` block: fences 1, 3, 6 fail; 2, 4, 5, 7 parse). Matches C126/C158/C234/C274 exactly. Corpus-wide operator DESIGN-Q |

**0 rows closed, 0 rows opened, 0 regressions.** Row survival 9/9 — per [[feedback_ledger_emptied_not_closed]], recorded so a future clean streak cannot be mistaken for an emptying ledger.

---

## §B — Window pass

**61 commits.** Each inbound gated before it was allowed to yield. Only one is subject-matter-adjacent:

| Commit | Artifact | Disposition |
|---|---|---|
| **`8d3808db` (#637)** | `web4-standard/test-vectors/validate_context_refs.py` — new standard-level CI gate: every `https://web4.io/contexts/<n>.jsonld` referenced under `test-vectors/` must have a backing file | **Applied to acp. acp PASSES** — see §B.1 |
| `01f410db` (#581) | `ontology/` — `web4:Tensor` superclass + `web4:observationCount` | No acp reach. `grep -c "acp" web4-standard/ontology/*.ttl` = 0 |
| ~25 hub commits | `hub/` hardening | Gated against carry N4 (§A.4). None admits an agentic caller to a write tool |
| 19 C-series audit docs | `docs/audits/` | Read for cross-doc carries routed here ([[feedback_cross_doc_carry_inbound]]). **C310 §C and C286 `:115` both bear on this pass and both killed a candidate** — §C.4 |
| 3 Publisher passes, 2 whitepaper, 4-life | — | Below altitude |

### §B.1 — The new context-ref gate, run against acp

```
$ python3 web4-standard/test-vectors/validate_context_refs.py
Scanned test-vectors/**: 283 web4.io context references, 9 distinct context names
  acp.jsonld    OK  (34 refs, 1 files)
  ...
ALL REFERENCED CONTEXTS BACKED (except 1 carried: t3v3.jsonld)
```

**acp PASSES: 34 references, backed.** The SDK (`acp.py:71 ACP_JSONLD_CONTEXT = "https://web4.io/contexts/acp.jsonld"`) and the vectors agree on the URI, and it resolves to `schemas/contexts/acp.jsonld`. Recorded, not fixed — greening a gate by editing a vector would be mutation of `web4-standard/`, which this pass forbids.

---

## §C — Artifact-tree sweep (the eight passes that did not run it)

### §C.0 — Exclusion rule, pre-registered before the sweep

`forum/` and `archive/` are excluded by a **standing corpus rule that predates this lineage's first delta**:

- `docs/audits/sal-internal-consistency-2026-05-27.md:310` — "this file is in `forum/nova/`, not in the canonical ontology directory, **so it is not authoritative**"
- `docs/audits/C23-…-2026-05-30.md:408` — `forum/nova/web4-sal-bundle` "(pre-C16 draft material) … **out of scope**"
- Codified verbatim at `C300-…:85` — *"(archive/ and forum/ excluded by standing rule)"*; repeated `C298:112`, `C298:222`, `C286:246`

`archive/reference-implementations/acp_{framework,executor,hardbound_e2e}.py` (1292 + 1299 + 510 lines, frozen `65cd5488` 2026-04-11) are therefore **excluded, recorded, not silently dropped.** Their single live pointer is noted: `archive/reference-implementations/rdf_ontology_consistency.py:322` loads `forum/nova/ACP-bundle/acp-ontology.ttl` — an excluded-tree file consumed by an excluded-tree script.

The exclusion is recorded *with* its citation rather than asserted, because this lineage has been quietly contracting its mirror set (v8): `archive/` appears in **0 of C196/C234/C274** with no rule stated either way — the C312-N3 shape.

### §C.1 — `forum/nova/ACP-bundle/` — **DECLINE row, published for the first time in nine passes** (I-1, INFO)

Enumerated here so that a later pass cannot mistake nine consecutive silences for coverage. Per [[feedback_frozen_parallel_spec]] (C74) the lifecycle question is answered first; the line-diff was never run.

**Ruling: SUPERSEDED. Frozen inbound Nova proposal, not a competing specification.**

| Test | Evidence |
|---|---|
| Provenance | `README.md`: `**Generated:** 2025-09-15T15:27:37.121413Z`. A generated dump, added once (`3041e7aa`), never touched again |
| Canonical successor exists, and is later | `web4-standard/schemas/acp-jsonld.schema.json` + `schemas/contexts/acp.jsonld` created `6300d34a` **2026-03-21, six months after** the bundle, inside the normative tree, same subject matter |
| The outward citation | `web4-standard/ACP_INTEGRATION_SUMMARY.md:239` lists `[ACP Bundle](../forum/nova/ACP-bundle/)` under `## References`. Bundle committed `3041e7aa` **08:29:32**; the summary `99eaf021` **08:34:20** — **five minutes later**. This is the integration *record* pointing at its own source material, not normative incorporation |
| **It disagrees with itself** | The bundle ships **two** ExecutionRecord schemas. `ACP.ExecutionRecord.schema.json` → `required: [type, intentId, grantId, lawHash, mcpCall, result, ledgerInclusion]`; `ExecutionRecord.schema.json` → `required: [type, intentId, grantId, lawHash, mcpCall, result]`. Otherwise identical. All four entity types are duplicated `ACP.X`/`X` this way. A generated dual-emission its own generator did not reconcile — [[feedback_does_the_impl_agree_with_itself]] applied to the bundle kills the "second specification" reading before any comparison with the standard is reached |
| Live consumers | **One**, itself in an excluded tree (`archive/…/rdf_ontology_consistency.py:322`). Nothing executes or tests the bundle |

**Class: coverage/instrument row under the existing `B-D1` / [[feedback_frozen_parallel_spec]] carry. NOT net-new.** The corpus has ruled this class repeatedly — `C182:78`, `C220:90`, `C258:82`, `C298:112` on `forum/nova/…/initial-registries.md`; `C270:59`, `C286:115`, `C310:419`, `C294:262` on `forum/nova/web4-sal-bundle/` — every time as *sync-vs-supersede lifecycle, not a line-diff finding, not net-new*. This row conforms to that ruling rather than reopening it.

### §C.2 — `schemas/contexts/acp.jsonld` — **N1 (LOW, net-new)**

**The published ACP JSON-LD context defines none of the 22 properties belonging to the six nested value objects the standard's own schema declares.**

`schemas/acp-jsonld.schema.json` declares 10 `$defs`. Four are the top-level node types that carry `@context`; six are nested value objects. Measured with `contexts/acp.jsonld` (36 non-`@` terms).

**Counting convention, stated because the four top-level rows are the only place it bites:** the `props` column counts **declared properties whose name does not begin with `@`**. AgentPlan, Intent, Decision and ExecutionRecord each additionally declare `@context` and `@type`; those are JSON-LD keywords, not terms a context can define, and scoring them would make every context in the standard permanently incomplete. Including them the four rows read 11 / 12 / 9 / 12 and the table sums to 70. **Every figure in this section — the 62, the 22, the 35.5%, and every cell of the corpus baseline below — is on the non-`@` convention**, so the column is too:

| `$def` | props | not in the context | of which schema-`required` |
|---|---|---|---|
| AgentPlan / Intent / Decision / ExecutionRecord | 9 / 10 / 7 / 10 | **0 / 0 / 0 / 0** | — |
| `Trigger` | 3 | 3 — `kind`, `expr`, `authorized` | `kind` |
| `PlanStep` | 5 | 5 — `id`, `mcp`, `args`, `dependsOn`, `requiresApproval` | `id`, `mcp`, `args` |
| `ResourceCaps` | 3 | 3 — `maxAtp`, `maxExecutions`, `rateLimit` | — |
| `HumanApproval` | 4 | 4 — `mode`, `autoThreshold`, `timeout`, `fallback` | — |
| `Guards` | 5 | 4 — `witnessLevel`, `resourceCaps`, `humanApproval`, `expiresAt` | — |
| `ProofOfAgency` | 6 | 3 — `nonce`, `audience`, `expiresAt` | `nonce` |

The column sums to 62 (36 top-level + 26 nested) and the undefined column to 22, so the headline is re-derivable from the table.

**22 of 62 properties (35.5%) undefined.** The context maps `steps`/`guards`/`proofOfAgency` as opaque terms with no nested `@context` and no `@type`, so a conformant JSON-LD 1.1 processor expanding an SDK-emitted document resolves the children against the active context, finds nothing, and **drops them**.

What is dropped is not incidental: `guards` (`witnessLevel`, `maxAtp`, `maxExecutions`, `rateLimit`, approval `mode`, `expiresAt`) and `steps` (`id`, `mcp`, `args`) are precisely the fields that *constrain* the agent, and `nonce` is the anti-replay field of the proof of agency. An AgentPlan survives expansion as its identity and provenance; its safety envelope and its actual instructions do not.

**Corpus baseline before calling it a defect** (binding condition 2). Same measurement over every schema/context pair in the standard:

| context | `$defs` | props | undefined | coverage |
|---|---|---|---|---|
| `atp.jsonld` | 2 | 11 | 0 | 100% |
| `capability.jsonld` | 3 | 13 | 0 | 100% |
| **`dictionary.jsonld`** | **10** | **38** | **0** | **100%** |
| `entity.jsonld` | 5 | 6 | 0 | 100% |
| `r7-action.jsonld` | 6 | 31 | 2 | 93.5% |
| `t3.jsonld` + `v3.jsonld` (via `t3v3-jsonld.schema.json`) | 3 | 18 | 2 | 88.9% |
| `lct.jsonld` (via `lct-jsonld.schema.json`) | 2 | 14 | 6 | 57.1% |
| **`acp.jsonld`** | **10** | **62** | **22** | **64.5%** |

There are **11** schema→context pairings over **10** distinct contexts; **3 are vacuous and are excluded rather than scored as 100%** — `attestation-envelope-jsonld.schema.json`, `lct.schema.json` and `t3v3.schema.json`, all 0 `$defs`. Counting a pair with no properties as fully covered was an error in this table's first draft, caught on the post-write re-run.

**The t3v3 row was omitted from this table's first draft and is added here**, because the baseline claims to cover *every* schema/context pair and did not. It is the one pairing where a schema faces two contexts: `t3v3-jsonld.schema.json` declares `DimensionScore`, `T3Tensor`, `V3Tensor`, and the 2026-03-24 reconciliation split the retired shared `t3v3.jsonld` into `contexts/t3.jsonld` and `contexts/v3.jsonld` (both live; both referenced by `test-vectors/validate_context_refs.py` and by `sdk/web4/trust.py:106-107`). **Scored against the union: 2 undefined, 88.9%.** Against either context alone it is 5 / 72.2% — but that penalises T3Tensor for not being defined in V3's context and vice versa, which is not a real defect: the SDK emits each tensor type with its own context, so `T3Tensor` scores 0 undefined against `t3.jsonld` and `V3Tensor` 0 against `v3.jsonld`. The residual 2 under every treatment are `DimensionScore`'s `observed_at` and `witnessed_by`, undefined in both. Union is therefore the fair figure and is what the table carries.

**Not the corpus idiom: 4 of the 8 pairs that declare any nested properties are at 100%** (`atp`, `capability`, `dictionary`, `entity`), **and `dictionary.jsonld` — the closest structural comparator, also 10 `$defs` with nested value objects — defines all 38.** acp is the largest gap in the standard both absolutely (22) and as a share of a multi-`$def` context. Adding the t3v3 row does not soften N1: t3v3 contributes at most 5 undefined and 2 on the fair treatment, against acp's 22.

- **Severity LOW, bounded by the consumption mechanism** (v13): nothing in the repo expands ACP JSON-LD to RDF. `grep -rn "pyld|jsonld.expand|from rdflib" --include=*.py web4-standard/ archive/` returns only the two MRH scripts, neither of which touches acp. The SDK's `to_jsonld()`/`from_jsonld()` round-trip is plain-dict and never consults the context; `validate_context_refs.py`'s own docstring records that the schemas "type `@context` as an array of URI strings and never dereference it." **Latent, not a live failure.**
- **Classification: net-new.** Distinct locus from carry M6 (which is about the `acp:` RDF *edge* predicates in §8, not JSON-LD terms) and from every other ledger row. The artifact has never been read.
- **Routed, not applied.** Widening the context is an edit to `web4-standard/`, and the fix is not obviously one-way: either add the 22 terms, or add scoped `@context` blocks to `steps`/`guards`/`proofOfAgency`, or ratify that nested value objects are deliberately opaque and say so. That is an author decision, and it is corpus-shaped — `lct.jsonld` (6) and `r7-action.jsonld` (2) have the same class of gap, so a per-file fix at acp's slot would leave the pattern half-addressed.

### §C.3 — Two instrument corrections (I-2, I-3, INFO)

**I-2 — carry M6's two published numbers are both off at HEAD.** The carry reads "11 `acp:` predicates in no TTL."
- Live count is **12**, not 11: `atpConsumed, derivedFrom, executedBy, executedIntent, hasAgent, hasDecision, hasExecutionRecord, hasPrincipal, recordedIn, status, underGrant, witnessedBy`. Matcher `grep -o "acp:[a-zA-Z]*" web4-standard/core-spec/acp-framework.md | sort -u`, minus the bare `acp:` prefix token and the two identifier strings `acp:plan`/`acp:intent` (which are JSON id values like `"acp:plan:invoice-processor"`, not predicates). C86 recorded "9+", which was already a floor rather than a count.
- The namespace `https://web4.io/ontology/acp#` is declared in **exactly 2 sites repo-wide, both inside acp-framework.md itself** (`:428` turtle `@prefix`, `:456` SPARQL `PREFIX`). Matcher `grep -rn "web4.io/ontology/acp" .` excluding `.git/`, `docs/audits/`, `**/target/`.
- The carry's *premise* survives unchanged. Only its arithmetic is corrected. Per [[feedback_enumeration_and_grep_hypotheses]], re-derived from ground truth rather than inherited.

**I-3 — a C37 remediation that was written in prose and never promoted into a ledger, and has therefore been invisible for 59 days.** `C37-…:126` records a secondary remediation: *"reconcile `ACP_INTEGRATION_SUMMARY.md:101` in a corpus follow-up (CROSS-TRACK, low urgency)."* It appears in **no** carry row — not in C86's, C125's, C234's, or C274's 9-row ledger — and at HEAD `ACP_INTEGRATION_SUMMARY.md:101` still carries `"ledgerInclusion": {...}`, the field C87 removed from the spec on the ground that it contradicts `canonicalHash`. This is [[feedback_prose_is_not_ledger]] with a 59-day dwell time: a remediation direction stated in prose, never asked "is this a carry?", and consequently never carried. **Promoted to a ledger row here** so it survives the next delta. Severity INFO (a summary doc, not a normative surface); the fix is a one-line replacement matching C87's, and it is **routed, not applied** — this pass mutates nothing.

### §C.4 — Three refutations, including the flagship

**REFUTED-1 — "the standard uses two namespaces for `web4:`."** True (`schemas/contexts/*.jsonld` 10 of 10 use `https://web4.io/ns/`; `ontology/*.ttl` and every core-spec RDF block use `https://web4.io/ontology#`), and **ratified**: `docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md` (2026-03-24, Status: Decided) assigns `ontology#` to OWL/RDF and `ns/` to application serialization. `C310-…:163` already refused to file it on exactly this ground. Not filed. Charging it would resurrect a ratified decision.

**REFUTED-2 — "the spec's §2.x examples carry no `@context`, while the schema makes `@context` required on all four node types."** Both halves verify (`grep -c "@context" acp-framework.md` = **0**; all four `$defs` list `@context` first in `required`). **But the corpus already adjudicated this and moved the opposite way.** `C37-…:264-266` ruled the §2.x examples are the SDK `to_dict()` illustrative dialect which the JSON-LD schema does not govern, and the remediation it chose — *applied at C87, confirmed HELD at `C86-…:43`* — was to **delete** the one stray `@context` so the four examples are uniformly dict-flavor. Filing this would be re-opening a ratified adjudication in the direction it was decided against.

**REFUTED-3 — the flagship. "C37's `ledgerInclusion` evidence cell is false, and a mutation to the standard rests on it."**

The candidate: `C37-…:125` states "`ledgerInclusion` appears in **the entire corpus** only twice — §2.4 and `ACP_INTEGRATION_SUMMARY.md:101` — never in SDK/schema/context/vectors," and C87/#283 removed the field from §2.4 on that finding. A repo-wide grep — `grep -rn "ledgerInclusion" . --exclude-dir=.git --exclude-dir=target --exclude-dir=audits` — returns **8 hits, 7 of them in `forum/nova/ACP-bundle/` across 6 files** (re-run post-write; the `--exclude-dir` form is required, since a trailing `| grep -v "^./docs/audits"` filter does not match GNU grep's path rendering here and silently leaves the audit corpus in the count) — including `ACP.ExecutionRecord.schema.json:13` where `ledgerInclusion` sits in the **`required`** array, `acp.jsonld:41` (a JSON-LD context), and two SPARQL ASK conformance queries dereferencing `web4:ledgerInclusion`. So both clauses appear to fail: not "only twice", and it *is* in a schema and a context.

It was put to an adversarial refuter with instructions to default to refuted. **It did not survive, on three independent legs:**

- **The cell's operative clause is true under canonical scope.** `grep -rn "ledgerInclusion" web4-standard/` returns **exactly 1 hit** — `ACP_INTEGRATION_SUMMARY.md:101`, which the cell itself names. SDK `acp.py:980`, schema `:233` (+ `additionalProperties:false` at `:236`), context `:43-44`, and vector `:162` all carry `canonicalHash` and no `ledgerInclusion`. Only the phrase "the entire corpus" overreaches.
- **`forum/` was already out of scope by a standing rule 11 days older than C37** (§C.0), and **the corpus has ruled this exact construction a wording nit rather than a defect**: `C286-…:115`, on a carry asserting corpus-wide absence of `sal-ontology.ttl` where the file exists only in `forum/nova/` — *"the carry's claim should be read as scoped to the canonical set. Wording nit … not a defect."* Filing C314's version would overturn a ruling made on an identically-shaped claim.
- **The consequence claim collapses.** C37's own remediation line `:126` justifies the edit *"to match SDK `to_jsonld()`, schema, and `acp-valid-008`"* — a three-artifact triad, all three verified at HEAD, none count-dependent. The resulting §2.4 value is byte-identical to the canonical vector. And the counterfactual runs the wrong way: admitting the bundle would not have changed the remediation, because the bundle wants `ledgerInclusion` while every canonical artifact wants `canonicalHash`.

**Filed as REFUTED.** What survives is the §C.1 DECLINE row and the §C.3 instrument notes — INFO, not the MEDIUM this would have been. Recorded at length as a **REFUTED-GUARD**: do not resurrect "C37's `ledgerInclusion` count is false" without first overturning `C286-…:115` and the §C.0 standing rule.

---

## Findings

| # | Severity | Class | Disposition |
|---|---|---|---|
| **N1** | **LOW** | **net-new** | `schemas/contexts/acp.jsonld` defines 0 of 22 nested-object properties the standard's own schema declares; 22/62 (35.5%) undefined, the largest gap in the standard, against a corpus where **4 of the 8 non-vacuous pairs** are at 100% and the closest comparator `dictionary.jsonld` is at 100%. Latent — nothing expands ACP JSON-LD. **Routed to author/SDK track; not applied.** The fix has three legitimate shapes and is corpus-shaped (`lct.jsonld` 6, `r7-action.jsonld` 2) |
| **I-1** | INFO | coverage row under `B-D1` / [[feedback_frozen_parallel_spec]] — **NOT net-new** | `forum/nova/ACP-bundle/` **DECLINED**: frozen 2025-09-15 inbound Nova proposal, superseded by canonical artifacts created 2026-03-21, internally self-inconsistent (two ExecutionRecord schemas disagreeing on `ledgerInclusion`), zero live consumers outside the excluded trees. Published so nine silences are not read as coverage |
| **I-2** | INFO | instrument | Carry M6's count is **12**, not 11, at HEAD; the `acp:` namespace is declared in exactly 2 sites, both inside acp-framework.md. Premise unchanged |
| **I-3** | INFO | instrument, **promoted to a ledger row** | `C37:126`'s secondary remediation (`ACP_INTEGRATION_SUMMARY.md:101` `ledgerInclusion`) lived in prose for 59 days, entered no ledger, and is still unfixed at HEAD. Routed, not applied |
| — | REFUTED | — | ×3, incl. the flagship (§C.4) |

**ZERO mutation of `web4-standard/`.** No spec, schema, context, vector or SDK file was edited.

**No accountability self-audit block:** this pass creates no surface and performs no consequential act — it writes one document under `docs/audits/`.

---

## Guards for the next acp delta (C354)

1. **These artifacts are now IN acp's swept set and may not contract back out silently** (v8): `web4-standard/schemas/contexts/acp.jsonld`, `forum/nova/ACP-bundle/` (declined — cite §C.1, do not re-derive), `archive/reference-implementations/acp_{framework,executor,hardbound_e2e}.py` (excluded — cite §C.0, do not re-derive). A pass that does not name all three has contracted the set.
2. **REFUTED-GUARD — do not resurrect** without first overturning the ruling that killed it: (a) "C37's `ledgerInclusion` corpus count is false" → killed by `C286-…:115` + the §C.0 standing rule; (b) "spec §2.x examples lack `@context`" → killed by the ratified `C37:264-266` adjudication applied at C87; (c) "`ns/` vs `ontology#` namespace split" → killed by `JSONLD-NAMESPACE-RECONCILIATION.md` (2026-03-24) and `C310-…:163`. C274's own REFUTED-GUARD (bare-string `witnesses`) also still stands and was not re-opened.
3. **N1 regression check:** re-run the schema/context coverage measurement over **all 11 pairings** (every `schemas/*.json` whose stem names a `schemas/contexts/*.jsonld`, plus the `t3v3-jsonld.schema.json` → `t3.jsonld`+`v3.jsonld` union pairing), on the **non-`@` convention** stated in §C.2, excluding the 3 vacuous pairs rather than scoring them 100%. If `contexts/acp.jsonld` has gained terms, say which; if the schema has gained `$defs`, the gap may have widened without anyone touching the context. **Instrument note:** this baseline is a new measurement born at C314 and its first draft got three cells wrong — a props column on a different convention from its own total, a summary row carrying a pre-correction denominator, and one whole pairing missing. Re-derive it; do not inherit these cells.
4. **C274-N1 regression checks remain live** and were both answered NO this pass — re-run them (schema `witnesses` widening; acp↔r7 cross-refs).
5. **Carry ledger is 9 rows + I-3 = 10.** Row survival this pass: 9/9. If a future pass reports fewer rows, check for an emptying ledger before certifying clean ([[feedback_ledger_emptied_not_closed]]).
6. **Matcher guard, born this pass:** when the token contains a `.` or `-`, publish the count with `grep -F`. `acp.jsonld` vs `acp-jsonld` differ by one character, and an unanchored regex conflates the never-read context with the well-covered schema — 0 files becomes 11. Any coverage cell in this lineage stated without `-F` should be re-measured before it is relied on. And exclude the pass's own document: `docs/audits/` is a tree this lineage writes into, so every coverage grep collides with its own output.
7. **Proportionality:** C274's ruling still binds. If C354 opens on an empty window *and* the artifact-tree sweep is already covered by guard 1, the correct output is a short NO-OP record. This pass was full-length because two artifacts had never been read — that justification is now spent.
