# PRD — Institutional Knowledge → Governance Ingestion

**Status:** draft for prototype  
**Date:** 2026-10-03  
**Scope:** Hub / Lawbook / organizational onboarding  
**Companions:** `hub/docs/PRD_LAWBOOK_IR.md`, Hestia `docs/PRD_INSTITUTIONAL_KNOWLEDGE_INGESTION.md`  
**External design reference:** https://github.com/EffortlessAPI/effortless-rulebooks/tree/main/rulebook-examples/procedural-knowledge-ontology

## 1. Product goal

Make Web4 useful to an existing human organization **before** that organization has already normalized its own governance.

A customer should be able to provide ordinary institutional material — policies, SOPs, org charts, workflow exports, role descriptions, event logs, interviews, exception stories — and receive:

1. an inspectable model of how the organization says it works;
2. an evidence-backed model of how it actually works;
3. explicit gaps, contradictions, stale controls, orphaned roles and informal dependencies;
4. candidate governance derived from that knowledge;
5. a ratification path that converts only authorized decisions into law;
6. generated Hub/Hestia enforcement projections;
7. continuous drift/conformance evidence after deployment.

Working customer-facing concept: **Governance Twin**.

> **A Governance Twin is an inspectable model of the organization's declared process, observed process, institutional knowledge, authority, and ratified governance.**

It is not a surveillance twin, an LLM summary, or automatically inferred law.

## 2. Why this exists

Hub and Hestia become valuable once roles, authority, procedures, evidence requirements, escalation paths and law are known.

Real organizations usually hold that information in fragmented forms:

- policy and procedure documents;
- org charts;
- job descriptions;
- spreadsheets and approval matrices;
- workflow engines;
- ticket systems;
- emails and chat conventions;
- oral practice;
- exceptions and precedents;
- informal experts;
- legacy workarounds;
- event logs that contradict documentation.

The onboarding problem is therefore not "how do we encode their law?"

It is:

> **How do we responsibly discover what the institution knows, distinguish description from authority, surface contradictions, and turn only ratified knowledge into executable governance?**

## 3. Design influences from Effortless Rulebooks

The Procedural Knowledge Ontology example is useful because it models institutional knowledge as more than a document corpus.

Relevant concepts include:

- procedure specifications vs executions;
- versioned procedures;
- steps / transitions / alternatives / fallback;
- roles and time-bounded occupants;
- requirements and verification;
- tacit / implicit / explicit / situated knowledge;
- elicitation sessions;
- exceptions;
- rationales;
- knowledge gaps;
- stewardship and authority;
- change requests / review cadence;
- communities of practice;
- controlled vocabulary;
- knowledge brokers;
- process-mining comparison between documented and actual flow.

Its strongest transferable pattern is:

```text
WitnessLoops -> RoleQuestions -> DerivedFields
```

A model grows because a named role needs a governance question answered.

Web4 should use the same discipline.

## 4. Core invariant: knowledge is not law

The ingestion pipeline MUST distinguish:

| State | Meaning |
|---|---|
| `SourceAssertion` | A document/system/person states X. |
| `ObservedPractice` | Execution evidence shows X happens. |
| `ElicitedPractice` | A practitioner describes X as how work is done. |
| `TacitCue` | A practitioner uses X but may not have stated it unprompted. |
| `DerivedFinding` | The model computes X from source evidence. |
| `DisputedClaim` | Multiple credible sources disagree. |
| `Interpretation` | A party explains what a source/rule means. |
| `RatifiedLaw` | Competent authority has formally made X governing. |
| `EnforcementProjection` | Hub/Hestia executable form of RatifiedLaw. |

**Only RatifiedLaw changes governance.**

Observation can create a finding or amendment request, never silent law.

## 5. Institutional Knowledge Graph

The first prototype should define or reuse typed RDF/Lawbook/MRH entities for:

### Organization
- Society / organization;
- organizational unit;
- community of practice;
- vocabulary/domain.

### People / roles / authority
- Role;
- RoleOccupancy;
- AuthorityScope;
- Delegation;
- StewardshipAssignment;
- informal KnowledgeBrokerLink.

### Process
- Procedure;
- ProcedureVersion;
- Step;
- Transition;
- Alternative;
- Fallback;
- Requirement;
- Verification;
- Exception;
- Rationale;
- Resource / tool / system.

### Knowledge
- KnowledgeFragment;
- KnowledgeHolding;
- ElicitationSession;
- Corroboration;
- Disagreement;
- KnowledgeGap;
- SourceArtifact.

### Operations
- ProcedureExecution;
- StepExecution;
- ObservedEvent;
- OperationalBinding;
- process-mining / conformance result.

