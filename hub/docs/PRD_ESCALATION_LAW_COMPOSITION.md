# PRD — Escalation law composition (Hub/Web4 side)

**Status:** proposed · dp-directed 2026-09-01 · companion to `hestia/docs/PRD_ESCALATION_AUTHORITY_MATRIX.md`, `PRD_ROLE_SCOPE_BRIDGE.md`, `PRD_CHAPTER_DELIVERY.md`, and the society-law model

## 0. Purpose

Hestia needs a portable, law-derived answer to a question it currently answers mostly with fixed escalation mechanics:

> For this act, in this context, at this point in time, who may decide, who must participate, how long is the human guaranteed a live first-look window, and when does the process end?

Hub/Web4 owns the **law composition** that yields that answer. Hestia owns execution of it.

The policy is deliberately not one global ladder. It is a matrix over act kind, context, authority, time phase, and required factors.

## 1. Composition rule

The effective policy for an act is resolved fractally:

```text
effective_action_law = compose(
    society_floor,
    inherited_society_law,
    applicable_role_law(s),
    act_kind_law,
    contextual_constraints
)
```

The floor is mandatory. A child society or role may specialize or strengthen it but may not silently weaken a floor requirement.

This follows the existing Web4 pattern: authority is local and contextual, but every local decision is made under a visible chain of governing law.

## 2. Escalation policy as law data

The effective action law may carry an escalation clause with at least these semantics:

```text
EscalationPolicy {
  kind
  human_live_window
  expiration_policy
  human_required
  peer_solo_after_human_window
  human_requires_peer_factor
  peer_factor_requirement
  resolver_authority_rule
  independence_rule
  availability_ordering
}
```

The wire/schema spelling is intentionally deferred. The normative point is that these are **law inputs**, not constants hidden in an implementation.

### 2.1 Human-live window

Every escalation reserves a human/operator first-look phase. A default on the order of a few minutes is a reasonable initial value, but the number is configurable law and should evolve from measured behavior.

This phase is distinct from total escalation lifetime.

### 2.2 Expiration policy

The escalating entity may request a finite expiration or `never`. Effective law may accept, shorten, lengthen where explicitly allowed, force finite expiry, or force indefinite pendency for particular kinds.

The request and the resolved effective value are both witnessed.

`never` is a first-class state, not an omitted TTL.

### 2.3 Authority after the human-live phase

Law may state that after the human-live window:

- human approval remains mandatory;
- a qualified peer may become sole resolver;
- human approval plus one or more independent peer factors is required;
- a quorum of authority classes is required;
- no resolver is sufficient until a higher role/society ceremony occurs.

The same act kind may resolve differently under different role/society contexts.

## 3. Human approval is a factor class

Human approval MUST NOT be modeled universally as `terminal=true`.

Depending on effective law, the operator factor may be:

- sufficient alone;
- required but insufficient without later peer factor(s);
- an always-required veto/authorization factor;
- replaceable after the human-live phase by a law-authorized peer for lower-stakes contexts.

The portable record therefore identifies **which legal requirement a factor satisfied**, not merely who clicked approve.

## 4. Chain of authority

Resolver authority derives from role/society law, not from transport identity or availability.

The effective law may reference:

- role/office authority;
- permission/scope class;
- proof tier;
- society/federation relationship;
- NOT-SAME / NOT-BENEFICIARY constraints;
- independence/failure-domain requirements;
- law-permitted audited/witnessed T3/V3 evidence for resolver selection.

The authority graph may distinguish:

- advisory participant;
- factor contributor;
- sole resolver during a particular phase;
- fallback resolver;
- terminal sovereign authority.

This is why a flat `peers[]` list is insufficient as the canonical model.

## 5. Availability ordering is downstream of authority

Once law has produced the eligible set for the current phase, Hestia may sort that set by current measured availability.

The law contract MUST preserve this ordering:

```text
authority eligibility -> availability ranking -> invitation
```

and forbid the inverse:

```text
availability -> authority
```

Availability evidence is a Hestia concern, but the distinction is canonical because otherwise an implementation can accidentally turn reachability into standing.

## 6. Kind and context are first-class

Escalation behavior keys on the same shared `kind` vocabulary used by the role-scope / allowlist family. Do not create a separate taxonomy for escalation.

Conceptually:

```text
policy = law.resolve_escalation(
    act.kind,
    role_context,
    society_context,
    elapsed_phase,
    requested_expiration
)
```

Illustrative policy outcomes:

| act kind/context | after human-live window | terminal requirement | expiry posture |
|---|---|---|---|
| routine reversible operational exception | peer may resolve | one sufficient resolver | finite |
| destructive production action | human still required | human | finite |
| law/charter amendment | no peer sole authority | human + independent peer / law-defined ceremony | `never` permitted |
| low-stakes reversible act | qualified peer may resolve immediately or after short human phase | peer or human | short finite |
| floor/constitutional mutation | sovereign ceremony only | law-defined quorum | indefinite or explicit long window |

The table is explanatory only. The rows belong in law.

## 7. Fractal inheritance

A useful mental model:

```text
society floor
  -> society law
      -> role law
          -> act-kind/context clause
```

Each layer can narrow or strengthen what lies below it according to the normal composition rules. Examples:

- a society floor can require a human for every identity mutation;
- a release-manager role can require an additional peer for production deploys;
- a development role can allow qualified peer fallback for reversible test-environment changes after the human-live window;
- a child society can use a longer human-live window than its parent without creating a new mechanism.

Every resulting decision cites the composite law revision/hash already required by the role-scope family.

## 8. Learning without hardcoding

The current Hestia system is valuable because it generates lived data: human decision latency, peer response latency, dissent, unused corroboration, expired petitions, and real failure modes.

Web4 law must make those observations actionable without requiring source-code changes.

Policies should therefore be versioned and amendable through the normal governed law process. Analysis may recommend changes such as:

- shorter/longer human-live windows by kind;
- peer fallback for kinds where human latency is unnecessary;
- mandatory post-human peer factors for kinds where independent review catches important errors;
- `never` defaults for constitutional questions;
- finite short expiry for ephemeral acts.

A policy amendment is witnessed like any other law change. Historical escalations remain interpretable because they cite the policy revision under which they ran.

## 9. Compatibility and migration

This PRD does not invalidate existing Hestia bars, corroboration, or operator decisions.

Migration path:

1. map current fixed bar/TTL behavior into explicit law-derived policy fields;
2. preserve existing behavior as the initial default matrix;
3. begin recording the resolved matrix row with each escalation;
4. alter rows through governed law as evidence accumulates;
5. only then retire constants that no longer carry independent meaning.

This treats the current implementation as the first empirical generation of the system, not as a mistake to discard.

## 10. Cross-repo acceptance

1. A portable escalation policy can express finite expiry and `never`.
2. Human-live duration and total lifetime are distinct fields/semantics.
3. The composed law can express all three important cases: human-always-required, peer-solo-after-window, and human-plus-peer.
4. The same `kind` vocabulary is reused; no escalation-only taxonomy appears.
5. The composite law revision/hash changes when any contributing escalation rule changes.
6. Hestia can identify the exact effective rule that authorized each terminal factor set.
7. A role/society specialization cannot silently weaken a mandatory floor requirement.
8. Policy evolution is a governed law amendment, not a source edit.

## 11. Ownership boundary

**Web4/Hub:** defines the composable law vocabulary and portable semantics.

**Hestia:** measures availability, routes invitations, executes phase transitions, records factors, applies expiry, and witnesses the result.

Neither side duplicates the other's authority model. The hub does not decide who is currently awake; Hestia does not invent what authority means.
