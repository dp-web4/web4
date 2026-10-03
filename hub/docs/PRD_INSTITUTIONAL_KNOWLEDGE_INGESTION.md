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
