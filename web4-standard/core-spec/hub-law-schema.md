# Hub Law Schema — YAML Surface + RDF Canonical

**Status:** Draft • **Last Updated:** 2026-07-13 • **Track:** U3

This document defines the **YAML ergonomic surface** for hub law and its
mapping to the canonical RDF representation (`ontology/hub-law.ttl`).

Chapter operators edit YAML. The hub validates, compiles to RDF, signs, and
stores the RDF graph. Both formats are valid for exchange; RDF is canonical
for verification.

---

## 0. Governing invariant (RWOA + S + V)

Hub law operates under the ratified accountability invariant (RWOA + S + V,
2026-07-12). Every consequential act is authorized by a **contextual preponderance
of evidence scaled to the act's stakes and irreversibility** (S), decided before
side effects (O), committed atomically with its evidence-basis (A); reachability is
weak evidence, not authority (R); witnessed identity + authority is strong (W);
irreversible / high-consequence acts pass a **catastrophic-risk veto** (V) that MAY
require a quorum of signatures by law. Unclassified surfaces default to
high-consequence. This is a **gradient, not a binary** — the same non-boolean model
as T3/V3 and MRH — so law should *not* flip to default-deny.

How the invariant is expressed in the YAML surface (see the starter law,
`web4/hub/examples/starter-law.yaml`, for a worked example):

- **Permissive base, stakes-gated exceptions.** A `DEFAULT-ALLOW` norm (priority 0)
  covers low-stakes reversible acts; specific `deny`/`escalate` norms gate the
  consequential ones at higher priority. Keeping the base permissive is deliberate —
  a too-strict-everywhere gate breeds unsafe-override escape hatches that become the
  next reachability-is-authority holes.
- **S conservative default (a norm).** An `escalate` norm whose `selector` is
  `r6.request.action` with `operator: in` over the set of **consequential
  action-kinds** (priority above `DEFAULT-ALLOW`, below the specific named norms), so
  a consequential act that no specific norm decides escalates rather than riding the
  permissive base. Extend the list as new consequential action-kinds land.
- **V catastrophic-risk veto (escalation).** An escalation trigger that fires on the
  **irreversible / high-consequence tail** regardless of any allow norm (a secret
  *release* has no undo; an irreversible law change; a lockout-risking operator-set
  change), and MAY demand a quorum of operator signatures. Reversible acts are
  risk-managed on preponderance; the irreversible tail gets the conservative veto.
- **O + A in procedures.** Consequential-action procedures carry the target the
  daemon enforces as gating lands: the authority decision is a **preflight** that
  dominates every side effect (O), and the act commits **atomically** with its signed
  hash-chained record and the evidence relied upon (A).
- **Bounded bootstrap.** Genesis acts run in a bounded, self-witnessing bootstrap
  window that ratchets shut once witnessed authority exists — no re-entry.

Full norm + write-time self-audit: the `accountability-invariant` thread and
`web4/CLAUDE.md` "Accountability self-audit (run before shipping a surface)."

---

## 1. YAML Law File

A chapter's law is a single YAML file with these top-level keys:

```yaml
# hub-law.yaml — example
version: "1.0.0"

norms:
  - id: ATP-LIMIT
    selector: r6.resource.atp
    operator: "<="
    value: 100
    decision: deny
    priority: 10
    description: "No single action may consume more than 100 ATP"

  - id: ADMIN-ONLY-ROLES
    selector: r6.request.action
    operator: "=="
    value: role_assigned          # r6.request.action = HubEvent::kind() (event-kind, not a verb)
    decision: escalate
    priority: 20
    description: "Role assignment requires Sovereign or Administrator"

procedures:
  - id: WITNESS-3
    requires_witnesses: 3
    applies_to: "consequential_actions"
    description: "Consequential actions require 3 independent witnesses"

  - id: ADMISSION-VOTE
    requires_quorum: 3
    applies_to: "member_join"
    description: "New member admission requires 3 existing members to approve"

delegation:
  max_depth: 2
  requires_approval: true
  allowed_roles:
    - administrator
    - archivist
    - witness

escalation:
  - condition: "r6.resource.atp > 50"
    escalate_to: sovereign
    description: "High-ATP actions escalate to Sovereign"

  - condition: "r6.request.action == 'amend_charter'"
    escalate_to: sovereign
    description: "Charter amendments always go to Sovereign"

admission:
  open: false
  requires_sponsor: true
  sponsor_role: citizen
  min_trust_score: 0.3
  description: "Closed admission — existing citizen must sponsor, minimum T3 aggregate 0.3"

atp_issuance:
  mint_authority: treasurer
  max_mint_per_cycle: 1000
  distribution: proportional_to_contribution
  description: "Treasurer mints up to 1000 ATP per cycle, distributed by V3 contribution score"
```

### Decision semantics

The four `decision` values and the evaluation order below transcribe the live
engine (`web4-policy/src/lib.rs`, `Decision` + `Law::evaluate_outcome`) — this
section is a sync surface, not a design surface; if it disagrees with the
engine, one of the two is a defect.

