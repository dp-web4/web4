# PRD — Web4 Lawbook IR Prototype

**Status:** draft for implementation  
**Date:** 2026-10-03  
**Scope:** Hub law / SAL / shared `web4-policy` semantics  
**External reference:** https://github.com/EffortlessAPI/effortless-rulebooks  
**Companion:** Hestia `docs/PRD_LAWBOOK_IR.md`

## 1. Problem

Web4 already has most of the right law machinery:

- SAL defines **Law as Data** and a versioned Law Dataset.
- Hub law has a typed YAML authoring surface.
- `hub-law-schema.md` maps that surface to canonical RDF.
- `web4-policy` provides the shared evaluator.
- Hub signs, witnesses and enforces law before governed acts commit.
- Hestia already consumes Hub law through the same canonical evaluator.

The remaining weakness is representational drift.

Today the same law semantics appear in several forms:

- YAML;
- RDF / JSON-LD;
- Rust types and evaluator behavior;
- Hub CLI/admin surfaces;
- Hestia's local LawGate projection;
- prose documentation;
- tests and examples;
- deny/escalation guidance;
- future UI representations.

Those surfaces are intended to agree, but agreement is mostly maintained by review and tests written around individual seams.

The design goal of this PRD is to make law itself a **canonical semantic IR** — a **Lawbook** — from which those surfaces are projections, and to make projection agreement mechanically testable.

This is not a proposal to replace RDF with another private format.

> **The Web4 Lawbook is a logical typed law model. Canonical verification remains RDF; YAML remains an ergonomic authoring projection.**

The transferable lesson from Effortless Rulebooks is the discipline:

> **one semantic source, many projections, conformance measured rather than assumed.**

## 2. Current-state anchors

The prototype must preserve, not replace, current working semantics.

### 2.1 Existing authoritative pieces

- `web4-standard/core-spec/web4-society-authority-law.md`
  - Law Oracle;
  - versioned Law Dataset;
  - norms, procedures, interpretations;
  - authority and quorum;
  - law-hash pinning;
  - witnessed law updates.

- `web4-standard/core-spec/hub-law-schema.md`
  - ergonomic YAML surface;
  - RDF canonical mapping;
  - decision vocabulary;
  - response vocabulary;
  - validation rules.

- `hub/hub-lib/src/law.rs`
  - Hub specialization over the shared `web4-policy` evaluator.

- `hub/docs/HUB-LAW.md`
  - live Hub enforcement semantics and amendment path.

### 2.2 Existing invariant

The prototype MUST NOT create a second law engine.

Hub and Hestia already converged on `web4-policy` for society-law evaluation. The Lawbook sits **above** execution engines as the semantic source and conformance oracle.

## 3. Product thesis

A society's law should be queryable as one structured object that can answer:

- What rules exist?
- Which version was in force at time T?
- Who had authority to amend each rule?
- Which procedure governs amendment?
- Which appeal path applies to a denial?
- Which interpretation supersedes which?
- What tests prove the rule behaves as declared?
- Which projections were generated from this law version?
- Do Hub, Hestia and human-readable renderings still agree?
- Is any rule unreachable, untestable, orphaned, stale, or internally inconsistent?

A Lawbook therefore contains not only executable norms, but **governance metadata about the law itself**.

## 4. Canonical object model

The initial prototype should model these objects explicitly.

| Object | Purpose |
|---|---|
| `Lawbook` | One versioned law corpus for a society/context. |
| `Rule` / `Norm` | Atomic pre-act decision rule. |
| `ResponseRule` | Post-recognition response rule. |
| `Procedure` | Required process: witness/quorum/review/appeal. |
| `AuthorityRole` | Who may create, amend, interpret, suspend or retire law. |
| `EffectivePeriod` | When a rule/version is in force. |
| `AmendmentRequest` | Proposed law change as a first-class object. |
| `Approval` | Authority decision on an amendment. |
| `WitnessAttestation` | Evidence of quorum / witnessing. |
| `Interpretation` | Precedent or interpretation tied to the rule/version it affects. |
| `AppealPath` | Machine-queryable route from a decision to review/adjudication. |
| `LawTestCase` | Scenario + expected decision/derivation. |
| `DecisionDerivation` | Why the law yields a decision for a specific request. |
| `Projection` | YAML/RDF/RuleSpeak/engine fixture/etc. generated from a Lawbook version. |
| `ProjectionWitness` | Evidence that a projection conforms to the Lawbook version. |
| `ComputedWitness` | Derived governance-integrity predicate. |

