# PRD — Hub LCT Identity Convergence

**Status:** Proposed  
**Date:** 2026-10-03  
**Issues:** [web4#874](https://github.com/dp-web4/web4/issues/874), [web4#875](https://github.com/dp-web4/web4/issues/875)  
**Parent note:** [LCT ecosystem convergence](../../docs/designs/lct-ecosystem-convergence-2026-10-03.md)

## 1. Problem

Hub uses UUIDs as durable member/routing identifiers and historically names them as LCTs.

That was sufficient when membership identity was the highest available layer. It is now semantically ambiguous because the same system also has a registry of real key-derived Web4 LCT documents.

A member UUID with a pinned signing key is authenticated membership evidence. It is not automatically the entity's canonical Web4 presence.

## 2. Target model

```text
HubMemberId(UUID)
      |
      +---- compatibility name/roster
      |
      v
CanonicalLctId(lct:web4:mb32:b...)
      |
      v
RegistryEntry.document
      |
      +-- binding proof
      +-- operational-key vouchers
      +-- MRH
      +-- citizenship references
      +-- lifecycle evidence
```

HubMemberId remains stable across LCT key rotation.

CanonicalLctId changes when the binding key changes and continuity is carried by lineage/subject evidence.

## 3. Functional requirements

### FR1 — distinct internal types

Introduce distinct type wrappers or equivalent strong boundaries:

```rust
struct HubMemberId(Uuid);
struct CanonicalLctId(String);
```

Compatibility APIs may continue to serialize historical field names initially.

New code and documentation must not call a UUID a canonical LCT.

### FR2 — member-to-presence mapping

Add a witnessed mapping:

```text
HubMemberId -> CanonicalLctId
```

Requirements:
- zero-or-one current mapping;
- old mappings/history preserved;
- rotation can replace current canonical id without changing member id;
- unknown old members remain explicitly unmapped.

### FR3 — one resolver

Provide one resolver for:
- HubMemberId;
- CanonicalLctId;
- verified legacy alias;
- human roster name at the outer UI boundary.

Return:
- resolved registry entry;
- source/evidence of resolution;
- unresolved/ambiguous outcome.

No caller independently parses identifier namespaces.

### FR4 — operational signer resolution

Preferred verification:

```text
reference -> canonical LCT -> vouched operational key -> envelope signature
```

Current UUID->pubkey member pins remain a compatibility fallback until migrated.

The fallback must stay distinguishable in evidence so a relying party can tell "member-key pin" from "canonical LCT-vouched operational key".

### FR5 — lifecycle evidence

Before new consequential actions, resolution must expose the current lifecycle evidence attached to the canonical LCT.

Unknown state is not "active".

The resolver returns evidence; Hub law decides whether the requested act is allowed.

### FR6 — relationship projection

Project existing witnessed ledger facts into MRH-compatible edges:
- citizenship/membership;
- role occupancy;
- pairing/introduction;
- witnessing.

The ledger remains authoritative. MRH is a projection/resolution surface, not a second editable relationship store.

### FR7 — compatibility

No flag day.

Pin:
- old UUID-only member authentication unchanged;
- canonical member authentication through vouched operational key;
- legacy alias resolves to one canonical LCT;
- forged/ambiguous alias refuses resolution;
- rotation preserves HubMemberId and history;
- old ledger replay remains valid.

## 4. Non-goals

- deleting member UUIDs;
- rewriting old events;
- making low-assurance identities invalid;
- embedding one global T3/V3 score in each LCT;
- deciding canonical lifecycle vocabulary inside Hub;
- implementing hardware assurance independently of web4#730.

## 5. Dependency decisions

Upstream:
- public-key-derived canonical ID correction from web4#819 or successor;
- lifecycle canonical ruling from web4#874;
- hardware evidence from web4#730.

Parallel:
- hestia#1202;
- SAGE#340.

## 6. Suggested delivery slices

### Slice A — vocabulary and types

No wire behavior change:
- `HubMemberId`;
- `CanonicalLctId`;
- comments/docs/API adapters;
- tests proving accidental interchange requires explicit conversion.

### Slice B — mapping and resolver

- witnessed member->canonical mapping;
- resolver;
- legacy alias support;
- admin/diagnostic visibility.

### Slice C — signer convergence

- resolve vouched operational key;
- evidence-tag compatibility UUID pin fallback;
- parity tests.

### Slice D — lifecycle + MRH projection

- lifecycle evidence surfaced to gate;
- ledger->MRH projection;
- rotation tests.

## 7. Done

Done means Hub can answer, without guessing:

> "This request came through Hub member X; X resolves to canonical presence Y through evidence Z; Y currently presents lifecycle/relationship evidence E."

The law can then decide what that evidence licenses.
