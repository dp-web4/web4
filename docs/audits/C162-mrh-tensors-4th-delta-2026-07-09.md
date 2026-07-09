# C162 Audit: `mrh-tensors.md` Fourth Delta Re-Audit (+ C161 no-op declaration)

**Date**: 2026-07-09
**Auditor**: Autonomous session (Legion, web4 track) — AUDIT turn
**Document**: `web4-standard/core-spec/mrh-tensors.md` (420 lines; **byte-frozen since C91 `f0c82118`**, 2026-06-24 — `git diff f0c82118 HEAD` empty across the file)
**Lineage**: C10 → C40 → C41 (remed, #290) → C90 (2nd delta) → C91 (remed, #382 `f0c82118`) → C129 (3rd delta, snapshot `a10affc0`) → C130 (remed of C129-O1, `4e3feb26`, #442) → **C162** (this 4th delta)
**Method**: §A prior-finding + carry verification re-run **at live HEAD** (not trusting C129's line numbers) + remediation-regression check on C130 + **re-derivation of C129's inbound-anchor census from ground truth**; §B refute-by-default 3-finder pass (internal/SDK-fidelity ∥ cross-section/vocab/numeric ∥ corpus-delta/inbound surface), each surviving candidate then sent to a **dedicated adversarial refuter prompted to kill it**.
**Reference materials**: SDK `web4-standard/implementation/sdk/web4/mrh.py` (+ `trust.py`); `t3-v3-tensors.md`; `web4-standard/ontology/{role-extension.ttl,role-extension-schema.md,t3v3-ontology.ttl,web4-core-ontology.ttl}`; `referenced-acts.md`; `society-roles.md`; `whitepaper/sections/02-glossary/index.md`; rdflib 7.6.0.

---

## C161 — presence-protocol REMEDIATION slot: genuine no-op (declared)

Per the C155→C156 precedent (a no-op remediation turn is declared inside the next audit doc rather than given its own session/PR):

C160 (`docs/audits/C160-presence-protocol-4th-delta-2026-07-08.md`, PR #488) recorded **zero net-new autonomous findings** — C128's remediation verified CLEAN, the schema-less ledger re-derived from ground truth and found complete and accurate, 0 surviving contradictions. The only open presence item is the **C127-1 cross-track carry** (author `Session`/`VaultEntry` schemas + 2 resources/read vectors), which is explicitly operator-gated and routed, not self-appliable.

**C161 therefore has nothing to apply. No presence file is touched.** This closes the presence C160/C161 pair.

---

## Summary

| | Count |
|---|---|
| **§A** C10 carries (9) | 8 HELD-REMEDIATED, 1 STILL-OPEN-INFO by design (C10-L2), **0 REGRESSED** |
| **§A** C40 F-findings (12) | 12/12 HELD-REMEDIATED, **0 REGRESSED** |
| **§A** C91 applied fixes (3) | 3/3 HELD (re-read at HEAD), **0 REGRESSED** — clean remediation, 2nd confirmation |
| **§A** C130 applied fix (1) | **1/1 HELD and CORRECT** — no remediation-introduced regression |
| **§A** standing carries | D1, D4, X4/N1(a), N4 all STILL-OPEN, correctly still escalated |
| **§A** net-new (audit-record defects, **not** mrh defects) | **2 INFO** (A1 census overcount; A2 anchor-spelling blindspot) |
| **§B** raw candidate findings | ~20 across 3 finders |
| §B CONFIRMED **new mrh (class-a) defects** | **1 INFO** (N1 — §4.2 note under-enumerates) |
| §B cross-track (class-b) observations | **1 INFO** (N2 — role-extension RDF island), routed |
| §B **flagship candidate REFUTED** | 1 (MRH-redefinition charge — killed by canonical glossary) |
| §B REFUTED / acknowledged / engine-artifact | ~17 |

**Verdict: `mrh-tensors.md` remains in good health and byte-stable.** Both prior remediations (C91 on the file, C130 on a doc that cites it) are verified **clean, with zero regressions**. The single class-(a) net-new item is an **INFO-level completeness slip in an explanatory comment** (§4.2's "Two API differences" is actually three), which four prior passes read without testing its *completeness claim*. C163 therefore has **exactly one autonomous item** — it is not a no-op.

The session's most valuable output is a **finding that did not survive**: the charge that the newly-promoted `role-extension.ttl` redefines the protected term MRH was **refuted** by the canonical glossary, which itself defines MRH in terms of scope dimensions. See §C.

---

## §A — Carry, Fix, and Prior-Finding Verification

### C91 applied fixes (3/3 HELD, 0 regressed) — re-read at live HEAD

| C91 item | Current state at HEAD | Status |
|----------|----------------------|--------|
| **N1(b)** §5.2 `web4:training 0.92` | mrh **L262** = `web4:training 0.92`. t3-v3 Alice-Surgeon = `0.92` (L375, L407). Contradiction stays closed **on both sides**. | **HELD** |
| **N2** §6 query-1 honest `ASK` | mrh **L384-386** = `ASK { <lct:alice> (web4:hasRelationship+) <lct:bob> . }`; parses under rdflib 7.6.0. | **HELD** |
| **N3** §4.2 `maximal()` empty-input guard | mrh **L228-231** = `max(…, default=0.0)`. Behaviourally re-verified: SDK `propagate_maximal([]) == 0.0`. | **HELD** |

### C130 applied fix (1/1 HELD, **no remediation-introduced regression**)

C130 (`4e3feb26`) applied C129-O1: repointed `FRACTAL_ROLE_IDENTITY.md:53` from `mrh-tensors.md:143` → `:174` for the "default depth 3" claim.

- mrh **L174** = `- Default horizon_depth = 3 (you, your connections, their connections)` — the anchor now lands **exactly** on the cited claim. ✓
- The surrounding sentence in FRACTAL:53 was re-read: no broken adjacent claim, no partial correction. ✓
- Side effect worth recording (favourable): `:174` sits in **§3.3**, whereas the old `:143` also sat in §3. Neither is inside §5 — so C130 did not add to the X4 blast radius.

Per [[feedback_remediation_introduced_regression]], a remediation of *this audit lineage's own prior finding* is exactly the class that must be re-tested rather than assumed. **It is clean.**

### C10 (9) & C40 (12) — spot-re-verified against frozen bytes

C40 F1 (`combined = 0.0`, L220) ✓ · F5 (§3.3 structural depth-bound note, L155-157) ✓ · F8 (`MRHEdge` clamp/coerce note, L68-71) ✓ · F10 (§4.2 divergence note, L198-206) ✓ · remainder unchanged since C129's per-site scan. C10 H1/M1-M4/L1/L3/L4 held. **C10-L2** (unnumbered preamble `## Evolution` @L5, `## Core Concept` @L14 before `## 1.` @L27) **STILL-OPEN INFO by design** — C41 declined the demotion; no normative dependency. **0 regressions.**

### Standing carries — status unchanged, correctly still escalated

- **D1** (operator DESIGN-Q) — ontology-vocabulary divergence. **Re-confirmed with fresh evidence**: of the illustrative predicates mrh uses, `web4:trustScore`, `web4:memberOf`, `web4:witnessRole`, `web4:interactionType`, `web4:t3Score`, `web4:RolePairing`, `web4:subjectRole`, and even the super-property `web4:hasRelationship` have **zero** definitions in `web4-core-ontology.ttl` (only `web4:T3Tensor` resolves). Unchanged. §B-N2 is a fresh sibling instance.
- **D4** (operator DESIGN-Q) — spec `horizon_depth = 3` (L174) vs SDK `MRH_MAX_HOPS = 4` (`trust.py:91`); the SELF/DIRECT/INDIRECT/PERIPHERAL/BEYOND zone taxonomy (`trust.py:563-574`) still lives only in code. Unchanged.
- **X4 / N1(a)** (operator DESIGN-Q) — structural shrink of §5 (L240-369). Recommended 4× (C40-X4, C42-F17, C82-D2, C129-O2). **STILL-OPEN.** Its cost input is corrected by §A-A1/A2 below.
- **N4** (folds into D1) — `web4:t3Score` (L323/L331) vs `web4:trustScore` (L395). Unchanged.

### Lead objective checks

- **Byte-freeze**: `git diff f0c82118 HEAD -- …/mrh-tensors.md` empty. Confirmed.
- **§7 reference links (L413-418)**: all 7 targets resolve from the doc's location. C40-L4 (SDK-module-first ordering) held.
- **Composite arithmetic**: `0.95×0.4 + 0.92×0.3 + 0.88×0.3 = 0.920` — exactly the `web4:t3Score 0.92` at L323. Internally consistent.
- **`RelationType` "12-member enum" (L64)**: SDK `len(list(RelationType)) == 12`; §2.1 declares exactly 12 `rdfs:subPropertyOf` subjects (4 binding + 4 pairing + 4 witness). Consistent.
- **RDF/SPARQL well-formedness**: all 4 Turtle fences (9/15/14/14 triples) and all 6 SPARQL fences parse under rdflib 7.6.0 (`prepareQuery`, SPARQL 1.1). No unbound projected vars.
- **L348 citation** `t3-v3-tensors.md §9.2 / §10.2 (parameter t3v3-001)`: both sections exist; §10.2 L629 normatively states `talent=0.4, training=0.3, temperament=0.3` under id `t3v3-001`. Citation **correct** (candidate defect refuted).

---

### A1 (INFO — defect in the **C129 audit doc**, not in mrh) — O2's inbound-anchor census overcounts by one

C129 §B-O2 states: *"`:246` ×6 (FRACTAL ×1, RFC-COMPOSITE ×4, RFC-SHARED ×1) … and `:143` ×2"*, concluding *"migrate the 8 inbound anchors"* and *"breaks all six `:246` citations."*

Re-derived from ground truth at **C129's own snapshot `a10affc0`** (and again at HEAD), counting **all spellings**:

| Citing doc | `:143` | `:246` | anchor spelling |
|---|---|---|---|
| `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md` | 1 (L53) | 1 (L37) | `mrh-tensors.md:N` |
| `web4-standard/rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md` | 1 (L97) | **3** (L54, L82, L117) | `mrh-tensors.md:N` |
| `web4-standard/rfcs/RFC-SHARED-POLICY-SUBSTRATE.md` | 0 | **1** (L165) | **`mrh §246`** |
| **TOTAL** | **2** | **5** | **7 anchors across 3 docs** |

So O2's `:246` count should be **×5, not ×6**, and its total **7, not 8**. The single erroneous unit is **RFC-COMPOSITE `:246` = 3, not 4** — C129 appears to have written that doc's *total* anchor count (4 = three `:246` + one `:143`) into the `:246` breakdown.

**Everything else in O2 is correct**: 3 downstream docs (RFC-SHARED **does** cite mrh), `:143` ×2, and `L246` does sit inside §5 (L240-369, verified at both snapshots). O2's qualitative conclusion — raw-line cross-refs into §5 are a fragility class; migrate to section anchors before any shrink — is **fully intact**, and the operator's X4 cost picture is not materially changed by an off-by-one across the same 3 docs.

**Severity INFO.** Disposition: a one-line correction to the C129 doc's numbers (8→7, RFC-COMPOSITE `:246` ×4→×3) at some future remediation turn; **not** urgent, and **not** an mrh defect.

At HEAD the census is unchanged in shape (7 anchors, 3 docs, `:246` ×5) with FRACTAL's `:143`→`:174` per C130. **All 7 anchors were opened and verified to land on the claim they are cited for.**

### A2 (INFO, **method — net-new**) — the `mrh §246` spelling defeats a filename-anchored grep, and would silently orphan RFC-SHARED in any X4 migration

`RFC-SHARED-POLICY-SUBSTRATE.md:165` cites mrh as **`` `mrh §246` ``** — a **line number wearing a section sigil**. `mrh-tensors.md` has only `## 1.`–`## 7.`; there is no §246. Consequences:

1. The natural census command (`git grep "mrh-tensors\.md:[0-9]"`) **misses it entirely**. This audit's first-pass census did exactly that and wrongly concluded RFC-SHARED "never cited mrh," nearly filing a false §A finding that would have **removed a real citation from the X4 migration scope**. The error was caught only by re-running with a loose pattern (`mrh[-_a-z]*\.md:[0-9]+|mrh §[0-9]+`).
2. Therefore any future X4 §5-shrink that enumerates its blast radius by grepping the filename form will **undercount and silently break `RFC-SHARED:165`**.

This **strengthens** C129-O2's recommendation and adds a concrete requirement to it: the anchor-migration must sweep **loose patterns**, and the corpus convention should additionally forbid `§N` where `N` is a line number (reserve `§` for real sections).

Route: fold into the standing **X4** operator DESIGN-Q alongside O2. Not an mrh defect.

---

## §B — New Findings

**Class-(a) net-new mrh defects: 1 (INFO).** Class-(b) cross-track: 1 (INFO, routed).

### N1 (INFO, class-a, **spec-local AUTONOMOUS** → the single item for C163) — §4.2's note claims "Two API differences" but there are three

`mrh-tensors.md` **L201-206**:

> *"Two API differences from the pseudocode below: (1) the SDK's `propagate_probabilistic`/`propagate_maximal` consume pre-computed path-trust scalars (`List[float]`) rather than raw `List[MRHEdge]` paths, and (2) they drop the `decay_factor` parameter … Only `propagate_multiplicative` carries `decay_factor`."*

Ground truth in the canonical SDK (`web4/mrh.py`):

```
L198  def propagate_multiplicative(path_weights: List[float], decay_factor: float = 0.7) -> float
L214  def propagate_probabilistic(path_trusts: List[float]) -> float
L228  def propagate_maximal(path_trusts: List[float]) -> float
```

**All three** SDK functions take `List[float]`. But the pseudocode's `multiplicative(self, path: List[MRHEdge], …)` (L208) takes `List[MRHEdge]`, and difference (1) is explicitly scoped **by name** to the other two functions. So `propagate_multiplicative`'s own input-type divergence from the pseudocode is a **third, unenumerated** API difference, and the note's exhaustiveness claim ("Two") is false.

The divergences are genuinely distinct, so this is not a restatement of (1): prob/max consume **one float per path** (path-trust scalars); multiplicative consumes **one float per edge** (edge weights — see the caller at `mrh.py:485`, `propagate_multiplicative(weights, decay_factor)`).

*Refutation attempted*: "identical mathematical semantics" up front, plus the pseudocode being labelled "conceptual structure," might excuse it. **Rejected** — the note's stated job is precisely to enumerate where the pseudocode diverges from the SDK, and it commits to a count. Statement (2) and the closing sentence are accurate.

**Severity INFO** (explanatory comment; no normative dependency; math is correct and byte-identical). **Autonomous, spec-local, ≤2 lines.** Suggested C163 edit: reword to note that all three SDK functions take `List[float]` — multiplicative per-**edge** weights, prob/max per-**path** scalars — and that only multiplicative carries `decay_factor`.

*Why four prior passes missed it*: they tested the note's **math** (C129: *"§4.2 propagation math diverges from SDK — REFUTED, multiplicative byte-identical"*) and never tested its **completeness claim**. See §D-3.

### N2 (INFO, class-b, cross-track → ROUTED, not self-applied) — `role-extension.ttl` is an RDF island: it declares `web4:` and never uses it

`web4-standard/ontology/role-extension.ttl` (NEW at `7201a765`, Phase-0 promotion; 90 triples, parses clean under rdflib):

- **L1** declares `@prefix web4: <https://web4.io/ontology#>` (canonical, hash form — correct, and **not** the known trailing-slash divergence carried against `hub-law.ttl`). But **zero triples touch that namespace** — the prefix is declared and never used.
- No `rdfs:subClassOf` / `owl:equivalentClass` relates `role:Scope` (or any `role:` term) to a `web4:` term; no `role:` property is `rdfs:subPropertyOf web4:hasRelationship`. Under mrh §3.3's typed-edge traversal (which walks `hasRelationship` sub-properties), a `role:Extension` is **unreachable** — it names MRH in prose but does not participate in the MRH graph.
- **L163** `role:driftMark` is the only one of 16 `rdf:Property` declarations lacking an `rdfs:domain`.

This is a **fresh sibling instance of standing carry D1** (ontology-vocabulary divergence), now appearing in a *promoted standard* ontology rather than an illustrative fence.

**Not an mrh defect** (mrh is frozen and asserts nothing about `role:`). **Routed, NOT self-applied**: `role-extension.{ttl,md}` is CBP-ratified Phase-0 under a concord, and PR **#489** (`feat/role-extension-registry`) is mid-review against these very artifacts. Suggested to the role-extension owner: either formally relate `role:Scope`/`role:rangesOver` into `web4:`, or drop the unused `web4:` prefix; and give `role:driftMark` an `rdfs:domain`.

---

## §C — The flagship candidate, and why it was REFUTED

The session's most promising candidate was that `role-extension.ttl` **redefines the protected term MRH**, in violation of `CLAUDE.md`'s Terminology Protection table (which names MRH DO-NOT-REDEFINE, spec = `mrh-tensors.md`). The evidence looked strong:

- `role:Scope` is `rdfs:label "Scope / MRH"`, commented *"The **Markov Relevancy Horizon** of the grant: repos, machines, channels, data classes, ATP budget the role ranges over"* (L49-50); `role:rangesOver` — *"a resource … inside the role's MRH"* (L136); `role-extension-schema.md:50` — `**scope / MRH** | over what resources does the grant range?`.
- mrh's **Key Principle #5** reads *"**Horizon Limits Scope**"* — the spec appears to hold horizon and scope **distinct** (the horizon *bounds* the scope), so equating them looked like an inversion.
- mrh's opening section is *"Evolution: From Lists to RDF Graphs"* — and `role:hasScope` → a flat list of `role:rangesOver` resources looked like the superseded list form.
- `role:atpBudget rdfs:range xsd:decimal` sits under the class whose comment says it **is** the MRH — and a scalar budget cannot be a node in a relationship graph.
- The corpus already has a precise non-MRH term for exactly this: `grant.scope.r6Caps.resourceCaps` (`acp-framework.md` §4.1 L254, `entity-types.md` §4.7), `max_atp` included.

**All of it fails against the canonical definition.** The glossary that `CLAUDE.md` itself designates as the place to check before coining terms — `whitepaper/sections/02-glossary/index.md:50` — defines MRH as: *"Each entity's contextual lens defining what is knowable, actionable, and relevant **within their scope** … Dimensions include fractal scale, **informational scope**, geographic scope, **action scope**, and temporal scope."* MRH-as-scope is not a corruption; it is the definition. And the idiom is canonical and widespread, predating role-extension:

- `web4-standard/core-spec/referenced-acts.md:43` — `## 2. Addressing — the MRH scope *is* the addressing` (§ header), and L10 *"who the reader is — i.e. in **MRH scope**."*
- `web4-standard/core-spec/society-roles.md:107` — *"multiple Policy-Entities at different **MRH scopes** (Compliance-Officer-for-Finance …)"* — MRH as an authorization scope.
- `web4-standard/core-spec/mcp-protocol.md:943` — *"MRH queries scoped to relevance."*
- `hub/hub-daemon/src/rest.rs:2395,2606` — *"MRH bound at the result layer"*, *"Scoping: bound how much this tier may see (MRH at the result layer)."*
- `CLAUDE.md`'s own canonical-equation table glosses MRH as **"Fractal context scoping."**

Further, `rdfs:label` / `rdfs:comment` / `dcterms:description` carry **no machine semantics**; `role:` is a separate namespace asserting no `owl:equivalentClass` / `owl:sameAs` / `rdfs:subClassOf` against any `web4:` term, and mrh-tensors declares no `web4:MRH` or `web4:Scope` class to collide with. There is **no redefinition at the ontology level** — only a mnemonic string, consistent with established usage.

**Verdict: REFUTED.** Not net-new, not MED, not a defect. What survives is only the far weaker encoding observation recorded as **§B-N2** (annotation-only "MRH" identity, no formal link). Recording this refutation is the point: it is a textbook instance of the standing **cross-doc overcall pattern** (C7/C9/C10/C11 streak) — *observation real, cross-doc framing overstated* — and it was caught only because the finding was handed to an adversarial refuter instructed to kill it.

---

## §B — Refuted / acknowledged / engine-artifact (default-to-refute upheld)

| Candidate | Disposition |
|-----------|-------------|
| `role-extension.ttl` **redefines the protected term MRH** | **REFUTED** — MRH-as-scope is the canonical definition (whitepaper glossary §MRH: "informational scope … action scope") and an established corpus idiom (`referenced-acts.md:43`, `society-roles.md:107`, hub `rest.rs`). Annotation-only; no `owl:equivalentClass`; no symbol collision. See §C. |
| C129-O2's census is wrong: RFC-SHARED cites mrh **zero** times → 6 anchors / 2 docs | **REFUTED (this audit's own first-pass candidate)** — missed the `` `mrh §246` `` spelling at `RFC-SHARED:165`. C129 was **right** that 3 docs cite mrh. Truth = 7 anchors / 3 docs. Survives only as the off-by-one **A1** + the method note **A2**. |
| mrh L348 mis-cites `t3-v3 §9.2` for the T3 composite weights | **REFUTED** — mrh cites **both** §9.2 and §10.2; §10.2 L629 is the normative home (`t3v3-001`, 0.4/0.3/0.3) and §9.2 L556 shows the same weights in a `BIND`. Citation correct. |
| `role:atpBudget` under `role:Scope` contradicts mrh's graph model | **REFUTED** — mrh asserts nothing about ATP; the glossary's MRH dimensions are explicitly non-exhaustive ("Dimensions include …"). No contradiction possible. |
| C130's O1 remediation introduced a regression | **REFUTED** — `:174` lands exactly on `Default horizon_depth = 3`; adjacent sentence intact. Clean. |
| C91 fixes regressed | **REFUTED** — 3/3 held; behaviourally re-verified against the SDK. |
| §4.2 propagation math diverges from SDK | **REFUTED** — multiplicative byte-identical; `propagate_probabilistic([]) == 0.0`, `pp([0.5,0.5]) == 0.75`, `propagate_maximal([]) == 0.0`. Only the note's *enumeration* is incomplete (**N1**), not the math. |
| §1.2 "12-member enum" (L64) miscount | **REFUTED** — SDK enum has exactly 12 members; §2.1 declares exactly 12. |
| §1.2 weight-clamp / str-coercion notes inaccurate | **REFUTED** — behaviourally verified: `MRHEdge(…,5.0).weight == 1.0`, `(…,-2.0).weight == 0.0`, `'pairedWith' → RelationType.PAIRED_WITH`. |
| Alice composite `0.92` vs Mechanic pairing2 `t3Score 0.15` mismatch | **REFUTED** — different role pairings (`Mechanic`-self vs `CarOwner`→`garage`); standalone illustrative values. Only the Surgeon example is designed to tie arithmetically, and it does, exactly. |
| §5.5b `web4:interactionType` absent from §5.4 example data | **REFUTED** — illustrative predicate; D1-class pre-existing carry, not new. |
| Any of 4 Turtle / 6 SPARQL blocks malformed | **REFUTED** — all parse under rdflib 7.6.0 (prefixes concatenated per the L81-83 contract). |
| §6-b `HAVING (?avg_trust > 0.8)` returns nothing | **ENGINE ARTIFACT** — rdflib decimal-vs-double quirk; query is SPARQL-1.1 correct (as at C90/C129). |
| §5.4 `web4:t3Score` vs §6 `web4:trustScore` | **KNOWN CARRY N4** — confirmed present, not re-reported. |
| `horizon_depth = 3` vs `MRH_MAX_HOPS = 4` + zone taxonomy | **KNOWN CARRY D4** — confirmed still divergent (`trust.py:91`, `:563-574`), not re-reported. |
| §5.3 `RoleContextualT3V3` fidelity defect | **REFUTED** — no SDK counterpart; illustrative, as acknowledged. |
| C10-L2 unnumbered preamble | **STILL-OPEN INFO by design** — C41 declined the demotion. |
| atp-adp §2.4 / reputation §9 / acp ×3 / hub Rust deltas contradict mrh | **REFUTED** — diff-grep of all four commits for `mrh\|markov\|horizon\|hasRelationship\|boundTo\|pairedWith\|witnessedBy\|0.92\|propagat` returns **nothing**. Corpus delta is fully disjoint from every mrh assertion. |

---

## Disposition for C163 (paired remediation)

- **Apply autonomous (exactly 1, spec-local, ≤2 lines, zero SDK/schema/`.ttl`/vector mutation):**
  - **N1** — `mrh-tensors.md` §4.2 note (L201-206): correct the "Two API differences" enumeration. All three SDK functions take `List[float]`; multiplicative takes per-**edge** weights, prob/max take per-**path** scalars; only multiplicative carries `decay_factor`.
  - *Guard for C163*: N1's edit site becomes the newest net-new prose in a byte-frozen file. Per [[feedback_remediation_introduced_regression]], the **C164** mrh delta must re-test this exact hunk against `mrh.py` rather than assume it.
- **Route cross-track (do NOT self-apply):**
  - **N2** → owner of `web4-standard/ontology/role-extension.{ttl,md}` (CBP Phase-0 concord; PR #489 in flight): unused `web4:` prefix; no formal link from `role:Scope`/`role:rangesOver` into `web4:`; `role:driftMark` missing `rdfs:domain`. D1-sibling.
  - **A1** → a one-line correction to `C129-…md` §B-O2's numbers (8→7; RFC-COMPOSITE `:246` ×4→×3). Low urgency; the audit record, not the standard.
  - **A2** → fold into the standing **X4** operator DESIGN-Q: any §5-shrink anchor-migration MUST sweep loose patterns (`mrh §N` as well as `mrh-tensors.md:N`), or it will silently orphan `RFC-SHARED:165`. Recommend the corpus convention also forbid `§N` where `N` is a line number.
- **Defer — operator DESIGN-Q (unchanged bundle)**: **X4/N1(a)** structural §5-shrink (cost context now O2 + A1 + A2); **D1** ontology-vocabulary (N4 and §B-N2 fold in); **D4** `horizon_depth=3` vs `MRH_MAX_HOPS=4` + zone taxonomy.
- **No date bump**: `mrh-tensors.md` carries no date/version banner; audit-only turn, nothing to stamp.

---

## §D — Method Notes

1. **Refute-by-default must be pointed at the auditor's own best finding, not just at the leftovers.** The MRH-redefinition charge (§C) had five independent supporting arguments, a `CLAUDE.md` policy hook, and real timeliness (PR #489 building on the artifact). It was **wrong**, and every one of those five arguments lost to a single glossary line. It died only because it was handed to a refuter *instructed to kill it*. A finder that merely "checks its work" would have shipped it. The stronger a cross-doc finding feels, the more it needs an adversary — this is the recorded **cross-doc overcall pattern** recurring on schedule.

2. **A grep pattern is a hypothesis about how people write citations, and it fails silently.** This audit's own first-pass census (`mrh-tensors\.md:[0-9]`) missed `` `mrh §246` `` and concluded a real citing document had *never* cited mrh — a false §A finding that would have shrunk the X4 migration scope and orphaned `RFC-SHARED:165`. [[feedback_prior_finding_path_provenance]] says to re-run a carried finding's grep at live HEAD; **A2 extends it**: re-run it with a *loose* pattern, because the defect you are hunting (inconsistent citation form) is the very thing that defeats a tight one. The correction ran in both directions here — C129 overcounted by one; this audit initially undercounted by one *and* dropped a whole document.

3. **Verifying a claim's content is not verifying its completeness.** §4.2's note has been read by four passes. C129 explicitly tested it and refuted "propagation math diverges from SDK — multiplicative byte-identical." That was **true and insufficient**: the note's defect is not in its math but in its *count* ("Two API differences" — there are three). A claim of the form "there are exactly N of X" must be tested by **re-deriving X from ground truth**, exactly as C160 proved the presence schema-less ledger complete by re-deriving the set from tool bindings. Enumeration claims are a distinct lens; add them to the delta method.

4. **A frozen file's health is a claim about its *neighbourhood*, and the neighbourhood is now growing faster than the file.** mrh has been byte-stable for 15 days across two audits. Everything C162 found — one INFO in the file, one in the audit record, one method note, one routed cross-track item, one refuted flagship — came from what moved *around* it: a newly-promoted ontology, a remediation of a citing doc, and the citation graph itself. C129's Method Note 1 said the inbound surface can grow; C162 adds that the inbound surface can also be **miscounted**, and that its census is now a load-bearing input to a pending operator decision.

---

*C162 verdict: `mrh-tensors.md` byte-stable and healthy; C91 (3/3) and C130 (1/1) both verified CLEAN with zero regressions. One class-(a) INFO net-new (§4.2 "Two API differences" is three) → the single autonomous item for C163, which is therefore **not** a no-op. Two INFO corrections to the audit record (A1 census off-by-one; A2 loose-pattern requirement). One routed cross-track INFO (role-extension RDF island, D1-sibling). The flagship MRH-redefinition charge was raised, pressed, and **refuted** by the canonical glossary. C161 presence remediation declared a genuine no-op. Standing D1/D4/X4/N4 correctly still escalated.*