### Governance
- ChangeRequest;
- ReviewEvent;
- CandidateLaw;
- Ratification;
- Lawbook projection.

Do not create duplicate concepts where SAL, LCT, MRH, R6/R7 or Lawbook already provide the correct semantic home.

## 6. Provenance requirements

Every imported or elicited claim MUST retain:

- source type;
- source identifier;
- source timestamp / effective period;
- extractor / interviewer / model;
- speaker / author where known;
- role of speaker at the relevant time;
- confidence/assertion status;
- corroborating sources;
- contradicting sources;
- whether the claim is formal, observed, elicited, inferred, or ratified.

An LLM-extracted claim is a claim about a source, not ground truth.

## 7. Ingestion channels

Prototype adapters SHOULD support at least:

1. Markdown/text policy;
2. structured org/role CSV or JSON;
3. BPMN-like process export or simple step/edge CSV;
4. execution/event CSV;
5. interview/elicitation transcript;
6. existing Hub/Hestia evidence.

Later adapters can include:
- PDFs;
- Google Drive / SharePoint / Notion;
- Jira / Linear / ServiceNow;
- Slack / Teams;
- HRIS;
- ERP;
- GitHub;
- approval/workflow platforms.

Adapters output typed claims with provenance. They do not output law directly.

## 8. Elicitation workflow

The prototype should support structured sessions inspired by the external PKO example:

- practitioner interview;
- facilitated workshop;
- shadowing/observation;
- critical-incident review;
- retrospective;
- concept laddering;
- repertory-grid comparison;
- process mapping;
- social-network / "who do you ask?" mapping.

Each session produces explicit artifacts:
- claims;
- exceptions;
- cues;
- role questions;
- gaps;
- corroborations;
- disputes.

## 9. Role questions

A customer model should be driven by questions a real role needs answered.

Example role-question object:

```yaml
id: rq-cfo-self-approval
asked_by_role: cfo
question: "Can the preparer approve their own close?"
why_it_matters: "Segregation of duties"
targets:
  - role_assignments
  - close_procedure
  - approval_records
expected_answer_type: boolean_with_evidence
```

A new computed witness should point back to the RoleQuestion that justified it.


## 9A. Fractal learning: learn at the MRH where the practice actually lives

Web4 roles, societies and law are fractally composable. The ingestion system MUST preserve that property during learning.

An observation should not be promoted immediately to "organization knowledge." It first belongs to the smallest MRH that actually explains it.

Examples:

- one operator's workaround -> individual/role MRH;
- a shift convention -> crew/team MRH;
- a department approval pattern -> department MRH;
- a cross-department handoff -> shared-process MRH;
- a company-wide policy interpretation -> organization MRH;
- a regulatory constraint -> parent/federated society MRH.

The system SHOULD therefore treat every learned claim as **MRH-scoped by default** and broaden scope only when evidence supports composition upward.

### 9A.1 Learning object

Every learned institutional claim SHOULD carry:

- `origin_mrh`;
- `candidate_scope_mrh`;
- `role_context`;
- `society_context`;
- `evidence_count`;
- `distinct_role_count`;
- `distinct_child_mrh_count`;
- `contradicting_evidence`;
- `scope_confidence`;
- `promotion_status`.

A claim discovered in one child MRH MUST NOT silently become a parent-society fact.

### 9A.2 Composition upward

Learning composes upward when independent child contexts support the same structure.

Example:

```text
team-a: release manager approves production deploy
team-b: release manager approves production deploy
team-c: security lead substitutes after-hours

        -> department-level candidate:
           "production deploy requires approval,
            normally Release Manager,
            with after-hours Security substitution"
```

The parent model should preserve both:
- the common rule;
- the local exception/override.

This mirrors SAL law inheritance rather than flattening the organization into one policy surface.

### 9A.3 Decomposition downward

Parent knowledge should also decompose into child questions.

If organization law says "all production deploys require independent approval," the Governance Twin should ask each relevant child MRH:

- what counts as production here?
- what role provides independent approval here?
- what is the local escalation path?
- what evidence proves approval?
- does an inherited exception exist?

This avoids false precision at the organization level.

### 9A.4 Scope disagreement is useful evidence

If two child MRHs disagree, do not average them away.

Represent:

- common inherited structure;
- child-specific override;
- unresolved conflict;
- possible stale parent assumption.

A disagreement across MRHs is itself a candidate governance finding.

## 9B. Learning by doing: shadow participation, not survey extraction

The default discovery mechanism SHOULD be **participatory observation in shadow mode**, not questionnaires.

The system should learn from work as it happens:

- who initiates;
- who is consulted;
- who approves;
- who actually performs the act;
- which exceptions recur;
- what evidence people attach;
- what gets escalated;
- which handoffs stall;
- which role is treated as authoritative;
- when actors deviate from the written process;
- which contextual cues distinguish cases.

The interaction itself supplies the elicitation.

Where clarification is needed, ask the smallest question at the moment the ambiguity becomes operationally relevant.

Bad:

> "Please complete this 47-question governance survey."

Better:

> "This deploy is normally approved by Release Manager, but the current request names Security Lead. Is that an after-hours exception, a delegation, or a different process?"

The answer becomes a provenance-bound claim in the relevant MRH.

### 9B.1 Fractal contributors learn by participating

Every role/child society can contribute locally through ordinary activity.

The Governance Twin can accumulate:

```text
local act
  -> local observation
  -> local role/context evidence
  -> local pattern
  -> cross-local comparison
  -> parent candidate structure
  -> ratification at the authority level that owns that scope
```

No participant needs to understand the entire organization.

This is important both ergonomically and epistemically: the people closest to a process contribute the knowledge they actually possess, while broader structure emerges from composition.

### 9B.2 Shadow mode has two outputs

Shadow mode is not only "what would this candidate rule have decided?"

It should emit:

1. **governance divergence**
   - candidate law vs actual action;

2. **learning evidence**
   - which roles, contexts, exceptions and handoffs the observed action teaches us about.

The second output is what makes shadow mode an onboarding mechanism rather than merely a pre-enforcement simulator.

### 9B.3 Attention should follow uncertainty and consequence

Do not interrogate every action.

The system SHOULD ask for clarification when one or more are true:

- high-consequence act;
- authority unclear;
- two MRHs disagree;
- repeated exception;
- novel role/action pairing;
- candidate rule would materially change outcome;
- evidence contradicts declared law;
- a local pattern appears ready for upward promotion.

Routine, well-understood actions should remain silent.

## 9C. MRH-scoped computed witnesses

Computed findings SHOULD identify the MRH at which they hold.

Examples:

| Witness | Scope behavior |
|---|---|
| `DeclaredObservedDrift` | May hold for one team without implying org-wide drift. |
| `KnowledgeSinglePoint` | Could be severe locally and irrelevant elsewhere. |
| `AuthorityAmbiguous` | May be a child override problem or parent-law ambiguity. |
| `RepeatedExceptionBecomingPractice` | Starts local; may become parent candidate if repeated across child MRHs. |
| `TerminologyConflict` | Most useful when comparing sibling MRHs. |
| `RoleChangedWithoutGovernanceUpdate` | Belongs where the role's authority is defined. |

A witness report MUST NOT drop the scope that made the finding true.

## 9D. Scope promotion is not ratification

Learning scope and legal scope are separate transitions.

```text
local observation
  -> local pattern
  -> broader candidate pattern
  -> organization-level candidate knowledge
  -> competent authority ratification
  -> law
```

Evidence may justify moving a claim upward in the knowledge graph. It does not grant authority to move it upward in law.

This preserves the core invariant:

> **Relevance can emerge bottom-up. Authority does not.**



## 9E. Situate role: the persistent institutional-learning function

The Governance Twin needs a named role responsible for **situating** observations, claims, questions and answers in the correct MRH.

Working role name: **Situate**.

**Onboarding is a bounded assignment/profile of Situate, not the whole role.** During initial deployment the role performs concentrated discovery. After onboarding it remains active at low intensity, learning from ordinary work, maintaining unresolved questions, detecting drift, and keeping institutional knowledge current.

### 9E.1 Function

Situate is responsible for:

1. observing work and incoming institutional evidence within its delegated MRH;
2. attaching observations to the narrowest defensible role/society/process context;
3. creating provenance-bound knowledge claims without upgrading them to law;
4. detecting uncertainty, contradiction, missing ownership and scope ambiguity;
5. forming the smallest useful clarification question;
6. routing the question to the role/entity most likely or authorized to answer it;
7. persisting the answer, including who answered, in what role, under what context and with what evidence;
8. seeking corroboration when stakes or ambiguity warrant it;
9. proposing upward composition when sibling MRHs support a broader pattern;
10. decomposing parent questions downward when local answers are required;
11. opening candidate governance/review items when learned structure exposes a governance gap.

Situate is therefore the connective role between:

```text
runtime observation
  <-> institutional knowledge
  <-> MRH structure
  <-> human/AI participants
  <-> candidate governance
```

### 9E.2 Authority boundary

Situate is **epistemic, not sovereign**.

