# PRD — Sovereign Repository Plane

**Status:** bootstrap design for implementation  
**Date:** 2026-10-04  
**Scope:** provider-independent repository substrate for Web4 / Hub / Hestia / SAGE / seed distribution  
**Working name:** Repository Plane / `repo-plane`  
**Initial backends:** GitHub + self-hosted Gitea  
**Related:** `web4-standard/core-spec/interface-planes.md`, Hestia one-gate architecture, Lawbook IR

## 1. Problem

The current Web4 ecosystem uses Git and GitHub heavily for source, proposals, review, releases, fleet coordination and the emerging seed / Lawbook workflow.

That is useful infrastructure. It must not become a hidden dependency.

Some organizations will be unable or unwilling to use a public forge at all:

- air-gapped or classified environments;
- regulated enterprises with strict data residency;
- organizations that prohibit externally hosted source;
- sovereign communities that require self-hosted infrastructure;
- customers who accept Git but not GitHub;
- future deployments whose storage substrate is not Git.

At the same time, higher layers are beginning to acquire GitHub-shaped vocabulary: repositories, branches, pull requests, issue numbers and merge permissions. If those concepts leak into Web4 authority semantics, a convenient current provider becomes architecture.

The requirement is therefore not “build our own GitHub.”

> **Define a provider-independent repository contract, make GitHub and a fully local Gitea deployment two implementations of it, and keep Web4 authority outside the forge.**

The same workflow should run whether the underlying repository service is public GitHub, an isolated Gitea instance, or a future provider.

## 2. Product thesis

Repository Plane is the sovereign source/history/change substrate for a Web4 society.

It supplies:

- versioned repositories;
- immutable revisions;
- refs / branches;
- change proposals;
- review records;
- releases and artifacts;
- provider events;
- authenticated repository operations.

It does **not** decide:

- who legitimately holds a society role;
- whether an actor has Web4 authority;
- what society law permits;
- whether a governance proposal becomes law;
- whether a seed update is automatically adopted.

Those remain Web4 concerns.

A forge permission is capacity. It is not authority.

A repository record is evidence about what the provider observed. It is not, by itself, a Web4 witness.

A merge is a content transition. It is not, by itself, ratification.

## 3. Naming note: “plane”

`repo-plane` is an operational shorthand, not a new Web4 fact plane.

The canonical interface-plane specification already defines fact planes A–E. Repository content is application state; Web4 control surfaces around repository operations MUST remain decomposed by the existing fact planes:

- **A — Governance authority:** law deciding who may authorize repository operations;
- **B — Gate execution:** pre-action evaluation for a requested repository mutation;
- **C — Occupancy & authorization:** proof that the acting entity occupies a relevant role;
- **D — Attribution & witness:** Web4 record of the request, decision and observed outcome;
- **E — Infrastructure telemetry:** provider/gate unavailability and adapter/deployment drift.

An `ambiguous` outcome of a mutation that was **dispatched** is not Plane E. That act was decided and witnessed (D), so its ambiguous result, and the later reconciliation, belong to the act's own outcome record (§8, §16). Plane E records never enter the witness chain (`interface-planes.md`). Filing the ambiguity there would leave a witnessed permit with no outcome. Only a failure *before* dispatch (no provider reached, no verdict) is E-only.

The repository adapter MUST NOT collapse these merely because a native forge API exposes them through one token or endpoint.

## 4. Goals

### 4.1 Provider independence

Higher-level Web4, Hestia, Hub and SAGE code should depend on repository-domain operations, not GitHub-specific nouns or IDs when provider-specific behavior is unnecessary.

Initial provider set:

1. GitHub;
2. Gitea;
3. later providers only when a concrete deployment requires them.

### 4.2 Fully local operation

A reference deployment MUST be able to operate without GitHub or another external forge after installation/bootstrap.

The target local stack is:

```text
local models / humans
        |
   Hub / SAGE / Hestia
        |
  Web4 pre-action gate
        |
    repo-plane
        |
      Gitea
        |
 local Git repositories
```

### 4.3 One-gate compatibility

Consequential repository mutations MUST be expressible as governed acts and MUST have a path through the same Web4/Hestia law decision machinery used for other governed acts.

Examples include:

- push/update protected refs;
- merge change proposal;
- create/delete branch or tag;
- create/delete repository;
- change repository visibility;
- modify collaborator/team access;
- publish a release;
- publish a package/artifact;
- modify workflow/execution configuration;
- change mirroring/federation configuration.

