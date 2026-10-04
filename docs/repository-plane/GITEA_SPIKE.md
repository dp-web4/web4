# Gitea Spike Plan — Repository Plane

**Status:** ready for implementation  
**Date:** 2026-10-04  
**Parent:** ../PRD_REPOSITORY_PLANE.md

## 1. Question

Can stock Gitea serve as the first fully self-hosted Repository Plane backend while preserving Web4's one-gate and evidence boundaries?

The spike MUST answer with measured behavior, not product descriptions.

## 2. Test deployment

Start with the smallest reproducible local deployment:
- current stable Gitea;
- SQLite first, Postgres follow-up only if a behavior depends on it;
- local filesystem repositories;
- local account + token;
- SSH and HTTP Git enabled;
- web UI enabled;
- API enabled;
- webhooks/events enabled;
- Actions disabled initially, then enabled for offline-dependency testing.

Record exact version, configuration and hashes used.

## 3. Provider-parity corpus

Implement or manually drive the provider-contract scenarios:
1. create repo;
2. create/read revision;
3. create/update branch;
4. create proposal;
5. submit review;
6. stale target conflict;
7. merge;
8. release;
9. provider event correlation;
10. restart and reconcile.

For every step record:
- API/native operation;
- returned identifiers;
- observed resulting state;
- emitted events;
- whether the operation can be made compare-and-swap safe.

## 4. Enforcement / bypass matrix

This is the main spike.

For each consequential mutation, determine every native route that can perform it.

| operation | web UI | REST API | Git HTTP | Git SSH | internal/background | hook/extension before act? |
|---|---|---|---|---|---|---|
| update branch | | | | | | |
| force push | | | | | | |
| create/delete tag | | | | | | |
| merge proposal | | | n/a | n/a | | |
| change ACL | | | n/a | n/a | | |
| create/delete repo | | | n/a | n/a | | |
| publish release | | | n/a | n/a | | |
| change workflow config | content path | content path | content path | content path | | |

A supported Web4-gated mutation is not complete until every route capable of producing the same effect is either:
- intercepted by the same semantic gate;
- disabled;
- constrained so it cannot bypass the governed route;
- explicitly out of scope and surfaced as an assurance gap.

## 5. Pre-action seam tests

Determine whether stock Gitea offers a safe supported seam for:
- pre-receive push authorization;
- merge authorization;
- ref create/delete;
- repository lifecycle;
- ACL/admin changes;
- release/package publication.

For each seam answer:
- before or after mutation?
- synchronous?
- can it fail closed?
- does it receive authenticated actor identity?
- target repository/ref/revision?
- proposed changes?
- stable correlation id?
- timeout semantics?
- can admin/API/background jobs bypass it?
- is custom code execution required?

A webhook alone scores **after-action observation**, not pre-action enforcement.

## 6. Broker architecture test

Before proposing a fork, test a brokered deployment:

```text
clients
  |
repo-plane broker
  |
Web4/Hestia gate
  |
Gitea API / Git endpoint
```

Then try to bypass it through every enabled native route.

If disabling direct routes leaves a practical system, document that.

If direct Git SSH/HTTP must remain exposed and cannot invoke the common gate safely, that is evidence for server-side integration.

## 7. Identity mapping

Test:
- local account;
- token;
- SSH key;
- OIDC if available in the test environment.

Document which stable native identity appears on each operation/event.

Do not treat successful login as Web4 role occupancy.

Prototype a mapping record:

```text
web4_entity_lct
provider = gitea
provider_instance
provider_identity
binding_method
bound_at
expires_at
witness
```

## 8. Offline test

After staging required binaries/images:
- disconnect external network;
- restart from cold;
- create repo;
- clone via HTTP and SSH;
- push;
- open/review/merge proposal;
- consume events;
- run provider adapter tests;
- if Actions are enabled, run one workflow using only locally hosted action/component references.

Record every outbound connection attempt.

Any required public dependency is a failed air-gap criterion until explicitly vendored or disabled.

## 9. Failure injection

At minimum:
- kill Gitea before request;
- kill during mutation request;
- delay response past adapter timeout;
- return 5xx;
- revoke token;
- make expected target revision stale;
- emit duplicate webhook/event;
- restart between ambiguous result and reconciliation.

Required rule: uncertain effect becomes `ambiguous`, then read/reconcile.

## 10. Fork decision record

At the end produce one of:

### A — stock Gitea sufficient
No fork. Build adapter/broker.

### B — narrow upstreamable seam needed
Open/implement the smallest extension against upstream first.

### C — maintained fork justified
Only if a required invariant cannot otherwise be met.

The decision record MUST identify:
- exact invariant;
- exact bypass or missing seam;
- test reproducing it;
- smallest code area requiring change;
- maintenance/security consequences.

## 11. Ideas to borrow, not dependencies

Review Forgejo and Radicle for:
- federation approaches;
- signed collaboration objects;
- identity/replication patterns;
- cross-instance authorization.

Do not import those semantics into Sprint 2 unless they solve a measured Gitea gap.

## 12. Exit criteria

The spike is complete when:
- provider parity results exist;
- bypass matrix is filled;
- air-gap test is measured;
- failure semantics are exercised;
- fork/no-fork decision is evidence-backed;
- remaining gaps are filed as concrete implementation issues.
