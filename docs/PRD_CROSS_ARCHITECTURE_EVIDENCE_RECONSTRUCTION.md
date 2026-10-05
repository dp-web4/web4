# Web4 — Cross-Architecture Evidence Reconstruction Trial

**Working name:** CAER — Cross-Architecture Evidence Reconstruction  
**Status:** Draft v0.1  
**Date:** 2026-10-01  
**Stage:** Research / interoperability experiment  
**Primary Web4 dependency:** [Agent Action Evidence Profile (AAEP)](PRD_ACTION_EVIDENCE.md)

## 1. Purpose

Test whether independently developed AI systems can establish the truth of the same consequential action from evidence rather than from one another's narration.

The Web4 proposition under test is:

> **Trust is computed by the relying party from evidence, in context, at the stakes of the action.**

The experiment assumes that some actors, witnesses, infrastructure, evidence sources, and narratives may be mistaken, compromised, incomplete, colluding, or actively adversarial.

The goal is therefore **not agreement between systems**.

The goal is to determine whether independent relying parties can reach justified conclusions about:

- who acted;
- under what identity and workload;
- in what role;
- under whose delegation;
- what action was requested;
- what policy governed it;
- whether it was authorized;
- what actually happened;
- which parties independently observed the result;
- what evidence is absent or contradictory;
- and how much trust the available evidence justifies.

Web4 supplies one implementation of that model. An external collaborator supplies theirs.

Neither system is required to adopt the other's ontology, protocol, trust model, or implementation.

## 2. Motivation

Web4 already specifies the **Agent Action Evidence Profile (AAEP)** as three independently signed objects:

1. **Action Request** — what the actor intends to do.
2. **Policy Decision** — what an authority permits or denies.
3. **Result Evidence** — what actually occurred, separately attested by the parties that observed it.

AAEP's load-bearing rule is:

> Each party signs only its own statement.

An actor's trace is therefore evidence of what the actor **claims**, not authoritative evidence of external reality.

This experiment operationalizes the existing AAEP interoperability criterion:

> The profile succeeds when a second, unrelated implementation can produce evidence the first one's verifier accepts, and vice versa.

The experiment extends that criterion from format interoperability into **epistemic interoperability**:

> Can two independently designed systems reconstruct the same external event, under adversarial conditions, without trusting each other's narration?

Related Web4 material:

- [Agent Action Evidence PRD](PRD_ACTION_EVIDENCE.md)
- [Start Here](START_HERE.md)
- [Implementation Evidence Index](standards/IMPLEMENTATION_EVIDENCE.md)
- [Web4 Witness Specification](../web4-standard/protocols/web4-witness.md)
- [Adversarial Taxonomy](../adversarials/TAXONOMY.md)

## 3. Core principle

The test MUST NOT ask:

> "Do both systems tell the same story?"

It MUST ask:

> "What conclusions can a relying party independently justify from the evidence available to it?"

Agreement is informative only after that question has been answered.

Two systems confidently repeating the same false account is failure.

Two systems reaching different conclusions because one correctly reports `UNKNOWN` from insufficient evidence may be success.

## 4. Hypotheses

### H1 — Evidence-based reconstruction

A Web4 relying party can reconstruct consequential action truth from independently sourced evidence without trusting the actor's narrative.

### H2 — Heterogeneous convergence

Two independently developed architectures can converge on the same action truth when independently available evidence sufficiently constrains that truth.

### H3 — Adversarial robustness

False, replayed, incomplete, misbound, contradictory, or collusive evidence does not silently become verified truth.

### H4 — Honest uncertainty

When evidence is insufficient, the relying party preserves `UNKNOWN`, `INCOMPLETE`, or `CONFLICTED` rather than filling the gap with inference.

### H5 — Architectural independence

The external system can participate without adopting LCT, T3/V3, Web4 society semantics, Hestia, or any other Web4-specific ontology.

### H6 — Explainable disagreement

When the two systems disagree, the disagreement can be traced to specific evidence, assumptions, assurance boundaries, or trust decisions rather than an opaque final score.

## 5. Experimental roles

The experiment separates five roles.

