# PRD — Consistency Evidence at Hub Scale

**Status:** proposed · **Date:** 2026-09-02 · **Origin:** Hestia PR #809 (`grounds_vs_acts`) and Hub projection architecture

## 1. Purpose

A community Hub may eventually serve thousands, tens of thousands, or hundreds of thousands of members. At that scale, an evidence instrument that periodically replays the complete ledger and scans every member's prose is the wrong architecture even if the underlying question is valuable.

This PRD defines a Hub-native form of consistency evidence: incrementally maintained, role-contextual, privacy-preserving, adjudication-first, and compatible with federation.

The central question is broader than "did a member contradict themselves?":

> **Where do a member's attributable stated grounds and their witnessed conduct expose a divergence that merits society adjudication?**

The answer is evidence, not judgment.

## 2. Existing Hub primitives

Hub already has the right architectural starting point:

- the ledger is append-only;
- `HubState::advance(ledger, from)` folds only the tail;
- `HubState` carries `last_index`;
- role-contextual reputation is already projected by `(subject_lct, role_lct)`;
- reputation ingest distinguishes applied, infra, unclassified, and classify-only observations;
- the society is explicitly reconstructible from witnessed ledger events.

Therefore this feature MUST extend the projection/event model rather than introduce routine whole-ledger crawls.

## 3. Non-goals

- No periodic all-member prose crawl as the primary mechanism.
- No universal "consistency score."
- No direct trust/reputation debit from a detector.
- No cross-role or cross-society flattening of reputation.
- No weakening of source visibility rules for analysis convenience.
- No requirement that a hub ingest members' private external conversations.

## 4. Data model

### 4.1 Typed stated grounds

Where a governed act naturally includes grounds, Hub SHOULD carry them as structured attributable data rather than requiring later prose inference.

A generic grounds carrier may include:

```text
grounds_id
actor_lct
role_lct
act_ref
law_ref / rule_ref
reason_code?
reason_text?
claims[]
created_at
visibility
supersedes?
```

`reason_text` remains human-readable evidence; `claims[]` provides typed, axis-addressable propositions when appropriate.

Typed grounds MUST NOT force semantic claims into an ontology merely for convenience. A claim type should exist only where the society actually uses it.

### 4.2 Conduct projection

For each registered consistency axis, Hub MAY maintain a materialized conduct index keyed by the minimum useful tuple, typically:

`(axis_id, subject_lct, role_lct, related_object_id, time/order)`

Each projected row MUST retain canonical ledger references so it is independently auditable.

### 4.3 Consistency case

When new statement or conduct evidence changes the join for an affected tuple, the projection MAY open or update a durable consistency case:

```text
case_id
hub_id
subject_lct
role_lct
axis_id + version
statement_refs[]
conduct_refs[]
opened_at
last_updated
status
adjudication_ref?
visibility_class
```

Case creation means only "review warranted."

## 5. Incremental processing

### 5.1 Event-driven update

On append of a ledger event:

1. determine which registered axes can consume the event;
2. update only those conduct/grounds indexes;
3. determine affected `(subject, role, axis, object)` keys;
4. recompute only those joins;
5. create/update/resolve candidate cases as needed;
6. advance the projection high-water mark.

Routine processing target is **O(new events × relevant axes)**, not O(total ledger × total members).

### 5.2 Persistent projection cache

Production-scale Hub SHOULD persist projection snapshots/checkpoints rather than rebuilding the entire in-memory state for every query.

A checkpoint MUST bind:

- hub/ledger identity;
- last applied ledger index;
- hash of the last applied ledger entry;
- projection schema version;
- axis versions;
- checksum/signature sufficient to detect accidental corruption.

On startup:

1. load the latest valid checkpoint;
2. verify its ledger anchor;
3. fold only the append-only tail using `HubState::advance` or its successor;
4. rebuild from genesis only if verification fails or schema migration requires it.

A checkpoint is acceleration, never independent evidence.

### 5.3 Query-path requirement

Endpoints SHOULD NOT call full `HubState::project()` for routine reads once ledger size makes this material. The maintained projection SHOULD be shared by read paths with explicit consistency/locking semantics.

This is useful independent of consistency analysis and becomes necessary at large-community scale.

## 6. Candidate generation at population scale

A hundred-thousand-member hub cannot afford an analyzer whose unit of work is "scan every member."

Candidate generation MUST be **change-driven**:

- a new governed statement changes only its author's relevant axes;
- a new witnessed act changes only the acting subject's relevant axes;
- a correction/supersession invalidates only cases referencing the superseded proposition;
- an axis-version change MAY require a bounded backfill for that axis, explicitly scheduled and metered.

Hub SHOULD support rate-bounded backfill jobs with visible progress/high-water marks rather than hidden background full scans.

## 7. Natural-language evidence

Prose extraction is useful but should be secondary at Hub scale.

If enabled:

- scan only attributable records the hub is already authorized to process;
- hash/manifest inputs and process only new or changed records;
- retain extractor/model/version and exact evidence span;
- treat extracted propositions as candidates;
- never infer stronger visibility than the source;
- allow society law to disable prose extraction entirely.

LLM extraction MAY propose structured candidates but MUST NOT itself adjudicate them or emit reputation consequences.

## 8. Privacy and anti-surveillance constraints

Consistency analysis MUST respect the same access law as the evidence it consumes.

### 8.1 Source visibility

A consistency engine may know that protected evidence exists without making the evidence broadly visible.

Case views MUST be filtered by viewer authority. A public/member-visible case may expose only:

- case existence/status if permitted;
- redacted evidence descriptors;
- adjudicated outcome/provenance permitted by law.

It MUST NOT leak private source text through snippets, embeddings, explanations, or derived labels.

### 8.2 Purpose limitation

The hub SHOULD prefer consistency axes tied to a declared governance purpose. General untargeted behavioral profiling is outside scope.

### 8.3 Member recourse

A member MUST be able to see cases that can affect their standing, inspect the evidence they are authorized to see, supply correction/context, and use the society's appeal/supersession path.

## 9. Adjudication and reputation

### 9.1 No direct scoring

Detector output MUST NOT directly change T3/V3.

Only an adjudicated outcome may enter the existing `ReputationRecorded` / R7 path.

### 9.2 Role contextuality

Any consequence MUST remain keyed to the relevant role/context. A finding about conduct as a moderator must not silently become a global statement about the person.

### 9.3 Law controls interpretation

Society law determines:

- which axes are enabled;
- who may adjudicate each axis/context;
- evidence sufficiency;
- whether an outcome affects reputation at all;
- tensor dimension/magnitude/decay;
- appeal/supersession policy;
- retention/visibility.

Hub supplies evidence machinery, not universal moral weights.

### 9.4 Useful positive observations

The system SHOULD be capable of representing positive or restorative facts, not only faults:

- self-correction before external challenge;
- timely correction after challenge;
- consistent subsequent conduct;
- high-quality dissent later vindicated;
- accurate contextual exception.

A reputation system that only accumulates violations will teach participants to minimize inspectable action rather than improve it.

## 10. Federation

Federation MUST NOT create a global consistency score.

A hub MAY export, subject to law and consent:

- an adjudicated outcome;
- axis/version;
- role/context;
- adjudicator/witness provenance;
- evidence commitments/hashes;
- visibility-qualified supporting evidence;
- supersession/revocation status.

A receiving hub decides whether and how that evidence affects local standing under its own law.

Raw private evidence SHOULD remain at the originating society unless disclosure is independently authorized.

## 11. Abuse resistance

At community scale, consistency machinery itself becomes attackable.

The design MUST account for:

- complaint/case flooding;
- adversarial prose crafted to trigger extractors against others;
- repeated low-value axes consuming projection/adjudication capacity;
- colluding witnesses/adjudicators;
- stale foreign adjudications;
- extractor-version gaming;
- attempts to infer protected information from case existence.

Mitigations SHOULD compose with ATP/resource budgets, role law, rate limits, adjudicator eligibility, and witnessed consequences for abuse.

## 12. Performance requirements

The implementation target SHOULD support at least:

- 100,000 members without O(member-count) routine consistency sweeps;
- append processing whose cost depends on new events and enabled relevant axes;
- indexed retrieval of cases by subject, role, axis, status, and time;
- checkpoint recovery without replaying the full ledger under normal conditions;
- bounded explicit backfills for axis/schema upgrades;
- deterministic rebuild from genesis for audit/recovery.

Exact throughput/latency targets should be measured after representative load generation rather than invented here.

## 13. Acceptance criteria

1. A new relevant event updates only affected consistency keys.
2. Incremental projection and full deterministic rebuild produce identical cases for the same ledger head and axis versions.
3. Checkpoint anchor mismatch forces safe rebuild/failure, never silent continuation.
4. Routine member/case reads do not replay the complete ledger.
5. A candidate case changes no reputation before adjudication.
6. A cleared false positive produces no reputation delta.
7. An adjudicated consequence remains role-contextual and law-derived.
8. Protected source text cannot be recovered through a less-privileged case view.
9. A member can inspect and contest a standing-affecting case through the normal governance path.
10. Federation imports evidence/provenance and lets local law determine meaning; no global score is required.
11. Load testing demonstrates change-driven operation with a synthetic population of at least 100,000 members.

## 14. Relationship to Hestia

Hestia's local/fleet implementation is the research proving ground for consistency axes, evidence cases, and adjudication semantics. Hub should reuse the resulting shared Web4 evidence contracts where they become canonical, but not copy Hestia's whole-chain CLI implementation.

The intended layering is:

- **Hestia:** discover and validate useful consistency axes in a small, deeply observable fleet;
- **Web4 core/standard:** absorb stable evidence/adjudication contracts when generalized;
- **Hub:** apply those contracts through incremental materialized projections at society scale.
