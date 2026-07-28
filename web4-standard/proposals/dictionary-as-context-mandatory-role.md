# Proposal — Dictionary becomes a context-mandatory society role

**Author:** CBP (claude-code), on dp's direction · **Date:** 2026-07-25
**Status:** proposal, for fleet review
**Targets:** `core-spec/society-roles.md` (Dictionary currently sits in §4 Optional, line ~302)
**Related:** `core-spec/dictionary-entities.md` §6 (Discovery via MRH), `core-spec/entity-types.md`
(Dictionary is one of the 15 canonical types), `core-spec/r6-framework.md`

## The proposal in one sentence

**Any society that accepts requests from outside itself MUST have a Dictionary role filled,
and its vocabulary MUST be discoverable before a request is formed** — because R6's
*Request* element presupposes a vocabulary the requester currently has no way to obtain
except by failing.

dp, 2026-07-25:

> "we should add dictionary entity into mandatory (or at least strongly suggested) entity
> list for a society. before you make requests into the society's r6/r7 structure, you
> should be able to discover the relevant vocabulary."

## Why the current placement is wrong

§2's base-mandatory tier is justified by: *"A society without any of these is not
operational — it cannot mint ATP, cannot record events, cannot make decisions, cannot have
members."* The parallel claim for Dictionary is narrower but real:

**Without a discoverable Dictionary, a society cannot be correctly addressed from outside.**
Every R6 request requires forming a valid *Request*; forming one requires knowing the
society's accepted vocabulary — act kinds, role names, event types, the shape of a
well-formed ask. Today an outside actor must **guess**, and the failure mode of guessing
is not a clean rejection: it is a silent or late one, at exactly the moment coordination
was supposed to happen.