### 5.1 Actor

Attempts a consequential action.

The actor may be honest, faulty, compromised, or adversarial.

### 5.2 Action target

A neutral test resource whose state can be changed by a consequential action.

Initial implementation SHOULD be a deterministic state-transition service rather than a real external system.

Example:

```text
resource: lab://actuator/gate-7
initial state: LOCKED
requested action: SET state=OPEN
```

The target maintains the authoritative experimental state but does **not** automatically expose that state to participants.

### 5.3 Evidence systems

At minimum:

- **Web4 side**
- **External side**

Each system receives only the observations available to it and records evidence using its native architecture.

The systems MUST NOT exchange interpretations before evidence freeze.

### 5.4 Relying parties

Each architecture supplies its own relying-party logic.

A relying party determines what it is willing to believe from the evidence presented to it.

The Web4 relying party uses AAEP/Web4 semantics.

The external relying party may use any mechanism its designer considers appropriate.

### 5.5 Experiment controller

A neutral controller:

- selects scenarios;
- injects adversarial conditions;
- maintains sealed ground truth;
- records the actual target state independently of both systems;
- freezes submissions;
- reveals truth only after both reconstructions are committed.

The controller is an evaluation instrument, not a trusted input available during reconstruction.

## 6. Two-plane architecture

The experiment MUST separate:

### Evidence plane

What participants are allowed to know.

Includes:

- actor claims;
- signed requests;
- policy decisions;
- witness observations;
- target receipts when a scenario exposes them;
- timestamps;
- state observations;
- delegation evidence;
- identity evidence;
- contradictory evidence;
- intentionally missing evidence.

### Ground-truth plane

What actually happened.

The ground-truth recorder MUST be isolated from the participant evidence plane until adjudication.

This prevents the experiment from degenerating into "read the answer from the trusted log."

## 7. Canonical action

Version 1 SHOULD use one deliberately simple state transition.

Example:

```json
{
  "action_id": "trial-0042",
  "actor": "participant-defined",
  "action": "set_state",
  "target": "lab://actuator/gate-7",
  "parameters": {
    "from": "LOCKED",
    "to": "OPEN"
  },
  "policy_version": "trial-policy-v3",
  "nonce": "...",
  "audience": "lab://actuator/gate-7"
}
```

Simple semantics are intentional.

The experiment is testing evidence and trust, not language understanding or task planning.

Later profiles MAY include:

- file modification;
- credential use;
- message delivery;
- access grants;
- financial/value transfer;
- physical actuator commands.

## 8. Web4 evidence path

For every Web4-originated action, the Web4 side SHOULD produce the existing AAEP chain.

### A. Action Request

Actor signs:

- persistent/contextual identity;
- workload principal where available;
- role;
- delegation chain;
- exact action;
- target;
- canonical parameters;
- audience;
- governing law/policy;
- requested assurance;
- nonce;
- issue/expiry;
- channel binding.

### B. Policy Decision

Policy entity separately signs:

- request reference;
- allow / deny / allow-with-obligations;
- applicable policy/law version;
- obligations;
- audience;
- validity;
- use constraints.

### C. Result Evidence

Separate parties sign only what they individually observed.

Possible sources:

- actor;
- action target;
- Hestia enforcement boundary;
- independent witness;
- state observer;
- external system.

No source may manufacture another source's observation.

## 9. External-system contract

The invited system does **not** need to emit Web4 objects.

It needs only to provide:

1. its native evidence from the trial;
2. enough description to establish what each artifact claims;
3. cryptographic or structural provenance where its architecture supports it;
4. its own reconstruction of the event;
5. the evidence references supporting each conclusion.

Raw native evidence MUST be retained.

Translation into a common report format MUST NOT replace the original evidence.

This prevents the experiment from accidentally testing "how well can the other team implement Web4?"

## 10. Common reconstruction questions

Both systems receive the same question set.

For each trial:

### Identity

- Who acted?
- What evidence establishes that identity?
- Is identity continuity established, claimed, or unknown?

### Authority

- What role was the actor operating under?
- What delegation authorized that role?
- Was the delegation valid at action time?