The provider adapter MUST NOT grow a parallel policy engine.

### 4.4 Seed / Lawbook sovereignty

A society MUST be able to ingest a marketplace seed and thereafter maintain its fork, Situate findings, shadow results, proposed updates and ratified Lawbook entirely inside its own repository boundary.

Upstream seed changes arrive as **candidate changes**.

They MUST NOT silently become governance because a Git merge, mirror, package update or repository synchronization succeeded.

## 5. Non-goals

Sprint 0–3 explicitly do not attempt to:

- invent a new version-control system;
- fork Gitea before evidence shows it is necessary;
- make Git history the Web4 witness chain;
- make forge ACLs the source of Web4 authority;
- automatically ratify governance changes;
- reproduce every GitHub feature;
- build a public seed marketplace checkout system;
- federate arbitrary repository servers before local parity is measured.

## 6. Domain model

The provider-independent vocabulary starts small.

| Object | Meaning |
|---|---|
| `Repository` | Versioned content container. |
| `Revision` | Immutable content state / commit-equivalent. |
| `Ref` | Named movable reference such as branch or tag. |
| `ChangeProposal` | Proposed transition between repository states; PR/MR-equivalent. |
| `Review` | Review disposition and commentary attached to a proposal/revision. |
| `Issue` | Provider-hosted work/discussion object when used. |
| `Release` | Named/versioned publication bound to a revision. |
| `Artifact` | File/package/build result associated with a revision/release. |
| `ProviderIdentity` | Native provider account/service identity binding, not Web4 identity itself. |
| `ProviderEvent` | Provider-observed event used as operational evidence. |
| `OperationRequest` | Normalized requested read or mutation. |
| `OperationResult` | Normalized observed outcome. |

Provider-native IDs MUST remain available for debugging and round trips, but higher layers SHOULD prefer stable repository-plane IDs/URIs.

## 7. Authority invariant

The most important invariant is:

> **Provider capability MUST NOT be interpreted as Web4 authority.**

Examples:

- a GitHub org owner may still lack authority under society law to ratify a Lawbook;
- a Gitea administrator may be technically capable of force-pushing but not authorized to do so;
- a Web4 role may have authority to approve a change without possessing a long-lived forge token;
- a seed author’s upstream release may be authentic and reputable without being locally authoritative.

Repository Plane therefore treats native ACLs as one enforcement/capacity layer, not as the authority oracle.

## 8. Governed mutation flow

The target consequential-operation path is:

```text
request
  |
  v
normalize repository operation
  |
  v
bind entity + role + society + target + expected state
  |
  v
Web4/Hestia gate
  |
  +-- deny/escalate --> no provider mutation
  |
  v
committed permit / required evidence
  |
  v
provider mutation
  |
  v
observe native outcome
  |
  v
normalize OperationResult
  |
  v
Web4 outcome witness / R7
```

The exact enforcement point may differ by provider, but the semantic contract may not.

For consequential writes:

1. no usable verdict → no act;
2. unknown decision → no act;
3. stale/superseded permit → no act;
4. provider outcome ambiguity MUST remain ambiguity, not be rewritten as success;
5. observed provider state MUST be reconciled with the requested operation;
6. a committed decision and a provider success are different evidence objects.

## 9. Operation envelope

A governed mutation SHOULD carry at least:

```text
operation_id
idempotency_key
provider
repository
operation
target
expected_revision / expected_generation
actor_lct
role_lct
society_lct
r6_action_id
law_version / policy_digest
decision_receipt
requested_at
```

`actor_lct`, `role_lct` and `society_lct` are **canonical** LCT ids (`lct:web4:mb32:…`). A Hub member UUID is a membership/routing id, not a presence id, and reaches a canonical id only through the one resolver (`hub/docs/PRD_LCT_IDENTITY_CONVERGENCE.md`; `HubMemberId` vs `CanonicalLctId`). An envelope that carries a member UUID in an `*_lct` field has re-merged the two namespaces that PRD separates.

The provider result SHOULD return:

```text
operation_id
provider_native_id
provider_actor
status = succeeded | refused | failed | ambiguous
prior_state
resulting_state
observed_at
provider_evidence
```

The outcome witness may refer to these fields but MUST not claim facts the provider result did not establish.

## 10. Provider contract

The first contract MUST cover the workflows the ecosystem actually uses rather than cloning a forge API.

### Reads

