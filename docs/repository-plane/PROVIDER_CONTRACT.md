# Repository Plane — Provider Contract v0

**Status:** draft  
**Date:** 2026-10-04  
**Parent:** ../PRD_REPOSITORY_PLANE.md

## 1. Purpose

This contract defines the minimum provider-independent repository semantics required by the current Web4 ecosystem.

It is intentionally smaller than GitHub's or Gitea's native APIs.

The adapter boundary MUST preserve provider-native identifiers and evidence for debugging, but higher layers MUST NOT depend on provider-specific nouns where a provider-independent meaning exists.

## 2. Core types

### RepositoryRef
- `provider`
- `namespace`
- `name`
- `stable_id`
- `native_id`
- `default_ref`
- `visibility`
- `generation` if provider exposes one

### RevisionRef
- repository
- immutable revision id
- parents when available
- authored/committed metadata
- provider evidence

### RefState
- repository
- ref name
- ref kind = branch | tag | other
- revision
- observed_at

### ChangeProposal
- stable_id
- native_id
- repository
- title/body
- source ref/revision
- target ref/revision
- state = open | draft | merged | closed
- author ProviderIdentity
- created/updated timestamps
- merge revision if merged

### Review
- stable_id
- proposal
- reviewer ProviderIdentity
- disposition = approve | request_changes | comment | dismiss | unknown
- revision binding if provider supports it (GitHub does, via the REST review object's `commit_id`. Some CLI/GraphQL projections return it as null, so an adapter must read the source that actually carries it before declaring the binding unsupported.)
- body / inline comments
- observed_at

### OperationRequest
- operation_id
- idempotency_key
- operation kind
- repository
- target
- expected state/generation
- requested provider principal
- Web4 bindings carried opaquely by the adapter

### OperationResult
- operation_id
- status = succeeded | refused | failed | ambiguous
- native operation/event ids
- prior state
- resulting state
- provider actor
- observed_at
- evidence
- error class/detail

## 3. Error classes

Adapters MUST normalize at least:

- `not_found`
- `already_exists`
- `permission_denied`
- `conflict`
- `expected_state_mismatch`
- `rate_limited`
- `provider_unavailable`
- `timeout_ambiguous`
- `invalid_request`
- `unsupported`
- `provider_error`

A timeout after a mutation request is sent MUST NOT be normalized to `failed` unless the adapter can prove the provider did not apply the mutation.

## 4. Read capabilities

### repository.get
Return repository metadata.

### repository.list
List repositories visible to the provider principal. Visibility is provider reachability, not Web4 authority.

### revision.get
Resolve an immutable revision.

### ref.get / ref.list
Resolve and enumerate refs.

### content.get
Fetch a file/blob/tree representation tied to an immutable revision when possible.

### revision.compare
Compare two immutable states.

### proposal.get / proposal.list
Fetch change proposals.

### review.list
Fetch review submissions and associated comments where available.

### issue.get / issue.list
Optional in minimal backend, required when higher-level workflow uses provider-hosted issues.

### release.get / release.list
Fetch releases and attached artifact metadata.

### event.consume
Consume provider events through webhook, polling or native event stream.

## 5. Mutation capabilities

Every mutation returns `OperationResult`.

### ref.create
Create a ref at an expected revision.

### ref.update
Move a ref using compare-and-swap semantics where possible.

Required input:
- current expected revision;
- target revision.

An adapter that cannot provide atomic expected-state protection MUST declare that limitation.

### commit.create / content.update
Create immutable content/revision state without implicitly updating a protected ref unless the request explicitly includes that transition.

### proposal.open
Open a change proposal from source to target.

### proposal.update
Update metadata or state.

### review.submit
Submit review disposition/comment.

### proposal.merge
Merge a proposal with:
- expected proposal state;
- expected target revision/generation where provider allows;
- requested merge strategy;
- idempotency key.

### issue.create / comment.create
Create provider-hosted work/discussion objects where used.

### release.create
Publish release metadata bound to a specific immutable revision.

### repository.create
Needed for local seed ingestion and sovereign provisioning.

Deletion, visibility change, ACL change, workflow execution, package publication and mirroring are separate capability groups and MUST NOT be implied by generic repository write permission.

## 6. Identity boundary

`ProviderIdentity` is an account/service identity asserted by the provider.

It MUST NOT be treated as:
- LCT identity;
- proof of role occupancy;
- proof of society membership;
- proof of authority.

An implementation MAY maintain a witnessed binding between Web4 identity and provider identity. That binding is separate evidence and may expire or be revoked.

## 7. Evidence boundary

Provider evidence MAY include:
- native event ids;
- HTTP response metadata;
- immutable revision ids;
- signed provider payloads where available;
- webhook/event body hashes;
- native actor ids;
- timestamps;
- compare results.

Provider evidence supports the claim “the provider reported/observed X.”

It does not by itself support “X was authorized under Web4 law.”

## 8. Idempotency and ambiguity

Consequential mutation methods SHOULD accept an idempotency key.

Where the provider lacks native idempotency:
1. adapter records the requested key before dispatch;
2. adapter binds it to the provider request/evidence available;
3. timeout after dispatch produces `ambiguous`;
4. reconcile by reading resulting state before retry;
5. retry only when the original effect is proven absent or the operation is naturally idempotent.

## 9. Expected-state discipline

Mutations that can overwrite or supersede state MUST carry expected-state information.

Examples:
- branch update expects old revision;
- merge expects target head;
- metadata update expects generation/etag if provider supports it.

If the expectation is stale, return `expected_state_mismatch`. Do not “helpfully” retry against newer state without a new governed request.

## 10. Conformance scenarios

Every backend MUST pass the same semantic corpus for supported capabilities.

### C1 — repository lifecycle
Create fixture repo, inspect metadata, create revision/ref, read exact content.

### C2 — compare and proposal
Create divergent revisions, open proposal, compare source/target, fetch normalized proposal.

### C3 — review
Submit review, observe normalized disposition and revision binding.

### C4 — expected-state conflict
Attempt ref update or merge against stale expected state. Must refuse/conflict rather than overwrite.

### C5 — merge
Merge approved fixture proposal and verify resulting immutable revision.

### C6 — ambiguity
Inject timeout/connection loss after dispatch. Adapter must produce or preserve `ambiguous` until state is reconciled.

### C7 — idempotent replay
Replay same operation id/idempotency key. Must not create a second semantic operation.

### C8 — provider denial
Native ACL denies operation. Normalized result remains refused/failed; higher layer cannot reinterpret as success.

### C9 — event correlation
Provider event can be correlated to normalized operation/result without relying only on human-readable text.

### C10 — restart
Restart adapter/provider where applicable. Idempotency/reconciliation state required for safe retry survives.

**Not covered by C1–C10.** PRD §18 invariants 1–3 are broker-layer properties, and an adapter cannot test them:
1. native permit with a Web4 deny refuses;
2. no verdict means no mutation;
3. a stale or superseded permit means no mutation.

The Sprint 4 broker corpus must add them as scenarios. Until then, passing C1–C10 says nothing about them.

## 11. Web4 integration contract

The adapter accepts a Web4 decision receipt as opaque binding material when a governed operation is dispatched.

The adapter MUST NOT:
- evaluate society law independently;
- mint authority;
- infer allow from possession of a provider credential;
- infer ratification from a merge;
- rewrite an absent/invalid decision receipt into provider authorization.

A later repository-plane broker MAY require a valid committed receipt before dispatching consequential mutations, but validation rules belong to the Web4/Hestia integration layer, not each provider implementation.

## 12. Capability declaration

Each backend MUST publish a machine-readable capability declaration, including:
- supported operations;
- expected-state guarantees;
- idempotency guarantees;
- event mechanism;
- pre-mutation interception availability;
- direct-path bypasses known to exist;
- external dependencies;
- offline support status.

This declaration is evidence for deployment planning, not a trust score.