The prototype does not need all objects to be executable in Sprint 1. It does need stable identifiers and relationships so later projections do not require another ontology.

## 5. Rule semantics

### 5.1 Preserve current Hub decision semantics

The Lawbook prototype MUST preserve current `web4-policy` semantics:

- decisions: `allow | warn | deny | escalate`;
- selectors over R6 request/resource/context;
- declared operators;
- priority/conflict behavior;
- escalation target;
- procedures;
- response rules and consequence classes;
- default behavior.

The prototype is not an opportunity to silently change policy behavior.

### 5.2 Explicit effective-law semantics

Every executable rule MUST be able to answer:

- lawbook version;
- rule version;
- effective-from;
- effective-to / superseded-by;
- authority that approved it;
- approval/witness evidence;
- projection hash used at decision time.

A decision transcript should therefore be able to identify the exact law state, not merely `version: 1.0.0`.

## 6. Computed witnesses

This is the most transferable implementation idea.

Governance defects should become **derived facts**, not reviewer advice.

Initial computed witnesses:

| Witness | Fires when |
|---|---|
| `RuleUnreachable` | selector/action vocabulary can never be emitted by the governed surface. |
| `RuleNeverFiresOnCorpus` | rule is syntactically valid but no conformance scenario can activate it. |
| `ConsequentialActionUngoverned` | a consequential action reaches only permissive/default behavior without an explicit norm. |
| `EscalationTargetInvalid` | escalation target is not a valid role/authority. |
| `EscalationTargetUnoccupied` | valid role exists but no currently effective occupant can resolve it. |
| `AppealPathUnreachable` | a decision promises appeal/review but no executable route exists. |
| `AmendmentMissingAuthority` | rule/version became effective without authorized approval. |
| `AmendmentMissingWitness` | required quorum/witness evidence is absent. |
| `EffectiveBeforeApproval` | rule/version effective timestamp precedes ratification. |
| `SupersededLawSelectable` | an older rule/version can still be selected as active after supersession. |
| `ProjectionStale` | projection hash/version does not match the active Lawbook. |
| `ProjectionDecisionMismatch` | two executable projections disagree on the same test case. |
| `ExplanationMismatch` | human/machine explanation names a rule or path different from the evaluator result. |

A witness result MUST identify:
- lawbook version;
- source objects;
- derivation;
- severity/class;
- whether it blocks activation or is advisory.

## 7. Projections

The prototype should treat these as projections of the same law semantics.

### 7.1 Required prototype projections

1. **Canonical RDF**
   - verification / exchange representation;
   - stable IDs;
   - semantic relationships.

2. **Hub YAML**
   - operator-editable;
   - round-trip testable;
   - no semantics that cannot be represented in canonical law.

3. **Hub evaluator fixture**
   - input consumable by `web4-policy`;
   - current behavior preserved.

4. **RuleSpeak-style human rendering**
   - deterministic prose generated from structured law;
   - never authoritative over the structured source.

5. **Conformance corpus**
   - input requests;
   - expected decision;
   - winning rule;
   - escalation target;
   - relevant procedure;
   - appeal path;
   - derivation trace.

### 7.2 Hestia projection

The companion Hestia PRD defines the Hestia-specific projection and local-policy extension.

The Hub prototype MUST expose enough normalized structure that Hestia can consume the same law version without hand-translating semantics.

## 8. Decision derivation graph

For every conformance case, the Lawbook should be able to emit a deterministic derivation graph:

```text
request facts
  -> selector resolution
  -> predicate/operator results
  -> matching rule set
  -> priority/conflict resolution
  -> escalation/veto checks
  -> winning rule
  -> decision
  -> resolver / procedure
  -> appeal path
```

This is analogous to an ExplainDAG.

Important boundary:

> **A law derivation proves why declared law yields a decision. It does not prove the real-world action occurred.**

Runtime action evidence remains the job of Web4/Hestia witnessed execution records.

## 9. Prototype slice

Do not start with all society law.

Use a deliberately small real slice already exercised in Hub:

- `DEFAULT-ALLOW`;
- `ESCALATE-MEMBER-JOIN`;
- `ESCALATE-ROLE-ASSIGN`;
- `ESCALATE-LAW-AMEND`;
- `WITNESS-3`;
- one explicit appeal/review path;
- one response rule if the response-side schema is stable enough.