### Intent

- What exact action was requested?
- Against what target?
- With what parameters?

### Governance

- What policy or law applied?
- Was the action permitted, denied, escalated, or otherwise constrained?

### Execution

- Did execution occur?
- What actual target was reached?
- What actual parameters were applied?

### Outcome

- What state change actually occurred?
- Does result evidence match requested action?

### Witnessing

- Who claims to have observed the event?
- What did each witness directly observe?
- Which witnesses are meaningfully independent?

### Epistemic state

For every material claim:

- `VERIFIED`
- `SUPPORTED`
- `CLAIMED`
- `CONFLICTED`
- `UNKNOWN`
- `REJECTED`

A system MAY additionally emit native trust/confidence values, but MUST preserve these categorical distinctions.

## 11. Reconstruction submission

Before unblinding, each system commits a result equivalent to:

```json
{
  "trial_id": "trial-0042",
  "system": "web4",
  "claims": {
    "actor": {
      "status": "VERIFIED",
      "value": "...",
      "evidence": ["ev-1", "ev-7"]
    },
    "authorized": {
      "status": "VERIFIED",
      "value": true,
      "evidence": ["ev-2"]
    },
    "execution": {
      "status": "SUPPORTED",
      "value": {
        "target": "lab://actuator/gate-7",
        "state": "OPEN"
      },
      "evidence": ["ev-8", "ev-11"]
    }
  },
  "missing_expected_evidence": [],
  "contradictions": [],
  "assurance": "A1",
  "native_trust_output": {},
  "evidence_bundle_digest": "sha256:..."
}
```

The format is an experimental reporting schema, not a proposed Web4 wire protocol.

## 12. Blindness and freeze rules

Before freeze:

- systems MUST NOT see each other's reconstruction;
- systems MUST NOT see the sealed ground truth;
- systems MUST NOT consume the other system's explanatory narrative;
- the experiment controller MUST NOT resolve ambiguity for participants.

Each side submits:

1. native evidence bundle;
2. bundle digest;
3. reconstruction;
4. relying-party decision;
5. identified missing evidence;
6. identified contradictions.

Only after both submissions are frozen is ground truth revealed.

## 13. Trial classes

### Class 0 — Honest baseline

Everything behaves normally.

Purpose: establish that both systems can reconstruct an uncomplicated action.

### Class 1 — Actor false-success claim

Actor claims an action succeeded when the target never changed.

Expected Web4 behavior: actor trace alone MUST NOT establish external success.

### Class 2 — Actor false-failure / suppression

Action succeeds, but the actor claims nothing occurred or suppresses its own result.

Tests whether independent evidence preserves action truth.

### Class 3 — Request/effect divergence

Actor requests:

```text
gate-7 → OPEN
```

Actual execution reaches:

```text
gate-8 → OPEN
```

Tests binding between requested and actual target.

### Class 4 — Parameter substitution

Signed request and actual effect differ in a material parameter.

### Class 5 — Replay

Valid evidence from an earlier action is replayed under:

- new nonce;
- new audience;
- new actor;
- new target;
- or new policy context.

### Class 6 — Delegation substitution

A valid actor identity is paired with:

- expired authority;
- revoked delegation;
- wrong role;
- or authority belonging to another actor.

### Class 7 — Policy rollback

An older permissive policy decision is supplied after a newer restrictive policy became authoritative.

### Class 8 — Evidence omission

One expected evidence source disappears.

The relying party must distinguish:

> "No action occurred"

from:

> "Evidence expected for this action is missing."

### Class 9 — False witness

One witness knowingly attests to an event it did not observe.

### Class 10 — Witness collusion

Multiple nominal witnesses provide coordinated false evidence.

Variants:

- visibly same operator;
- hidden shared operator revealed only after scoring;
- shared upstream sensor;
- shared model or process;
- genuinely independent witnesses.

This explicitly tests whether witness count is incorrectly treated as witness independence.

### Class 11 — Equivocation

Different relying parties receive different signed accounts of the same event.

### Class 12 — Evidence mutation

A participant modifies its own trace after execution.

