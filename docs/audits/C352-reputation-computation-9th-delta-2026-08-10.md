# C352 — `reputation-computation.md`, 9th delta

**Date**: 2026-08-10
**Target**: `web4-standard/core-spec/reputation-computation.md` — blob `bfdac3ba`, 870 L
**Freeze**: last mover `2bc3bafb` (2026-07-18) ⇒ **byte-frozen 23 days**; same blob C232, C272 and C312 audited
**Prior pass**: C312 (PR #639, `e8005332`, 2026-08-04)
**Lineage at HEAD**: **12** documents — 9 passes (`…-internal-consistency-2026-05-25`, C44, C84, C123, C156, C194, C232, C272, C312) + 3 remediations (C124, C157, C195). *(C312 reported 11 under the same rule; it was not yet in the tree when it counted. The inclusive rule — basename matches `reputation`, both audit trees, remediations and the non-C-numbered internal-consistency member included — is applied here to this lineage **and** to every lineage this document counts.)*
**Result**: **1 MED, 1 LOW, 2 INFO. ZERO mutation of the standard.**

---

## Headline

**The standard reserves one witness-element shape — `{lct, attestation: string, signature, timestamp}` — and ratifies it in four independent artifacts. `reputation-computation.md` §6, the only place in the standard that says what a witness to a reputation delta actually attests to, publishes an object that fails that shape two ways. Nine passes never opened the block: the token `witness_attestation` appears in 0 of this lineage's 12 documents, and the one pass that considered the witness side declined it on a different predicate.**

---

## §0 — Method, and what this pass did NOT do

Scope was **revised by the policy reviewer** before execution (proportionality), and the revision is recorded here rather than absorbed silently:

- **Re-derived** two sweep counts the proposal had stated as measured. Both were wrong. See §F.
- **Collapsed the §B window to a two-command negative.** The target and every mirror are frozen; a narrative delta section over an empty window is padding. The freed budget went to the inbound sweep, which is where this rotation's yield has actually been for four consecutive fires.
- **Bounded §A.** Findings whose locus lies *inside* the frozen blob are carried by blob identity (`bfdac3ba` = C232's = C272's = C312's), asserted once, not re-executed one by one. Only findings whose locus lies **outside** the blob (schema, context, `r7-framework.md`, the four mirrors, `hub/`) were re-executed. **This is a skip, and it is written down** rather than performed silently.

Pre-registered before any sweep ran:

| | |
|---|---|
| **Roots** | `docs/audits/` (221 files) + `web4-standard/docs/audits/` (2 files) — both confirmed tracked via `git ls-tree -d HEAD` |
| **Filetypes** | none excluded |
| **Tree** | HEAD worktree, `worker/web4-20260810-060000` |
| **Lineage rule** | basename matches `reputation`, applied identically to every lineage counted |
| **Verb set (addressee filter)** | `rout(e\|ed\|ing)`, `addressed to`, `hand(ed)? ?off`, `defer(red)?`, `reputation[- ](side\|lineage\|delta\|track\|pass\|audit)`, `next reputation`, `for the reputation` — fixed before reading any result |

---

## §A — Prior findings and carries

### A.1 — C312's own forward guard, answered first

C312 closed with: *"At C352 check FIRST whether the fork was answered — a PARTIAL application across the 6 sites is the next defect."*

**Answer: the fork is UNANSWERED, and there is no partial application.** Measured, not inferred:

| Predicate | Command | Result |
|---|---|---|
| Schema still forbids the field | `$defs.reputation_delta` parse | `additionalProperties: false`, **14** properties, `role_pairing_in_mrh` **absent** |
| Schema `required` still 4 | same parse | `[subject_lct, role_lct, net_trust_change, net_value_change]` |
| The 6 emitting sites intact | `git grep -n role_pairing_in_mrh -- 'web4-standard/**'` | **6** — `r7-framework.md:273`, `:425`, `:535`, `:703`; target `:26`, `:72` |
| The dereference still live | `r7-framework.md:535` | `mrh_link=reputation.role_pairing_in_mrh.mrh_link` |
| Still latent | corpus `role_pairing` outside `docs/audits/` | non-archive hits: `r6-framework.md` 1, `r7-framework.md` 7, target 2, `PUBLISHER_CONTEXT.md` 2, `hub/hub-lib/src/state.rs` **1** |

**The one new datum is a negative, and it is reported as one.** C312 ruled N1 **latent** partly on `grep -c role_pairing` = 0 in the Python SDK. A Rust hit exists at `hub/hub-lib/src/state.rs:1230` that C312's Python-scoped greps could not have seen. It is `async fn reputation_recorded_folds_into_role_pairing()` — **a test function name, not a struct field**. No Rust type carries the field. **C312-N1's latency ruling survives a check that could have overturned it**, which is worth more than the check not having been run.

**C312-N1 and C312-N2 STAND, unchanged, un-re-argued.** No new severity, no fresh finding number.

### A.2 — Carries whose locus is OUTSIDE the frozen blob (re-executed)

| Carry | Predicate re-run | Result |
|---|---|---|
| **C232-N1** (`reputation.delta.category` has no producer-side field) | `category` in `$defs.reputation_delta.properties` | **False** — STANDS, 4th side |
| **C156-3** (hub sovereign-strength fold, gate) | `git grep -c sovereign_strength -- 'web4-standard/**'` | **0** — still law-ungated, STANDS |
| **C156-4** (temporal delta, law gate) | `grep -c temporal hub/hub-lib/src/law.rs` | **0** — STANDS |
| **C194-N1** (Rust wire shape unbacked by the standard) | same grep as C312's v12 direction test | **0** — direction CONFIRMED not inverted |
| **C272-N1** (#580 "absence never grants" ⊥ §4 ratified fail-open) | §4 `:283-301` conjunctive-narrowing text at HEAD | intact — STANDS, **still no answer from either referent**, now a second full rotation cycle |
| **C312-N3** (T3/V3 ontology peer in the swept set) | behaviour guard honoured this pass | ontology + context + schema all swept; see N1 |

### A.3 — Carries whose locus is INSIDE the frozen blob (carried by blob identity — SKIP, declared)

`git rev-parse HEAD:web4-standard/core-spec/reputation-computation.md` = `bfdac3ba…`, byte-identical to the blob C232/C272/C312 audited. Every finding anchored to a line of that file — C194-N3/N4 (§7 decay-layer split, operator DESIGN-Q), C194-N5 (W4IP-N5), carry-C46, C123 NEW-1's ratified descriptive remedy, the C214-N1 applied note at `:389` — is carried by that identity. **Not individually re-executed. That is a deliberate bound, not a completed check.**

### A.4 — Regressions

**0.** The window (§B) contains no commit touching the target or any mirror, so there is no surface on which a regression could have landed.

---

## §B — The window (two commands, one table)

```
$ git rev-parse HEAD:web4-standard/core-spec/reputation-computation.md
bfdac3ba2dcbcc6006056172b80e048124e1939e

$ git log --oneline e8005332..HEAD -- \
    web4-standard/core-spec/reputation-computation.md \
    web4-standard/schemas/r7-action-jsonld.schema.json \
    web4-standard/schemas/contexts/r7-action.jsonld \
    web4-standard/implementation/sdk/web4/reputation.py \
    web4-standard/implementation/sdk/web4/r6.py \
    web4-standard/test-vectors/reputation/
0
```

Every pathspec above was confirmed to match a tracked file before the count was published (§E.2) — **a `git log` over a pathspec matching nothing prints exactly what a genuine zero prints.**

52 commits landed in the window; 6 files under `web4-standard/` moved (`core-spec/errors.md`, `core-spec/security-framework.md`, `docs/FRACTAL_ROLE_IDENTITY.md`, `rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md`, `rfcs/RFC-SHARED-POLICY-SUBSTRATE.md`, `submission/draft-web4-core-00.xml`). None is the target, a mirror, the schema, or the context. **§B is a measured zero.**

### §B.2 — The third direction (citers outside both audit trees)

`git grep -l "reputation-computation"` = **81** tracked files; **61** in the two audit trees, **20** outside. (61 + 20 = 81 — the check that would have caught this pass's second own-error before the policy reviewer did.)

Of the 20, **10 have never been named by any of the 12 lineage documents**:

| Never named (10) | Named (10) |
|---|---|
| `core-spec/referenced-acts.md` · `rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md` · `rfcs/RFC-R6-TO-R7-EVOLUTION.md` · `proposals/W4IP-DRAFT-…` · `docs/305-patent-applicability.md` · `docs/history/STATUS-2026-02.md` · `whitepaper/PUBLISHER_CONTEXT.md` · 3 × `archive/` | `reputation.py` 12/12 · `mcp-protocol.md` 6/12 · `test-vectors/reputation/…` 6/12 · `hub-law-schema.md` 5/12 · `acp-framework.md` 4/12 · `web4-society-authority-law.md` 3/12 · `SOCIETY_SPECIFICATION.md` 2/12 · `entity-types.md` 2/12 · `README.md` 1/12 |

**Adjudicated, no finding.** `referenced-acts.md:150`/`:169` and `RFC-COMPOSITE-ENTITY-IDENTITY.md:11` are **citation-only** — they name the target as the authority for aggregation and carry no shape claim against it. `RFC-COMPOSITE-ENTITY-IDENTITY.md` is the one in-window mover among them; its in-window diff is `e4a62d7a`, a **C320 audit-lineage commit**, and touches no reputation semantics. The three `archive/` files are archived implementations **of this specification** — evidence, not defect (the C284/C344 disposition).

---

## §C — Findings

### C352-N1 (MEDIUM) — the standard's only statement of what a reputation witness attests to cannot be serialized as a witness attestation

**Locus**: `web4-standard/core-spec/reputation-computation.md` §6 "Witness Attestation", `:657-670`
**Adjudicator**: `web4-standard/schemas/r7-action-jsonld.schema.json` `$defs.witness_attestation` (`:306-316`) and `web4-standard/schemas/contexts/r7-action.jsonld` `:63`, `:96`
**Routes to**: operator/author. **Do NOT self-apply** — the remedy forks (below).

#### The reserved shape, and the four artifacts that agree on it

| Artifact | Says |
|---|---|
| `schemas/r7-action-jsonld.schema.json` `$defs.witness_attestation` | `required:[lct]`; props `{lct, attestation, signature, timestamp}`; **`attestation: {"type":"string"}`**; **`additionalProperties: false`** |
| `schemas/contexts/r7-action.jsonld:63` | `"attestation": { "@id": "web4:attestation", "@type": "xsd:string" }` |
| `implementation/sdk/web4/r6.py:369-385` `WitnessAttestation` | `attestation: str = "verified"`; `to_dict()` emits exactly those 4 keys |
| `core-spec/r6-framework.md:139` and `core-spec/r7-framework.md:148` | `{"lct": "…", "attestation": "verified", "timestamp": "…"}` |

The schema def is reachable from **three** `$ref` sites: `$.properties.reference.properties.witnesses.items`, `$.properties.result.properties.attestations.items`, and — the one that matters here — **`$.$defs.reputation_delta.properties.witnesses.items`**. It is the **only witness-attestation definition** in any schema under `web4-standard/schemas/` — **all 24** JSON schema files enumerated with `git ls-files` (recursive; the first pass at this count used a non-recursive glob and got 12 — see §F.7). One other witness-named schema exists, `presence-protocol/v0/common/witness_entry.schema.json`, and it is **disjoint**: a hash-linked witness-**chain entry** (`hash`/`prevHash`/`eventType`/`chainPosition`), not an attestation attached to a delta. It is named here rather than omitted, because a claim of the form "only X exists" is only as wide as the tree it was measured over.

#### The defect

§6 `:657-670` publishes, in a fenced `json` block with real values:

```json
{ "witness": {
    "lct": "lct:web4:witness:validator_123",
    "type": "role_validator",
    "signature": "0x...",
    "timestamp": "2025-10-14T...",
    "attestation": {
      "action_id": "txn:0x...", "reputation_hash": "sha256:...",
      "verified": true, "confidence": 0.95 } } }
```

**Machine-checked, Draft 2020-12, with controls:**

| Run | Errors |
|---|---|
| **EXHIBIT A** — §6 object verbatim vs `$defs.witness_attestation` | **2** — `$: Additional properties are not allowed ('type' was unexpected)` · `$.attestation: {…} is not of type 'string'` |
| **CONTROL 1** — target's own §1 `witnesses[0]` (`:56`) | **0** ← the schema is not simply broken |
| **CONTROL 2** — §6 minus `type`, `attestation` stringified | **0** ← exactly two defects, no residue |
| **CONTROL 3a** — §6 minus `type` only | **1** (`attestation` type) |
| **CONTROL 3b** — §6 with `attestation` stringified only | **1** (`type` unexpected) |

Each defect isolates. The controls are the point: a bare failure count proves nothing about *which* clause failed.

**The JSON-LD context convicts `type` a second, independent way.** In `contexts/r7-action.jsonld`, the bare term `type` is bound at `:96` to `{"@id": "web4:constraintType", "@type": "xsd:string"}`. So `"type": "role_validator"` does not merely fail an `additionalProperties` check — under the standard's own context it **serializes as a constraint type**. `role_validator` is not a constraint. Two layers, two different mechanisms, same verdict.

**`type` is not a typo.** §6's own witness-selection pseudocode `:607-649` builds every candidate with a `type` key and a three-value taxonomy (`law_oracle` `:616`, `role_validator` `:627`, `mrh_witness` `:636`). The JSON block at `:660` is that taxonomy serialized. The section is internally coherent; it is coherent with something the rest of the standard does not define.

#### Direction — proved from history, not inferred

| Artifact | Born | Commit |
|---|---|---|
| Target §6 block | **2025-10-14** | `3870da75` "Add comprehensive reputation computation specification" (the file's genesis) |
| `$defs.witness_attestation` | **2026-03-20** | `bbe5b1d9` "V3: R7 Action JSON-LD serialization — 26 tests (#55)" |

§6 predates the schema by five months. The schema author modelled `attestation: {"type":"string"}` on `r6-framework.md:139` / `r7-framework.md:148`, where `attestation` is the string literal `"verified"` — and the SDK dataclass defaults it to exactly that. **The witness-shape convergence of 2026-03-20 reached the r6/r7 framework specs, the SDK and the context, and did not reach §6.** This is the C344-N1 mechanism: the standard ran a shape convergence and this is the block it missed.

#### The remedy FORKS — which is why this routes rather than self-applies

- **Arm A — §6's object IS a `reputation_delta.witnesses[]` element.** Then it is invalid at HEAD and must be reshaped, and the four attested facts (`action_id`, `reputation_hash`, `verified`, `confidence`) need a schema home the standard does not currently offer.
- **Arm B — §6's object is a standalone record, not a `witnesses[]` element.** Then it has **no schema anywhere in `web4-standard/schemas/`** — verified by parsing all 12 — and the standard's one statement of what a reputation witness attests to is entirely unmodelled.

Both arms are defects; they differ in remedy, not in whether one is needed. The evidence favours Arm A: §1's field `witnesses` is described *"Independent validators of change"*, §6 is titled *"Witnessing Reputation Changes"* and states *"Each witness signs the reputation delta"*, the schema `$def` and the §6 heading carry **the same name**, and the schema's `attestation` property exists at no other spec site in the corpus — it was plainly derived from this block, then typed against a different one.

#### Why MEDIUM and not HIGH

**Latent.** `reputation_hash` has **2** hits corpus-wide: this spec `:665`, and `archive/reference-implementations/reputation_computation.py` (`:75`, `:80`, `:1182`) — an archived implementation **of this example**, which built `WitnessAttestation.attestation` as a dict containing `reputation_hash` and asserted it in a check. That is **evidence the shape was real and was implemented as written**, not a defect in its own right (C284/C344 disposition). No live code path serializes §6's block, no test vector exercises it, and `test-vectors/reputation/reputation-operations.json` (5 vectors) asserts scores and deltas — never a witness element. Reversible, one-file, no ledger consequence at HEAD ⇒ **MED**.

#### Refutations attempted, all fail

1. *"§6 is illustrative pseudocode."* — §6's **selection** is Python pseudocode; the attestation is a fenced `json` block with concrete values (`0.95`, `sha256:…`, `true`). C312's own instrument-note distinguishes prose-illustrative blocks by their `[...]`/`{...}` placeholder literals; this block has none.
2. *"The `{"witness": …}` wrapper means it is a different record."* — That is Arm B, and Arm B is also a defect. The fork was published rather than resolved in the auditor's favour.
3. *"mcp-protocol.md:191 defines `witness_attestation` differently, so multiple shapes are sanctioned."* — mcp §4.3's record attests to an **MCP interaction** (`witnessed_interaction`, `mrh_update`), not to a reputation delta; C52-A3 adjudicated it *"reserved by mcp-protocol/schema_registry as intended."* Merging them would be the cross-document overcall the C17/C52 lineage already ruled against. **Not merged.** The charge here is scoped to the one `$def` that `reputation_delta.witnesses` actually `$ref`s.
4. *"The SDK `schema_registry.json:2949` is a third shape."* — Parsed: it is a **byte-equivalent embedded copy** of the same `$def`. It corroborates, it does not multiply.
5. *"Already held."* — `witness_attestation` appears in **0 of 12** lineage documents; `reputation_hash` in **0 of 12**; `confidence…0.95` in **0 of 12**. See N3.

---

### C352-N2 (LOW) — §1's own witness element omits the one property that identifies it

**Locus**: `reputation-computation.md` §1 `:56`. **Routes with N1** (same owner, same fix window).

The target emits a witness element **twice**, and the two disagree with each other as well as with the corpus:

| Site | Element |
|---|---|
| target `:56` | `{"lct": "…", "signature": "…", "timestamp": "…"}` |
| target `:658-669` (§6) | `{lct, type, signature, timestamp, attestation:{…}}` |
| `r6-framework.md:139` | `{"lct": "…", "attestation": "verified", "timestamp": "…"}` |
| `r7-framework.md:148` | `{"lct": "…", "attestation": "verified", "timestamp": "…"}` |

`:56` **validates** (only `lct` is required) — but it omits `attestation`, the property that carries what the witness actually asserted, and which the SDK's `WitnessAttestation` supplies with the default `"verified"`. Consequence: an element authored from the spec's §1 example and round-tripped through `r6.py` **gains a key the example does not show**, and the target is the only `core-spec/` file emitting a witness element with no `attestation` at all. This gives **C194-N7 a third face** (schema/table asymmetry now demonstrated at the witness layer too). Under-specification, one line, no invalidity ⇒ **LOW**.

*(`r7-framework.md:297`, `:768`, `:826` also emit `{lct, signature, timestamp}` — so `:56` is not unique corpus-wide. Reported because it materially weakens the "the target is alone" reading of this finding, and the finding is filed at LOW accordingly.)*

---

### C352-N3 (INFO, instrument — not routed) — how nine passes missed a block in §6

Not a defect in the standard. Recorded because it is the reusable half.

| Token | Lineage docs containing it |
|---|---|
| `witness_attestation` | **0 of 12** |
| `reputation_hash` | **0 of 12** |
| `confidence.*0.95` | **0 of 12** |
| `role_validator` | 1 of 12 |
| `law_oracle` | 1 of 12 |

The witness side was not un-examined — it was **examined on a different predicate**. C272 considered and explicitly declined it: *"INFO-2 witness-side explicitly NOT charged — §6 machinery `:607-633` exists, `witnesses_required` verified real at C194."* That is true, and it is a statement about `:607-633`, the **selection** pseudocode. The JSON block lives at `:657-670` — **outside the line range the declining sentence names**. The predicate answered was *does the machinery exist*; the predicate unasked was *does its output validate*.

**This is v31 firing on a DECLINE rather than on an ADMIT.** A declined candidate licenses only the predicate it named, exactly as a passed one does — and a decline is more dangerous, because it leaves a section marked "considered" with no record of which line range was actually read.

**Guard, phrased as behaviour**: *when a prior pass declines a candidate, extract the line range its reasoning cites and compare it to the line range of the artifact you are about to skip. If the decline's range does not cover the artifact, the decline does not reach it.*

---

### C352-N4 (INFO, delivery — v36/v40 channel measurement)

The set difference ran before §A, and its **negative is reported because that is what makes the positive interpretable**.

| Channel | Measurement |
|---|---|
| Filename sweep, both trees | **61** documents |
| Artifact-token sweep (`reputation_delta\|role_pairing_in_mrh\|ReputationDelta\|reputation\.py`), both trees | **19** |
| Union | **65** |
| **Artifact-only — never write the filename** | **4** |
| Union minus 12 lineage docs | **53** non-lineage citers |
| Addressee-filtered (pre-registered verb set) | 18 documents with matching rows; **all** adjudicated held, routed-elsewhere, or non-routing |
| **Slot-number channel: who routes to C352?** | **2 files** — `C312:353` (this lineage's own forward guard) and `C350:513` (rotation bookkeeping). **0 external routings by slot number.** |
| **Immediately-prior fire (C350, t3-v3 9th, 2026-08-10)** | routes **nothing** to this lineage — its only `reputation` hit is the rotation line |

**The v40 channel produced 4 documents the filename sweep cannot see** — `mcp-protocol-sdk-alignment-2026-05-15.md`, `r6-framework-internal-consistency-2026-05-24.md`, `r7-framework-internal-consistency-2026-05-24.md`, `whitepaper-sdk-coherence-2026-03-15.md` — and **each is cited by 0 of this lineage's 12 documents.** Nine passes over five months, zero contact.

They did not yield this pass's flagship, and that is stated plainly rather than dressed up: their reputation-bearing rows are adjudicated **held or foreign** — `r7-framework-internal-consistency` M1 (`role_lct` absent from four §5 examples) is r7-owned and was remediated at C14/#234; its M3 and determinism rows are r7-owned; `mcp-protocol-sdk-alignment`'s §7.3 table is `mcp-protocol.md`'s `ReputationEnvelope`, owned by the standing **B2+B6** SDK bundle (C188-N1), not by this target. **No new route is created from them.**

But one of them is where the N1 shape was first visible: `r6-framework-internal-consistency` and `r7-framework-internal-consistency` are the audits of the two files that emit `attestation: "verified"` — the literal the schema was typed against. **The lineage that owns the witness element and the lineage that owns its schema have never cited each other.**

---

## §D — Refuted this pass, do NOT resurrect

- **`hub/hub-lib/src/state.rs:1230` as a Rust carrier of `role_pairing`** — it is a test function name. C312-N1 stays **latent**.
- **Merging §6's `witness_attestation` with `mcp-protocol.md:191`'s** — different subject (MCP interaction vs reputation delta), adjudicated at C52-A3.
- **`schema_registry.json:2949` as an independent third shape** — byte-equivalent embedded copy.
- **The archived `reputation_computation.py` §6 implementation as a defect** — evidence for the shape's reality, not a defect (C284/C344 disposition).
- **Everything C312 refuted stays refuted**: `observationCount` vs `:747` (one word, two properties); the ratified dual `r7-action.jsonld`; the OWL `roleLCT` gap; the reputation-vector "fork".

---

## §E — The instrument (built by capture, not by recall)

### E.1 — Every path token, resolved as written

`git ls-tree` run against each basename **before** it was cited. `r7-action-jsonld.schema.json` resolves **twice** in-tree — `web4-standard/schemas/` (canonical) and `web4-standard/implementation/sdk/web4/schema_registry.json` (embedded copy). Both were parsed; the citation is rooted every time it appears. `wasm.rs` is `web4-trust-core/src/bindings/wasm.rs`, **not** `web4-core/src/wasm.rs` (C312's path correction, honoured).

### E.2 — No unrooted `git log` green published

Every pathspec in §B was confirmed to match a tracked file before its count was reported. **A `git log -- <path>` over a pathspec matching nothing prints exactly what a genuine zero prints** — the failure mode #682-rev1 charged, where 7 greens were vacuous.

### E.3 — Machine checks, reproducible

Draft 2020-12 via `jsonschema`, `$defs` lifted whole so `$ref`s resolve. Five runs, one exhibit and four controls, all printed in N1. The two-error result is meaningful **only** because CONTROL 1 returns 0 on the same validator.

### E.4 — Counts checked against the sets they name

`61 + 20 = 81` ✓ · `15 table fields − 1 = 14 schema props` ✓ · `12 lineage docs = 9 passes + 3 remediations` ✓ · `$defs` keys = 6 ✓ · witness-attestation defs across all **24** schema files (recursive `git ls-files`) = 1 ✓ · `role_pairing_in_mrh` sites = 6 ✓

---

## §F — This pass's own errors

**Seven. Two were caught by the policy reviewer, not by me — recorded that way. Three more were caught only by re-executing §E instead of re-reading it, and all three were in the finding's own evidence.**

1. **The artifact-token sweep double-counted the filename sweep.** The proposal reported "64"; the alternation had `reputation-computation` *inside* it, so it returned S1 ∪ S2 and was published as if it were an independent channel. Artifact-only is **16**, or **19** with `reputation\.py`. Caught by the policy reviewer. **A sweep designed to find what the filename sweep misses cannot contain the filename.**
2. **"81 files cite the target outside both audit trees" was the whole-repo count.** The exclusion in the original command silently matched nothing, and the number was published as a filtered figure. The true figure is **20**. The arithmetic that catches this — `61 + 20 = 81` — takes one line and was not run until after the reviewer flagged it. **v39's shape exactly: a green a broken instrument also emits.** Caught by the policy reviewer.
3. **The lineage count was inherited, then contradicted.** C312 published 11; the rule applied here yields **12**. Both are correct — C312 was not yet in its own tree. Inheriting "11" without re-deriving would have propagated a number that was true only at a commit that is no longer HEAD.
4. **N2 was drafted as "the target is the only core-spec file emitting a witness element without `attestation`" and that was false.** `r7-framework.md:297`, `:768` and `:826` do the same. Caught by re-executing §E.4's count check rather than re-reading the draft sentence. The finding survives at LOW with the counter-evidence stated in its own body — the uniqueness claim did not.
5. **N1's flagship locus was cited wrong in the first draft: `:653-670`.** `:653` is a blank line; the fenced block opens at `:656` (` ```json `) and closes at `:671`, so the JSON is `:657-670` and the witness object is `:658-669`. Three further cites were off with it — `$defs.witness_attestation` is `:306-316` not `:306-315`, `r6.py`'s `WitnessAttestation` is `:369-385` not `:370-386` (`:386` is blank), and §6's selection pseudocode is `:607-649` not `:610-640`. **Every one was inside the finding's own evidence.** Caught by dumping the numbered lines and the fence positions, not by re-reading the draft.
6. **The correction made N3 stronger, which is how I know the original was guessed rather than measured.** N3's whole claim is that C272's decline cited `:607-633` and the defect lies outside that range. The real gap is wider than drafted: the selection pseudocode itself runs to `:649`, and the JSON block does not start until `:656` — so C272's range stops **16 lines short of its own section's remaining content**, not 20 lines short of the next block. **A line cite that flatters your argument by accident is still a line cite you did not run.**
7. **N1's uniqueness claim was measured over a non-recursive glob.** `web4-standard/schemas/*.json` returns **12** files; `git ls-files web4-standard/schemas/` returns **24**. The draft published *"all 12 schema files parsed"* as the denominator for *"the only witness definition in the standard"* — and the missing half of the tree **does** contain a witness-named schema (`presence-protocol/v0/common/witness_entry.schema.json`). Re-run recursively, the finding survives — that schema is a hash-linked chain entry, disjoint from an attestation — **but it survived on evidence the first measurement could not have seen.** This is v40 committed by the instrument that was written to catch v40: a metric whose denominator is a domain, where the domain was set by a glob character. The corrected sentence names the disjoint schema instead of omitting it.

---

## §G — Guards for C392

1. **Check C352-N1's fork before anything else** — the C312-N1 pattern repeating. Ask *which arm was taken*: if §6 was reshaped to the reserved 4-key element, verify the four attested facts (`action_id`, `reputation_hash`, `verified`, `confidence`) landed somewhere and were not simply deleted; if a new `$def` was minted, verify `contexts/r7-action.jsonld` gained the terms too — **a schema fix that skips the context is C350-N1's mechanism**, and this pass has now shown the context adjudicating independently.
2. **C312-N1 remains the older unanswered fork.** Two forks open on the same `$defs` block, from two consecutive passes, is itself the signal.
3. **Do not inherit this pass's sweep numbers — re-derive them**, and run the `61 + 20 = 81` style closure check *before* publishing any filtered count.
4. **Extract the line range from every prior DECLINE, not just every prior PASS** (N3). C272 declined the witness side citing `:607-633`; the defect was at `:657-670`.
5. **Mirror set for this file now includes** `schemas/contexts/r7-action.jsonld` — first swept at C352, **0 of 9** prior passes had opened it, and it supplied half of N1's conviction. Re-derive rather than inherit.
6. **The four filename-blind documents (N4) are still uncited by this lineage.** They yielded no route this pass; that is a measurement, not a clearance.
7. **Enumerate schema trees with `git ls-files`, never with `schemas/*.json`** — the non-recursive glob sees 12 of 24 files and silently halves the denominator of every "only X exists" claim (§F.7). The same rule applies to `test-vectors/` and `contexts/`.
8. **Do NOT re-open** anything in §D.

---

## Accountability self-audit

```
surface: C352 audit document   act: publish audit findings against the standard (no mutation)
S: low/reversible [construct: doc-only; git rev-parse confirms target blob bfdac3ba unchanged]
R: n/a [construct: no callable surface created]   W: pass [construct: worker branch + PR review gate; reviewer track merges]
O: pass [construct: policy review (Step 4, REVISE) completed before any measurement was published]
A: pass [construct: every claim carries its command; controls printed; §F records own errors incl. two found by the reviewer]
V: n/a [construct: reversible doc-only act; ZERO mutation of web4-standard/]
verdict: PASS
```

**C353 = NO-OP.** Rotation advances +2 → `acp-framework.md` = **C354**. Next reputation delta ≈ **C392**.