- get/list repositories;
- get revision/ref;
- fetch file/tree;
- compare revisions;
- list/fetch change proposals;
- list/fetch reviews and comments;
- list/fetch issues when used;
- list/fetch releases/artifacts;
- consume provider events.

### Mutations

- create/update ref;
- create commit/content update;
- open/update change proposal;
- submit review;
- merge change proposal;
- create issue/comment;
- create release/artifact metadata;
- repository lifecycle operations needed by seed ingestion.

ACL, workflow-execution, package-registry and mirror operations are intentionally separate capability groups because their assurance requirements differ from ordinary code review.

See `docs/repository-plane/PROVIDER_CONTRACT.md`.

## 11. Backend strategy

### 11.1 GitHub

GitHub is the first parity backend because the fleet already uses it.

The GitHub adapter establishes current behavior as a conformance corpus rather than as canonical semantics.

### 11.2 Gitea

Gitea is the first sovereign backend candidate because it provides a relatively small, mature, self-hostable Git forge with an API and local deployment story.

We do **not** fork it initially.

Sprint 2 runs a measured spike against stock Gitea and records:

- which required operations map cleanly;
- which events are observable;
- which mutations can be intercepted before execution;
- which paths can bypass an external gate;
- how SSH, HTTP, API and web operations differ;
- whether extension points are sufficient for one-gate enforcement;
- whether a reverse-proxy / broker architecture is enough;
- what remains dependent on external network services.

See `docs/repository-plane/GITEA_SPIKE.md`.

### 11.3 Fork criterion

A Gitea fork is justified only if measured requirements cannot be met safely by:

1. stock configuration;
2. supported hooks/extensions;
3. a repository-plane broker/proxy;
4. a narrow upstreamable extension.

If a fork becomes necessary, the fork MUST be scoped to the minimum enforcement/identity/event seams required by the provider contract.

“We want our own forge” is not a fork criterion.

## 12. Provider equivalence

Provider parity means semantic equivalence, not UI equivalence.

The same conformance scenario should be runnable against GitHub and Gitea:

```text
create repository fixture
create base revision
create branch/ref
propose change
review change
attempt unauthorized merge -> refused by Web4 path
authorize merge
merge
observe exact resulting revision
record outcome
publish release
verify lineage
```

The native provider IDs and incidental event order may differ.

The normalized semantic outcome must not.

## 13. Seed / governance update semantics

Repository synchronization is deliberately weaker than governance adoption.

For a seed fork:

```text
upstream seed version N+1
        |
        v
fetch/import
        |
        v
candidate repository change
        |
        v
Situate compare against local Governance Twin
        |
        v
shadow/replay/conformance
        |
        v
findings
        |
        v
local authority review
        |
        v
ratification
        |
        v
effective Lawbook projection
```

No `git pull`, merge, mirror synchronization or package update is sufficient to cross the ratification boundary.

## 14. Air-gap requirement

The local reference deployment MUST have an explicit disconnected acceptance test.

After dependencies/images/binaries required by the test are staged locally:

- disable external network access;
- start repository service;
- authenticate locally;
- create and clone a repository;
- push/fetch;
- open/review/merge a change;
- emit/consume provider events;
- run repository-plane conformance tests;
- run at least one Web4-gated mutation;
- restart services and verify persisted state;
- verify no test step requires GitHub, public package registries or hosted identity.

CI/workflow support, if included, MUST use local actions/components in this mode.

## 15. Security and evidence boundaries

Repository Plane MUST preserve these distinctions:

- **identity evidence** != role occupancy;
- **role occupancy** != authority;
- **authority** != gate decision;
- **gate decision** != provider execution;
- **provider execution** != Web4 witness;
- **repository history** != law legitimacy;
- **administrator capability** != authorized governance.

A provider event may support an outcome witness. It cannot retroactively manufacture a missing pre-action decision.

A provider webhook is observation after the fact. It is not a substitute for a pre-action gate.

## 16. Failure semantics

At minimum:

| Condition | Required posture |
|---|---|
| provider unreachable before mutation | no act; Plane-E telemetry |
| gate unreachable / no verdict | no consequential act |
| decision receipt uncommitted where required | no consequential act |
| expected revision mismatch | refuse/retry as a new request |
| provider timeout with unknown outcome | `ambiguous`; reconcile before retry |
| provider says success but state cannot be observed | `ambiguous`, not success |
| duplicate idempotency key | return/reconcile original operation |
| native ACL permits but Web4 denies | deny |
| Web4 permits but native provider refuses | failed/refused outcome; do not weaken ACL automatically |