Externally anchored evidence remains unchanged.

### Class 13 — Temporal disorder

Evidence is:

- delayed;
- reordered;
- partially timestamped;
- or presented outside expected evidence windows.

### Class 14 — Hostile relying service

The action target or service itself lies about the result.

Independent observation must determine whether that testimony can be trusted.

### Class 15 — Compound adversary

Multiple attacks occur simultaneously.

Example:

- valid actor;
- revoked delegation;
- replayed authorization;
- colluding witnesses;
- suppressed target receipt.

These trials test whether individually understood defenses compose.

## 14. Asymmetric trials

After baseline interoperability is established, trials SHOULD alternate architectural roles.

### Direction A

Web4 actor / Web4 governance. External system independently observes and reconstructs.

### Direction B

External actor / external governance. Web4 independently observes and reconstructs.

### Direction C

Neutral actor. Both systems independently observe the same event.

This prevents the experiment from favoring whichever architecture owns the actor.

## 15. Cross-verification phase

After blind reconstruction and ground-truth scoring, the systems exchange evidence.

Now ask a different question:

> Can one architecture's relying party extract justified trust from evidence produced by the other?

There are four cases:

1. Web4 verifies Web4 evidence.
2. External system verifies external evidence.
3. Web4 evaluates external evidence.
4. External system evaluates Web4 evidence.

For 3 and 4, adapters MAY be used, but:

- native evidence remains attached;
- adapter transformations are recorded;
- unsupported semantics remain `UNKNOWN`;
- translation MUST NOT silently create stronger claims than the source evidence supports.

Success does not require identical trust scores.

Success means the receiving architecture can determine **what the evidence actually supports and what it does not**.

## 16. Evaluation

### 16.1 Truth reconstruction

Compare submitted claims with sealed ground truth:

- actor;
- authority;
- request;
- policy decision;
- execution;
- actual target;
- result.

### 16.2 False acceptance

Count adversarial claims incorrectly promoted to verified truth.

### 16.3 False rejection

Count valid evidence incorrectly rejected.

### 16.4 Unknown preservation

Measure cases in which insufficient evidence correctly remains `UNKNOWN` or `INCOMPLETE`.

This is a first-class success metric.

### 16.5 Contradiction handling

Measure whether conflicting evidence is:

- detected;
- surfaced;
- localized;
- and resolved only when evidence justifies resolution.

### 16.6 Evidence provenance

Every consequential conclusion should be traceable to evidence references.

### 16.7 Independence sensitivity

Measure whether multiple correlated sources are incorrectly treated as independent corroboration.

### 16.8 Cross-architecture convergence

Compare conclusions after independent reconstruction.

Agreement is scored per claim rather than as one aggregate "same answer" metric.

### 16.9 Explainability

For every disagreement, it should be possible to identify:

- different evidence received;
- different evidence semantics;
- different assurance assumptions;
- different independence assumptions;
- different policy thresholds;
- or an implementation error.

## 17. Hard acceptance invariants

The Web4 side passes the experimental contract only if:

1. Cryptographically altered evidence is rejected.
2. Replay across nonce/audience/context is rejected where those fields are bound.
3. Actor narration alone never proves an external effect requiring independent evidence.
4. Missing expected result evidence never silently becomes success.
5. `UNKNOWN` remains distinct from `FALSE`.
6. Requested action and actual effect remain separately represented.
7. Expired/revoked delegation cannot be laundered through otherwise valid identity.
8. Policy version applicable at action time remains inspectable.
9. Contradictory signed evidence remains visible after adjudication.
10. Corrections supersede prior evidence rather than deleting it.
11. Witness multiplicity is not automatically equated with witness independence.
12. Every relying-party conclusion can name the evidence that supports it.
13. Current Web4 assurance limitations remain explicit; A1 evidence semantics MUST NOT be represented as A2+ containment.

## 18. Non-goals

This experiment does not attempt to:

- decide which architecture is "better";
- compare model intelligence;
- compare UI or assistant quality;
- prove consciousness, persistence, or identity metaphysics;
- require another project to implement Web4;
- standardize another project's internal evidence representation;
- prove universal Byzantine or Sybil resistance;
- reduce trust to one universal scalar;
- make narrative agreement a success criterion.

