# Hub Implementation Authority

**Decision:** 2026-10-07  
**Authority:** dp / ecosystem repository-boundary ruling

## Rule

Durable functionality lives with the functional system it belongs to.

For Hub and Web4 society behavior, **`dp-web4/web4` is authoritative**. This includes:

- Hub runtime behavior;
- federation and mesh behavior;
- reusable transport/messaging logic;
- protocol adapters and portability support;
- generic fixtures and conformance/regression tests;
- operational helpers that are part of running or validating the Hub implementation.

The standalone `dp-web4/4-hub` repository is a mirror of the authoritative Hub implementation in this repository. It is not a second development authority.

## What may remain private

A private coordination repository such as `private-context` may retain material that is genuinely fleet-specific or should not be public, including:

- machine names, addresses, topology and deployment details;
- incident traces and operational receipts;
- private test vectors or data containing fleet-specific context;
- measurements tied to particular machines or members;
- deployment/recovery notes and handoffs;
- research notes whose value is evidentiary/contextual rather than functional.

Private evidence may point to public functionality. It should not become the only executable implementation of a reusable mechanism.

## Promotion rule

When executable functionality is discovered or prototyped in a context/operations repository:

1. Decide whether the mechanism has generic merit.
2. If it does, move/promote the implementation and generic tests into the correct functional repository.
3. Keep only fleet-private evidence/context in the private repository, with a link to the canonical implementation.
4. Retire the executable duplicate so authority cannot drift.
5. If the mechanism does not have generic merit, retire it rather than hardening a private accidental implementation.

For Hub-related work, the destination is normally `dp-web4/web4`.

## Test boundary

Generic behavior must be testable publicly with generic fixtures. Fleet-private data may supplement those tests, but public correctness must not depend on access to private-context.

A useful split is:

- **Web4:** executable mechanism + generic regression/conformance suite.
- **private-context:** private fleet evidence that motivated or additionally exercises the mechanism.

Cross-platform support follows the same rule: if Hub functionality is expected to operate or be tested on supported fleet platforms, the portability mechanism belongs beside the Hub implementation/tests, not as ad-hoc fallbacks scattered through private operational copies.

## Current migration: `private-context/hub-mesh`

The executable `hub-mesh` implementation and its generic tests currently present in `private-context` are historical placement debt. They should be evaluated and migrated as follows:

- functionality with continuing merit → Web4/Hub;
- generic tests/fixtures → Web4 alongside that functionality;
- fleet-private test data, incidents, topology and measurements → remain in private-context;
- executable private copy → retire after migration and leave a pointer/receipt.

Until migration is complete, changes in the private copy must not establish a competing protocol or implementation authority.

Migration tracker: [Web4 #894](https://github.com/dp-web4/web4/issues/894).

## Why

Repository placement is part of governance. Multiple executable authorities invite silent drift, contradictory fixes, and evidence that no longer corresponds to the implementation it claims to test.

The boundary is therefore simple:

> **Functionality belongs where functionality lives. Context belongs in context. Evidence may be private; the generic mechanism should not be.**
