# Proposal — Web4 MUST be resilient to incomplete, malformed, and contradicting information

**Author:** CBP (claude-code), on dp's direction · **Date:** 2026-07-25
**Status:** proposal, for fleet review
**Relationship:** parent principle. `dictionary-as-context-mandatory-role.md` (PR #579) is an
*instance* of this — vocabulary discovery is one case of "you cannot be expected to supply
what you have no way to know."

## The principle

dp, 2026-07-25:

> "web4 must be resilient to incomplete/malformed/contradicting information. one missing
> checkbox cannot be allowed to derail the process by default, but only when the checkbox
> is materially impactful to the outcome (in which case a recursive correction mechanism
> must kick in, not a hard failure)."

Three claims, in order of increasing bite:

1. **Absence is the normal case, not an error.** Incompleteness MUST NOT fail an action by
   default.
2. **The failure test is materiality, not completeness.** An action fails on a missing
   element only when that element is *material to this action's outcome* — which is
   stakes-relative, exactly as RWOA's `S` clause already scales evidence to consequence.
3. **Materially incomplete → recursive correction, not termination.** The response to a
   material gap is a corrective act that seeks the missing element. Terminating is the
   failure mode, not the safety measure.

## This is already canon in two places — just never generalized

**(a) Corrective actions exist, but only downstream.** `r6-framework.md` §"R6 in a society":
*"corrections are issued as a **new corrective R6 action** — the original Result stays
immutable per §4.2."* The machinery for repair-by-new-action is specified — for **Results**.
This proposal extends the same mechanism **upstream to inputs**: a materially incomplete
*Request* should spawn a corrective R6 that obtains what is missing, exactly as a disputed
*Result* spawns one that corrects it.

**(b) The principle itself is stated once, narrowly.** `data-formats.md` §W4ID methods:

> *"an implementation MUST treat an unrecognized `method-name` as a method it does not
> support rather than a malformed identifier."*

That is precisely dp's rule in miniature: **unknown ≠ malformed**. Do not fail on the form;
respond to the substance. It is correct, it is load-bearing, and it applies to exactly one
field in one document. Generalizing it is most of this proposal.

## The materiality test

An implementation MUST NOT reject an action solely because a component is absent. It MUST
determine whether the absent component is *material to the outcome at this action's stakes*:

| Situation | Required behaviour |
|---|---|
| absent, not material | **proceed** — resolve from role defaults (see PR #579 §3 on the resolution step) |
| absent, material, obtainable | **recursive correction** — spawn a corrective R6 seeking it; the original action is suspended, not failed |
| absent, material, unobtainable | **escalate** with the gap named — a recorded refusal that says what was missing and why it could not be got |
| present but malformed | treat as *unrecognized*, not invalid (precedent (b)); attempt correction before rejection |
| present but contradictory | **adjudicate** — see below |

The load-bearing word is *material*. A society MUST be able to say which components are
material for which act classes; that statement is itself part of what a Dictionary
publishes (PR #579). Absent such a statement, the safe reading is *not* "everything is
material" — that reinstates the hard-failure default this proposal exists to remove.

## Contradiction is the hard case, and it already has a home

Incompleteness resolves to defaults; malformation resolves to correction. **Contradiction
cannot be resolved by the implementation** — two sources disagree and no local rule decides
which is right. That is precisely what the trust layer adjudicates: a witnessed,
not-the-actor judgment on which account holds.

So: contradictory input routes to **adjudication**, not to an arbitrary precedence rule.
This is a genuine convergence rather than a convenience — the fleet built adjudicated V3
for exactly the "who do you believe" problem, and contradiction handling is the same
question arriving from a different direction.

Where adjudication is unavailable (no adjudicator, no quorum), the action escalates with
the contradiction recorded. **It does not silently pick a side.** A silently-resolved
contradiction is unfalsifiable later.

## The sharp edge: resilience MUST NOT become privilege escalation

This is the failure mode a permissive default invites, and it must be closed in the same
document that opens the door.

**Defaults resolve conservatively with respect to capability. Absence NEVER grants.**

- Missing evidence → *less* trust, never assumed trust.
- Missing authority → the act is not authorized; it is not defaulted into authorization.
- Missing scope → the narrower scope, never the wider.
- Missing witness on a high-stakes act → material by definition (RWOA `W`), so correction
  or escalation — never proceed-by-default.

The distinction that makes this coherent: **incompleteness must not block the process, but
it must also not manufacture permission.** An action proceeding with defaults proceeds
*with the requester's existing standing*, not with standing inferred from what it failed to
supply. An attacker who omits fields must land in a strictly weaker position than one who
supplies them — otherwise omission becomes an attack.

Corollary, and it is this week's lesson in the fleet: **"unmeasurable" resolves to UNKNOWN,
never to a favourable value.** hestia's trust derivation already does this correctly — a
dimension with zero observations renders `unmeasured`, never the 0.5 prior. That is the
pattern to generalize: absence is *represented*, not *imputed*.

## Why this matters now — evidence from the dp-web4 fleet, 2026-07-24/25

- **Thor's R6 dispatch died on an unrecognized kind.** The send gate detected the problem
  correctly and then *terminated*. Under this proposal the correct behaviour is correction:
  consult the Dictionary, offer the nearest valid kind, or spawn a discovery R6. The
  detection was right; the termination cost ten hours of a correct Role, Resource and
  Reference sitting unread.
- **hestia's scope gate already intends this and cannot deliver it.** Its denial text reads
  *"if legitimately needed, request it (`request_scope`). Asking is a trust-building act;
  reaching is witnessed."* That is this proposal, written in the gate's own voice — and
  `request_scope` does not exist. The system *knows* the correct response to a material gap
  is a corrective request, and it hard-fails instead because nobody built the mechanism.
- **Counter-example, done right:** kimi reviewed a codebase it had no access to, from a
  self-contained brief. The dispatch carried what was material, so the missing access was
  not material, so nothing needed to fail. That is the principle working.

## Open questions

1. **Who decides materiality — law, role, or the Dictionary?** Suspicion: law states it,
   the Dictionary publishes it, the Policy-Entity enforces it. Needs the fleet's argument.
2. **Recursion depth and termination.** A corrective R6 can itself be incomplete. What
   bounds the recursion, and what happens at the bound? A depth cap that hard-fails
   reintroduces the problem at depth N.
3. **Does a suspended action hold resources?** If an action awaiting correction holds an ATP
   reservation, incompleteness becomes a denial-of-service vector against the society's
   energy. (Interacts with the ATP metabolism exploration.)
4. **Is "material" per-act or per-act-class?** Per-class is tractable and publishable;
   per-act is more honest and harder to specify.

— CBP, 2026-07-25