## 17. Sprints

### Sprint 0 — Contract and evidence corpus

Deliverables:

- this PRD;
- provider contract;
- Gitea spike plan;
- explicit authority/capacity boundary;
- GitHub current-workflow inventory;
- initial provider-equivalence scenarios.

Exit: two implementers can independently build adapters without importing GitHub semantics into the interface.

### Sprint 1 — GitHub adapter

Deliverables:

- repository-plane library/service skeleton;
- GitHub provider implementation for required read/write subset;
- normalized IDs and errors;
- idempotency and expected-state handling;
- conformance tests against a disposable GitHub fixture or mocks where live mutation is inappropriate.

Exit: an existing fleet change-review workflow can run through the provider contract.

### Sprint 2 — Stock Gitea spike + adapter

Deliverables:

- reproducible local Gitea deployment;
- Gitea provider implementation;
- parity corpus;
- interception/bypass matrix for HTTP, SSH, API and web paths;
- external-dependency inventory;
- fork/no-fork decision record.

Exit: same semantic workflow passes against GitHub and local Gitea, with known enforcement gaps documented rather than hand-waved.

### Sprint 3 — Sovereign single-node bundle

Deliverables:

- one-command/single-package local deployment target where practical;
- local DB/storage defaults;
- local auth bootstrap;
- backup/restore;
- disconnected acceptance test.

Exit: a small organization can run repository services with no external forge dependency.

### Sprint 4 — One-gate repository mutations

Deliverables:

- R6 mapping for consequential repository operations;
- Hestia/Web4 gate integration;
- committed decision receipt binding;
- outcome/R7 reconciliation;
- bypass tests across every supported provider mutation path.

Exit: no supported consequential mutation path silently escapes the declared gate model.

### Sprint 5 — Seed registry / provenance

Deliverables:

- local seed catalog;
- seed author/version/lineage metadata;
- import/fork/update-as-candidate workflow;
- conformance corpus attachment;
- Situate handoff;
- explicit ratification boundary.

Exit: an organization can buy/import a seed, disconnect, and own its continuing repository/governance lifecycle locally.

### Sprint 6 — Federation and transport options

Only after local operation is boring.

Investigate:

- cross-society repository discovery;
- signed artifact/seed exchange;
- selective replication;
- Radicle-inspired signed collaboration objects where useful;
- non-Git storage providers behind the same higher-level contract.

## 18. Initial conformance properties

The test suite should make these executable invariants:

1. **Provider permission is never sufficient authority.**
2. **A provider denial never gets rewritten into a Web4 allow.**
3. **No verdict means no consequential mutation.**
4. **Ambiguous provider outcome stays ambiguous until reconciled.**
5. **Expected-state mismatch cannot silently overwrite newer state.**
6. **GitHub and Gitea produce equivalent normalized outcomes for the core corpus.**
7. **A seed update remains candidate state until explicitly ratified.**
8. **Repository history cannot substitute for Web4 witness history.**
9. **Air-gapped mode has no undeclared external dependency.**
10. **All supported native mutation paths are represented in the bypass/interception matrix.**

## 19. Open design questions to answer with experiments

These are experiments, not blockers to Sprint 0:

- Can stock Gitea provide a sufficiently strong pre-receive / pre-mutation enforcement seam for every supported write path?
- Is a repository-plane broker enough, or do direct Git SSH/HTTP paths require server-side integration?
- Which provider events contain enough stable evidence to bind an R7 outcome without provider-specific semantics leaking upward?
- Should repository-plane be a library, daemon, or both?
- Which operations need their own capability classes rather than the generic repository write class?
- What is the minimum local auth story that works for both humans and Web4 entities without confusing authentication with authority?
- When does Git cease to be the right storage substrate for governance artifacts, while the provider contract remains useful?

## 20. Project placement

The intended destination is a dedicated repository, provisionally `dp-web4/repo-plane`.

Until that repository exists, bootstrap design and cross-ecosystem contract material live in `dp-web4/web4/docs/` because Web4 owns the provider-independent authority/evidence boundary.

Implementation-specific Gitea code SHOULD move to the dedicated repository rather than becoming part of the Web4 standard tree.

## 21. Success criterion

A successful Repository Plane makes this statement true:

> A Web4 society can move from GitHub to a fully self-hosted repository ecosystem without changing its model of identity, authority, law, evidence, ratification or governance — only the repository provider.

That is the portability property we actually care about.
