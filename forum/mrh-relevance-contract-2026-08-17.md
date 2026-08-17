# MRH as a Relevance Contract: Web4 Implications

**Date:** 2026-08-17  
**Status:** forum / candidate architectural interpretation  
**Source:** `dp-web4/Synchronism/forum/Markov_Relevancy_Horizon_as_Relevance_Contract.md`

A Synchronism Markov/coherence exploration has converged with several structures already present in Web4.

The candidate refinement is:

> **MRH is a witness-relative contract over which distinctions still matter for the present question.**

This is broader than a graph radius or fixed `horizon_depth`. Relationship depth remains a useful implementation coordinate, but the same relevance boundary can also be temporal, evidentiary, policy-relative, lineage-relative, evaluator-relative, and assurance-relative.

## Why this matters to Web4

Web4 already says that trust is contextual and that LCT presence is established through witnessed relationships rather than a universal identity authority. The current LCT structure also carries MRH relationships, policy, T3/V3, attestations, lineage, and revocation.

The new synthesis suggests that those pieces can be interpreted more cleanly if MRH is treated as the **justified set of distinctions a relying party must retain for one decision**, rather than as only the neighborhood around an entity.

For example, a relying party asking:

- "is this token a valid descendant of the token I admitted?";
- "is it the only recognized live continuation in this society?";
- "does the current descendant still satisfy the policy behavior I relied on?";
- "what trust evidence does my evaluator actually consume?";

has four different relevance horizons even when all four questions concern the same LCT.

## Prediction and provenance should stay orthogonal

One important correction from the arc is that behavioral equivalence and historical identity are different axes.

Two entities may be equivalent for a particular interaction while having different provenance. A clone and an authorized continuation can behave identically while carrying different authority, obligation, sanction, delegation, or inheritance histories.

So a useful governed-identity picture is:

\[
\text{predictive/relevance quotient}
+
\text{provenance position}.
\]

The first permits irrelevant distinctions to be compressed. The second preserves which historical token this actually is.

That fits LCT lineage better than forcing lineage itself to define behavioral sameness.

## Claim-specific proof horizons

A complete witness/provenance history should not imply that every ordinary decision must traverse the entire history.

A relying party can instead receive a claim-specific proof bundle containing the relevant lineage, witnesses, law references, registry commitments, or trust receipts needed for its question.

The full authoritative record remains available because a later question may expand the MRH and make previously omitted history relevant again.

Thus:

> **local proof compression should not imply destruction of authoritative provenance.**

## Freshness becomes dependency-relative

The same perspective adds a forward-looking side to MRH.

An old proof can remain semantically current through thousands of unrelated events. A brand-new proof can become stale immediately when one of its load-bearing dependencies changes.

So evidence should ideally state not only when it was produced, but **what changes invalidate it**.

That suggests a useful duality:

- the dependency contract determines what evidence must be fetched;
- the same dependency contract determines what future changes make the result stale.

Maintaining those as unrelated hand-written rules would invite drift.

## A possible common interface, not a new mega-schema

The repeated metadata can be summarized conceptually as:

```text
RelevanceBasis {
    claim_kind
    subject/context
    evaluator/plan
    authoritative basis state
    dependency contract
    completeness for this claim
    assurance basis
    lineage references
    escalation / re-expansion path
}
```

This should **not** replace LCTs, AssuranceReceipts, trust receipts, policy proofs, or other domain-specific objects.

The useful direction would be a small shared interface that lets a relying party ask the same meta-questions of each:

- what exactly is this claiming?
- what did the evaluator depend on?
- what authoritative state is it tied to?
- is this basis complete for this claim or merely a projection?
- what assurance supports it?
- what change would invalidate it?
- how do I expand the evidence horizon if my stakes require more?

## Escalation as MRH expansion

This gives escalation a particularly clean interpretation.

When the current basis is insufficient, the response need not be a negative verdict. It may be:

```text
local lineage -> authoritative registry/fencing proof
windowed trust -> full relevant witness traversal
old proof + delta -> historical backfill to anchor
weak assurance -> stronger assurance ceremony
```

In that sense:

> **escalation is deliberate MRH expansion until the question is decidable at the required assurance.**

## Posture

No normative Web4 change is proposed here yet.

Most mathematical ingredients have established neighbors in coarse-graining, predictive equivalence, provenance slicing, dependency analysis, and incremental computation. The useful contribution is the systems synthesis and its fit with structures Web4 already has.

The compact principle worth testing against future design work is:

> **retain the distinctions that matter to the relying party's present question, make that relevance boundary inspectable, and preserve the ability to expand it when the question or stakes change.**