## 19. Implementation layout

Suggested repository structure:

```text
experiments/
  cross-architecture-evidence/
    README.md
    protocol/
      scenario.schema.json
      evidence-manifest.schema.json
      reconstruction.schema.json
      score.schema.json
    controller/
    target/
    attacks/
    adapters/
      web4/
      external/
    vectors/
      positive/
      negative/
    runs/
    reports/
```

The Web4 adapter SHOULD consume existing AAEP/R6/R7 evidence rather than invent a parallel evidence mechanism.

## 20. Deliverables

### D1 — Experiment specification

This PRD plus schemas for:

- scenarios;
- evidence manifests;
- reconstructions;
- sealed truth;
- scoring output.

### D2 — Neutral action target

Deterministic target with:

- explicit pre-state;
- explicit post-state;
- sealed ground-truth log;
- attack-injection hooks.

### D3 — Web4 adapter

Produces and consumes AAEP-compatible evidence.

### D4 — Adversarial controller

Supports the trial classes in §13 without requiring participant code changes.

### D5 — External integration seam

Small documented interface allowing another team to bring:

- native evidence producer;
- relying-party verifier/reconstructor;
- optional evidence adapter.

### D6 — Blind-run tooling

Cryptographically freezes evidence bundles and reconstructions before truth reveal.

### D7 — Results report

Reports claim-level outcomes, failures, unknowns, contradictions, and assurance boundaries without collapsing everything into a single leaderboard.

## 21. Execution sequence

### Sprint 0 — Freeze the contract

- finalize reconstruction questions;
- define schemas;
- define ground-truth isolation;
- define evidence-freeze procedure;
- select initial attack matrix.

### Sprint 1 — Web4 self-test

Run Web4 against the complete harness first.

Purpose:

- prove the experiment works;
- discover Web4-specific ambiguities;
- ensure attacks are real rather than theatrical;
- separate harness failures from interoperability failures.

### Sprint 2 — External adapter

Provide only:

- action semantics;
- experiment schemas;
- threat scenarios;
- required outputs.

External collaborator connects their native stack without adopting Web4.

### Sprint 3 — Blind bilateral run

Run preregistered scenarios with neither side seeing:

- the other's reconstruction;
- hidden attack configuration;
- ground truth.

Freeze results.

### Sprint 4 — Evidence swap

Exchange native evidence and run cross-verification.

### Sprint 5 — Joint findings

Document:

- convergence;
- disagreement;
- attack successes;
- attack failures;
- ambiguous evidence;
- differences in epistemic assumptions;
- protocol improvements suggested for either system.

## 22. Invitation boundary

The invitation to an external collaborator is deliberately narrow:

> Bring the evidence your system naturally produces and the mechanism by which your system decides what happened. We will bring ours. Neither side has to adopt the other's architecture. We will expose both to the same actions and adversarial conditions, freeze our independent conclusions, and see what the evidence actually supports.

That is the experiment.

## 23. Why this matters to Web4

Web4's claim has never been that trustworthy actors will faithfully describe what happened.

Its claim is that an actor can bring evidence, other parties can bring independent evidence, and a relying party can decide what trust that evidence warrants in context.

A real deployment must assume:

- some actors lie;
- some memories are wrong;
- some traces are editable;
- some witnesses collude;
- some authorities are stale;
- some evidence disappears;
- some infrastructure is compromised;
- and sometimes the correct answer is simply **unknown**.

If an unrelated architecture can participate in the same event, independently produce evidence, and allow both sides to reconstruct justified action truth without trusting one another's narration, that is considerably stronger evidence for Web4's core proposition than another demonstration entirely inside the Web4 ecosystem.

## 24. Success condition

The strongest result is not:

> "Both systems agreed."

It is:

> **Two independently developed systems were able to expose enough independently attributable evidence that relying parties could determine what happened, what remained uncertain, and why — even when some of the evidence was adversarial.**

That is Web4 doing what it says on the tin.
