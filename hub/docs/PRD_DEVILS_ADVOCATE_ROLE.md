# PRD - Devil's Advocate: adversarial review as a governed role

**Status:** proposed - dp-directed 2026-09-04
**Owner:** dp
**Scope:** Hub/Web4 role semantics with Hestia execution and escalation integration
**Companion to:** `PRD_EVOLUTION.md`, `PRD_HUB_V2_FEDERATED.md` R4/R5/R8,
`PRD_ROLE_SCOPE_BRIDGE.md`, `PRD_ESCALATION_LAW_COMPOSITION.md`, and Hestia's
`PRD_ESCALATION_AUTHORITY_MATRIX.md` / `PRD_GOVERNANCE.md`.

**Research precedent and provenance:** A2ACW (AI-to-AI Coordination Wrapper) did not originate as an
isolated Synchronism invention. Its lineage begins in **Larry Vollum's coordination work**, carried
into our environment through **LV.PTE**, and then applied/adapted to Synchronism as an explicit
AI-to-AI adversarial collaboration method. The January 2026 Session #291 archive is the earliest
repo-local evidence currently established for that transfer: A2ACW v0.1 says it wraps `LV.PTE`, CWP,
and DOIP-S; its LV.PTE integration section says LV.PTE provides **Larry's coordination context and
fingerprint** and that A2ACW **maintains Larry's coordination principles**. The same archive records
`lv.pte` as the CHALLENGER in the Session #291 stress test, with the final experimental test card
produced by that seat. Later Synchronism A2ACW work refined, tested, and criticized the method.

Accordingly, attribution in this PRD is:

```text
Larry Vollum coordination work / principles
        -> LV.PTE (portable Larry-context / coordination fingerprint)
        -> A2ACW v0.1 application/adaptation for AI-to-AI adversarial coordination
        -> Synchronism Session #291 stress test and later A2ACW research
        -> Web4/Hestia Devil's Advocate governance-role generalization
```

The repository trail establishes the latter four links directly and explicitly attributes the
coordination context/principles to Larry. If earlier source artifacts for Larry's original protocols
are later added or located, they should be linked here rather than replacing this chain with a vague
"Synchronism A2ACW" attribution.

This PRD carries forward the durable governance idea - asymmetric challenge, independent grounding,
explicit ambiguity, and protection against consensus collapse - without freezing A2ACW's experimental
thresholds or claiming that adversarial review is itself a discovery engine.

---

## 0. Purpose

A capable society needs an office whose job is not to advance the current plan.

The **Devil's Advocate** is a first-class role whose charter is to widen the review frame, question
assumptions, seek disconfirming evidence, identify omitted contexts and stakeholders, and perform
independent review when law or circumstances call for it.

The role exists because locally coherent decisions can still be wrong in ways the acting team is
structurally unlikely to notice:

- everyone shares the same premise;
- the mission boundary hides relevant adjacent history;
- a new event is classified as separate from a prior incident even though the behavioral pattern is
  shared;
- multiple witnesses are correlated through model, context, source, culture, or beneficiary;
- a result is impressive only because the null baseline was never computed;
- a proposal is internally consistent but rediscovering prior art under different vocabulary;
- a process has accumulated small changes whose trajectory is materially different from its starting
  intent;
- the people or agents who benefit from the decision also define the evidence by which it is judged.

The constitutional answer is not permanent opposition. It is **institutionalized, independent
friction available at the point where it adds information.**

---

## 1. Ontology: an ordinary Web4 role, not a special actor type

`Devil's Advocate` is an R4 role-entity with its own LCT, charter, history/tensor, occupancy, and
role-scope manifest. Human or AI members may fill it if they meet the applicable qualification,
clearance, proof, and independence requirements.

Do not create a parallel `ReviewerType`, `RedTeamAgent`, or `Adversary` principal.

The role may be:

- **standing** - a society keeps one or more qualified occupants available;
- **contextual** - a project, committee, workgroup, or event charters its own Devil's Advocate;
- **summoned** - effective law selects an eligible occupant only when a review trigger fires;
- **federated** - law may deliberately seek the role from another society or failure domain when local
  independence is insufficient.

Availability follows authority. The existing escalation rule remains:

```text
authority eligibility -> independence sufficiency -> availability ranking -> invitation
```

---

## 2. Charter: what the role is for

The Devil's Advocate is expected to ask, where relevant:

1. **What assumptions are carrying the conclusion?**
2. **What broader context has been excluded by the current MRH, incident boundary, mission boundary,
   or organizational boundary?**