It MAY:
- observe within delegated scope;
- record claims/findings;
- ask/reroute questions;
- request corroboration;
- maintain open knowledge gaps;
- propose candidate law/amendments;
- recommend that a claim's applicability MRH broaden or narrow.

It MUST NOT:
- ratify law;
- grant authority;
- silently promote observed practice into policy;
- alter active Hub/Hestia enforcement;
- treat frequency as legitimacy;
- erase a lower-level exception when composing upward.

This keeps the role distinct from:
- **Law Oracle** — publishes authoritative law;
- **Policy-Entity** — decides specific acts under law;
- **Auditor** — reviews compliance/evidence and may have trust-adjustment powers;
- **Archivist** — preserves records;
- **Administrator** — operates the system.

### 9E.3 Fractal filling

Situate itself is fractally composable.

A large organization may have:

```text
org-situate
  <- finance-situate
      <- AP-situate
      <- treasury-situate
  <- engineering-situate
      <- release-situate
      <- security-situate
```

Each child Situate learns locally. Parent Situate receives:
- promoted candidate patterns;
- cross-child contradictions;
- unresolved questions requiring broader authority;
- scope-change evidence.

The parent does not ingest every local act as globally relevant knowledge.

### 9E.4 Persistent question objects

Questions MUST be first-class durable objects, not chat ephemera.

A minimum `KnowledgeQuestion` shape:

```yaml
id: kq-release-approval-after-hours
origin_mrh: engineering/release
asked_by_role: situate/release
question: "Who may approve a production deploy after hours when Release Manager is unavailable?"
trigger:
  kind: observed_divergence
  evidence: act:deploy-18421
candidate_answer_roles:
  - release-manager
  - security-lead
  - engineering-director
routing_state: routed
status: open
answers: []
```

An answer SHOULD record:
- answerer entity;
- answerer role at answer time;
- answer MRH;
- timestamp;
- source/evidence;
- confidence/qualification;
- whether the answer is descriptive, interpretive or authoritative;
- corroborating/contradicting answers.

### 9E.5 Question routing

Situate SHOULD route by the graph before falling back to broad human interruption.

Preferred route:

```text
question
  -> owning process/role
  -> current role occupant
  -> delegated/parent authority
  -> knowledgeable peer / broker
  -> broader MRH
```

If no route exists, emit a finding such as:
- `KnowledgeOwnerMissing`;
- `QuestionUnroutable`;
- `AuthorityForQuestionAmbiguous`.

The inability to find who can answer is itself institutional knowledge.

### 9E.6 Attention budget

Situate SHOULD optimize for **learning by doing**, not form completion.

Ask only when:
- an answer would materially change the model or candidate governance;
- ambiguity blocks correct scope attribution;
- consequence is high;
- recurrence suggests a pattern;
- sibling MRHs conflict;
- promotion to a broader MRH is under consideration;
- the current answer is stale.

Routine acts should contribute passive evidence without interruption.

### 9E.7 Onboarding profile

During onboarding, Situate temporarily raises its sampling/elicitation intensity:

- ingest existing documents and structure;
- observe representative workflows;
- ask more frequent local clarification questions;
- map role ownership;
- identify vocabulary;
- establish initial knowledge gaps;
- build the first MRH decomposition.

As confidence grows, it decays toward steady-state participation.

A useful onboarding completion condition is not "survey complete." It is:

> **For the selected pilot process, the role/authority graph, major procedure branches, evidence expectations and unresolved gaps are sufficiently situated that shadow governance can run without systematically asking humans what everything means.**


## 10. Computed institutional witnesses

Initial prototype witnesses:

| Witness | Meaning |
|---|---|
| `DeclaredObservedDrift` | Observed execution differs from declared procedure. |
| `ControlHasNoWitness` | A control exists but there is no mechanism/evidence showing satisfaction or failure. |
| `BlockingControlBypassed` | Execution continued past an unsatisfied blocking control. |
| `RoleUnoccupied` | Required authority/role has no effective occupant. |
| `AuthorityAmbiguous` | Multiple sources conflict about who may decide. |
| `KnowledgeSinglePoint` | Important procedure knowledge depends on one person/source. |
| `TacitKnowledgeUnformalized` | High-impact practice exists only as tacit/elicited knowledge. |
| `EscalationUnreachable` | Procedure/law names escalation but no live resolver exists. |
| `AppealUnreachable` | A promised appeal path is not executable. |
| `PolicyStale` | Review cadence or source version is past due. |
| `TerminologyConflict` | Multiple departments use inconsistent terms for the same concept. |
| `RoleChangedWithoutGovernanceUpdate` | Role occupant/type changed without dependent process/law review. |
| `AIHandoverUnratified` | AI/automation now performs a role formerly assigned to a human without explicit authority transition. |
| `RepeatedExceptionBecomingPractice` | An exception recurs enough to warrant review but is not silently promoted to law. |