The slice must be large enough to exercise:
- allow;
- deny or escalation;
- priority;
- authority;
- procedure;
- amendment;
- conformance;
- explanation.

## 10. Cross-substrate conformance

For one Lawbook version, execute the same corpus through:

1. canonical `web4-policy` evaluation used by Hub;
2. Hestia LawGate projection;
3. any generated test oracle / reference evaluator.

Compare at minimum:

- decision;
- winning rule ID;
- rule version;
- escalation target;
- consequence/stakes metadata when present;
- required procedure;
- appeal path;
- lawbook/version/hash;
- explanation/derivation root.

A mismatch is a test failure, not a documentation note.

## 11. Amendment model

A law amendment should eventually become a structured transition:

```text
AmendmentRequest
  -> proposed object delta
  -> impact findings
  -> conformance run
  -> authority approval
  -> witness/quorum
  -> effective timestamp
  -> new Lawbook version
  -> generated projections
  -> projection-conformance witnesses
  -> activation
```

The existing `hub set-law` path remains the operational path during the prototype.

Sprint 1-3 must not change activation semantics. The prototype first demonstrates that the current amendment can be represented and verified under this model.

## 12. Non-goals

Initial prototype does NOT:

- replace RDF;
- replace `web4-policy`;
- redesign R6/R7;
- change Hub decision semantics;
- create a second policy language;
- make Hestia local machine policy identical to society law;
- prove action execution from decision derivation;
- define universal trust thresholds;
- solve all interpretation/precedent semantics.

## 13. Implementation plan

### Sprint 0 — model + fixture

Deliverables:
- `lawbook.schema.json` or equivalent typed prototype schema;
- RDF mapping note;
- one canonical Lawbook fixture encoding the prototype slice;
- stable object IDs;
- explicit effective periods / authority / appeal path.

Acceptance:
- fixture validates;
- every current Hub YAML rule in the slice maps without semantic loss.

### Sprint 1 — projections

Deliverables:
- Lawbook -> Hub YAML projection;
- Lawbook -> RDF projection;
- Lawbook -> RuleSpeak Markdown projection;
- round-trip comparison for supported fields.

Acceptance:
- generated Hub YAML parses with current Hub validator;
- generated YAML produces the same `web4-policy` decisions as the hand-written fixture.

### Sprint 2 — computed witnesses

Deliverables:
- initial witness evaluator;
- at least: unreachable rule, invalid escalation target, missing appeal route, stale projection;
- machine-readable witness report.

Acceptance:
- seeded broken fixtures make each witness fire;
- clean fixture passes.

### Sprint 3 — conformance corpus

Deliverables:
- shared scenario corpus;
- Hub evaluator runner;
- Hestia runner;
- comparison report.

Acceptance:
- same law version yields identical expected decision metadata on both substrates;
- seeded mismatch fails deterministically.

### Sprint 4 — amendment proof

Deliverables:
- structured AmendmentRequest fixture;
- before/after Lawbook versions;
- approval/witness records;
- generated projections;
- diff + conformance report.

Acceptance:
- old and new effective periods are unambiguous;
- active version cannot be confused with superseded projection;
- amendment has a reproducible evidence chain.

## 14. Success criteria

The prototype succeeds if a reviewer can start from one Lawbook version and mechanically answer:

1. what law was in force;
2. who authorized it;
3. what each projection contains;
4. whether Hub and Hestia agree on the same governed scenarios;
5. why a decision occurred;
6. whether the denial/escalation has a reachable resolution path;
7. whether any known law-integrity witness is failing.

The prototype fails if the reviewer still has to compare prose, YAML, Rust and Hestia behavior manually to establish semantic agreement.

## 15. Relationship to Effortless Rulebooks

External reference:
https://github.com/EffortlessAPI/effortless-rulebooks

Useful transferable patterns:

- one semantic IR, many projections;
- no privileged execution substrate;
- generated human rendering;
- cross-substrate conformance;
- derivation graphs;
- computed governance witnesses.

Web4 retains its own ontology, RDF canon, identity, authority, witnessing and runtime evidence model.

This is architectural cross-pollination, not a dependency.

## 16. First implementation question

The first implementation spike should answer one bounded question:

> **Can the existing Hub starter-law slice be represented once, projected into current Hub law without semantic loss, consumed by Hestia through the same law version, and proven conformant by one shared scenario corpus?**

If yes, expand.

If no, record exactly which semantics resist canonicalization before designing around them.