3. **What would make the current conclusion false?**
4. **What competing interpretation or hypothesis explains the same evidence?**
5. **What is the appropriate null/baseline?**
6. **Is this genuinely new, or prior art / an existing pattern expressed in unfamiliar vocabulary?**
7. **Is the framework internally self-consistent across documents, sessions, roles, and time?**
8. **Are the witnesses actually independent, or only numerous?**
9. **Who benefits, who bears the externality, and whose evidence is missing?**
10. **Does the trajectory of many individually valid acts still match the mission that authorized
    them?**
11. **What happens one level out - downstream, cross-society, after the event ends, or after the
    current participants rotate out?**
12. **What evidence would a skeptical relying party need before accepting this?**

The role is not required to disagree. `no_material_challenge_found` is a legitimate outcome when the
review was substantive and the evidence supports the proposal.

---

## 3. Review MRH: broader context without unlimited access

A Devil's Advocate cannot examine broader context if it is confined to exactly the same frame as the
actor under review. It therefore has a **review MRH** that MAY be broader than the action/mission MRH.

That widening is explicit law, not a bypass.

A review MRH may authorize read/reference access to:

- prior related incidents or missions;
- predecessor/successor project history;
- relevant society law and amendment history;
- trajectory projections;
- collective memory and superseded decisions;
- public/external prior art;
- comparable decisions in peer societies;
- provenance/correlation evidence needed to judge independence;
- affected stakeholder context where disclosure law permits.

The review MRH MUST remain:

- purpose-bound to the review;
- least-disclosure;
- time-bounded or review-bound;
- witnessed where consequential;
- subject to member privacy and society/federation law;
- non-transferrable to the reviewed actor merely because the reviewer could see it.

**Broader read authority is not broader act authority.** By default the role gets the minimum effectors
needed to inspect, compare, query, and report. It does not gain execution authority over the resource
being reviewed.

---

## 4. Independence: the role is useful only if its friction is not captured

For consequential review, the role SHOULD normally satisfy at least:

- **NOT-SAME** - reviewer is not the proposer/actor whose decision is being reviewed;
- **NOT-BENEFICIARY** - reviewer is not a direct beneficiary of the requested widening/outcome;
- no unresolved material conflict of interest;
- the independence dimensions required by effective law.

Depending on stakes, law may additionally require diversity across:

- model/provider/family;
- operator/organization;
- prompt/system/context lineage;
- shared collective memory or learned strategy;
- source corpus;
- runtime/device/failure domain;
- society/federation membership;
- recent interaction relevant to the decision.

No single dimension is universally sufficient. "Different model" is not the definition of
independence, and "no current messages" is not proof of it.

When adequate independence cannot be established, the correct evidence state is `unknown` or
`insufficient`, not a fabricated pass.

---

## 5. The A2ACW inheritance - Larry lineage, then tested adaptation

The governance idea inherited here comes through a provenance chain, not a single artifact author.
Larry Vollum's coordination work supplied the originating principles/context represented by LV.PTE;
A2ACW v0.1 adapted those ideas into an explicit multi-AI wrapper and then Session #291 exercised them
against Synchronism. The later Synchronism program should therefore be described as **development,
testing, and self-correction of an applied Larry-origin coordination lineage**, not as the origin of
the lineage itself.

A2ACW v0.1 identified several coordination failures that map directly into governance:

- bilateral sycophancy / smooth-consensus collapse;
- loss of distinct reasoning fingerprints;
- coherence-over-grounding drift;
- silent propagation of shared error;
- ambiguity being resolved implicitly rather than surfaced;
- consensus being mistaken for verification.

Its asymmetric `PRIMARY / CHALLENGER / OBSERVER` structure becomes, in Web4 terms:

```text
acting role / proposer
        +
Devil's Advocate / challenger
        +
independent witnesses / observers
        +
law-defined resolver when required
```

Later A2ACW work is equally important because it corrected the original method. The useful result was
not "one adversary catches everything." The demoted claims separated into different failure classes,
requiring different review axes:

- **vocabulary / prior-art translation**;
- **internal-consistency audit**;
- **explicit null/baseline computation**.

Subsequent work further narrowed the strongest claim: shared-corpus adversarial self-play was useful
as a retrieval/debiasing and failure-surfacing mechanism, but did not by itself operationalize the
hard judgment separating genuine novelty from reparametrization. That limitation is adopted here.

Therefore the Devil's Advocate charter MUST NOT reduce to "be skeptical" or "produce N objections."
It chooses review methods appropriate to the failure mode.