Witnesses are findings, not enforcement decisions.

## 11. Candidate governance compilation

The system MAY propose candidate Lawbook objects from institutional knowledge:

- roles and role scopes;
- norms;
- procedures;
- evidence/witness requirements;
- delegation rules;
- escalation;
- appeal;
- communication constraints;
- review cadence;
- expiry/effective periods;
- amendment triggers.

Every candidate MUST carry:
- source claims;
- derivation;
- uncertainty;
- proposed competent authority;
- affected roles;
- conformance tests.

No candidate may activate itself.

## 12. Ratification workflow

Candidate governance becomes law only through a governed change:

```text
CandidateLaw
  -> source/evidence review
  -> stakeholder objections
  -> impact/conformance run
  -> competent authority approval
  -> required witness/quorum
  -> effective date
  -> Lawbook version
  -> Hub/Hestia projections
  -> activation
```

This should reuse the Lawbook amendment model.

## 13. Deployment ladder

A customer pilot should not jump directly from ingestion to hard enforcement.

Stages:

### Stage 0 — Discovery
- ingest sources;
- no governance change.

### Stage 1 — Governance Twin
- model roles/process/knowledge;
- show computed findings.

### Stage 2 — Shadow governance
- candidate rules evaluate real or replayed acts;
- decisions are recorded but not enforced.

### Stage 3 — Advisory
- approved rules warn/escalate;
- humans can compare proposed decisions with current practice.

### Stage 4 — Enforcement
- only explicitly ratified controls become blocking.

### Stage 5 — Continuous conformance
- new evidence can open review/change requests;
- no automatic law drift.

## 14. Customer pilot: first convincing demonstration

Target a process small enough to model in days, not months.

Ask for:
- 3-10 documents;
- one org/role map;
- one workflow;
- one event sample;
- 3-5 interviews;
- one memorable failure/exception.

Deliver:

1. **Process/authority map**
2. **Declared-vs-observed map**
3. **Knowledge-risk map**
4. **Computed witness board**
5. **Candidate governance diff**
6. **One ratified live rule**
7. **One Hub/Hestia shadow-to-live demonstration**

The sales proof should be a customer-specific finding, not a feature tour.

Example:
> "The procedure requires VP Ops review, but the role has no current occupant, and the actual workflow bypassed that review in 14 of 52 executions."

Then:
> "Here is the proposed escalation repair. If you ratify it, Hub and Hestia can enforce and witness it."

## 15. Prototype domain

Create a synthetic but customer-realistic mini organization:

- 5-step approval process;
- 3 roles;
- one policy document;
- one tacit exception;
- one stale role assignment;
- one execution log showing drift;
- one AI role handoff;
- one unreachable appeal/escalation.

Prototype must demonstrate:

```text
source artifacts
  -> typed institutional claims
  -> role questions
  -> computed findings
  -> candidate Lawbook
  -> ratification
  -> Hub law projection
  -> Hestia projection
  -> shadow replay
  -> enforced/witnessed act
```

## 16. Acceptance criteria

The prototype passes when:

- every claim is provenance-bound;
- documented and observed behavior can disagree without either being overwritten;
- tacit knowledge can be represented without being treated as law;
- at least five computed institutional witnesses fire on seeded defects;
- candidate law cites the institutional facts that motivated it;
- candidate law cannot activate without authority/witness evidence;
- one ratified rule is projected into both Hub and Hestia;
- replayed action produces the same law decision in both;
- a subsequent observed drift opens a review item instead of silently changing law.

## 17. Relationship to the Lawbook PRD

Lawbook answers:

> **How is governing meaning represented once and projected consistently?**

This PRD answers:

> **How does an existing organization get from messy institutional reality to candidate governing meaning?**

Together:

```text
Institutional knowledge
  -> Governance Twin
  -> candidate law
  -> ratification
  -> Lawbook
  -> Hub/Hestia projections
  -> witnessed execution
  -> observed drift
  -> review
```

## 18. External dependency posture

Effortless Rulebooks is an architectural reference, not a required dependency.

Web4 should borrow:
- elicitation discipline;
- institutional-knowledge vocabulary;
- role-question pattern;
- computed witnesses;
- process-mining comparison;
- structured source -> multiple projections.

Web4 keeps:
- RDF/MRH ontology;
- LCT identity;
- SAL authority;
- R6/R7 action grammar;
- Lawbook;
- Web4 evidence/witnessing;
- Hub/Hestia enforcement.