- `allow` — proceed silently.
- `warn` — proceed, but flag the action as noteworthy. A **non-blocking
  flagged-allow**: a genuine fourth outcome, not a flag on `allow`. The
  advisory text rides the winning norm's `description`.
- `deny` — block the action (terminal).
- `escalate` — block pending a higher authority's decision (default
  `escalate_to: sovereign` when no escalation trigger names one).

Evaluation order:

1. Walk norms; among those that fire, **highest `priority` number wins**
   (ties → first declared).
2. A winning `deny` is terminal (a winning `warn` is NOT — it proceeds,
   like `allow`).
3. Otherwise walk `escalation` triggers; first match → `escalate`.
4. Otherwise the winning norm's decision applies.
5. No firing norm and no trigger → default `allow`.

### Response vocabulary (W4IP N3 — prescriptive)

> **Sync direction — inverse of the Decision-semantics section.** The section
> above *transcribes* the live engine; this section *prescribes* schema that
> does not yet exist. Until the Phase 2 schema+parse extension lands
> (hub-track PR against `web4-policy`/`hub-lib`), the engine neither parses
> nor enacts responses. If code and this section later disagree, adjudicate in
> that PR's review — do not let either drift silently. Field-level YAML shape
> below is a minimal contract the implementing PR MAY reshape; the normative
> content of this section is the **verb set, the ladder semantics, and
> parse-don't-enact on the kinetic class**.

*Provenance (informative):* this section lands W4IP N3
(`proposals/W4IP-DRAFT-2026-07-13-governance-immune-enforcement.md`) per the
review-ratified Phase 2 sequencing; the F clause below is that proposal's R-1
as hardened two-part in review. The W4IP draft itself remains non-normative;
this section is the normative expression of its N3 item.

Decisions and responses answer different questions. A `decision` is
**first-person and pre-act**: *may this act I am requesting proceed?* A
`response` is **second-person and post-recognition**: *what does the society
do about a target's witnessed act?* Overloading `decision` with response verbs
would invite gate rules that silently emit responses — exactly the
first-person/second-person conflation the response side exists to prevent — so
the vocabularies are parallel and disjoint.

#### The graded ladder

Every enacted response is an **R7 act** whose required evidence and veto scale
with the rung's `ConsequenceClass` (`referenced-acts.md` §4) — the ladder *is*
S and V applied to responses; there is no separate enforcement principle.

| rung | ConsequenceClass | semantics |
|------|------------------|-----------|
| `notice` | Reversible | Formal, witnessed notification to the target that a recognition delta has accrued against it. Does not interfere with the target's ability to act. Maps to existing machinery (the witnessed reputation delta plus an advisory record). |
| `quarantine` | Reversible *(by construction)* | Reversible containment of the target's interaction surface within the society (e.g. pairing, channel, or resource access paused) pending adjudication. MUST be liftable by the same authority that imposed it — a containment that cannot be lifted is not `quarantine` and MUST be declared under the kinetic class instead. First genuinely new rung. |
| `correct` | Costly | Restorative: undo or compensate the violation's effects (e.g. return of extracted ATP). Undoable at a cost. |
| `rehabilitate` | Reversible | The return path: earned restoration of standing against a rehab-bound. (N5 ports the bound into `reputation-computation.md` §7; this rung is its verb.) |
| kinetic class — `slash`, `suspend`, `revoke`, `terminate`, `halt` | Costly / Irreversible | Interferes with the target's ability to act — the response side's own kinetic acts. **Parse-don't-enact** (below). |

#### The kinetic class — unification, not new authority

The five kinetic verbs *name existing scattered primitives* so law can cite
them uniformly; naming them here creates **no new enactment authority**:

- `slash` — ATP stake slashing, `atp-adp-cycle.md` (`slash_atp`, already
  evidence- and witness-shaped).
- `suspend` — citizenship lifecycle event, `SOCIETY_SPECIFICATION.md` §4.2
  (`suspend` → Suspended).
- `revoke` — LCT/credential revocation, `LCT-linked-context-token.md`
  (revocation record, `status = "revoked"`).
- `terminate` — citizenship lifecycle event, `SOCIETY_SPECIFICATION.md` §4.2
  (`terminate` → Terminated).
- `halt` — CRISIS motor-halt, `entity-types.md` ("halt effectors").

**Parse-don't-enact:** the validator MUST accept a law file whose response
rules use kinetic verbs; the engine MUST NOT enact them (they are law-inert)
until each rung's enactment is individually ratified and implemented. This
mirrors how V gates the irreversible tail: the vocabulary exists so law can be
drafted and reviewed against it before any machinery can act on it.

#### Gating — RWOA + S + V + F

A response is itself a consequential act under the ratified invariant (§0),
plus one clause specific to responses (W4IP R-1 as hardened in review):

- **F-a — forfeiture predicate.** Enactment requires bound recognition
  evidence that *the target's own act was kinetic toward others* — witnessed
  deltas under the Coercive/Extractive Behavior Rules category
  (`reputation-computation.md` §4). The enacted response's R7 Reference MUST
  bind this evidence. The evidence-quality bar scales with the response's
  ConsequenceClass: `notice` may rest on preponderance; the kinetic tail
  requires bound, witnessed attribution.