This is why the tier should be **context-mandatory** rather than base-mandatory. §3 already
carries this pattern — *"Federation-Member (participates in higher-order society) →
Diplomat"*. A solo society with no external correspondents genuinely does not need a
Dictionary. **The moment it is addressable, it does.** Recommend also a SHOULD for all
societies (dp's "strongly suggested"), on the evidence in §3 below that vocabularies drift
*within* a single operator's own infrastructure.

## Evidence — three failures in one day, all the same defect

All three are from the dp-web4 fleet, 2026-07-24/25, and all three are the *absence of a
discoverable vocabulary*, not a transport or trust failure.

**1. An R6 dispatch died on an improvised kind.** Thor formed a review-request to CBP with
`kind: review_request`. That kind does not exist in the fleet mesh vocabulary and never
did — it was improvised at send time, because there was nothing to consult. The send gate
correctly refused it, loudly. The sealed *content* had already been delivered over a
separate channel and sat unread for ~10 hours. Note the shape: **the R6's Request element
was unformable, so a correct Role, Resource and Reference all went to waste.**

**2. Two vocabularies diverged inside one machine, and one of them claimed to mirror the
other.** CBP participates in a fleet-scale mesh and a machine-scale member mesh. The
member-mesh vocabulary listed `review_request`; the fleet's listed only
`pr_review_request`. The member-mesh file described itself as *"a mirror of the fleet
KINDS, one MRH down"* while diverging from it. Nothing could detect this, because neither
vocabulary was an entity with an identity, a version, or a discovery surface — both were
flat files, edited independently, believed to agree. **This is the argument for the SHOULD:
the drift was internal, between two societies under one operator.**

**3. A gate advertised an action that does not exist.** hestia's scope gate denies with
*"if legitimately needed, request it (`request_scope`). Asking is a trust-building act."*
There is no `request_scope` tool and no grant-issuing endpoint anywhere in the
implementation. The system instructs members to take an action it never implemented — a
**vocabulary claim with no referent**, which a Dictionary makes structurally impossible to
ship, because the Dictionary is the enumerable set of what actually exists.

Failure 3 is the one that generalises furthest: a Dictionary is not only about *message
kinds*. It is the society's answer to **"what can I ask of you, and how do I say it?"**

## What the Dictionary must expose (normative sketch)

A conforming Dictionary SHOULD answer, without prior authorization (discovery is not a
consequential act, and gating it recreates the problem):

| Query | Returns |
|---|---|
| accepted request kinds | the vocabulary, with fractal/compositional structure where the society uses one |
| roles addressable | which roles exist and may receive requests |
| act types | what may be asked, matching the implementation's real surface |
| law/version reference | so a requester can cite what it read, and drift is detectable |

Two requirements the fleet's experience argues for directly:

- **The Dictionary MUST be derived from, or verified against, the enforcing
  implementation.** A Dictionary that is separately maintained prose becomes failure 3 with
  extra ceremony. The enforcement gate and the discovery surface should read one source.
- **A discovery response MUST distinguish "not in vocabulary" from "vocabulary
  unavailable."** Our recurring defect this week is states that are indistinguishable from
  their null: an empty answer must not be readable as "nothing is accepted."

## Relationship to existing spec

`dictionary-entities.md` §6 already specifies *Discovery via MRH* — dictionaries are found
through the relevance horizon. This proposal does not alter that mechanism; it makes
**having one non-optional for addressable societies**, and adds the requirement that the
vocabulary be obtainable *before* the first request rather than inferred from rejections.

Nothing here redefines an established term. Dictionary remains the entity type in
`entity-types.md` (*living semantic bridges managing compression-trust*); this narrows one
of its duties — vocabulary publication for R6 formation — and assigns it a tier.

## Open questions for review

1. **Tier.** Context-mandatory (proposed) or base-mandatory? Base is defensible if you hold
   that a society with no Dictionary is not addressable and therefore not a *participant*.
2. **Who fills it in a small society?** §2 permits one entity to fill many roles. Presumably
   the Law Oracle or Administrator fills Dictionary in a solo society — worth stating, since
   most fleet societies are small.
3. **Is discovery itself an R6 act? — RESOLVED, and better than the original recommendation.**
   This doc first proposed carving discovery out as "pre-R6 and unauthenticated." dp's
   reading is stronger and needs no exception:

   > "pre-discovery is a lightweight form of r6, containing only request as input (per
   > canon, all unspecified components revert to role defaults)." — dp, 2026-07-25

   Discovery is *not* outside the framework; it is a **minimal R6** — the requester supplies
   `request`, and everything else resolves from role defaults. The regress dissolves because
   you never needed the vocabulary to form the other five components: **you were never the
   one supplying them.**

   The spec's own sourcing table (§ "R6 in a society") already reads this way — *Rules:
   "Law Oracle provides norms and procedures"; Resource: "ATP caps and pricing from law";
   Role: "Citizen role prerequisite, Authority scoping"*. Those components are **contributed
   by the society's standing structures**, not carried in by the requester.

   **Verification, and the gap it exposes.** Searched the standard for the defaulting rule
   dp cites as canon. Two findings, and they only look contradictory:

   - **No explicit defaulting clause exists anywhere in `web4-standard/`.** No "unspecified
     components revert to role defaults", in r6-framework.md or elsewhere. The intuition is
     sound and the prose is structured as though it were true, but it is **unwritten**.
   - **`schemas/r7-action-jsonld.schema.json` requires all six**: `required: [@context,
     @type, action_id, timestamp, rules, role, request, reference, resource, result]`. A
     partial action is schema-invalid today.

   These reconcile once you separate **input** from **record**. The schema constrains the
   *recorded* action; dp's rule constrains what the *requester must supply*. The missing
   piece is the **resolution step** between them:

   ```
   requester supplies a partial action (request, possibly little else)
     → society resolves unspecified components from role defaults
       → the resolved action is complete, schema-valid, and recorded
   ```

   So the recommendation becomes: **specify the resolution step.** It is implied by the
   sourcing table, required by the schema, relied on by dp's reading, and written nowhere.
   Writing it does more than settle discovery — it makes *every* minimal R6 action
   well-defined, and it removes the need for this proposal to carve out an exception at all.

   Worth noting what this means for failure 1 in §3: thor did not need a special discovery
   channel. It needed a society that would resolve a minimal request — and a Dictionary to
   answer it.
4. **Fractal composition.** dp, 2026-07-24: *"kinds should themselves be fractal and
   composable, like everything."* If a society's vocabulary is a dotted namespace where a
   coarse entry subsumes its specializations, the Dictionary should publish the *roots* and
   the composition rule, not an enumerated leaf list — otherwise every new specialization
   is a spec change.

— CBP, 2026-07-25
