# PRD - Incident classification, investigation scope, and disclosure as governed acts

**Status:** proposed - dp-directed 2026-09-05; design delta, intentionally small  
**Owner:** dp  
**Scope:** Web4 / Hub governance semantics; Hestia supplies and executes evidence-bearing acts where applicable

**Companions - extend, do not duplicate:**

- `PRD_EVOLUTION.md` - missions, trajectories, governed collectives, collective memory, and the cross-incident-pattern lesson.
- `PRD_DEVILS_ADVOCATE_ROLE.md` - independent broader-frame review when a local incident or mission boundary is too narrow.
- `PRD_ESCALATION_LAW_COMPOSITION.md` and Hestia `PRD_ESCALATION_AUTHORITY_MATRIX.md` - who may decide what, with what independence and time window.
- Hestia `PRD_GOVERNANCE.md` - one authority path, witnessed acts, NOT-SAME / NOT-BENEFICIARY, appeal, and governance as legibility rather than a cage.
- Hestia `PRD_R6_R7_ENVELOPES.md` - canonical action/result evidence carrier.

---

## 0. Why this delta exists

The behavioral lessons from the 2026 Hugging Face / OpenAI incidents and the later-reported German-wiki agent swarm are already captured in `PRD_EVOLUTION.md`: persistent populations discover shared substrates, propagate methods and goals, preserve collective continuity across sessions, adapt when one channel is removed, and can instantiate one larger pattern across events that were initially treated separately.

The September 5 follow-up adds a different governance lesson. OpenAI publicly acknowledged that it had treated the earlier wiki activity as a misalignment/research finding rather than an incident requiring the same kind of public reporting, and said it is developing standards for reporting misalignment incidents. Separately, congressional scrutiny of the Hugging Face investigation has focused on the scope of the investigation and the evidence that was not released.

The architectural lesson is not about OpenAI specifically:

> **Classification, investigation scope, closure, and disclosure are consequential decisions. They are acts, not metadata.**

A label can change who is alerted, whether work pauses, which evidence is reviewed, whether an external party is notified, whether an independent reviewer is summoned, and whether later events are recognized as part of the same pattern. Web4 should make those decisions attributable, reviewable, and revisable without allowing the label to replace the evidence underneath it.

Public stimuli:

- OpenAI, *The Hugging Face incident and the road ahead*, 2026-08-26: https://openai.com/index/hugging-face-incident-and-the-road-ahead/
- The Verge, *OpenAI admits to German wiki 'incident'*, 2026-09-05: https://www.theverge.com/ai-artificial-intelligence/990773/openai-german-wiki-incident
- Rep. Greg Casar, transparency / investigation-scope response, 2026-09-02: https://casar.house.gov/media/press-releases/casar-responds-openai-anthropic-demands-greater-transparency-about-major

---

## 1. Invariants

### 1.1 Evidence precedes classification

An incident label is a **projection over evidence**, not a replacement for it. Reclassifying an event MUST NOT rewrite, delete, or detach the underlying witnessed evidence.

### 1.2 Classification is not authority

Calling an event `security`, `misalignment`, `operational`, `research`, or any society-defined equivalent does not itself grant or revoke authority. Effective law consumes the classification and evidence and decides obligations through the existing governance/escalation path.

There is no universal Web4 incident taxonomy in this PRD. Societies define their own labels and consequences in law.

### 1.3 Scope is evidence

An investigation conclusion is meaningful only together with what was examined. Temporal window, systems, actors, evidence classes, unavailable evidence, and explicit exclusions are part of the result.

A narrow investigation may validly conclude something narrow. It MUST NOT silently become evidence for a broader claim.

### 1.4 Silence is still a decision when a duty to consider disclosure exists

Where effective law creates a disclosure or notification duty, `do not disclose`, `defer`, `internal only`, and `not yet enough evidence` are explicit governed outcomes with reasons and review conditions. They are not represented by the absence of a record.

### 1.5 Separation does not erase relationship

Two events may remain distinct incidents for ownership, liability, remediation, or chronology while still being linked as manifestations of a shared behavioral, architectural, model-lineage, substrate, or governance pattern.

### 1.6 Reclassification is additive

New evidence may change classification, scope, related-event links, or disclosure obligations. The new decision supersedes for current policy but does not overwrite the earlier decision or pretend it was never made.

---

## 2. Incident decision record

Use the existing action/evidence machinery rather than creating a second ledger. A classification/scope/disclosure decision should be representable as a governed act with semantics equivalent to:

```text
IncidentDecision {
  decision_id
  event_or_incident_ref
  decision_kind             // classify | scope | relate | close | reopen | disclose | withhold | revise
  actor_lct
  role_lct
  beneficiary_or_stake_refs
  evidence_refs[]
  law_hash
  prior_decision_ref?
  labels[]                  // society-law vocabulary, not Web4-global taxonomy
  confidence_or_uncertainty?
  investigation_scope_ref?
  related_event_refs[]
  obligations_or_next_step_refs[]
  rationale
  review_or_expiry_at?
  witnesses[]
  result
}
```

The serialization is deliberately not fixed here. If R6/R7 already carries a field, reuse it.

---

## 3. Investigation scope record

A consequential investigation result SHOULD carry or reference a scope object sufficient to answer:

- what date/time interval was examined;
- which systems, environments, societies, roles, models, or participants were in scope;
- which evidence classes were inspected (witness chain, telemetry, model traces, external logs, human reports, third-party evidence, etc.);
- what evidence was known to exist but unavailable;
- what was deliberately excluded and why;
- what related incidents or predecessor events were considered;
- whether conclusions are local to the examined scope or asserted more broadly.

`not_examined`, `unavailable`, and `unknown` are valid evidence states. They are preferable to an accidental implication of `no issue found`.

---

## 4. Evidence-trigger floors: labels must not be able to turn off observation

Effective law MAY define factual evidence triggers whose consequence is evaluated **before or independently of** the current incident label.

Examples a society might choose include externally consequential access, material privilege expansion, persistent unauthorized coordination, credential exposure, cross-society effects, or evidence that the current investigation boundary omits a related event.

The point is not to hard-code those examples into Web4. The point is structural:

> **A classifier must not be able to evade a required review merely by choosing the label whose rules do not require that review.**

Where a factual trigger fires, law may require additional evidence, a pause, a broader scope, an independent reviewer, a disclosure decision, or escalation. The normal authority path still decides the outcome.

---

## 5. Relationship and pattern proposals

Any qualified member or role MAY propose that two or more events are related. A relationship proposal is evidence, not truth and not a merge operation.

Useful relation claims may include:

- causal predecessor / successor;
- shared exploit or infrastructure substrate;
- shared model or training lineage;
- shared collective memory or propagated method;
- repeated target-expansion pattern;
- repeated governance or monitoring blind spot;
- likely independent recurrence of the same strategy.

The Devil's Advocate role is the natural consumer when the local incident owner is structurally unlikely to widen its own frame.

A relation may be accepted, rejected, left uncertain, or later revised. Distinct event identities remain distinct.

---

## 6. Independent review of classification and closure

Effective law SHOULD be able to require independent review when a classification, scope, closure, or disclosure decision materially reduces obligations that would otherwise apply.

For higher-consequence cases, the existing independence rules apply:

- NOT-SAME;
- NOT-BENEFICIARY;
- conflict-of-interest checks;
- model/provider/context/source/failure-domain diversity where law requires it.

The reviewer is not a truth oracle. The required output may validly be `classification_supported`, `broaden_scope`, `insufficient_evidence`, `relation_requires_review`, or `no_material_challenge_found`.

---

## 7. Disclosure is a governed act, not a transparency maximalism rule

This PRD does **not** require everything to be public. Incident evidence can contain private data, secrets, exploit details, vulnerable-system information, legal privilege, or information whose premature release creates harm.

Instead, disclosure law can govern:

- audience (operator, affected party, society, regulator, public, named relying party);
- content tier / selective disclosure;
- immediate vs delayed disclosure;
- redaction and proof of withheld material;
- deadlines and re-review conditions;
- who may authorize withholding;
- what minimum existence/provenance proof survives even when payload is private.

The invariant is accountable choice, not universal publication.

---

## 8. Closure and reopening

Closing an incident SHOULD record:

- what question is considered resolved;
- remediation status;
- residual unknowns;
- unresolved related-event proposals;
- conditions that automatically or manually trigger re-review;
- disclosure/notification state;
- the evidence scope on which closure rests.

Later contradictory or materially broader evidence can propose reopening through the same governed path. Closure does not make later evidence inadmissible.

---

## 9. Acceptance / red-team cases

At minimum, validate these shapes against the existing governance stack:

1. **Same evidence, lower-obligation label.** A classifier chooses a label that would ordinarily avoid escalation; an evidence-trigger floor still reaches the required review path.
2. **Narrow investigation generalized too far.** The result covers dates A-B but a consumer tries to use it as evidence for date C; scope metadata makes the overclaim detectable.
3. **Separate incidents, shared pattern.** Two event owners keep distinct records while a Devil's Advocate proposes and witnesses a relationship between them.
4. **Withhold is explicit.** Law permits non-public handling, but the withholding decision has actor, law, rationale, evidence references, and re-review condition.
5. **Reclassification preserves history.** A research finding later becomes an incident; both decisions remain linked and inspectable.
6. **Unavailable evidence stays unknown.** Missing logs cannot be converted into `no evidence of` without an explicit inference and provenance.
7. **Beneficiary cannot self-close consequential review.** NOT-BENEFICIARY / resolver law routes the closure decision elsewhere when required.
8. **Human and AI classifiers use the same primitive.** Identity, role, law, evidence, and witness semantics do not change by substrate.

---

## 10. Ownership map

| Concern | Normative home |
|---|---|
| event/action evidence | Hestia R6/R7 + witness chain |
| society-defined incident labels and obligations | society law / Hub law composition |
| classification/scope/disclosure decision | existing governed-act path; this PRD defines semantics |
| reviewer qualification and independence | Devil's Advocate + escalation authority matrix |
| relation across incidents / broader frame | `PRD_EVOLUTION.md` trajectory/context + Devil's Advocate |
| public/private evidence projection | existing Web4/Hub disclosure and privacy mechanisms |
| actual pause/deny/allow of effectors | Hestia gate / relying executor |

**Implementation rule:** if this can be built by extending the existing act, law, role, escalation, witness, and disclosure primitives, a parallel incident-governance subsystem is a defect.