- **F-b — proportionality bound.** The response's magnitude is bounded by the
  target's violation. F-b is *ontic* (about the target's act); S stays
  *epistemic* (evidence scaled to the response's own stakes). A
  fully-evidenced, carefully-vetoed response can satisfy S perfectly and still
  violate F-b — which is why F is a distinct clause and not folded into R/W:
  "I was authorized" ≠ "they forfeited".

#### YAML surface (minimal contract)

Response rules live under a top-level `responses:` key, deliberately parallel
in shape to `norms:` — same rule anatomy, different verb field, selectors over
recognition evidence rather than the pre-act R6 request:

```yaml
responses:
  - id: QUARANTINE-ON-AGENCY-OVERRIDE
    selector: reputation.delta.category
    operator: "=="
    value: coercive_extractive
    response: quarantine
    priority: 10
    description: "Witnessed agency-override delta → reversible containment pending adjudication"
```

Prescriptive validation (folds into §2 when the implementing PR lands): every
response rule has `id`, `selector`, `operator`, `value`, `response`;
`response` is one of `notice`, `quarantine`, `correct`, `rehabilitate`,
`slash`, `suspend`, `revoke`, `terminate`, `halt`; kinetic verbs are valid to
parse. Prescriptive RDF mapping: `responses[]` compiles parallel to `norms[]`
(`law:hasResponse` → `law:responseId` / `law:selector` / `law:operator` /
`law:value` / `law:response` / `law:priority`); the `hub-law.ttl` ontology
extension lands with the same PR.

#### Decision point — first-rung name (`notice` vs `warn` vs `caution`)

W4IP N3 and the review sequencing name the first rung `warn`. The gate
vocabulary above already has `warn` (a non-blocking flagged-allow on one's
*own* act). Same token, two persons and two tenses — precisely the conflation
this section exists to prevent. This spec therefore proposes **`notice`**:
inherently second-person (a notice is *served on* a party), and distinct from
gate register, where `caution` still reads as advisory-to-self. (ISP §5.1's
secession "notice period" is a duration, not a verb — no collision.) Keeping
`warn` would maximize continuity with the W4IP text at the cost of importing
the collision into the schema permanently. **This is the N3 spec-review
decision; a one-token substitution (`notice` → `warn` or `caution`) reverts
the choice without touching the rest of the section.**

## 2. Validation Rules

A law file is valid if:

1. `version` is a semver string.
2. Every norm has `id`, `selector`, `operator`, `value`, `decision`.
3. `decision` is one of: `allow`, `warn`, `deny`, `escalate`.
4. `operator` is one of: `<=`, `>=`, `==`, `!=`, `<`, `>`, `in`, `not_in`, `matches`.
5. Norm `id` values are unique within the file.
6. `delegation.max_depth` >= 0.
7. `delegation.allowed_roles` entries are valid SocietyRole names.
8. `escalation[].escalate_to` is a valid role name.
9. `admission.sponsor_role` is a valid role name.
10. `atp_issuance.mint_authority` is a valid role name.

## 3. YAML → RDF Compilation

Each YAML key maps to the `hub-law.ttl` ontology:

| YAML path | RDF predicate |
|-----------|--------------|
| `norms[].id` | `law:normId` |
| `norms[].selector` | `law:selector` |
| `norms[].operator` | `law:operator` |
| `norms[].value` | `law:value` |
| `norms[].decision` | `law:decision` |
| `norms[].priority` | `law:priority` |
| `procedures[].id` | `law:procedureId` |
| `procedures[].requires_witnesses` | `law:requiresWitnesses` |
| `procedures[].requires_quorum` | `law:requiresQuorum` |
| `procedures[].applies_to` | `law:appliesTo` |
| `delegation.max_depth` | `law:maxDepth` |
| `delegation.requires_approval` | `law:requiresApproval` |
| `delegation.allowed_roles` | `law:allowedRoles` |
| `escalation[].condition` | `law:condition` |
| `escalation[].escalate_to` | `law:escalateTo` |

The compiled RDF graph is a `law:LawDataset` node with `law:hasNorm`,
`law:hasProcedure`, etc. edges to typed child nodes.

## 4. Extension Mechanism

Communities define custom predicates via `web4:subPredicateOf`:

```yaml
# custom extension
custom_predicates:
  - id: requires_kyc
    sub_predicate_of: law:appliesTo
    description: "Whether this procedure requires KYC verification"
```

This compiles to:

```turtle
ex:requires_kyc a law:CustomPredicate ;
    web4:subPredicateOf law:appliesTo ;
    rdfs:label "requires KYC" .
```

## 5. Validator CLI

```bash
web4-law-check hub-law.yaml          # validate structure
web4-law-check hub-law.yaml --rdf    # compile to RDF (Turtle)
web4-law-check hub-law.yaml --json   # compile to JSON-LD
```

The validator is a standalone binary (or wasm module) that:
1. Parses YAML
2. Validates against the rules in §2
3. Optionally emits compiled RDF or JSON-LD
4. Returns exit code 0 on success, 1 on validation failure
