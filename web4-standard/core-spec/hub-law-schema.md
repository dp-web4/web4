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