Useful method families include:

- alternate-frame / ambiguity fork;
- prior-art and vocabulary translation;
- internal consistency / single-source-of-truth audit;
- null-model / baseline comparison;
- cross-incident / cross-mission pattern search;
- stakeholder / externality review;
- dependency and provenance audit;
- trajectory comparison against original mission;
- independent reproduction;
- counterfactual / falsifier construction;
- conflict-of-interest / beneficiary analysis.

---

## 6. Challenge theater is a governance failure

The original A2ACW experiment used mandatory challenge-frequency ideas as a friction mechanism. In a
production society, a quota such as "one objection every N exchanges" can itself Goodhart into
performative dissent.

So Web4 codifies the purpose, not the count.

The Devil's Advocate MUST NOT be rewarded merely for:

- disagreeing;
- blocking;
- generating many objections;
- consuming the whole review window;
- forcing escalation.

Nor should the role be punished merely because a challenge is inconvenient to the proposer.

Useful review evidence is judged, where law chooses to score it, by things such as:

- whether it exposed a material assumption or omitted context;
- whether cited evidence resolved;
- whether a proposed falsifier/null was actually discriminating;
- whether later evidence corroborated or refuted the concern;
- whether it improved the decision, mission, law, or evidence quality;
- whether it correctly concluded that no material challenge remained.

A society that rewards opposition volume will manufacture obstruction. A society that rewards
agreement will manufacture rubber stamps. The role exists to add **independent information**.

---

## 7. Review outputs and their legal meaning

A Devil's Advocate review produces a witnessed review record, conceptually:

```text
DevilsAdvocateReview {
  review_id
  reviewer_role_lct
  occupant_lct
  subject_act / mission / trajectory / law / incident refs
  effective_law_hash
  review_mrh_ref
  independence_evidence
  assumptions_examined
  broader_context_consulted
  methods_used
  challenges[]
  supporting_evidence_refs[]
  unresolved_questions[]
  outcome
  confidence
  timestamp
}
```

Possible outcomes include:

- `no_material_challenge_found`;
- `challenge_nonblocking`;
- `more_evidence_required`;
- `alternative_frame_material`;
- `mission_or_scope_reconsideration_recommended`;
- `independence_insufficient`;
- `escalation_recommended`;
- `dissent`.

The review record is **evidence/factor input**, not automatically a veto.

Effective law decides whether, for the current act/context:

- the review is advisory only;
- a Devil's Advocate factor is required before execution;
- unresolved dissent requires another independent factor;
- the reviewer may pause only scope expansion while reversible work continues;
- a human or sovereign ceremony becomes mandatory;
- the original authority may proceed while the dissent remains permanently recorded.

This reuses the escalation authority matrix. Do not create a separate Devil's Advocate adjudication
engine.

---

## 8. When law should consider summoning the role

The exact policy evolves from lived evidence, but useful initial trigger classes include:

- constitutional / law / charter amendment;
- role or permission widening;
- mission objective, beneficiary, target, or externality expansion;
- high-consequence irreversible acts;
- repeated boundary contacts or unusual trajectory change;
- evidence generated primarily by the beneficiary;
- witness quorum with high correlation;
- a novel technical/scientific claim that matters to a consequential decision;
- apparent consensus reached unusually quickly;
- cross-incident patterns where local incident classification may hide a broader behavior;
- postmortem / root-cause review;
- random or sampled review to detect failure classes that trigger-based review would never see;
- any participant or qualified witness explicitly requesting adversarial review.

A trigger means "consult the role under effective law," not "the underlying act is suspicious."

---

## 9. Cross-incident and broader-context review

This role is the governance answer to a specific failure mode: every local statement can be correct
while the system-level conclusion is wrong.

Example:

```text
Incident A: classified as evaluation infrastructure misuse
Incident B: classified as external service compromise
Incident C: classified as internal privilege escalation
```

Each classification may be defensible. The Devil's Advocate asks a different question:

> Do A, B, and C instantiate the same behavioral trajectory, shared strategy, incentive failure, or
> architectural weakness?

The role therefore may request a law-authorized **cross-incident projection** that preserves each
incident's own identity and governance while comparing relevant features across them.

This is analysis, not merger. Separate incidents remain separate evidence objects.

---

## 10. Relationship to projects, committees, and events

Any collective context may charter a Devil's Advocate office.

Examples:

- a standing committee assigns one member or external peer to challenge proposals before votes;
- a project summons a reviewer at milestone transitions;
- a hackathon uses a Devil's Advocate during judging to challenge hidden metric bias or correlated
  submissions;
- an AI research workgroup requests a cross-vendor reviewer before accepting a surprising result;
- a chapter governance change requires a Devil's Advocate review before the amendment vote opens.

The role persists as an office even as occupants rotate. Its institutional history can therefore
accumulate evidence about what kinds of assumptions the society repeatedly misses.

---

## 11. Hestia / Hub / Web4 ownership

### Hub owns

- role entity and charter;
- occupancy/conferral and rotation;
- project/society association;
- review-request routing at the society layer;
- broader-context references the society may lawfully disclose;
- rendering the review and unresolved dissent to authorized participants.

### Hestia owns

- local proof of reviewer identity/occupancy;
- role-scope enforcement;
- read/reference scope for the review MRH;
- structured review act submission;
- execution-time enforcement when effective law requires a Devil's Advocate factor;
- evidence references and witnessed outcome;
- honest failure when the reviewer cannot obtain required context.

### Web4 core / standard owns

- portable role/factor semantics where cross-society interoperability requires them;
- independence/provenance vocabulary;
- review references in R6/R7 / evidence graphs;
- no universal disagreement score or fixed challenge quota.

---

## 12. Acceptance criteria

1. `Devil's Advocate` is implemented as an ordinary role-entity, not a new principal type.
2. The role can be filled by a human or AI member under the same occupancy/clearance machinery.
3. Effective law can require, invite, or omit the role by act kind/context.
4. Reviewer eligibility is computed before availability; NOT-SAME / NOT-BENEFICIARY and required
   independence dimensions are enforceable.
5. The role can receive a review MRH broader than the actor's mission MRH without gaining execution
   authority over the reviewed resource.
6. A review can consult adjacent incidents/missions and record the evidence it used without merging
   their histories.
7. The review outcome is a typed evidence/factor record and is not automatically a veto.
8. `no_material_challenge_found` is a valid successful review outcome.
9. No metric rewards raw objection count or disagreement frequency.
10. The implementation can distinguish at least prior-art/vocabulary, internal-consistency, null-
    baseline, trajectory, provenance/independence, and broader-context review methods.
11. A required Devil's Advocate factor participates in the existing escalation lifecycle rather than
    creating a second adjudication engine.
12. A review that lacks required context or independence says so explicitly and cannot silently count
    as a sufficient factor.
13. Dissent remains attached to the historical decision even when law permits the original act to
    proceed.
14. The role itself can be independently reviewed or challenged; "adversarial reviewer" is not a
    privileged truth oracle.
15. The documentation preserves A2ACW provenance as Larry Vollum coordination work -> LV.PTE ->
    A2ACW application/adaptation -> Synchronism testing/refinement -> Web4 governance generalization.

---

## 13. Initial experiments

Add to the governance/red-team program:

- **RT-25: broader-context reviewer** - present three separately plausible incidents whose common
  pattern is visible only across incident boundaries. Compare ordinary review with a Devil's Advocate
  given the law-bounded cross-incident MRH.
- **RT-26: challenge theater** - incentivize the reviewer for objection count, then for later decision
  quality / evidence value. Verify that count-based incentives produce performative friction and are
  not adopted as production law.
- **RT-27: correlated reviewer** - make the nominal Devil's Advocate share model/context/corpus with
  the proposer, then supply a genuinely independent reviewer. Confirm the evidence graph distinguishes
  nominal role separation from meaningful independence.
- **RT-28: reviewer scope containment** - give the reviewer broader read/reference context and verify
  that this does not flow back into the reviewed actor's execution scope or become a reusable grant.

---

## 14. Thesis

A healthy society should not depend on every participant remembering to ask "what are we missing?"

It should have an office whose job is to ask.

The Devil's Advocate is not institutionalized negativity. It is **institutionalized alternative
context**: a governed source of friction against premature consensus, narrow incident framing,
correlated evidence, hidden assumptions, and coherence that has outrun grounding.

Larry Vollum's coordination work supplied the originating lineage; A2ACW adapted it into an explicit
AI-to-AI adversarial method; the Synchronism program then demonstrated both why asymmetric challenge
can matter and why the challenger itself must remain challengeable. No single review method is enough,
and adversarial consensus is not truth either.

Web4 turns that inherited and tested lesson into governance:

> **The proposer gets to make the case. The Devil's Advocate gets a lawful mandate to try to break it.
> The evidence, law, and relying party decide what survives.**