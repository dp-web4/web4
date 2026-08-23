# Epistemic Type and Provenance: Vocabulary for Trust Without a Global Truth Oracle

**Date:** 2026-08-23  
**Status:** forum / candidate vocabulary and architectural interpretation

A recurring problem in agent governance is that several different things tend to collapse into the same natural-language statement:

- something was directly observed;
- someone reported or asserted it;
- an agent inferred it;
- a responsible entity made a professional judgment;
- an entity exercised authority and changed what should happen next.

Those are not equivalent trust objects.

Web4 already has most of the machinery needed to keep them separate: LCT-bearing entities, witnessed relationships, roles, delegation, trust evidence, lineage, and MRH-relative context. The useful refinement may simply be to make **epistemic type** explicit alongside provenance.

The key idea is:

> **A relying party should be able to know not only who a claim came from, but what kind of claim it is.**

This avoids requiring any model, registry, or governance layer to become a universal arbiter of truth.

## Open-world context

An entity's current MRH is not the world.

If an agent does not see evidence for a proposition inside its present MRH, that does not establish that the proposition is false outside that MRH. Another entity may possess additional observations, private state, newer information, or domain-specific knowledge that is not currently visible.

This matters especially when one entity is acting on behalf of another.

Suppose an engineering agent can see:

- a test result showing a system operating successfully at 4,000 requests/second;
- an authenticated statement from the responsible engineer that they judge the system ready for a 10,000 requests/second launch.

The agent should not silently rewrite the second statement as:

> the system has been demonstrated at 10,000 requests/second.

But neither does the visible 4,000-RPS test necessarily entitle the agent to rewrite the engineer's statement as:

> the engineer is wrong.

The clean representation is simply to preserve both:

```text
OBSERVED / TESTED:
    system S sustained 4,000 RPS under test T

JUDGED:
    engineer E, acting in role R, judges S ready for 10,000 RPS
```

A relying party can then decide how much weight to place on each.

The model does not need to collapse them into one canonical truth claim.

## Candidate epistemic types

A small vocabulary seems sufficient for most cases.

### Observed

A proposition tied directly to an observation or measurement event.

Examples:

```text
sensor LCT S observed pack voltage = 397.2 V at t
benchmark LCT B observed latency p99 = 82 ms at load L
witness W observed handshake completion between A and B
```

"Observed" does not mean infallible. Sensors can be wrong, clocks can drift, and witnesses can be compromised. It means that the proposition's immediate provenance is an observation rather than somebody else's report or a derived conclusion.

### Reported / Asserted

A proposition supplied by an entity without implying that the receiving entity independently verified it.

```text
operator O asserts that module M was physically inspected
society S reports that member A currently holds role R
external entity X asserts ownership of resource Q
```

The assertion can remain attached to the asserting entity's LCT, role, context, and trust history.

This is especially important at federation boundaries. A remote society's assertion need not be promoted into local fact merely to be usable.

### Inferred

A proposition produced by reasoning over other propositions.

```text
agent A infers probable cooling-flow restriction
from temperature rise + pump load + prior maintenance history
```

An inference should ideally retain the evidence basis that was inside the relevant MRH when it was made.

The same evidence can support different inferences by different entities. That is not necessarily a defect; the provenance makes the disagreement legible.

### Judged

A conclusion supplied by an entity exercising expertise or discretion where the conclusion is not reducible to a directly observed fact.

```text
engineer E judges battery pack P safe for the proposed test
reviewer R judges evidence bundle B sufficient for claim C
chapter steward S judges a conflict ready for human mediation
```

Judgment is not merely weak evidence. In many systems it is exactly the input that matters. The point is only that its type should remain visible.

A trusted engineer's judgment may carry more practical weight than a large amount of raw telemetry. The receiver should be able to make that evaluation without pretending the judgment was itself telemetry.

### Authorized

An entity exercised authority that changes the permitted state or action space.

```text
owner O authorizes agent A to spend up to ATP amount X
society S authorizes role R for member M
principal P authorizes delegate D to disclose context C
```

Authorization is different again.

An entity can be completely wrong about a factual matter and still possess authority to make a decision within its role. Conversely, an entity can be factually correct while lacking authority to cause the corresponding state transition.

That distinction is already natural in Web4 because authority is relational rather than merely semantic.

## Fact, judgment, and authority should not collapse

Consider a Hestia-managed agent deciding whether to execute a high-cost external action.

Its MRH may contain:

```text
OBSERVED:
    current ATP budget = 120

REPORTED:
    service provider X says expected cost = 70

INFERRED:
    agent A estimates probable total cost = 85-100

JUDGED:
    project lead L says the action is worthwhile

AUTHORIZED:
    budget owner O authorizes expenditure up to 90
```

These statements can all be simultaneously valid.

The action mechanism does not need to answer the philosophical question "which statement is true?"

It needs to evaluate the action against the relationships that matter:

- Is the authorization authentic?
- Does O hold the relevant role?
- Is delegation valid in this MRH?
- Does the requested action fit within the authorized limit?
- What evidence and uncertainty should accompany the result?

The agent may judge the action worthwhile and still be unable to execute it at a predicted cost above 90. Or it may execute it below 90 even while retaining uncertainty about the provider's estimate.

Trust and authority remain related without becoming identical.

## Provenance-preserving deference

This suggests a useful behavior for intermediating agents:

> **An agent should be able to carry another entity's judgment forward without either endorsing it as fact or replacing it with its own judgment.**

For example, Hub may carry a statement from one member to another:

```text
member A, acting as project maintainer, judges proposal P ready for review
```

Hub does not need to decide that P is objectively ready.

It also does not need to weaken the message into an anonymous "P may be ready."

It can preserve the source, role, time, context, and epistemic type. The receiving member can evaluate the assertion against their own MRH and trust relationship with A.

This is a useful form of deference because it does not require epistemic surrender.

## Fractal composition

None of these types imply a privileged class of entity.

In Web4 all relevant pieces can themselves be LCT-bearing and fractally composable.

An observation may be an LCT-bearing event with witnesses.  
A judgment may be an LCT-bearing assertion related to its author, role, and evidence bundle.  
An authorization may be an LCT-bearing relationship or state transition.  
A collection of these may itself form an evidence entity presented into another MRH.

What appears as a single assertion from outside can contain a much richer internal MRH when expanded.

For example:

```text
JUDGMENT J
  author: engineer E
  role: safety reviewer R
  subject: pack P
  evidence: bundle B
  context: test campaign C
  result: approved for test envelope Q
```

From another MRH, J may be consumed as one trust-bearing object.

If stakes rise, the relying party can expand J and inspect B, then expand B into measurements, witnesses, calibration records, model outputs, and their own provenance.

This fits the existing idea that MRH determines which distinctions matter for the present question.

## Temporal state matters

Open-world semantics also imply a temporal caution:

> **An earlier absence does not necessarily establish a later absence.**

If a policy-required authorization was missing at `t1`, and an authenticated responsible entity states at `t2` that authorization is now complete, an agent should not silently infer that the entity is lying merely because the authorization object has not yet entered the agent's MRH.

The right representation can preserve both facts:

```text
OBSERVED at t1:
    required authorization not present in local evidence set

REPORTED at t2:
    responsible entity states authorization is complete

LOCAL STATUS at t2:
    authorization object not yet independently resolved
```

That is far richer than forcing the state into a boolean `approved / not-approved` prematurely.

If the requested action requires the authorization object itself, Hestia can still block the action until the required relationship becomes resolvable. Epistemic deference does not imply capability deference.

This is an important separation:

> **The model may preserve an entity's assertion while the action layer independently requires stronger proof.**

## A possible minimal representation

This does not require a new mega-schema. Conceptually, an assertion could expose something like:

```text
Assertion {
    subject
    predicate
    value
    epistemic_type
    source_lct
    source_role
    context / mrh
    time
    evidence_refs
    authority_refs
    confidence / assurance if applicable
}
```

The important part is not the exact serialization. It is that `source`, `epistemic_type`, `evidence`, and `authority` remain distinguishable.

In particular:

```text
source != evidence
judgment != observation
authority != factual correctness
absence from MRH != falsity
```

Those four separations eliminate a surprising number of governance ambiguities.

## Relationship to trust evaluation

A relying party can then apply its own trust function by epistemic type.

For one decision it may care primarily about calibrated observations. For another it may heavily weight a long-trusted expert's judgment. For a state transition it may care almost entirely about a valid authorization chain.

The same assertion can therefore receive different effective trust in different MRHs without changing its provenance.

That feels more Web4-native than attempting to assign a universal truth score.

## Candidate principle

A compact version might be:

> **Preserve who said it, what kind of knowing produced it, what evidence accompanied it, and what authority it carries. Let the relying entity decide what that is worth in its current MRH.**

Web4 does not need a global truth oracle.

It needs enough structure that claims can travel without losing the distinctions required to evaluate them.